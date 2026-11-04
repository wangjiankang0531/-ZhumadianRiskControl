"""Resolve the fixed public R44 into the existing synthetic G, without apply.

Only the private configuration manifest pin is adapted; raw configuration never
leaves its owner. Every public R44 program/controller byte remains unchanged.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';T=A/'tools'
PUBLIC=R/'Document/Deployment/original_backend_bootstrap_r45_20261104'
B=R/'work/original-backend-bootstrap-r847/r36/bundle/payload'
D=R/'Document/Deployment/r45_owned_backend_r848_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
cache={}
def sha(p):
 p=Path(p);st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key not in cache:
  with p.open('rb')as f:cache[key]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[key]
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.exists()else None
assert not D.exists()and J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
assert J(PUBLIC/'prepared-bundles-r847.json')['runtimeSHA256']=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
assert sha(B/'release-manifest.json')=='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
baseline=sha(G/'release-manifest.json');assert baseline=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
release=J(B/'release-manifest.json');payload=J(B/'payload-manifest.json');original=copy.deepcopy(release)
config=pin(G/'private/server-configuration.json');installation=pin(G/'UserData/OriginalServer/installation.json')
payload['files']['private/server-configuration.json']=config
payloadRaw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payloadRaw).hexdigest()
releaseRaw=enc(release)
assert {k for k in release if release[k]!=original[k]}=={'payloadManifestSHA256'}
old=J(R/'Document/Deployment/integrated_online_candidate_r678_20261104/full-source-and-restore-plan.private.json')
resolved=J(R/'work/r39-full-preflight-r37-r341/resolution.json');prior={**resolved['programs'],**resolved['controls']}
expected={n:p for n,p in payload['files'].items()if not n.startswith('seed/mysql/')}
for n,h in release['controllerFiles'].items():
 if n in expected:assert expected[n]['sha256']==h
 else:
  candidates=[B/n,G/n,A/n]
  if n in prior:candidates.append(Path(prior[n]['source']))
  found=next((p for p in candidates if p.is_file()and sha(p)==h),None);assert found,'UNRESOLVED_CONTROL:'+n
  expected[n]=pin(found)
sources={};missing=[]
for index,(n,pinExpected)in enumerate(sorted(expected.items()),1):
 assert not n.startswith(('UserData/','Assets/','Reference/','seed/'))and'..'not in Path(n).parts
 options=[B/n,G/n,A/n]
 if n in prior:options.append(Path(prior[n]['source']))
 if n in old['sources']:options.append(Path(old['sources'][n]['source']))
 for p in options:
  if p.is_file()and pin(p)==pinExpected:
   for parent in [p,*p.parents]:assert not parent.is_symlink()and not parent.lstat().st_file_attributes&0x400
   sources[n]={'source':str(p),**pinExpected};break
 else:missing.append(n)
 if index%5000==0:print(json.dumps({'resolvedFiles':len(sources),'inspected':index,'servicesStarted':False}),flush=True)
assert not missing,'UNRESOLVED_PROGRAMS:'+','.join(missing[:10])
mutations={}
for n,p in sources.items():
 after={'bytes':p['bytes'],'sha256':p['sha256']};before=pin(G/n)
 if before!=after:
  assert not n.startswith(('private/','UserData/','Assets/','seed/'))
  mutations[n]={'source':p['source'],'before':before,'after':after}
retired={n:p for n,p in J(G/'payload-manifest.json')['files'].items()if n.startswith('frontend/')and n not in payload['files']and(G/n).exists()}
for n,p in retired.items():assert pin(G/n)==p
known=old['knownRebuildableCachesToRemoveOnlyDuringFutureApply']
for n,p in known.items():assert pin(G/n)==p
spec=importlib.util.spec_from_file_location('original_r44_health_r716',Path('D:\\CodexData\\home\\visualizations\\2026\\10\\28\\01a1836e-e4ee-7fb0-be6f-b24f2e2672e4\\tencent-feedback-20261031\\original_public_test_update_r45_bootstrap_r847.py'));runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
checks={}
for name,args in [('history_declared',(release,)),('original_mapper_defaults_declared',(release,)),('runtime_pool_declared',(release,)),
 ('workflow_declared',(release,payload)),('material_declared',(release,payload)),('team_declared',(release,payload)),
 ('native_default_declared',(release,payload)),('async_declared',(release,payload)),('native_plan_runtime_declared',(release,payload))]:
 assert getattr(runtime,name)(*args)is True;checks[name]=True
D.mkdir();(D/'candidate').mkdir()
for n,raw in [('payload-manifest.json',payloadRaw),('release-manifest.json',releaseRaw)]:
 p=D/'candidate'/n;p.write_bytes(raw);mutations[n]={'source':str(p),'before':pin(G/n),'after':pin(p)}
plan={'schema':'xnby.r45-original-backend.owned-full-candidate.plan.v1','target':str(G),'onlyExistingOwnedSyntheticFixture':True,
 'baseOwnedReleaseSHA256':baseline,'candidateReleaseSHA256':hashlib.sha256(releaseRaw).hexdigest(),
 'candidatePayloadManifestSHA256':hashlib.sha256(payloadRaw).hexdigest(),'publicR45ReleaseSHA256':sha(B/'release-manifest.json'),
 'publicProgramAndControllerBytesUnchanged':True,'onlyPrivateConfigurationManifestPinAdapted':True,'rawConfigurationNotCopied':True,
 'sources':sources,'mutations':mutations,'retiredKnownFrontendPaths':retired,'knownRebuildableCachesToRemoveOnlyDuringFutureApply':known,
 'configBefore':config,'installationBefore':installation,'callbackOverlay':old['callbackOverlay'],
 'minimumAvailableMemoryBeforeApplyOrStart':6*1024**3,'durablePointerBeforeSnapshotRequiredBeforeApply':True,
 'exactRunOwnerAndChildrenReceiptSelectionRequired':True,'fullCloneReady':False}
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
proof={'prepared':True,'resolvedInstalledProgramFiles':len(sources),'codeWritePaths':len(mutations),'retiredFrontendPaths':len(retired),
 'retainedMetadataChecks':checks,'publicR45BytesUnchanged':True,'ownedManifestOnlyPrivatePinAdapted':True,
 'GFilesOrDataOrServicesOrDesktopOrPublicChanged':False,'actualR45OriginalBackendLifecycleStillPending':True,'fullCloneReady':False}
(D/'prepared-owned-r45-r848.json').write_bytes(enc(proof));print(json.dumps(proof))
