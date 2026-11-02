from pathlib import Path
import copy,hashlib,importlib.util,json,os,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';G=R/'_g/Application';W=R/'work/user_feedback_20261031';S=W/'r32-avatar-candidate-r1';C=R/'work/event_delivery_consistency_20261030/full-controller-r158';P=C/'prepared-r1'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert not P.exists()and J(R/'work/r32gv-r1/full-preflight-result.json')['allPassed']and J(S/'result.json')['allCompositionContractsPassed'];assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
base=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json');assert sha(G/'release-manifest.json')==base['releaseSHA256']
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count";r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
source=T/'original_public_test_update_r32_20261102.py';spec=importlib.util.spec_from_file_location('r32_actual_own_update',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(G/'release-manifest.json');previous=J(G/'payload-manifest.json');q=copy.deepcopy(previous);candidate=J(S/'bundle/payload/payload-manifest.json');prefix=('frontend/security_pc/','frontend/emergency_pc/');q['files']={n:p for n,p in q['files'].items()if not n.startswith(prefix)};q['files'].update({n:p for n,p in candidate['files'].items()if n.startswith(prefix)});qraw=enc(q)
release=copy.deepcopy(old);release[m.R32_AVATAR_FIELD]=copy.deepcopy(m.R32_AVATAR_CONTRACT);release.update(payloadManifestSHA256=hashlib.sha256(qraw).hexdigest(),publicTestRevision='20261102-R32-two-native-portals-avatar-source-and-default-icon',publicAccepted=False);release['controllerFiles']['tools/original_public_test_update.py']=sha(source);rraw=enc(release)
plan=J(S/'bundle/update-manifest.json');plan.update(targetApplication=G.as_posix(),acceptedOldReleases={sha(G/'release-manifest.json'):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],newReleaseSHA256=hashlib.sha256(rraw).hexdigest());plan['files']['payload-manifest.json']={'bytes':len(qraw),'SHA256':hashlib.sha256(qraw).hexdigest()};plan['files']['release-manifest.json']={'bytes':len(rraw),'SHA256':hashlib.sha256(rraw).hexdigest()}
P.mkdir(parents=True);bundle=P/'bundle'
for n,p in plan['files'].items():
 if n=='payload-manifest.json':put(bundle/'payload'/n,qraw)
 elif n=='release-manifest.json':put(bundle/'payload'/n,rraw)
 else:
  path=m.check_file(S/'bundle/payload',n,p['SHA256'],p['bytes']);dest=bundle/'payload'/n;dest.parent.mkdir(parents=True,exist_ok=True);os.link(path,dest)
put(bundle/'update-manifest.json',enc(plan));loaded,oldpin,changes=m.load_bundle(G,bundle,sha(bundle/'update-manifest.json'),expected_target=G);assert len(changes)==1385;budget=m.candidate_runtime_pool_preflight(G,bundle,loaded);assert budget['budget']['mysqlMaxConnections']==24
put(P/'temporary-code-scope.json',enc({'onlyOwnedSyntheticG':True,'files':changes,'oldReleaseSHA256':oldpin,'newReleaseSHA256':plan['newReleaseSHA256'],'privateConfigurationOrDataModified':False,'actualLoadBundleAndCandidateBudgetPassedBeforeMutation':True,'mustRestoreAfterAllActualDescendantsZero':True}))
m.backup_code(G,P/'code-backup',changes);m.replace_code(G,bundle,changes)
for n,p in changes.items():assert sha(G/n)==p['after']if p['after']else not(G/n).exists()
base.update(releaseSHA256=sha(G/'release-manifest.json'),updaterSHA256=sha(source),temporaryR32AvatarCompiledFrontendsAndUpdaterOnly=True);put(P/'controller-fixture-ready.json',enc(base));put(P/'own-serial-definition.json',(R/'work/event_delivery_consistency_20261030/full-controller-r154/closed-readback-r1/own-serial-definition.json').read_bytes());print(json.dumps({'onlyOwnSyntheticR32CandidateInstalled':True,'actual1385PathLoadBundleAndBudgetPassed':True,'allPrivateDataAnd19OtherControlsKept':True,'mustRestoreAfterNormalRuntimeChecks':True}))
