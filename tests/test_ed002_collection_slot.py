"""Offline pilot lifecycle and static job tests, with invented child receipts."""
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import socket
import subprocess
from zoneinfo import ZoneInfo

import pytest

from scripts.research import run_ed002_collection_slot as slot


H, M = slot.HOUR, slot.MINUTE
START = 2000*H+5*M


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args,**kwargs):
        raise AssertionError("test attempted network or external process")
    for name in ("socket","create_connection","getaddrinfo"):
        monkeypatch.setattr(socket,name,refuse)
    for name in ("Popen","run","call","check_call","check_output"):
        monkeypatch.setattr(subprocess,name,refuse)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def prepared(tmp_path):
    for name in slot.INPUTS:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(slot.ROOT/name,target)
    name="research/ed002_public_inputs/plans/invented.json"
    plan=json.loads((slot.ROOT/"research/ed002_public_inputs/plans/feasibility_20261028.json").read_bytes())
    write(tmp_path/name,plan)
    policy={"schema":"ed002-local-pilot-v1","enabled":True,"pilot_id":"invented",
        "start_ms":START,"end_ms":START+slot.DAY,"max_slots":48,"max_lateness_ms":120000,
        "capture_plan":name,"inputs_sha256":{n:hashlib.sha256((tmp_path/n).read_bytes()).hexdigest()
            for n in [*slot.INPUTS,name]}}
    return tmp_path,policy


class FakeChild:
    pid=654321
    def __init__(self,mode):
        self.mode,self.waits,self.alive=mode,[],mode in ("timeout","interrupt","exception","cleanup_failed")
    def wait(self,timeout):
        self.waits.append(timeout)
        if len(self.waits)==1:
            if self.mode in ("timeout","cleanup_failed"):raise subprocess.TimeoutExpired("invented",timeout)
            if self.mode=="interrupt":raise KeyboardInterrupt
            if self.mode=="exception":raise RuntimeError("sensitive exception must never be logged")
        return 2 if self.mode=="failed" else 0


def run(prepared,*,mode="success",now=START+1,execute=True,free=100*1024*1024):
    root,policy=prepared
    children,calls,kills=[],[],[]
    def popen(command,**kwargs):
        calls.append((command,kwargs));child=FakeChild(mode);children.append(child)
        output=Path(command[command.index("--output")+1])
        write(output/"manifest.json",{"status":"COMPLETE" if mode!="failed" else "INCOMPLETE",
            "owned_worker_cleanup_failed":False,"scoring_authorized":False,
            "transport_calls_started":26,"stored_payload_bytes":1000})
        return child
    def exists(pid):
        assert children and pid==children[0].pid
        return children[0].alive
    def kill(pid,sig):
        assert pid==children[0].pid and sig==signal.SIGKILL
        kills.append(pid)
        if mode=="cleanup_failed":raise PermissionError("do not log")
        children[0].alive=False
    result=slot.run_slot(policy,root=root,execute=execute,wall_ms=lambda:now,
        popen=popen,group_exists=exists,kill_group=kill,disk_free=lambda _:free)
    return result,calls,children,kills


def pilot_dir(prepared):
    root,policy=prepared
    return root/"research/ed002_public_inputs/pilots"/policy["pilot_id"]


def test_default_preview_and_disabled_execute_never_create_pilot(prepared):
    result,calls,_,_=run(prepared,execute=False)
    assert result["dry_run"] and result["max_public_gets"]==1296 and result["scheduled_slots"]==48
    assert not calls and not pilot_dir(prepared).exists()
    prepared[1].update(enabled=False,start_ms=None,end_ms=None)
    result,calls,_,_=run(prepared)
    assert result["reason"]=="pilot_disabled" and not calls and not pilot_dir(prepared).exists()


def test_success_uses_one_clean_isolated_cli_and_preserves_slot(prepared):
    result,calls,children,kills=run(prepared)
    assert result["status"]=="COMPLETE" and result["collection_started"]
    assert len(calls)==1 and not kills and children[0].waits==[140,5]
    cmd,kwargs=calls[0]
    assert cmd[1:3]==["-I","-B"] and cmd[-1]=="--execute"
    assert kwargs["env"]==slot.CLEAN_ENV and kwargs["stdin"]==subprocess.DEVNULL
    assert kwargs["start_new_session"] is True and kwargs["close_fds"] is True
    directory=pilot_dir(prepared)/("slot_"+str(START))
    assert slot.read_json(directory/"RESULT.json")==result
    before=(directory/"RESULT.json").read_bytes()
    again,calls,_,_=run(prepared)
    assert again["reason"]=="slot_already_claimed" and not calls
    assert (directory/"RESULT.json").read_bytes()==before


