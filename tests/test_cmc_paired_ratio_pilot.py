import copy
import json

import pytest

from scripts.research import run_cmc_paired_ratio_pilot as pilot


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "OUT", tmp_path)
    monkeypatch.setattr(pilot, "identity", lambda: {"test_identity": "locked",
        "candidate":"c"*64,"contract":"d"*64,"numpy":"test","python":"test"})
    return tmp_path


def interval_result(positive=False):
    return {"status": "CANDIDATE_INTERVAL", "positive": positive,
            "candidate_result": {"status": "CANDIDATE_INTERVAL",
                "interval": [1.,2.] if positive else [-1.,1.], "scoring_authorized": False}}


def part(model="iid",days=90,trial=0,result=None):
    result=interval_result() if result is None else copy.deepcopy(result)
    if "candidate_result" in result:
        inner=result["candidate_result"]
        ident=pilot.identity()
        inner.update(calendar_days=days,block_length=pilot.candidate.block_length(days),
            replicates=2000,seed=pilot.models.stream_seed(pilot.STAGE,model,days,0,trial,"bootstrap",allowed=(pilot.STAGE,)),
            eligible_events=days+(19 if model=="shared_unequal" else 0),
            contract_sha256=ident["contract"],implementation_sha256=ident["candidate"],
            numpy_version=ident["numpy"],python_version=ident["python"],input_sha256="a"*64,
            event_weighted_mean=0.,qualification="UNVALIDATED_CONDITIONAL_METHOD_CANDIDATE",
            completed_replicates=2000,reason="not_statistical_certification")
    return {"identity":pilot.identity(),"stage":pilot.STAGE,"model":model,
            "days":days,"trial":trial,"mean_index":0,"seconds":.01,
            "result":result,"scoring_authorized":False}


def approve(root):
    pilot.write_new(root/"runner_review.json",{"identity":pilot.identity(),"status":"ACCEPTED_WITH_RISK"})


def budget(root):
    durations=[{"model":m,"days":n,"seconds":.01} for m in pilot.models.SUPPORTED for n in pilot.LENGTHS]
    pilot.write_new(root/"benchmark.json",{"identity":pilot.identity(),"stage":pilot.BENCH,
        "status":"BENCHMARK_COMPLETE","durations":durations,"unique_stream_seeds":2232,
        "projected_seconds":40*sum(r["seconds"] for r in durations)+10,
        "within_budget":True,"scoring_authorized":False})
    pilot.write_new(root/"budget_review.json",{"identity":{"identity":pilot.identity(),
        "benchmark_sha256":pilot.digest(root/"benchmark.json")},"status":"ACCEPTED"})


def grid(root, positives=0):
    for model,days,trial in sorted(pilot.EXPECTED):
        r = interval_result(trial<positives) if model in pilot.models.SUPPORTED else {"status":"REFUSED","reason":"registered_refusal_model_policy"}
        pilot.write_new(root/"trials"/f"{model}_{days}_{trial}.json",part(model,days,trial,r))


def test_stream_manifest_unique():
    assert pilot.stream_audit()==2232
    old=pilot.models.stream_seed("v3_confirmation","iid",90,0,0,"bootstrap")
    new=pilot.models.stream_seed(pilot.STAGE,"iid",90,0,0,"bootstrap",allowed=(pilot.STAGE,))
    assert old!=new


def test_new_file_never_overwrites(isolated):
    path=isolated/"test.json"
    pilot.write_new(path,{"original":True})
    with pytest.raises(FileExistsError):pilot.write_new(path,{"original":False})
    assert json.loads(path.read_bytes())=={"original":True}


@pytest.mark.parametrize("damage",["identity","stage","days","trial","interval","positive","seconds"])
def test_part_validation(isolated,damage):
    p=part()
    if damage=="identity":p["identity"]={}
    if damage=="stage":p["stage"]="v3_confirmation"
    if damage=="days":p["days"]=90.0
    if damage=="trial":p["trial"]=True
    if damage=="interval":p["result"]["candidate_result"]["interval"]=[float("nan"),1.]
    if damage=="positive":p["result"]["positive"]=True
    if damage=="seconds":p["seconds"]=float("inf")
    with pytest.raises(ValueError):pilot.validate(p)


