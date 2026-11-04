"""Compose four static files over complete sealed R45 for an owned original-backend check."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
OLD=R/'Document/Deployment/r45_owned_backend_r848_20261104';D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
S=V/'performance-assets-r893';C=S/'candidate-r900';H=V/'home_full_r905'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
assert not D.exists() and not H.exists()
assert sha(OLD/'full-source-and-restore-plan.private.json')=='204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09'
assert J(R/'work/ha902/gateway-result.json')['passed'] and J(R/'work/fb889/verified-feedback-chain-r889.json')['passed']
plan=copy.deepcopy(J(OLD/'full-source-and-restore-plan.private.json'));payload=J(OLD/'candidate/payload-manifest.json');release=J(OLD/'candidate/release-manifest.json')
built=J(S/'lossless-candidate-r900.json');assert built['passed'] and built['image']['originalICCProfilePreserved']
assert pin(G/'private/server-configuration.json')==plan['configBefore'] and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
for n,row in plan['sources'].items():assert pin(Path(row['source']))=={'bytes':row['bytes'],'sha256':row['sha256']},'ORIGINAL_FULL_PROGRAM_SOURCE_DRIFT:'+n
before=copy.deepcopy(payload['files']);old_release=copy.deepcopy(release)
for n,p in built['files'].items():
    assert pin(C/n)==p
    rel='frontend/security_pc/'+n;payload['files'][rel]=p;plan['sources'][rel]={'source':str(C/n),**p}
field='nativePlanExerciseRetainedFrontend'
def front(role):
    rows={n:p for n,p in payload['files'].items()if n.startswith('frontend/'+role+'/')}
    return {'files':len(rows),'manifestSHA256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
assert front('emergency_pc')==release[field]['frontends']['emergency_pc'] and front('security_pc')['files']==840
# The older frontend descriptor is a feature-layer baseline (836 files); R44
# adds its separately declared period stylesheet. Preserve those descriptors.
feature={'revision':'lossless-navigation-assets-r900','originalR45HTMLSHA256':before['frontend/security_pc/index.html']['sha256'],
 'changedFiles':{'frontend/security_pc/'+n:p for n,p in built['files'].items()},'allOriginalGlyphsRetained':True,'originalICCAndPixelsRetained':True,
 'staticFixturePixelChecksPassed':3,'completeSecurityFrontendAfter':front('security_pc'),'normalOriginalSDKAccepted':False,'publicAccepted':False}
release['homeTransferAssets']=feature;release['publicTestRevision']='20261104-home-transfer-owned-candidate-r905'
raw_payload=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(raw_payload).hexdigest();raw_release=enc(release)
changed={n for n in set(before)|set(payload['files'])if before.get(n)!=payload['files'].get(n)}
assert changed=={'frontend/security_pc/'+n for n in built['files']} and len(changed)==4
assert {k for k in release if release[k]!=old_release.get(k)}=={'homeTransferAssets','publicTestRevision','payloadManifestSHA256'}
D.mkdir();(D/'candidate').mkdir();H.mkdir()
for n,raw in [('payload-manifest.json',raw_payload),('release-manifest.json',raw_release)]:
    (D/'candidate'/n).write_bytes(raw)
rows={}
for n,p in plan['sources'].items():
    after={'bytes':p['bytes'],'sha256':p['sha256']};before_pin=pin(G/n)
    if before_pin!=after:rows[n]={'source':p['source'],'before':before_pin,'after':after}
for n in ['payload-manifest.json','release-manifest.json']:rows[n]={'source':str(D/'candidate'/n),'before':pin(G/n),'after':pin(D/'candidate'/n)}
plan.update(schema='xnby.home-transfer.owned-full-candidate.plan.v1',candidateReleaseSHA256=hashlib.sha256(raw_release).hexdigest(),candidatePayloadManifestSHA256=hashlib.sha256(raw_payload).hexdigest(),
 mutations=rows,publicProgramAndControllerBytesUnchanged=False,onlyFourFrontendFilesDifferFromR45=True,privateConfigurationNotChanged=True,
 originalR45ControllerAndAllOtherProgramBytesRetained=True,sourceR45PlanSHA256=sha(OLD/'full-source-and-restore-plan.private.json'),homeTransferFeature=feature)
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
# Derive the previously exercised full lifecycle. Startup/stop/restore function
# bodies remain identical apart from the explicit 7-GiB/4-GiB budget constants.
runner=(A/'tools/run_r45_original_backend_r850.py').read_text('utf8')
pairs=[("D=R/'Document/Deployment/r45_owned_backend_r848_20261104'","D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'"),
 ("P=O/'component-bootstrap-r850';Z=R/'work/original-backend-full-r850'","P=O/'home-transfer-r906';Z=R/'work/hf906'"),
 ('204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09',sha(D/'full-source-and-restore-plan.private.json')),
 ('xnby.r45-original-backend.owned-full-candidate.plan.v1','xnby.home-transfer.owned-full-candidate.plan.v1'),
 ("R/'work/bootstrap-full-r845/verified-component-bootstrap-r845.json'","R/'work/fb889/verified-feedback-chain-r889.json'"),
 ('r45-compatibility-source-pins-r850.json','home-transfer-source-pins-r906.json'),('r45_original_backend_health_r849.py','home_transfer_health_r906.py'),
 ('probe_r45_original_backend_r850.py','home_transfer_probe_r906.py'),('verified-component-bootstrap-r850.json','verified-home-transfer-r906.json'),('r45-backend-full-result-r850.json','home-transfer-full-result-r906.json'),
 ('REQUIRED=6*1024**3','REQUIRED=7*1024**3'),('CONTROLLER_BUDGET=3*1024**3','CONTROLLER_BUDGET=4*1024**3')]
for a,b in pairs:assert runner.count(a)>=1,(a,runner.count(a));runner=runner.replace(a,b)
old_functions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse((A/'tools/run_r45_original_backend_r850.py').read_bytes()).body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(runner).body if isinstance(n,ast.FunctionDef)}
assert old_functions==new_functions,'ALL_EXISTING_LIFECYCLE_FUNCTION_BODIES_MUST_REMAIN_IDENTICAL'
(H/'run_home_transfer_full_r906.py').write_text(runner,encoding='utf8')
health=(A/'tools/r45_original_backend_health_r849.py').read_text('utf8').replace("D=R/'Document/Deployment/r45_owned_backend_r848_20261104'","D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'")
health=health.replace('r45-compatibility-source-pins-r850.json','home-transfer-source-pins-r906.json').replace('xnby.r45-original-backend.owned-full-candidate.plan.v1','xnby.home-transfer.owned-full-candidate.plan.v1')
health=health.replace("runtimePath=V/'original_public_test_update_r45_bootstrap_r847.py'","runtimePath=Path("+repr(str(V/'original_public_test_update_r45_bootstrap_r847.py'))+")")
(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(A/'tools/probe_r45_original_backend_r850.py').read_text('utf8').replace("P=R/'work/original-manager-full-lifecycle-r609/component-bootstrap-r850'","P=R/'work/original-manager-full-lifecycle-r609/home-transfer-r906'")
probe=probe.replace("OUT=R/'work/bootstrap-browser-r850'","OUT=R/'work/home-browser-r906'").replace('r45_original_backend_health_r849.py','home_transfer_health_r906.py').replace('verify_r45_original_backend_browser_r850.mjs','verify_home_transfer_browser_r906.mjs')
probe=probe.replace('probe_r45_original_gateway_r850.py','home_transfer_gateway_r906.py').replace('business-result-r850.json','business-result-r906.json')
(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
gateway=(A/'tools/probe_r45_original_gateway_r850.py').read_text('utf8').replace("O=Path('D:/Project/Zhumadian/work/original-backend-full-r850')","O=Path('D:/Project/Zhumadian/work/hf906')")
(H/'home_transfer_gateway_r906.py').write_text(gateway,encoding='utf8')
report={'prepared':True,'newFrontendFiles':3,'changedFrontendFiles':1,'allOtherOriginalR45ProgramsAndControllersRetained':True,'fullProgramSources':len(plan['sources']),
 'codeMutationPaths':len(rows),'lifecycleFunctionBodiesRetained':True,'entryResourceGateGiB':7,'controllerCommitBudgetGiB':4,
 'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'newReleaseSHA256':plan['candidateReleaseSHA256'],'browserSourceStillToPrepare':True,
 'servicesOrDatabaseOrDesktopOrPublicChanged':False,'fullCloneReady':False}
(D/'prepared-r905.json').write_bytes(enc(report));print(json.dumps(report))
