from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);o=p.parse_args();assert __import__('re').fullmatch('r[1-9][0-9]{0,2}',o.attempt);C=R/'work/event_delivery_consistency_20261030/full-controller-r152';P=C/('prepared-'+o.attempt);J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();scope=J(P/'temporary-synthetic-config-scope.json');assert scope['onlyOwnedG']and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
attempt=C/o.attempt
if(attempt/'controller-started.json').exists():
 terminal=J(attempt/'controller-terminal.json');assert terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed']
 if terminal['exitCode']!=0:
  assert sha(A/'tools/serve_original_server_release.py')==J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['controllerSHA256'];assert terminal['exitCode']==1;log=(attempt/'controller.private.log').read_text(encoding='utf-8');assert 'line 129, in main'in log and '1<=a.qa_seconds<=600'in log and log.rstrip().endswith('AssertionError');pid=J(attempt/'controller-started.json')['pid'];current=J(A/'UserData/OriginalServer/current-run.json');assert current['controllerPID']!=pid;assert not any(J(p).get('controllerPID')==pid for p in(A/'UserData/OriginalServer/runs').glob('*/receipt.json'))
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { $cmd=($_.CommandLine -replace '\\\\','/').ToLowerInvariant(); $cmd.Contains('d:/project/zhumadian/_g/application') -or $cmd.Contains('"+attempt.as_posix().lower()+"') } | Measure-Object).Count";s=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert s.returncode==0 and s.stdout.decode('utf-8-sig').strip()=='0';bodies={}
for name,pin in scope['files'].items():
 f=A/name;b=P/'before'/name;assert f.resolve()==f and b.resolve()==b and not f.is_symlink()and not b.is_symlink()and not f.lstat().st_file_attributes&0x400 and not b.lstat().st_file_attributes&0x400;assert sha(f)in[pin['beforeSHA256'],pin['afterSHA256']]and sha(b)==pin['beforeSHA256'];bodies[name]=b.read_bytes()
for name,raw in bodies.items():
 f=A/name
 if sha(f)==scope['files'][name]['beforeSHA256']:continue
 temp=f.with_name(f.name+'.owned-r152-restore.tmp');assert not temp.exists();temp.write_bytes(raw);os.replace(temp,f)
assert all(sha(A/name)==pin['beforeSHA256']for name,pin in scope['files'].items());proof={'passed':True,'onlyOwnFakeConfigurationAndItsManifestPinsRestored':True,'exactOriginalBytesRestored':True,'activeOwnedProcesses':0,'originalOrProtectedUserDataOrR30ScopeTouched':False,'forceTerminationUsed':False};(P/'configuration-restored.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