@pytest.mark.parametrize("now,reason",[(START-1,"pilot_not_started"),
    (START+slot.DAY,"pilot_expired"),(START+120001,"off_schedule_or_late"),
    (START+slot.DAY-30*M+120001,"off_schedule_or_late")])
def test_outside_fixed_opportunities_never_launches(prepared,now,reason):
    result,calls,_,_=run(prepared,now=now)
    assert result["reason"]==reason and not calls
    assert not list(pilot_dir(prepared).glob("slot_*"))


def test_lateness_boundary_is_inclusive(prepared):
    assert run(prepared,now=START+120000)[0]["status"]=="COMPLETE"


@pytest.mark.parametrize("mode,reason",[("timeout","owned_controller_timeout"),
    ("interrupt","operator_interrupt"),("exception","controller_failure"),
    ("failed","capture_failed_or_unreadable"),("cleanup_failed","owned_group_cleanup_failed")])
def test_child_failures_have_bounded_owned_cleanup_and_sanitized_receipts(prepared,mode,reason):
    result,calls,children,kills=run(prepared,mode=mode)
    assert result["status"]=="INCOMPLETE" and result["reason"]==reason and len(calls)==1
    assert "sensitive" not in json.dumps(result) and "do not log" not in json.dumps(result)
    assert all(t<=140 for t in children[0].waits)
    if mode in ("timeout","interrupt","exception"):assert kills and children[0].waits[-1]==5
    if mode=="cleanup_failed":
        again,calls,_,_=run(prepared,now=START+30*M)
        assert again["reason"]=="prior_slot_unsettled" and not calls
    else:assert result["owned_group_cleanup_failed"] is False


def test_uncertain_hard_death_blocks_later_slot_even_with_released_lock(prepared):
    directory=pilot_dir(prepared)/("slot_"+str(START));directory.mkdir(parents=True)
    write(directory/"CLAIM.json",{"phase":"invented interruption before final receipt"})
    result,calls,_,_=run(prepared,now=START+30*M)
    assert result["reason"]=="prior_slot_unsettled" and not calls


def test_real_nonblocking_flock_contention_and_reuse_without_unlink(prepared):
    directory=pilot_dir(prepared);directory.mkdir(parents=True)
    path=directory/".lock"
    fd=os.open(path,os.O_CREAT|os.O_RDWR,0o600);inode=path.stat().st_ino
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result,calls,_,_=run(prepared)
        assert result["reason"]=="pilot_busy" and not calls
    finally:os.close(fd)
    assert run(prepared)[0]["status"]=="COMPLETE" and path.stat().st_ino==inode


def test_final_receipt_write_failure_releases_lock_but_blocks_new_acquisition(prepared,monkeypatch):
    original=slot._write
    def fail(path,value):
        if path.name=="RESULT.json":raise OSError("invented full filesystem")
        original(path,value)
    monkeypatch.setattr(slot,"_write",fail)
    with pytest.raises(OSError):run(prepared)
    monkeypatch.setattr(slot,"_write",original)
    result,calls,_,_=run(prepared,now=START+30*M)
    assert result["reason"]=="prior_slot_unsettled" and not calls


def test_low_disk_and_insufficient_expiry_margin_refuse_before_child(prepared):
    result,calls,_,_=run(prepared,free=24*1024*1024-1)
    assert result["reason"]=="insufficient_disk_headroom" and not calls
    prepared[1]["end_ms"]=START+100000
    prepared[1]["pilot_id"]="short"
    result,calls,_,_=run(prepared)
    assert result["reason"]=="insufficient_time_before_expiry" and not calls


@pytest.mark.parametrize("field,value",[("max_slots",49),("max_slots",True),
    ("max_lateness_ms",120001),("enabled",1),("start_ms",True),
    ("end_ms",START+slot.DAY+1),("pilot_id","../outside"),("capture_plan","../outside.json")])
