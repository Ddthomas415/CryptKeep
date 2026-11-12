"""In-memory unit composition only; no systemd, process, network or installs."""
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from services.control import group_a_unit_composition as composition
from services.control.group_a_alert_units import render_group_a_alert_units
from services.control.group_a_quote_routing import render_group_a_quote_routing
from services.control.group_a_systemd_policy import render_group_a_policy


RELEASE = 'frozen42'
USERS = {'service_user':'cbp-ga-paper', 'alert_user':'cbp-ga-alert'}


def synthetic_refs():
    # Attribution fixtures, NOT working backup code or proof of an operating role.
    return {name:hashlib.sha256(('SYNTHETIC source '+name).encode()).hexdigest()
            for name in composition.ENTRYPOINTS}


def build(**kwargs):
    return composition.compose_group_a_units(RELEASE, **USERS,
        runtime_sources=kwargs.pop('runtime_sources', synthetic_refs()), **kwargs)


def test_complete_structural_roster_has_one_start_per_base_and_unchanged_lifecycle():
    result=build()
    policy=render_group_a_policy(RELEASE)
    files=dict(result.files)
    failure=f'cbp-group-a-{RELEASE}-failed@.service'
    base={*policy.services,failure}
    assert len(files)==len(result.files)==45
    assert set(files)==set(dict(policy.files))|base
    assert result.composition_complete is True and result.missing_entrypoints == ()
    assert result.deployment_status == 'INCOMPLETE'
    assert result.stop_argv == policy.stop_argv
    for name,text in policy.files:
        assert files[name] == text
    for name in base:
        starts=re.findall(r'^ExecStart=(.+)$',files[name],re.M)
        assert len(starts)==1
        assert starts[0].startswith('"/usr/bin/env" "-i" ')
    assert len(result.launch_args)==22
    assert dict(result.runtime_source_refs)==synthetic_refs()
    assert build()==result
    with pytest.raises(FrozenInstanceError):
        result.files=()


def test_quote_replacements_and_distinct_users_paths_credentials_preserved():
    result=build()
    files=dict(result.files)
    quote=render_group_a_quote_routing(RELEASE,service_user=USERS['service_user'])
    alert=render_group_a_alert_units(RELEASE,**USERS)
    for name,fragment in (*quote.fragments,*alert.fragments):
        assert files[name].startswith(fragment)
    for name,argv in (*quote.launch_args,*alert.launch_args):
        assert dict(result.launch_args)[name] == argv
    for name in files:
        if name.endswith('-strategy.service') or name.endswith('-paper.service'):
            assert files[name].count('BindReadOnlyPaths=')==1
            assert 'User=cbp-ga-paper\n' in files[name]
            assert 'LoadCredential' not in files[name]
            assert 'UMask=0077\n' in files[name]
    watcher=files[f'cbp-group-a-{RELEASE}-watcher.service']
    terminal=files[f'cbp-group-a-{RELEASE}-failed@.service']
    assert 'User=cbp-ga-alert\n' in watcher+terminal
    assert 'Type=exec\n' in watcher
    assert 'Type=oneshot\n' in terminal
    assert watcher.count('LoadCredential=queue-receipt:')==1
    assert 'queue-receipt' not in terminal
    assert terminal.count('"%i"')==1
    assert all('"%i"' not in text for name,text in files.items() if name!=f'cbp-group-a-{RELEASE}-failed@.service')


@pytest.mark.parametrize('absent', composition.ENTRYPOINTS)
def test_missing_source_returns_no_partial_units_or_target(absent):
    refs=synthetic_refs()
    refs.pop(absent)
    result=build(runtime_sources=refs)
    assert result.files == result.launch_args == ()
    assert result.composition_complete is False
    assert result.deployment_status == 'INCOMPLETE'
    assert result.missing_entrypoints == (absent,)


def test_four_existing_entrypoint_refs_do_not_hide_the_missing_backup():
    refs=synthetic_refs()
    refs.pop('scripts/run_group_a_backup.py')
    result=build(runtime_sources=refs)
    assert result.missing_entrypoints == ('scripts/run_group_a_backup.py',)
    assert not result.files and not result.composition_complete


@pytest.mark.parametrize('bad',[None,True,1,'a'*63,'G'*64,'a'*64+'\n',{'sha256':'a'*64}])
def test_invalid_source_reference_is_rejected_without_echo(bad):
    refs=synthetic_refs()
    refs[composition.ENTRYPOINTS[0]]=bad
    with pytest.raises(ValueError,match='source_reference'):
        build(runtime_sources=refs)


@pytest.mark.parametrize('refs',[None,[],(),True,'secret'])
def test_source_mapping_shape_rejected(refs):
    with pytest.raises(ValueError,match='source_reference'):
        build(runtime_sources=refs)


def test_input_mutation_cannot_rewrite_returned_source_identity():
    refs=synthetic_refs()
    result=build(runtime_sources=refs)
    refs.clear()
    assert len(result.runtime_source_refs)==5


