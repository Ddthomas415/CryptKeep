"""Synthetic metadata and local timeout fixtures; no SSH or application imports."""
import importlib.util
import ast
import json
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load('compatibility_values_20261111')
R = load('compatibility_remote_20261111')
PRIOR_TEST = load('test_instrumented_ssh_preflight_20261111')


def fixture():
    base = PRIOR_TEST.fixture_inventory()
    base['checkout_head']['output'] = '580ca31ea983af6452a1e02ab8d4b51645e9b43c\n'
    base['paths'] = [{'path': p, 'present': False} for p in (
        '/srv/cryptkeep', '/srv/cryptkeep/app', '/srv/cryptkeep/releases', '/srv/cryptkeep/state',
        '/var/lib/cryptkeep', '/run/cryptkeep', '/etc/systemd/system')]
    base['paths'][0].update(present=True,uid=1000,gid=1000,mode='0o755',directory=True,
                            symlink=False,available_bytes=123456,available_inodes=234)
    base['selected_unit_properties'] = command('Id=cbp-crypto-edge-collector.service\nLoadState=loaded\nActiveState=active\nUser=cryptkeep\nWorkingDirectory=/srv/cryptkeep/app\n')
    base['checkout_runtime'] = command(json.dumps({'python':'3.12.3 (compiler)', 'sqlite':'3.45.1',
        'executable':'/srv/cryptkeep/app/.venv/bin/python'}))
    base['memory'] = {'MemTotal_bytes':4000000000,'MemAvailable_bytes':2000000000}
    spec = W.profile()
    packages = {'site':'/srv/cryptkeep/app/.venv/lib/python3.12/site-packages',
                'packages':{p:{'version':v} for p,v in [('ccxt','4.5.48'),('pyyaml','6.0.3'),('numpy','2.4.4'),('pytest','9.1.1')]}}
    extra = {'candidate_sha256':W.CANDIDATE_SHA,'release':W.RELEASE,
        'manager':command('systemd 255 (255.4-1ubuntu8)\n'),
        'package_metadata':command(json.dumps(packages)),
        'proposed_units':command('\n\n'.join('Id='+u+'\nLoadState=not-found\nActiveState=inactive' for u in spec['units'])),
        'candidate_paths':[{'path':p,'present':False} for p in spec['paths']],
        'proposed_users':{u:{'present':False} for u in spec['users']},
        'finished_utc':'2026-11-11T14:30:00+00:00'}
    return {'base':base,'compatibility':extra},spec


def command(output):
    return {'exit':0,'output':output,'truncated':False}


def project(value,spec):
    return W.project(json.dumps(value).encode(),spec,W.controller())


def test_pinned_candidate_profile_and_render_compile_only():
    spec = W.profile()
    assert len(spec['units']) == len(set(spec['units'])) == 44
    assert all(W.UNIT.fullmatch(x) for x in spec['units'])
    payload = W.render(spec)
    compile(payload,'synthetic_compile_only','exec')
    assert W.PRIOR_SHA != W.hashlib.sha256(payload).hexdigest()
    assert b'PRIOR_SOURCE=' in payload and W.CANDIDATE_SHA.encode() in payload


def test_retains_only_safe_typed_values():
    value,spec = fixture()
    value['base']['checkout_head']['error'] = 'Bearer secret'
    value['compatibility']['manager']['output'] += 'secret arbitrary version suffix'
    result = project(value,spec)
    safe = result['safe_values']
    assert safe['systemd_version'] == 255
    assert safe['venv_package_metadata']['packages']['ccxt'] == {'version':'4.5.48'}
    assert safe['venv_interpreter'] == {'python':'3.12.3','sqlite':'3.45.1'}
    assert safe['paths']['/srv/cryptkeep']['available_bytes'] == 123456
    assert safe['candidate_paths'][spec['paths'][0]] == {'present':False}
    assert len(safe['proposed_unit_collision_observations']['units']) == 44
    assert result['atomic_inventory'] is False and result['full_runtime_readiness_verified'] is False
    assert 'secret' not in json.dumps(result)


@pytest.mark.parametrize('section',['manager','package_metadata','proposed_units'])
def test_unavailable_and_truncated_commands_stay_unknown(section):
    value,spec = fixture()
    value['compatibility'][section] = {'exit':0,'truncated':True,'output':'Bearer secret'}
    safe = project(value,spec)['safe_values']
    key = {'manager':'systemd_version','package_metadata':'venv_package_metadata','proposed_units':'proposed_unit_collision_observations'}[section]
    assert safe[key] in (None,{'status':'unavailable'})
    assert 'secret' not in json.dumps(safe)


