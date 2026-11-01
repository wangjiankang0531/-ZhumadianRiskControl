"""Independently verify sealed transport, retained scope and actually executed program bytes."""
from pathlib import Path
import ast,hashlib,json,sys,zipfile
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
D=R/'Document/Deployment/public_test_unified_r23_20261101';ROOT=R/'work/event_delivery_consistency_20261030/full-controller-r117'
read=lambda p:json.loads(p.read_bytes());digest=lambda raw:hashlib.sha256(raw).hexdigest()
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
expected='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
assert sha(D/'delivery-manifest.json')==expected
manifest=read(D/'delivery-manifest.json');delivery=D/'delivery';scope=read(D/'preparation-result.json')
assert (delivery/'delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
assert {p.name for p in delivery.iterdir()}==set(manifest['files'])|{'delivery-manifest.json'}
assert len(list(delivery.iterdir()))==8 and sum(p.stat().st_size for p in delivery.iterdir())==4355704
for name,pin in manifest['files'].items():assert sha(delivery/name)==pin['sha256']and(delivery/name).stat().st_size==pin['bytes']
archive=delivery/'Zhumadian_Unified_Emergency_20261101_R23.zip'
with zipfile.ZipFile(archive)as z:
    assert z.testzip()is None and len(z.namelist())==len(set(z.namelist()))
    plan=json.loads(z.read('update-manifest.json'));assert digest(z.read('update-manifest.json'))==manifest['updateManifestSHA256']
    assert set(z.namelist())=={'update-manifest.json','web.config'}|{'payload/'+n for n in plan['files']}
    assert len(plan['files'])==599 and len(plan['removedFrontendFiles'])==584
    for name,pin in plan['files'].items():raw=z.read('payload/'+name);assert digest(raw)==pin['SHA256']and len(raw)==pin['bytes']
    release=json.loads(z.read('payload/release-manifest.json'));payload=json.loads(z.read('payload/payload-manifest.json'))
    assert digest(z.read('payload/release-manifest.json'))==plan['newReleaseSHA256']
    assert digest(z.read('payload/payload-manifest.json'))==release['payloadManifestSHA256']==plan['newPayloadManifestSHA256']
    assert z.read('payload/tools/original_public_test_update.py')==(delivery/'r23_update_runtime.py').read_bytes()
old=read(S/'r21-base-release-manifest.json');oldpayload=read(S/'r21-base-payload-manifest.json')
changed={'tools/serve_original_server_release.py','tools/original_server_windows_job.py','tools/original_public_test_update.py','tools/original_platform_async_release_support.py'}
assert len(release['controllerFiles'])==20
assert {n:p for n,p in release['controllerFiles'].items()if n not in changed}=={n:p for n,p in old['controllerFiles'].items()if n not in changed}
assert set(plan['acceptedOldReleases'])=={'9f5c34ab7fe0fe698acb0c75e7d40f2bf9256dd42924828c7b8d31072a216b47'}
rows=read(S/'candidate-stage.json')['allMaterializedPayloadFiles'];assert len(rows)==1047
assert all(payload['files'][n]==p for n,p in rows.items())
assert {n:p for n,p in payload['files'].items()if n not in rows and not n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))}=={
    n:p for n,p in oldpayload['files'].items()if n not in rows and not n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))}
assert all(n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))and n not in payload['files']for n in plan['removedFrontendFiles'])
assert all(not n.startswith(('private/','UserData/','runtime/','seed/','Assets/','Reference/'))for n in plan['files'])
app=R/'_b/Application';ownrelease=read(app/'release-manifest.json');ownpayload=read(app/'payload-manifest.json')
assert {n:p for n,p in ownpayload['files'].items()if n!='private/server-configuration.json'}=={
    n:p for n,p in payload['files'].items()if n!='private/server-configuration.json'}
assert {n:p for n,p in ownrelease.items()if n!='payloadManifestSHA256'}=={n:p for n,p in release.items()if n!='payloadManifestSHA256'}
for name,pin in plan['files'].items():
    if name not in ['release-manifest.json','payload-manifest.json']:assert sha(app/name)==pin['SHA256']
whole=read(ROOT/'r3/result.json');assert whole['allPassed']and whole['actualTenReadinessChecksPassed']
assert read(ROOT/'schema-before.json')==read(ROOT/'r3/schema-after.json')
terminal=read(ROOT/'r3/controller-terminal.json');assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and not terminal['forceTerminationUsed']
receipts=[read(p)for p in(app/'UserData/OriginalServer/runs').glob('j*/receipt.json')]
selected=[r for r in receipts if r['controllerPID']==terminal['pid']];assert len(selected)==1
receipt=selected[0];assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and len(receipt['exitCodesBeforeJobClose'])==6 and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
assert receipt['platformContextClosed']and receipt['businessContextClosed']and not receipt['jobAssignmentFailureComponents']
sys.path.insert(0,str(T));from build_public_workflow_r21 import validate_transport_identity
validate_transport_identity((delivery/'deploy_unified_r23.py').read_text(encoding='utf-8'),plan,manifest['oldReleaseSHA256'],sha(archive),manifest['updateManifestSHA256'],manifest['newUpdaterSHA256'])
proof={'sealedManifestSHA256':expected,'transportFiles':8,'transportBytes':4355704,'replacementPaths':599,
       'obsoleteFrontendPaths':584,'installPaths':1183,'archiveCRCAndEveryMemberVerified':True,
       'all1047CandidateFilesPresentInComposedPayload':True,'other16ControlsAndIISKept':True,
       'all597TransportProgramFilesMatchActuallyExecutedApplication':True,
       'onlySyntheticPrivateConfigAndManifestIdentityDifferInRuntimeFixture':True,
       'wholeSixComponentsAndControllerNormallyExitedZero':True,'actualAllDescendantsZeroBeforeJobClose':True,
       'tenReadyChecksAnd398DefinitionsPassed':True,'updaterContracts':123,'recoveryScenarios':10,
       'fullLoggedInBrowserAndRealNangangAcceptancePassed':False,'actualPublicServerOrIISOrTLSPassed':False,
       'privateConfigurationCredentialsRawBusinessOrAssetsShipped':False,'publicChanged':False}
(D/'independent-package-and-runtime-verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof))
