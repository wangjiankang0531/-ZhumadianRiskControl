"""Seal one sparse unified transport from the already tested program bytes."""
from pathlib import Path
import ast,hashlib,json,sys,zipfile

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T))
from build_public_workflow_r21 import validate_transport_identity
S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
D=R/'Document/Deployment/public_test_unified_r23_20261101';assert not D.exists()
read=lambda p:json.loads(p.read_bytes())
digest=lambda raw:hashlib.sha256(raw).hexdigest()
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
bundle=S/'sparse-graceful-update-preparation-r1/bundle'
plan=read(bundle/'update-manifest.json');tx=read(bundle.parent/'result.json')
checks=read(R/'work/user_feedback_20261031/r23-graceful-updater-contract-r1/result.json')
full=read(R/'work/r23gv-r1/full-preflight-result.json')
whole=read(R/'work/event_delivery_consistency_20261030/full-controller-r117/r3/result.json')
assert checks['allPassed']and checks['checks']==123
assert len(tx['recoveryScenarios'])==10 and all(v['allOriginalBytesRestored']and v['allNewPathsRemoved']for v in tx['recoveryScenarios'])
assert tx['foreignDriftRefusedBeforeAnyRestore']and full['allPassed']and whole['allPassed']
assert whole['wholeSixComponentControllerActuallyExecuted']and whole['actualTenReadinessChecksPassed']and not whole['forceTerminationUsed']
updater=T/'original_public_test_update_r23_graceful_20261101.py'
assert sha(updater)==checks['sourceSHA256']==whole['updaterSHA256']==full['updaterSHA256']
assert sha(bundle/'payload/tools/serve_original_server_release.py')==whole['controllerSHA256']
assert sha(bundle/'payload/tools/original_server_windows_job.py')==whole['jobSHA256']
OLD='9f5c34ab7fe0fe698acb0c75e7d40f2bf9256dd42924828c7b8d31072a216b47'
assert set(plan['acceptedOldReleases'])=={OLD}
assert len(plan['files'])==599 and len(plan['removedFrontendFiles'])==584
assert plan['targetApplication']=='C:/inetpub/wwwroot/Zhumadian/Application'and plan['gatewayPort']==18892
release=read(bundle/'payload/release-manifest.json');payload=read(bundle/'payload/payload-manifest.json')
assert len(release['controllerFiles'])==20
assert sha(bundle/'payload/release-manifest.json')==plan['newReleaseSHA256']
assert sha(bundle/'payload/payload-manifest.json')==release['payloadManifestSHA256']==plan['newPayloadManifestSHA256']
assert all(not name.startswith(('private/','UserData/','runtime/','seed/','Assets/','Reference/'))for name in plan['files'])
old=read(S/'r21-base-release-manifest.json')
changed={'tools/serve_original_server_release.py','tools/original_server_windows_job.py','tools/original_public_test_update.py','tools/original_platform_async_release_support.py'}
assert {n:p for n,p in release['controllerFiles'].items()if n not in changed}=={n:p for n,p in old['controllerFiles'].items()if n not in changed}
delivery=D/'delivery';D.mkdir();delivery.mkdir()
deny=b'<?xml version="1.0" encoding="utf-8"?><configuration><system.webServer><security><authorization><clear/><add accessType="Deny" users="*"/></authorization></security></system.webServer></configuration>\r\n'
archive=delivery/'Zhumadian_Unified_Emergency_20261101_R23.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
    z.writestr('update-manifest.json',(bundle/'update-manifest.json').read_bytes());z.writestr('web.config',deny)
    for name,pin in plan['files'].items():
        raw=(bundle/'payload'/name).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']
        z.writestr('payload/'+name,raw)
wrapper=(T/'risk_r22_transport.py.in').read_text(encoding='utf-8').replace('r22','r23').replace('R22','R23')
wrapper=wrapper.replace('Zhumadian_Risk_Unit_20261101_R23.zip',archive.name)
for token,value in [('__ARCHIVE_SHA__',sha(archive)),('__MANIFEST_SHA__',sha(bundle/'update-manifest.json')),
                    ('__OLD__',OLD),('__NEW__',plan['newReleaseSHA256']),('__UPDATE_ID__',plan['updateId']),('__UPDATER_SHA__',sha(updater))]:
    wrapper=wrapper.replace(token,value)