def test_requires_runner_review(isolated):
    with pytest.raises(FileNotFoundError):pilot.benchmark()


def test_budget_and_no_generation_on_complete_resume(isolated,monkeypatch):
    approve(isolated)
    budget(isolated)
    grid(isolated)
    monkeypatch.setattr(pilot,"evaluate",lambda *args:pytest.fail("must not repeat histories"))
    assert pilot.pilot()["status"]=="SMALL_PILOT_ONLY"
    assert pilot.summarize()["histories"]==360


def test_screen_failure_not_hidden(isolated):
    approve(isolated)
    budget(isolated)
    grid(isolated,positives=3)
    result=pilot.summarize()
    assert result["status"]=="PILOT_SCREEN_FAILED"
    assert sum(c["flagged"] for c in result["cells"])==12
    assert result["scoring_authorized"] is False


def test_incomplete_grid_refuses(isolated):
    approve(isolated)
    budget(isolated)
    pilot.write_new(isolated/"trials/iid_90_0.json",part())
    with pytest.raises(ValueError,match="incomplete"):pilot.summarize()


def test_refusal_model_no_candidate_call(monkeypatch):
    monkeypatch.setattr(pilot.candidate,"candidate_interval",lambda *args,**kwargs:pytest.fail("policy refuses"))
    assert pilot.evaluate(pilot.BENCH,"sparse",90,0)["status"]=="REFUSED"


def test_shared_unequal_adapter_preserves_event_weights(monkeypatch):
    def check(data,**kwargs):
        assert data["eligible_events"]==109
        assert data["calendar"][45]["pair"][1]==20
        return interval_result()["candidate_result"]
    monkeypatch.setattr(pilot.candidate,"candidate_interval",check)
    assert pilot.evaluate(pilot.BENCH,"shared_unequal",90,0)["status"]=="CANDIDATE_INTERVAL"


@pytest.mark.parametrize("key",["seed","calendar_days","replicates","completed_replicates", "input_sha256", "implementation_sha256"])
def test_inner_identity_missing_refuses(isolated,key):
    p=part()
    p["result"]["candidate_result"].pop(key)
    with pytest.raises(ValueError):pilot.validate(p)


def test_boolean_mean_index_refuses(isolated):
    p=part();p["mean_index"]=False
    with pytest.raises(ValueError):pilot.validate(p)


def test_degenerate_requires_interval(isolated):
    p=part();p["result"]={"status":"DEGENERATE"}
    with pytest.raises((ValueError,KeyError)):pilot.validate(p)


def test_benchmark_resume_without_generation(isolated,monkeypatch):
    approve(isolated);budget(isolated)
    monkeypatch.setattr(pilot,"evaluate",lambda *args:pytest.fail("benchmark repeated"))
    assert pilot.benchmark()["status"]=="BENCHMARK_COMPLETE"


def test_incomplete_budget_receipt_refuses(isolated):
    with pytest.raises(ValueError):
        pilot.validate_benchmark({"identity":pilot.identity(),"within_budget":True})


def test_failed_attempt_persisted_and_not_retried(isolated,monkeypatch):
    approve(isolated);budget(isolated)
    def failed(*args):raise RuntimeError("injected failure")
    monkeypatch.setattr(pilot,"evaluate",failed)
    assert pilot.pilot()["status"]=="PILOT_ABORTED_FAILURE"
    saved=pilot.parts()
    assert len(saved)==1 and next(iter(saved.values()))["seconds"]>=0
    monkeypatch.setattr(pilot,"evaluate",lambda *args:pytest.fail("failure retried"))
    assert pilot.pilot()["status"]=="PILOT_ABORTED_FAILURE"


def test_aggregation_requires_budget_review(isolated):
    approve(isolated)
    with pytest.raises(FileNotFoundError):pilot.summarize()


def test_post_replicate_overflow_refusal_is_valid(isolated):
    p=part()
    p["result"]["status"]="INCOMPLETE"
    p["result"]["positive"]=False
    p["result"]["candidate_result"].update(status="INCOMPLETE",interval=None,
        completed_replicates=2000,reason="nonfinite interval")
    assert pilot.validate(p)==("iid",90,0)
