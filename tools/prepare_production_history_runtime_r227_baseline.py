from pathlib import Path
import copy,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r115';W=R/'work/addsign-history-r180/production-module-r208'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert P.exists()and not(C/'r115').exists()and not(P/'history-runtime-scope.json').exists()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()and J(W/'support-test-result.json')['passed']
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
model=J(W/'module-pins.json');q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');original_async=copy.deepcopy(release['platformAsyncRequestMetadata'])
paths={'tools/serve_original_server_release.py':W/'serve_original_server_release.py','tools/original_public_test_update.py':R/'Application/tools/original_public_test_update_r36_20261103_r2.py','tools/original_native_history_release_support.py':W/'original_native_history_release_support.py','payload/platform/run-template/own-before-addsign-history.jar':W/'own-before-addsign-history.jar','payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class':W/'launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class'}
before={n:(A/n).read_bytes()for n in ['tools/serve_original_server_release.py','tools/original_public_test_update.py','private/server-configuration.json','payload-manifest.json','release-manifest.json']}
newpaths=[n for n in paths if n not in before];assert len(newpaths)==3 and all(not(A/n).exists()for n in newpaths)
after={n:p.read_bytes()for n,p in paths.items()};after['private/server-configuration.json']=before['private/server-configuration.json']
for n,pin in model['contract']['files'].items():assert hashlib.sha256(after[n]).hexdigest()==pin['sha256']and len(after[n])==pin['bytes'];q['files'][n]=pin
after['payload-manifest.json']=enc(q);release['nativeBeforeAddsignOpinionHistory']=model['contract'];release['payloadManifestSHA256']=hashlib.sha256(after['payload-manifest.json']).hexdigest()
for n in paths:
 if n.startswith('tools/'):release['controllerFiles'][n]=hashlib.sha256(after[n]).hexdigest()
assert release['platformAsyncRequestMetadata']==original_async and len(release['controllerFiles'])==21
after['release-manifest.json']=enc(release);stock=J(P/'temporary-synthetic-config-scope.json')
for n,pin in stock['files'].items():assert hashlib.sha256(before[n]).hexdigest()==pin['afterSHA256']
for n,b in before.items():p=P/'history-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
scope={'onlyOwnedSyntheticG':True,'oldFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in before.items()},'newFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in after.items()},'newPaths':newpaths,'privateConfigurationBytesChangedByHistory':False,'originalAsyncDescriptorAndHelperAndArchivesKept':True,'originalAuthObservationAndCallbackUnchanged':True,'mustRestoreAfterActualDescendantsZero':True}
(P/'history-runtime-scope.json').write_bytes(enc(scope))
for n,b in after.items():
 p=A/n;assert p.resolve()==p
 for parent in [p.parent,*p.parents]:
  if parent.exists():assert not parent.is_symlink()and not getattr(parent.lstat(),'st_file_attributes',0)&0x400
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.is_file()and not p.lstat().st_file_attributes&0x400;p.unlink()
 p.write_bytes(b)
for n,pin in original_async['files'].items():assert sha(A/n)==pin['sha256']
assert (A/'private/server-configuration.json').read_bytes()==before['private/server-configuration.json']
baseline=J(P/'controller-fixture-ready.json');baseline.update(releaseSHA256=sha(A/'release-manifest.json'),controllerSHA256=sha(A/'tools/serve_original_server_release.py'),updaterSHA256=sha(A/'tools/original_public_test_update.py'),temporaryOwnedSeparateNativeHistoryModule=True);(P/'controller-fixture-ready.json').write_bytes(enc(baseline))
print(json.dumps({'prepared':True,'onlyOwnedSyntheticG':True,'separateHistoryArchiveAndLauncher':True,'originalAsyncAuthAndPrivateConfigurationKept':True,'newOwnedPaths':3,'restoreRequiredAfterNormalStop':True}))
