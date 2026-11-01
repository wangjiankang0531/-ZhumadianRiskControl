"""Seal R25 only after exact offline contracts, full-program preflight and actual controller exit pass."""
from pathlib import Path
import ast,hashlib,json,sys,zipfile
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T))
from build_public_workflow_r21 import validate_transport_identity
W=R/'work/user_feedback_20261031';S=W/'r25-material-unified-candidate-r1';D=R/'Document/Deployment/public_test_material_r25_20261101';assert not D.exists()
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes());enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
bundle=S/'bundle';plan=read(bundle/'update-manifest.json');tx=read(S/'result.json')
proofs=[read(W/n/'result.json')for n in ['r25-inherited-updater-contract-r1','r25-workflow-contract-r1','r25-material-contract-r1']]
assert all(x['allPassed']for x in proofs)and [x['checks']for x in proofs]==[123,34,57]
full=read(R/'work/r25gv-r1/full-preflight-result.json');whole=read(R/'work/event_delivery_consistency_20261030/full-controller-r131/r1/result.json')
assert len(tx['recoveryScenarios'])==8 and all(x['allOriginalBytesRestored']and x['allNewPathsRemoved']for x in tx['recoveryScenarios'])
assert tx['foreignDriftRefusedBeforeAnyRestore']and full['allPassed']and whole['allPassed']
assert whole['checks']['actualR25MaterialRuntimePinsPassed']and whole['checks']['actualR24WorkflowGuardRuntimePinsPassed']
assert whole['actualTenReadinessChecksPassed']and whole['allSixComponentsNormallyExitedZero']and whole['allActualDescendantsExitedBeforeOuterJobClosed']and not whole['forceTerminationUsed']
updater=T/'original_public_test_update_r25_20261101.py';pin=sha(updater)
assert all(x['sourceSHA256']==pin for x in proofs)and pin==whole['updaterSHA256']==full['updaterSHA256']==tx['newUpdaterSHA256']
old=read(W/'r24-unified-candidate-r1/sparse-graceful-update-preparation-r1/bundle/payload/release-manifest.json')
OLD='a2a2ebb961a8cfd906b4e5fd8e46588140233b83c238f4b0c06ce831f4fccb43'
assert set(plan['acceptedOldReleases'])=={OLD}and len(plan['files'])==189 and len(plan['removedFrontendFiles'])==182
assert plan['targetApplication']=='C:/inetpub/wwwroot/Zhumadian/Application'and plan['gatewayPort']==18892
release=read(bundle/'payload/release-manifest.json');payload=read(bundle/'payload/payload-manifest.json')
assert len(release['controllerFiles'])==20 and sha(bundle/'payload/release-manifest.json')==plan['newReleaseSHA256']
assert sha(bundle/'payload/payload-manifest.json')==release['payloadManifestSHA256']==plan['newPayloadManifestSHA256']
control='tools/original_public_test_update.py'
assert {n:p for n,p in release['controllerFiles'].items()if n!=control}=={n:p for n,p in old['controllerFiles'].items()if n!=control}
assert release['controllerFiles']['tools/serve_original_server_release.py']==whole['controllerSHA256']and release['controllerFiles']['tools/original_server_windows_job.py']==whole['jobSHA256']
assert all(not n.startswith(('private/','UserData/','runtime/','seed/','Assets/','Reference/'))for n in plan['files'])
delivery=D/'delivery';delivery.mkdir(parents=True)
deny=b'<?xml version="1.0" encoding="utf-8"?><configuration><system.webServer><security><authorization><clear/><add accessType="Deny" users="*"/></authorization></security></system.webServer></configuration>\r\n'
archive=delivery/'Zhumadian_Material_Emergency_20261101_R25.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
    z.writestr('update-manifest.json',(bundle/'update-manifest.json').read_bytes());z.writestr('web.config',deny)
    for n,pin in plan['files'].items():
        b=(bundle/'payload'/n).read_bytes();assert len(b)==pin['bytes']and digest(b)==pin['SHA256'];z.writestr('payload/'+n,b)