@pytest.mark.parametrize('body',[
    b'{"base":{},"base":{},"compatibility":{}}', b'{"base":NaN,"compatibility":{}}',
    b'{"base":Infinity,"compatibility":{}}', b'Bearer secret', b'{} trailing'])
def test_bad_json_never_returns_remote_text(body):
    with pytest.raises(Exception) as error:
        W.project(body,{},W.controller())
    assert 'secret' not in str(error.value)


@pytest.mark.parametrize('change',[
    lambda x:x['compatibility'].update(extra='secret'),
    lambda x:x['compatibility'].update(candidate_sha256='0'*64),
    lambda x:x['compatibility'].update(release='other'),
    lambda x:x['base']['checkout_head'].update(output='a'*40),
    lambda x:x['compatibility']['candidate_paths'][0].update(present=1),
    lambda x:x['compatibility']['candidate_paths'][0].pop('present'),
    lambda x:x['compatibility']['candidate_paths'][0].update(path='/etc/passwd'),
    lambda x:x['base']['paths'][0].update(uid=True),
    lambda x:x['base']['paths'][0].update(mode='secret'),
    lambda x:x['base']['memory'].update(extra='secret'),
    lambda x:x['compatibility']['proposed_users'].update(root={'present':True}),
    lambda x:x['compatibility']['proposed_users']['cbp-ga-paper'].update(present=True,uid=True,gid=1),
    lambda x:x['compatibility']['proposed_users']['cbp-ga-paper'].update(present=0),
    lambda x:x['compatibility'].update(finished_utc='2026-11-11T14:30:00'),
])
def test_schema_identity_roster_and_type_violations_refused(change):
    value,spec = fixture()
    change(value)
    with pytest.raises(Exception) as error:
        project(value,spec)
    assert 'secret' not in str(error.value)


@pytest.mark.parametrize('output',[
    'Id=cbp-crypto-edge-collector.service\nLoadState=loaded',
    'Id=cbp-crypto-edge-collector.service\nLoadState=loaded\nActiveState=active\nEnvironment=secret',
    'Id=cbp-crypto-edge-collector.service\nId=cbp-crypto-edge-collector.service\nLoadState=loaded\nActiveState=active',
    '', 'Id=other.service\nLoadState=loaded\nActiveState=active'])
def test_unit_minimum_schema_no_environment_or_ambiguity(output):
    with pytest.raises(ValueError):
        W.units(command(output))


def test_unknown_unit_values_are_not_echoed():
    result = W.units(command('Id=cbp-test.service\nLoadState=secret\nActiveState=active\nWorkingDirectory=/tmp/secret\nUser=Bearer secret\n'))
    assert result['units']['cbp-test.service']['LoadState'] is None
    assert 'secret' not in json.dumps(result)


def test_missing_unit_roster_is_not_a_no_collision_claim():
    value,spec = fixture()
    value['compatibility']['proposed_units']['output'] = value['compatibility']['proposed_units']['output'].split('\n\n')[0]
    with pytest.raises(ValueError,match='roster'):
        project(value,spec)


@pytest.mark.parametrize('metadata',[
    {'site':'/tmp/secret','packages':{}},
    {'site':'/srv/cryptkeep/app/.venv/lib/python3.12/site-packages','packages':{'ccxt':{'version':'secret'}}},
    {'site':'/srv/cryptkeep/app/.venv/lib/python3.12/site-packages','packages':{p:{'version':'1.0 secret'} for p in ('ccxt','pyyaml','numpy','pytest')}},
])
def test_package_strings_cannot_reach_receipt(metadata):
    value,spec = fixture()
    value['compatibility']['package_metadata'] = command(json.dumps(metadata))
    with pytest.raises(ValueError) as error:
        project(value,spec)
    assert 'secret' not in str(error.value)


def test_default_does_not_prepare_or_connect(monkeypatch):
    monkeypatch.setattr(W,'controller',lambda:pytest.fail('must not prepare'))
    assert W.run(None)['connection_processes_started'] == 0