@pytest.mark.parametrize('fragment',[
    '[Service]\nExecStart=/bin/false\n', '[Service]\nExecStartPre=/bin/false\n',
    '[Service]\n ExecStop = /bin/false\n', '[Service]\nexecstart=/bin/false\n',
    '[Service]\n[Install]\nWantedBy=default.target\n', '[Unit]\nDescription=x\n',
    '[Service]\nUser=x\x00\n', '[Service]\nUser=x\r\n',
])
def test_inherited_exec_hooks_or_wrong_section_refused(fragment):
    with pytest.raises(ValueError,match='fragment'):
        composition._with_start(fragment,('/usr/bin/env','-i','/bin/false'))


def test_duplicate_fragment_or_roster_drift_is_not_overwritten(monkeypatch):
    original=composition.render_group_a_quote_routing
    def duplicate(*args,**kwargs):
        result=original(*args,**kwargs)
        return replace(result,fragments=(*result.fragments,result.fragments[0]))
    monkeypatch.setattr(composition,'render_group_a_quote_routing',duplicate)
    with pytest.raises(ValueError,match='roster'):
        build()


def test_missing_launcher_and_unexpected_member_refused(monkeypatch):
    original=composition.render_group_a_quote_routing
    def missing(*args,**kwargs):
        result=original(*args,**kwargs)
        return replace(result,launch_args=result.launch_args[:-1])
    monkeypatch.setattr(composition,'render_group_a_quote_routing',missing)
    with pytest.raises(ValueError,match='roster'):
        build()


@pytest.mark.parametrize('value',['\nExecStart=x','\t','\x00','\x7f','coin\u00e9',';','/bin/true; /bin/false'])
def test_unsafe_argument_refused(value):
    with pytest.raises(ValueError,match='argument'):
        composition._exec_start(('/usr/bin/env','-i',value))


def test_systemd_escaping_is_not_shell_quoting_or_expansion():
    result=composition._exec_start(('/usr/bin/env','-i','a b','',r'a\b','a"b','$HOME','${X}','%n','%i'))
    assert result == 'ExecStart="/usr/bin/env" "-i" "a b" "" "a\\\\b" "a\\"b" "$$HOME" "$${X}" "%%n" "%%i"\n'
    assert composition._exec_start(('/usr/bin/env','-i','%i'),instance=True).endswith(' "%i"\n')
    assert '"%%i"' in composition._exec_start(('/usr/bin/env','-i','%i','x'),instance=True)


@pytest.mark.parametrize('argv',[(),('/bin/sh','-c','true'),('/usr/bin/env','PATH=/bin'),['/usr/bin/env','-i'],('/usr/bin/env','-i',True)])
def test_missing_environment_clear_or_invalid_argv_refused(argv):
    with pytest.raises(ValueError,match='argument'):
        composition._exec_start(argv)


def test_other_release_keeps_all_files_launches_and_stop_scope_disjoint():
    first=build()
    second=composition.compose_group_a_units('frozen43',**USERS,runtime_sources=synthetic_refs())
    assert set(dict(first.files)).isdisjoint(dict(second.files))
    assert set(first.stop_argv[4:]).isdisjoint(second.stop_argv[4:])


def test_equal_alert_and_paper_identity_rejected_even_with_missing_sources():
    with pytest.raises(ValueError,match='distinct'):
        composition.compose_group_a_units(RELEASE,service_user='cbp-ga-paper',
            alert_user='cbp-ga-paper',runtime_sources={})


def test_fresh_import_only_reads_python_sources_and_composition_does_no_io():
    root=Path(__file__).resolve().parents[1]
    code='''import json,os,sys
from pathlib import Path
root=Path(sys.argv[1])
sys.path.insert(0,str(root))
phase='import'
reads=0
def audit(event,args):
    global reads
    if event in ('os.mkdir','os.remove','os.rename','os.rmdir','os.chmod',
                 'subprocess.Popen','os.system','os.fork','socket.__new__',
                 'socket.connect','socket.bind'):
        raise RuntimeError('external_operation_refused')
    if event=='open':
        name,mode,flags=args
        if phase=='compose' or type(name) is not str or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            raise RuntimeError('file_operation_refused')
        path=Path(name)
        if path.suffix not in ('.py','.pyc'):
            raise RuntimeError('non_source_read_refused')
        reads+=1
sys.addaudithook(audit)
from services.control.group_a_unit_composition import compose_group_a_units,ENTRYPOINTS
phase='compose'
result=compose_group_a_units('frozen42',service_user='cbp-ga-paper',alert_user='cbp-ga-alert',
                            runtime_sources={name:'a'*64 for name in ENTRYPOINTS})
assert len(result.files)==45 and result.deployment_status=='INCOMPLETE'
print(json.dumps({'source_reads':reads,'files':len(result.files),'deployment':result.deployment_status}))
'''
    result=subprocess.run([sys.executable,'-I','-B','-c',code,str(root)],
        capture_output=True,timeout=10)
    assert result.returncode==0,result.stderr.decode()
    proof=json.loads(result.stdout)
    assert proof['source_reads']>0 and proof['files']==45