def test_changed_operating_contract_requires_new_design(prepared,field,value):
    prepared[1][field]=value
    with pytest.raises(ValueError):run(prepared)
    assert not pilot_dir(prepared).exists()


@pytest.mark.parametrize("change",["source","plan","added_package","pin_set","symlink"])
def test_pins_and_package_shape_checked_before_import_or_spawn(prepared,change):
    root,policy=prepared
    if change=="source":(root/slot.INPUTS[1]).write_text("raise RuntimeError('must not execute')")
    elif change=="plan":write(root/policy["capture_plan"],{})
    elif change=="added_package":(root/slot.ABSENT_PACKAGES[0]).write_text("raise RuntimeError")
    elif change=="pin_set":policy["inputs_sha256"].pop(slot.INPUTS[0])
    else:
        directory=root/"research/ed002_public_inputs/pilots";directory.mkdir(parents=True)
        (directory/policy["pilot_id"]).symlink_to(root/"config",target_is_directory=True)
    with pytest.raises(ValueError):run(prepared)


def test_calendar_arrays_are_static_and_policy_disabled_in_template(prepared):
    root,policy=prepared;policy.update(enabled=False,start_ms=None,end_ms=None)
    p=root/"research/ed002_public_inputs/plans/draft.json";write(p,policy);digest=hashlib.sha256(p.read_bytes()).hexdigest()
    job=slot.job_template(p,digest,root=root)
    assert plistlib.loads(plistlib.dumps(job))==job
    assert job["StartCalendarInterval"]==[{"Minute":5},{"Minute":35}]
    assert job["RunAtLoad"] is False and job["KeepAlive"] is False
    assert not {"StartInterval","WatchPaths","Sockets","StartOnMount"}&job.keys()
    assert job["ProgramArguments"][1:4]==["-I","-S","-B"]
    assert job["EnvironmentVariables"]==slot.CLEAN_ENV
    assert not pilot_dir(prepared).exists()
    with pytest.raises(ValueError,match="hash"):slot.job_template(p,"0"*64,root=root)


def test_utc_slot_keys_do_not_collapse_the_repeated_DST_hour():
    ny=ZoneInfo("America/New_York")
    times=[datetime(2026,11,1,1,5,tzinfo=ny,fold=i) for i in [0,1]]
    keys=[slot.slot_at(int(t.timestamp()*1000)) for t in times]
    assert keys[1]-keys[0]==H
    assert all(datetime.fromtimestamp(t/1000,timezone.utc).minute==5 for t in keys)
    assert slot.slot_at(2001*H+4*M)==2000*H+35*M


def test_main_checks_policy_digest_and_emits_no_exception_message(prepared,monkeypatch,capsys):
    root,policy=prepared;policy.update(enabled=False,start_ms=None,end_ms=None)
    p=root/"draft.json";write(p,policy)
    assert slot.main(["--policy",str(p),"--policy-sha256","0"*64])==2
    assert json.loads(capsys.readouterr().out)["reason"]=="pilot_preflight_or_receipt_failure"


def test_dispatch_is_rechecked_after_claim_and_before_spawning(prepared):
    root,policy=prepared
    clocks=iter([START+1,START+120001,START+120002])
    def forbidden(*args,**kwargs):raise AssertionError("should not spawn")
    result=slot.run_slot(policy,root=root,execute=True,wall_ms=lambda:next(clocks),popen=forbidden)
    assert result["reason"]=="dispatch_window_lost" and not result["collection_started"]


def test_source_pin_rejects_warmup_profile_in_a_pilot(prepared):
    root,policy=prepared
    plan=root/policy["capture_plan"]
    data=slot.read_json(plan);data["schema"]="ed002-public-warmup-plan-v1";write(plan,data)
    policy["inputs_sha256"][policy["capture_plan"]]=hashlib.sha256(plan.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match="two_completed_hour"):run(prepared)


@pytest.mark.parametrize("raw",['{"a":1,"a":2}', '{"a":NaN}'])
def test_ambiguous_or_nonfinite_policy_json_refused(tmp_path,raw):
    p=tmp_path/"bad.json";p.write_text(raw)
    with pytest.raises(ValueError):slot.read_json(p)
