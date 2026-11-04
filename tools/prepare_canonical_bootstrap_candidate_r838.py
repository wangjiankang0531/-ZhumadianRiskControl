"""Resolve the complete compiled online frontend into the owned full candidate.

No G mutation, data copy, application start, port binding, public update or role
grant. Code manifests are applied by the outer code transaction; the one-setting
inner transaction then produces the final runtime manifests without weakening
the code transaction's private-path exclusion.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
OLD=R/'Document/Deployment/supervision_factory_candidate_r694_20261104'
BUILD=R/'work/canonical-bootstrap-full-r835'
PROOF=R/'Document/Deployment/canonical_bootstrap_build_r835_20261104'
D=R/'Document/Deployment/canonical_bootstrap_candidate_r838_20261104'
J=lambda p:json.loads(p.read_bytes())
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.exists()else None
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
assert not D.exists()
full=J(BUILD/'verified-bounded-full-build-r673.json');analysis=J(V/'canonical-bootstrap-analysis-r836/result.json');links={'passed':analysis['passed'],'compiledFiles':analysis['candidate']['compiledFiles']}
assert full['passed']and full['completeBuildExecuted']and full['sourceRestored']and full['terminal']['actualJobDescendantsZeroBeforeClose']
assert links['passed']and links['compiledFiles']==full['compiledFiles']==len(full['files'])
base=J(OLD/'full-source-and-restore-plan.private.json');assert base['target']==str(G)and base['onlyExistingOwnedSyntheticFixture']
assert sha(G/'release-manifest.json')==base['baseOwnedReleaseSHA256']=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert pin(G/'private/server-configuration.json')==base['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==base['installationBefore']
assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
release=J(OLD/'code-candidate/release-manifest.json');payload=J(OLD/'code-candidate/payload-manifest.json')
assert sha(OLD/'code-candidate/release-manifest.json')==base['codeCandidateReleaseSHA256']
prefix='frontend/emergency_pc/'
for n in list(payload['files']):
    if n.startswith(prefix):del payload['files'][n]
sources={n:dict(row)for n,row in base['sources'].items()if not n.startswith(prefix)}
for n,p in full['files'].items():
    file=BUILD/'dist'/n;assert pin(file)==p
    payload['files'][prefix+n]=p;sources[prefix+n]={**p,'source':str(file)}
assert len(sources)==len(base['sources'])-sum(n.startswith(prefix)for n in base['sources'])+len(full['files'])
release['publicTestRevision']='owned-canonical-component-bootstrap-r838-not-public'
payload_raw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payload_raw).hexdigest();release_raw=enc(release)
expected={n:p for n,p in payload['files'].items()if not n.startswith('seed/mysql/')}
for n,h in release['controllerFiles'].items():
    if n in expected:assert expected[n]['sha256']==h
    else:expected[n]={'bytes':sources[n]['bytes'],'sha256':h}
assert set(expected)==set(sources)
for n,p in sources.items():assert {'bytes':p['bytes'],'sha256':p['sha256']}==expected[n]and pin(Path(p['source']))==expected[n],'FULL_SOURCE_RESOLUTION_DRIFT:'+n

# Derive the final runtime hashes from the exact code candidate, not by writing
# a credential-containing candidate configuration outside its private owner.
sys.path.insert(0,str(A/'tools'));import owned_task_configuration_r637 as task
raw_before={task.CONFIG:(G/task.CONFIG).read_bytes(),task.PAYLOAD:payload_raw,task.RELEASE:release_raw}
runtime=task.task_candidate(raw_before)
assert json.loads(runtime[task.CONFIG])['configuration']['business']['flow.event-task-handle']=='tj_eventTask'
assert pin(G/'private/server-configuration.json')==base['configBefore']
D.mkdir();(D/'code-candidate').mkdir();(D/'runtime-manifests').mkdir()
(D/'code-candidate/payload-manifest.json').write_bytes(payload_raw);(D/'code-candidate/release-manifest.json').write_bytes(release_raw)
(D/'runtime-manifests/payload-manifest.json').write_bytes(runtime[task.PAYLOAD]);(D/'runtime-manifests/release-manifest.json').write_bytes(runtime[task.RELEASE])
mutations={}
for n,p in sources.items():
    current=pin(G/n);after={'bytes':p['bytes'],'sha256':p['sha256']}
    if current!=after:
        assert not n.startswith(('private/','UserData/','Assets/','seed/'))
        mutations[n]={'before':current,'after':after,'source':p['source']}
for name,raw in [('payload-manifest.json',payload_raw),('release-manifest.json',release_raw)]:
    mutations[name]={'before':pin(G/name),'after':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'source':str(D/'code-candidate'/name)}
retired={n:p for n,p in J(G/'payload-manifest.json')['files'].items()if n.startswith('frontend/')and n not in payload['files']and(G/n).exists()}
for n,p in retired.items():assert pin(G/n)==p
for n,p in base['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():assert pin(G/n)==p
plan={'schema':'xnby.integrated-online.owned-full-candidate.plan.v1','target':str(G),'onlyExistingOwnedSyntheticFixture':True,
      'baseOwnedReleaseSHA256':base['baseOwnedReleaseSHA256'],'codeCandidateReleaseSHA256':hashlib.sha256(release_raw).hexdigest(),
      'runtimeCandidateReleaseSHA256':hashlib.sha256(runtime[task.RELEASE]).hexdigest(),
      'runtimePayloadManifestSHA256':hashlib.sha256(runtime[task.PAYLOAD]).hexdigest(),
      'runtimeConfigurationAfterPin':task.raw_pin(runtime[task.CONFIG]),'configBefore':base['configBefore'],'installationBefore':base['installationBefore'],
      'sources':sources,'mutations':mutations,'retiredKnownFrontendPaths':retired,
      'knownRebuildableCachesToRemoveOnlyDuringFutureApply':base['knownRebuildableCachesToRemoveOnlyDuringFutureApply'],
      'callbackOverlay':base['callbackOverlay'],'sixComponentLifecycleMinimumAvailableBytes':6*1024**3,
      'codeThenInnerTaskTransactionApplyAndReverseRestoreOrderRequired':True,'rawConfigurationNotWrittenOutsideOwnedPrivateFile':True,
      'designerPermissionAndModelAbsenceAndNormalBusinessWorkflowNotVerified':True,'newFullParentAndHealthProfileStillRequired':True,
      'publicUpdaterNotPreparedForThisIntegratedScope':True,'fullCloneReady':False}
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
summary={'prepared':True,'resolvedInstalledProgramFiles':len(sources),'compiledEmergencyFrontendFiles':len(full['files']),
         'codeMutationPaths':len(mutations),'retiredKnownFrontendPaths':len(retired),'knownRebuildableCaches':len(base['knownRebuildableCachesToRemoveOnlyDuringFutureApply']),
         'estimatedIndependentCodeWriteBytes':sum(r['after']['bytes']for r in mutations.values()),
         'estimatedBeforeCodeBackupBytes':sum(r['before']['bytes']for r in mutations.values()if r['before'])+sum(p['bytes']for p in retired.values()),
         'runtimeCandidateReleaseSHA256':plan['runtimeCandidateReleaseSHA256'],'codeAndRuntimeManifestPhasesExplicit':True,
         'rawCredentialContainingCandidateConfigurationWritten':False,'GFilesOrDataOrServicesOrPublicChanged':False,
         'completeCompiledFrontendAndStaticGraphVerified':True,'fullParentHealthNormalRoleWorkflowOrPublicAccepted':False,'fullCloneReady':False}
assert sha(G/'release-manifest.json')==base['baseOwnedReleaseSHA256']and pin(G/'private/server-configuration.json')==base['configBefore']
(D/'prepared-canonical-bootstrap-r838.json').write_bytes(enc(summary));print(json.dumps(summary))