def test_existing_receipt_prevents_launch(tmp_path,monkeypatch):
    receipt=tmp_path/'compatibility_attempt_synthetic.json'
    receipt.write_bytes(b'preserve')
    monkeypatch.setattr(W,'HERE',tmp_path)
    ctl={'prepare':lambda:([],b'',None),'_collect':lambda *a,**k:pytest.fail('must not launch')}
    monkeypatch.setattr(W,'controller',lambda:ctl)
    monkeypatch.setattr(W,'profile',lambda:{})
    monkeypatch.setattr(W,'render',lambda _:b'synthetic')
    with pytest.raises(FileExistsError):
        W.run(receipt,execute=True)
    assert receipt.read_bytes() == b'preserve'


def test_expired_deadline_does_not_disarm_timer(monkeypatch):
    monkeypatch.setattr(R.time,'monotonic',lambda:10)
    monkeypatch.setattr(R.signal,'setitimer',lambda *a:pytest.fail('expired must raise'))
    with pytest.raises(TimeoutError):
        R.arm_deadline(9)


@pytest.mark.parametrize('attempted_alarm',[0,70])
def test_old_collector_cannot_cancel_or_extend_deadline(attempted_alarm):
    code=('import importlib.util,time; from types import SimpleNamespace; '
          's=importlib.util.spec_from_file_location("remote",'+repr(str(HERE/'compatibility_remote_20261111.py'))+'); '
          'r=importlib.util.module_from_spec(s); s.loader.exec_module(r); '
          'deadline=time.monotonic()+.15; r.arm_deadline(deadline); '
          'old=SimpleNamespace(alarm=lambda _seconds:r.arm_deadline(deadline)); '
          'time.sleep(.02); old.alarm('+str(attempted_alarm)+'); time.sleep(5)')
    result=subprocess.run([sys.executable,'-I','-S','-B','-c',code],capture_output=True,timeout=2)
    assert result.returncode == -14
    assert not result.stdout and not result.stderr


def test_metadata_reader_rejects_symlinked_directories_and_files(tmp_path):
    tree=ast.parse((HERE/'compatibility_remote_20261111.py').read_text())
    code=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant)
              and isinstance(n.value,str) and n.value.startswith('import json,sys,os,stat'))
    code=code.replace('/srv/cryptkeep/app/.venv/lib/',str(tmp_path)+'/')
    site=tmp_path/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages'
    site.mkdir(parents=True)
    valid=site/'ccxt-4.5.48.dist-info'
    valid.mkdir()
    (valid/'METADATA').write_text('Name: ccxt\nVersion: 4.5.48\n')
    outside=tmp_path/'outside'
    outside.mkdir()
    (outside/'METADATA').write_text('Version: 9.9.9\n')
    (site/'pyyaml-6.0.3.dist-info').symlink_to(outside,target_is_directory=True)
    directory=site/'numpy-2.4.4.dist-info'
    directory.mkdir()
    (directory/'METADATA').symlink_to(outside/'METADATA')
    result=subprocess.run([sys.executable,'-I','-S','-B','-c',code],capture_output=True,timeout=3)
    assert result.returncode == 0
    packages=json.loads(result.stdout)['packages']
    assert packages == {'ccxt':{'version':'4.5.48'},'pyyaml':{'status':'unavailable'},
                        'numpy':{'status':'unavailable'},'pytest':{'status':'absent_at_inspected_site'}}


def test_remote_final_emission_remains_under_timer():
    old=b'def inspect():\n print(\'{"checkout_head":{"output":"base"}}\')\n return 0\n'
    code=('import importlib.util,time,signal; from types import SimpleNamespace; '
          's=importlib.util.spec_from_file_location("remote",'+repr(str(HERE/'compatibility_remote_20261111.py'))+'); '
          'r=importlib.util.module_from_spec(s); s.loader.exec_module(r); '
          'r.PRIOR_SOURCE='+repr(old)+'; r.EXPECTED_BASE="base"; '
          'r.PROFILE={"units":[],"paths":[],"users":[],"candidate_sha256":"synthetic","release":"synthetic"}; '
          'r.subprocess.run=lambda *a,**k:SimpleNamespace(returncode=0,stdout=b"",stderr=b""); '
          'r.arm_deadline=lambda _:signal.setitimer(signal.ITIMER_REAL,.15); '
          'r.print=lambda *_a,**_k:time.sleep(5); r.inspect_compatibility()')
    result=subprocess.run([sys.executable,'-I','-S','-B','-c',code],capture_output=True,timeout=2)
    assert result.returncode == -14
    assert not result.stdout and not result.stderr
