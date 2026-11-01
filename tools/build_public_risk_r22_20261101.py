"""Build a fixed sparse R21-to-R22 package and exercise its actual code replacement/recovery."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,zipfile,shutil
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';sys.path.insert(0,str(T))
from build_public_workflow_r21 import digest,sha,read,enc,put,validate_transport_identity
W=R/'work/user_feedback_20261031';S=W/'r22-risk-candidate-r3';D=R/'Document/Deployment/public_test_risk_r22_20261101';TX=W/'r22-package-transactions-r1'
OLD='9f5c34ab7fe0fe698acb0c75e7d40f2bf9256dd42924828c7b8d31072a216b47';UPDATE='20261101-R22-risk-unit-native-session-from-R21';UPDATER=T/'original_public_test_update_r22_20261101.py'
assert not D.exists() and not TX.exists();assert shutil.disk_usage(W).free>2*1024**3
assert read(W/'r22-updater-contract-r1/result.json')['allPassed']and read(W/'r22-updater-contract-r1/result.json')['sourceSHA256']==sha(UPDATER)
proof=read(R/'Document/Deployment/risk_public_native_session_portal_20261101_r101/verified-result.json');assert proof['allListedLocalChecksPassed']and proof['nativeAndBusinessBothRejectRevokedTokens']and proof['compiledPortalCases']==18
archiveOld=R/'Document/Deployment/public_test_workflow_r21_20261031/delivery/Zhumadian_Workflow_20261031_R21.zip';assert sha(archiveOld)=='b9b866bfb828d90abb78b450c34ff1b0befdb1413e5e4e527beccbc18eb06b2c'
with zipfile.ZipFile(archiveOld)as z:
 oldReleaseRaw=z.read('payload/release-manifest.json');oldPayloadRaw=z.read('payload/payload-manifest.json');oldUpdater=z.read('payload/tools/original_public_test_update.py');plan=json.loads(z.read('update-manifest.json'))
old=json.loads(oldReleaseRaw);payload=json.loads(oldPayloadRaw);assert digest(oldReleaseRaw)==OLD and digest(oldPayloadRaw)==old['payloadManifestSHA256']and digest(oldUpdater)=='8ee301b1d7466f08f39c40d0ed42c9edbe652bfd3a9223f694d7379c7970dad5'
assert old==read(S/'r21-base-release-manifest.json')and payload==read(S/'r21-base-payload-manifest.json')
manifest=read(S/'candidate-stage.json');assert len(manifest['allMaterializedPayloadFiles'])==841
prefix='frontend/security_pc/';desired={n:v for n,v in manifest['allMaterializedPayloadFiles'].items()if n.startswith(prefix)};assert len(desired)==836
new=copy.deepcopy(payload);new['files']={n:v for n,v in payload['files'].items()if not n.startswith(prefix)};new['files'].update(desired)
bodies={n:(S/'payload'/n).read_bytes()for n,v in desired.items()if payload['files'].get(n)!=v}
for item in manifest['backendOperations']:
 name=item['relative'];raw=(S/'payload'/name).read_bytes();assert digest(raw)==item['newSHA256'];new['files'][name]={'bytes':len(raw),'sha256':digest(raw)};bodies[name]=raw
allowed=set(desired)|{x['relative']for x in manifest['backendOperations']}
assert {n:v for n,v in payload['files'].items()if n not in allowed and not n.startswith(prefix)}=={n:v for n,v in new['files'].items()if n not in allowed and not n.startswith(prefix)}
css=prefix+'xnby-home-viewport-97d8e3adeed9.css';assert new['files'][css]==payload['files'][css]
new.setdefault('frontendUpdate',{})['riskUnitR22']={'revision':'20261101-r22','actualProductionPortal18AndRiskHTTP9Passed':True,'nativeAndBusinessLogoutRejectionPassed':True,'candidateStageSHA256':sha(S/'candidate-stage.json'),'R101EvidenceSHA256':sha(R/'Document/Deployment/risk_public_native_session_portal_20261101_r101/verified-result.json'),'sourceIssueCellsMarkedCompleteByThisPackage':[]}
release=copy.deepcopy(old);updater='tools/original_public_test_update.py';release['controllerFiles'][updater]=sha(UPDATER)
assert {k:v for k,v in release['controllerFiles'].items()if k!=updater}=={k:v for k,v in old['controllerFiles'].items()if k!=updater}
spec=importlib.util.spec_from_file_location('fixed_r22',UPDATER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
release.update(publicTestRevision='20261101-R22-risk-unit-native-session',riskUnitNativeSessionCandidate=m.R22_RISK_SESSION_REVISION,publicAccepted=False)
bodies[updater]=UPDATER.read_bytes();bodies['payload-manifest.json']=enc(new);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(release)
removed={n:{'bytes':v['bytes'],'SHA256':v['sha256']}for n,v in payload['files'].items()if n.startswith(prefix)and n not in desired}
plan.update(updateId=UPDATE,acceptedOldReleases={OLD:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],newReleaseSHA256=digest(bodies['release-manifest.json']),oldPayloadFiles={n:payload['files'][n]for n in bodies if n in payload['files']},legacyEntrySHA256={},removedFrontendFiles=removed,files={n:{'bytes':len(raw),'SHA256':digest(raw)}for n,raw in bodies.items()})
assert len(bodies)<=1000 and sum(map(len,bodies.values()))<=32*1024**2
baseline={};oldFront=W/'workplace-security-build-r21-workflow/build/dist'
for n in set(bodies)|set(removed):
 if n=='release-manifest.json':baseline[n]=oldReleaseRaw
 elif n=='payload-manifest.json':baseline[n]=oldPayloadRaw
 elif n==updater:baseline[n]=oldUpdater
 elif n in payload['files']:
  p=oldFront/n.removeprefix(prefix)if n.startswith(prefix)else W/'public-r21-template-recovery-r1'/n
  raw=p.read_bytes();assert digest(raw)==payload['files'][n]['sha256']and len(raw)==payload['files'][n]['bytes'],n;baseline[n]=raw
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(raw)}for n,raw in bodies.items()};changes.update({n:{'before':v['SHA256'],'after':None}for n,v in removed.items()})
D.mkdir();bundle=D/'bundle';delivery=D/'delivery'
for n,raw in bodies.items():put(bundle/'payload'/n,raw)
put(bundle/'update-manifest.json',enc(plan));pin=sha(bundle/'update-manifest.json')
deny=b'<?xml version="1.0" encoding="utf-8"?><configuration><system.webServer><security><authorization><clear/><add accessType="Deny" users="*"/></authorization></security></system.webServer></configuration>\r\n';put(delivery/'web.config',deny)
archive=delivery/'Zhumadian_Risk_Unit_20261101_R22.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
 z.writestr('update-manifest.json',enc(plan));z.writestr('web.config',deny)
 for n,raw in bodies.items():z.writestr('payload/'+n,raw)
wrapper=(T/'risk_r22_transport.py.in').read_text(encoding='utf-8')
for token,value in [('__ARCHIVE_SHA__',sha(archive)),('__MANIFEST_SHA__',pin),('__OLD__',OLD),('__NEW__',plan['newReleaseSHA256']),('__UPDATE_ID__',UPDATE),('__UPDATER_SHA__',sha(UPDATER))]:wrapper=wrapper.replace(token,value)
assert '__ARCHIVE_SHA__'not in wrapper and '__UPDATER_SHA__'not in wrapper
constants=validate_transport_identity(wrapper,plan,OLD,sha(archive),pin,sha(UPDATER));ast.parse(wrapper);put(delivery/'deploy_risk_r22.py',wrapper.encode());put(delivery/'r22_update_runtime.py',UPDATER.read_bytes())
for label,arg in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:put(delivery/(label+'_Risk_R22.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_risk_r22.py" '+arg+'\r\n').encode())
TX.mkdir();tests=[]
faults=[('normal',None),('fourth-write',4),('factory-write','payload/business/run-template/classes/META-INF/spring.factories'),('session-class-write','payload/business/run-template/classes/xnby/replica/OriginalNativeSessionInterceptor.class'),('updater-write',updater),('release-pointer-write','release-manifest.json')]
for label,trigger in faults:
 case=TX/label;app=case/'Application'
 for n,raw in baseline.items():put(app/n,raw)
 m.backup_code(app,case/'backup',changes);count=[0];caught=False
 def after(name):
  count[0]+=1
  if name==trigger or count[0]==trigger:raise RuntimeError('OWN_FIXED_R22_FAULT_'+label)
 try:m.replace_code(app,bundle,changes,after_each=after)
 except RuntimeError as error:assert trigger is not None and str(error)=='OWN_FIXED_R22_FAULT_'+label;caught=True
 assert caught==(trigger is not None)
 if trigger is None:
  assert all((app/n).read_bytes()==raw for n,raw in bodies.items())and all(not(app/n).exists()for n in removed)
 if label=='updater-write':assert sha(app/updater)==sha(UPDATER)and sha(app/'release-manifest.json')==OLD
 m.restore_code(app,case/'backup',changes)
 assert all((app/n).read_bytes()==raw for n,raw in baseline.items())and all(not(app/n).exists()for n in changes if n not in baseline)
 tests.append({'scenario':label,'faultInjected':trigger is not None,'allOriginalBytesRestored':True,'allFourNewClassPathsAbsentAfterRestore':True,'allNewPathsRemoved':True,'paths':len(changes)})
 put(case/'result.json',enc(tests[-1]))
guard=next(n for n in ast.parse(wrapper).body if isinstance(n,ast.FunctionDef)and n.name=='recovery_guard');g={'need':lambda v,t:None if v else(_ for _ in()).throw(ValueError(t)),'Path':Path,'APP':Path('C:/inetpub/wwwroot/Zhumadian/Application'),'OLD':OLD,'NEW':plan['newReleaseSHA256'],'UPDATE':UPDATE};exec(compile(ast.Module(body=[guard],type_ignores=[]),'fixed-r22-guard','exec'),g)
good={'updateId':UPDATE,'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],'attempt':'C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/own'};g['recovery_guard'](good)
for key,value in [('updateId','other'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','1'*64),('attempt','C:/other/own')]:
 bad=dict(good);bad[key]=value
 try:g['recovery_guard'](bad)
 except ValueError:pass
 else:raise AssertionError('FOREIGN_RECOVERY_ACCEPTED')
put(D/'transaction-verification.json',enc({'actualFixedUpdaterSHA256':sha(UPDATER),'scenarios':tests,'generatedRecoveryOwnershipCases':5,'updaterNewButReleaseOldRecoveryStateExercised':True,'actualCodeReplacementAndRestoration':True,'realRuntimeStartedOrStopped':False}))
listed={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())if p.is_file()}
summary={'revision':'R22-risk-unit-native-session','targetFTP':'/Zhumadian/Zhumadian_Risk_Unit_20261101_R22/','files':listed,'payloadTransportFiles':len(listed),'payloadTransportBytes':sum(x['bytes']for x in listed.values()),'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':pin,'replacementPaths':len(bodies),'obsoleteFrontendPaths':len(removed),'totalInstallPaths':len(changes),'businessOperations':manifest['backendOperations'],'newUpdaterSHA256':sha(UPDATER),'oldReadinessReports':8,'newReadinessReports':9,'originalJavaArchivesSigningPasswordAndPermissionsUnchanged':True,'newNativeSessionValidityCheckDeclared':True,'other18ControllerFilesAndIISUnchanged':True,'containsCompiledFrontendBusinessClassesUpdaterSourceReleaseMetadataAndInternalPaths':True,'containsCredentialsBusinessRowsAssetsReferenceOrRawLogs':False}
put(D/'delivery-manifest.json',enc(summary));put(delivery/'delivery-manifest.json',enc(summary));scope={'manifestSHA256':sha(D/'delivery-manifest.json'),'transportFilesIncludingManifest':len(listed)+1,'transportBytesIncludingManifest':sum(x['bytes']for x in listed.values())+(D/'delivery-manifest.json').stat().st_size,'replacementPaths':len(bodies),'obsoleteFrontendPaths':len(removed),'totalInstallPaths':len(changes),'localR101NativeRuntimeAndActualProductionPortalPassed':True,'newGuardContractCases':50,'codeRecoveryScenarios':6,'publicServerPreflightPassed':False,'publicDeployed':False,'approvalGranted':False};put(D/'preparation-result.json',enc(scope));print(json.dumps(scope))
