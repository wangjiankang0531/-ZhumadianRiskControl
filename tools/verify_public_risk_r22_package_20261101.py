"""Independent read-only verification of the sealed R22 transport, composed scope and recovery proof."""
from pathlib import Path
import ast,hashlib,json,zipfile,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/public_test_risk_r22_20261101';S=R/'work/user_feedback_20261031/r22-risk-candidate-r3';read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest()
EXPECTED='9482746b9a8a7d7ccbe7a6279ca813bb3fda05ed83bf188f8da042f4dba7f5f5';assert sha(D/'delivery-manifest.json')==EXPECTED
scope=read(D/'preparation-result.json');manifest=read(D/'delivery-manifest.json');delivery=D/'delivery';assert (D/'delivery-manifest.json').read_bytes()==(delivery/'delivery-manifest.json').read_bytes()
assert {p.name for p in delivery.iterdir()}==set(manifest['files'])|{'delivery-manifest.json'}
for n,pin in manifest['files'].items():assert sha(delivery/n)==pin['sha256']and (delivery/n).stat().st_size==pin['bytes']
assert len(list(delivery.iterdir()))==8 and sum(p.stat().st_size for p in delivery.iterdir())==2978667
with zipfile.ZipFile(delivery/'Zhumadian_Risk_Unit_20261101_R22.zip')as z:
 names=z.namelist();assert len(names)==len(set(names))and z.testzip()is None
 raw=z.read('update-manifest.json');plan=json.loads(raw);assert digest(raw)==manifest['updateManifestSHA256']
 assert set(names)=={'update-manifest.json','web.config'}|{'payload/'+n for n in plan['files']}
 for n,pin in plan['files'].items():b=z.read('payload/'+n);assert len(b)==pin['bytes']and digest(b)==pin['SHA256']
 release=json.loads(z.read('payload/release-manifest.json'));payload=json.loads(z.read('payload/payload-manifest.json'))
 assert digest(z.read('payload/release-manifest.json'))==plan['newReleaseSHA256']and digest(z.read('payload/payload-manifest.json'))==release['payloadManifestSHA256']==plan['newPayloadManifestSHA256']
 assert z.read('payload/tools/original_public_test_update.py')==(delivery/'r22_update_runtime.py').read_bytes()==(T/'original_public_test_update_r22_20261101.py').read_bytes()
old=read(S/'r21-base-release-manifest.json');oldPayload=read(S/'r21-base-payload-manifest.json');candidate=read(S/'candidate-stage.json')
assert set(plan['acceptedOldReleases'])=={'9f5c34ab7fe0fe698acb0c75e7d40f2bf9256dd42924828c7b8d31072a216b47'}
assert plan['targetApplication']=='C:/inetpub/wwwroot/Zhumadian/Application'and plan['gatewayPort']==18892 and not plan['databaseUploadsCredentialsGISOrDependenciesIncluded']
assert plan['callbackOverlaySHA256']==release['missingAuthOverlayManifestSHA256']=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb'
assert {k for k in old['controllerFiles']if old['controllerFiles'][k]!=release['controllerFiles'][k]}=={'tools/original_public_test_update.py'}
assert set(old['controllerFiles'])==set(release['controllerFiles'])and len(release['controllerFiles'])==19
backend={x['relative']for x in candidate['backendOperations']};assert len(backend)==5
assert {n for n in plan['files']if n.startswith('payload/business/')}==backend
prefix='frontend/security_pc/';desired={n:pin for n,pin in candidate['allMaterializedPayloadFiles'].items()if n.startswith(prefix)};assert len(desired)==836
assert {n:p for n,p in payload['files'].items()if n.startswith(prefix)}==desired
for n,pin in candidate['allMaterializedPayloadFiles'].items():assert payload['files'][n]==pin
assert {n:p for n,p in oldPayload['files'].items()if not n.startswith(prefix)and n not in backend}=={n:p for n,p in payload['files'].items()if not n.startswith(prefix)and n not in backend}
assert all(not n.startswith(('private/','UserData/','runtime/','seed/','Assets/','Reference/'))for n in plan['files'])
assert not any('OwnReadOnlyLoginSnapshot' in n or 'OriginalPublicRiskObservation' in n or 'own-import-fixtures' in n for n in plan['files'])
assert len(plan['files'])==526 and len(plan['removedFrontendFiles'])==517 and not set(plan['files']).intersection(plan['removedFrontendFiles'])
for n,row in plan['removedFrontendFiles'].items():assert n.startswith(prefix)and row=={'bytes':oldPayload['files'][n]['bytes'],'SHA256':oldPayload['files'][n]['sha256']}and n not in payload['files']
sys.path.insert(0,str(T))
from build_public_workflow_r21 import validate_transport_identity
wrapper=(delivery/'deploy_risk_r22.py').read_text();validate_transport_identity(wrapper,plan,manifest['oldReleaseSHA256'],sha(delivery/'Zhumadian_Risk_Unit_20261101_R22.zip'),manifest['updateManifestSHA256'],manifest['newUpdaterSHA256'])
assign={t.id:ast.literal_eval(n.value)for n in ast.parse(wrapper).body if isinstance(n,ast.Assign)for t in n.targets if isinstance(t,ast.Name)and t.id in ['OLD_UPDATER_SHA','UPDATER_SHA']};assert assign['OLD_UPDATER_SHA']==old['controllerFiles']['tools/original_public_test_update.py']and assign['UPDATER_SHA']==release['controllerFiles']['tools/original_public_test_update.py']
checks=read(R/'work/user_feedback_20261031/r22-updater-contract-r1/result.json');tx=read(D/'transaction-verification.json');assert checks['checks']==50 and checks['allPassed']and checks['sourceSHA256']==manifest['newUpdaterSHA256'];assert len(tx['scenarios'])==6 and all(x['allOriginalBytesRestored']and x['allNewPathsRemoved']for x in tx['scenarios'])and tx['updaterNewButReleaseOldRecoveryStateExercised']and tx['generatedRecoveryOwnershipCases']==5
result={'sealedManifestSHA256':EXPECTED,'transportFiles':8,'transportBytes':2978667,'archiveCRCAndEveryMemberPinMatched':True,'everyMaterializedR101CandidateFileIncludedInComposedManifest':841,'exactNewBackendPaths':5,'original18OtherControllersAndIISPreserved':True,'privateDataAssetsOriginalSDKAndQAObserversNotShipped':True,'newUpdaterAndRecoveryWrapperBothPinned':True,'newGuardContractChecks':50,'normalAndSensitiveWriteRecoveryScenarios':6,'thisUpdateRecoveryIdentityCases':5,'replacementPaths':526,'obsoleteFrontendPaths':517,'installPaths':1043,'scopeIsLocalPackageVerificationNotLiveServerPreflight':True,'publicChanged':False};(D/'independent-package-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