ast.parse(wrapper)
validate_transport_identity(wrapper,plan,OLD,sha(archive),sha(bundle/'update-manifest.json'),sha(updater))
put(delivery/'deploy_unified_r23.py',wrapper.encode('utf-8'));put(delivery/'r23_update_runtime.py',updater.read_bytes());put(delivery/'web.config',deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
    put(delivery/(label+'_Unified_R23.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_unified_r23.py" '+flag+'\r\n').encode('ascii'))
listed={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())if p.is_file()}
manifest={'revision':'R23-unified-risk-emergency-graceful-controller',
    'targetFTP':'/Zhumadian/Zhumadian_Unified_Emergency_20261101_R23/',
    'targetApplication':plan['targetApplication'],'files':listed,'payloadTransportFiles':len(listed),
    'payloadTransportBytes':sum(v['bytes']for v in listed.values()),'oldReleaseSHA256':OLD,
    'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':sha(bundle/'update-manifest.json'),
    'replacementPaths':599,'obsoleteFrontendPaths':584,'totalInstallPaths':1183,
    'newUpdaterSHA256':sha(updater),'newControllerSHA256':whole['controllerSHA256'],'newJobSHA256':whole['jobSHA256'],
    'oldReadinessReports':8,'newReadinessReports':10,'updaterContractChecks':123,'actualCodeRecoveryScenarios':10,
    'actualFullProgramDependencyFilesVerified':15408,'wholeSixComponentControllerOnSyntheticDataPassed':True,
    'actualNativeAndBusinessContextClosedNormally':True,'original398DefinitionsUnchanged':True,
    'candidateDisposalAndReopenBrowserCasesInSeparateComponentFixture':20,
    'fullLoggedInBrowserOnWholeControllerAndRealNangangAcceptancePassed':False,
    'privateConfigAndActualPublicIdentityOrIISOrTLSVerified':False,
    'other16OriginalControllersAndIISPreserved':True,'originalBusinessAndPlatformJarAuthenticationAndDatabaseKept':True,
    'containsCompiledFrontendOwnJavaClassesUpdaterControllerSourceMetadataAndInternalPaths':True,
    'containsActualPrivateConfigurationCredentialsDatabaseBusinessRowsAssetsReferenceScreenshotsOrRawLogs':False,
    'publicUploadedOrInstalled':False,'publicGitIncluded':False}
put(D/'delivery-manifest.json',enc(manifest));put(delivery/'delivery-manifest.json',enc(manifest))
# Check generated recovery ownership independently, including wrong update/base/target rejection.
node=next(n for n in ast.parse(wrapper).body if isinstance(n,ast.FunctionDef)and n.name=='recovery_guard')
namespace={'Path':Path,'APP':Path(plan['targetApplication']),'OLD':OLD,'NEW':plan['newReleaseSHA256'],'UPDATE':plan['updateId'],
           'need':lambda v,message:None if v else(_ for _ in()).throw(ValueError(message))}
exec(compile(ast.Module(body=[node],type_ignores=[]),'fixed-r23-recovery-guard','exec'),namespace)
good={'updateId':plan['updateId'],'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],
      'attempt':'C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/own'}
namespace['recovery_guard'](good)
for key,value in [('updateId','other'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','1'*64),('attempt','C:/other/own')]:
    bad=dict(good);bad[key]=value
    try:namespace['recovery_guard'](bad)
    except ValueError:pass
    else:raise AssertionError('FOREIGN_RECOVERY_ACCEPTED')
with zipfile.ZipFile(archive)as z:
    assert z.testzip()is None and set(z.namelist())=={'update-manifest.json','web.config'}|{'payload/'+n for n in plan['files']}
    assert len(z.namelist())==len(set(z.namelist()))
    for name,pin in plan['files'].items():raw=z.read('payload/'+name);assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']
scope={'manifestSHA256':sha(D/'delivery-manifest.json'),'transportFilesIncludingManifest':len(listed)+1,
       'transportBytesIncludingManifest':sum(v['bytes']for v in listed.values())+(D/'delivery-manifest.json').stat().st_size,
       'replacementPaths':599,'obsoleteFrontendPaths':584,'totalInstallPaths':1183,
       'archiveCRCAndAllMembersVerified':True,'recoveryOwnershipCases':5,
       'maxServerExtractionPathCharacters':max(len(plan['targetApplication']+'/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/payload/'+n)for n in plan['files']),
       'localFullControllerPassed':True,'publicServerPreflightPassed':False,'publicDeployed':False,'approvalGranted':False}
assert scope['maxServerExtractionPathCharacters']<260
put(D/'preparation-result.json',enc(scope));print(json.dumps(scope))
