from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r91';W=R/'work/addsign-history-r180/runtime-module-r191';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert P.exists()and not(C/'r91').exists()and not(P/'history-runtime-scope.json').exists()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
check=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert check.returncode==0 and check.stdout.decode('utf-8-sig').strip()=='0'
model=J(W/'module-pins.json');jar='payload/platform/run-template/own-platform-async-request.jar';helper='tools/original_platform_async_release_support.py';updater='tools/original_public_test_update.py';names=[jar,helper,updater,'private/server-configuration.json','payload-manifest.json','release-manifest.json'];before={n:(A/n).read_bytes()for n in names}
assert sha(A/jar)==model['oldAsyncModuleSHA256'];assert J(P/'controller-fixture-ready.json')['releaseSHA256']==sha(A/'release-manifest.json')
cfg=json.loads(before['private/server-configuration.json']);name='xnby.platform.history.NativeBeforeAddsignHistoryInitializer';flag='-Down.workflow.before-addsign.history.enabled=true';initializers=cfg['configuration']['platform']['context.initializer.classes'].split(',');assert name not in initializers and not any('workflow.before-addsign.history' in x for x in cfg['platformArguments'])
cfg['configuration']['platform']['context.initializer.classes']=','.join(initializers+[name]);cfg['platformArguments'].insert(0,flag)
after={jar:(W/'own-platform-async-with-before-history.jar').read_bytes(),helper:(W/Path(helper).name).read_bytes(),updater:(W/Path(updater).name).read_bytes(),'private/server-configuration.json':enc(cfg)}
q=json.loads(before['payload-manifest.json'])
for n,b in after.items():
 if n in q['files']:q['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
after['payload-manifest.json']=enc(q);release=json.loads(before['release-manifest.json']);release['platformAsyncRequestMetadata']=model['newAsyncContract'];release['payloadManifestSHA256']=hashlib.sha256(after['payload-manifest.json']).hexdigest()
for n in [helper,updater]:release['controllerFiles'][n]=hashlib.sha256(after[n]).hexdigest()
after['release-manifest.json']=enc(release);stock=J(P/'temporary-synthetic-config-scope.json')
for n,pin in stock['files'].items():assert hashlib.sha256(before[n]).hexdigest()==pin['afterSHA256']
for n,b in before.items():p=P/'history-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
scope={'onlyOwnedSyntheticG':True,'oldFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in before.items()},'newFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in after.items()},'eighteenOtherControllerBytesUnchanged':True,'originalSDKArchiveUnchanged':True,'originalAuthObservationAndCallbackUnchanged':True,'oldAsyncClassBytesUnchanged':True,'onlyOwnInitializerEnableFlagAndExactExtensionPinsChanged':True,'mustRestoreAfterActualDescendantsZero':True}
(P/'history-runtime-scope.json').write_bytes(enc(scope))
for n,b in after.items():p=A/n;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(b)
baseline=J(P/'controller-fixture-ready.json');baseline.update(releaseSHA256=sha(A/'release-manifest.json'),updaterSHA256=sha(A/updater),temporaryOwnedNativeBeforeAddsignHistoryModule=True);(P/'controller-fixture-ready.json').write_bytes(enc(baseline))
print(json.dumps({'prepared':True,'onlyOwnedAsyncExtensionAndExactDeclarationPinsChanged':True,'originalAuthObservationAndCallbackUnchanged':True,'restoreRequiredAfterNormalStop':True}))