wrapper=(T/'risk_r22_transport.py.in').read_text(encoding='utf-8').replace('r22','r25').replace('R22','R25').replace('EXACT_R21','EXACT_R24')
wrapper=wrapper.replace('Zhumadian_Risk_Unit_20261101_R25.zip',archive.name)
old_updater=old['controllerFiles'][control];assert old_updater=='4931c7fbb58880f228423f8324d3b40cb22e500bc299f053a8fe455a742c7878'
assert wrapper.count("OLD_UPDATER_SHA='8ee301b1d7466f08f39c40d0ed42c9edbe652bfd3a9223f694d7379c7970dad5'")==1
wrapper=wrapper.replace("OLD_UPDATER_SHA='8ee301b1d7466f08f39c40d0ed42c9edbe652bfd3a9223f694d7379c7970dad5'","OLD_UPDATER_SHA='"+old_updater+"'")
for token,value in [('__ARCHIVE_SHA__',sha(archive)),('__MANIFEST_SHA__',sha(bundle/'update-manifest.json')),('__OLD__',OLD),('__NEW__',plan['newReleaseSHA256']),('__UPDATE_ID__',plan['updateId']),('__UPDATER_SHA__',sha(updater))]:wrapper=wrapper.replace(token,value)
ast.parse(wrapper);validate_transport_identity(wrapper,plan,OLD,sha(archive),sha(bundle/'update-manifest.json'),sha(updater))
put(delivery/'deploy_material_r25.py',wrapper.encode());put(delivery/'r25_update_runtime.py',updater.read_bytes());put(delivery/'web.config',deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
    put(delivery/(label+'_Material_R25.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_material_r25.py" '+flag+'\r\n').encode('ascii'))
files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())if p.is_file()}
manifest={'revision':'R25-material-file-transaction-retained-emergency-guards','targetFTP':'/Zhumadian/Zhumadian_Material_Emergency_20261101_R25/',
    'targetApplication':plan['targetApplication'],'files':files,'payloadTransportFiles':len(files),'payloadTransportBytes':sum(x['bytes']for x in files.values()),
    'oldReleaseSHA256':OLD,'oldUpdaterSHA256':old_updater,'newReleaseSHA256':plan['newReleaseSHA256'],'newUpdaterSHA256':sha(updater),'updateManifestSHA256':sha(bundle/'update-manifest.json'),
    'replacementPaths':189,'obsoleteFrontendPaths':182,'totalInstallPaths':371,'oldReadinessReports':10,'newReadinessReports':10,
    'updaterContractChecks':214,'actualCodeRecoveryScenarios':8,'actualFullProgramDependencyFilesVerified':15549,
    'wholeSixComponentControllerOnSyntheticDataPassed':True,'actualMaterialThreeClassRuntimePinsPassed':True,
    'allSixComponentsAndControllerNormallyExitedZero':True,'original398DefinitionsUnchanged':True,
    'workflowCompiledFrontendFiles':338,'workflowSourceInputs':235,'workflowSourceOverlays':53,
    'threeMaterialWholeFileImportClassesExactlyPreviouslyNativeBrowserVerified':True,'nativeBrowserChecksArePriorScopedFixturesNotThisPublicServer':True,
    'other19ControllersAndIISPreserved':True,'originalBusinessAndPlatformJarsAuthenticationDatabaseAndNonEmergencyFrontendKept':True,
    'fullLoggedInBrowserOnWholeControllerAndRealNangangAcceptancePassed':False,'actualPublicPrivateIdentityOrIISOrTLSVerified':False,
    'containsCompiledFrontendOwnMaterialJavaClassesUpdaterCodeMetadataAndInternalPaths':True,
    'containsActualPrivateConfigurationCredentialsDatabaseBusinessRowsAssetsReferenceScreenshotsOrRawLogs':False,
    'publicUploadedOrInstalled':False,'publicGitIncluded':False,'wholeModuleAccepted':False,'fullCloneReady':False}
put(D/'delivery-manifest.json',enc(manifest));put(delivery/'delivery-manifest.json',enc(manifest))
node=next(n for n in ast.parse(wrapper).body if isinstance(n,ast.FunctionDef)and n.name=='recovery_guard')
ns={'Path':Path,'APP':Path(plan['targetApplication']),'OLD':OLD,'NEW':plan['newReleaseSHA256'],'UPDATE':plan['updateId'],'need':lambda v,msg:None if v else(_ for _ in()).throw(ValueError(msg))}
exec(compile(ast.Module(body=[node],type_ignores=[]),'fixed-r25-recovery-guard','exec'),ns)
good={'updateId':plan['updateId'],'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],'attempt':plan['targetApplication']+'/UserData/OriginalPublicUpdates/own'};ns['recovery_guard'](good)
for key,val in [('updateId','other'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','1'*64),('attempt','C:/other/own')]:
    bad=dict(good);bad[key]=val
    try:ns['recovery_guard'](bad)
    except ValueError:pass
    else:raise AssertionError('FOREIGN_RECOVERY_ACCEPTED')
with zipfile.ZipFile(archive)as z:
    assert z.testzip()is None and set(z.namelist())=={'update-manifest.json','web.config'}|{'payload/'+n for n in plan['files']}and len(z.namelist())==len(set(z.namelist()))
    for n,pin in plan['files'].items():b=z.read('payload/'+n);assert len(b)==pin['bytes']and digest(b)==pin['SHA256']
scope={'manifestSHA256':sha(D/'delivery-manifest.json'),'transportFilesIncludingManifest':len(files)+1,'transportBytesIncludingManifest':sum(x['bytes']for x in files.values())+(D/'delivery-manifest.json').stat().st_size,
    'replacementPaths':189,'obsoleteFrontendPaths':182,'totalInstallPaths':371,'archiveCRCAndAllMembersVerified':True,'recoveryOwnershipCases':5,
    'maxServerExtractionPathCharacters':max(len(plan['targetApplication']+'/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/payload/'+n)for n in plan['files']),
    'localFullControllerPassed':True,'publicServerPreflightPassed':False,'publicDeployed':False,'approvalGranted':False}
assert scope['maxServerExtractionPathCharacters']<260;put(D/'preparation-result.json',enc(scope));print(json.dumps(scope))
