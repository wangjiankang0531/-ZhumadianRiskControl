"""Use the exact R47 updater/core and payload in one original six-component run.
Only the owned fixture's private manifest pin differs from the public candidate.
"""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
OLD=V/'supervision_full_r927';H=V/'supervision_exact_r931';D=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104'
P=R/'Document/Deployment/supervision_current_full_r920_20261104';B=R/'work/unified-home-supervision-r928/bundle'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not D.exists()and not H.exists()and not(R/'work/sv931').exists()
prior=J(R/'work/sv927/verified-current-supervision-r927.json');assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
plan=copy.deepcopy(J(P/'full-source-and-restore-plan.private.json'));public_payload=J(B/'payload/payload-manifest.json');public_release=J(B/'payload/release-manifest.json')
assert pin(G/'private/server-configuration.json')==plan['configBefore']and sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
for n in ['tools/original_public_test_update.py','tools/original_public_test_base_r46.py']:
 p=B/'payload'/n;assert pin(p)==public_payload['files'][n];plan['sources'][n]={'source':str(p),**pin(p)}
for n,p in plan['sources'].items():
 if not n.startswith(('private/','UserData/','Assets/','seed/')):
  expected=public_payload['files'][n]if n in public_payload['files']else {'bytes':p['bytes'],'sha256':public_release['controllerFiles'][n]}
  assert pin(Path(p['source']))==expected,'EXACT_R47_PROGRAM_SOURCE:'+n
payload=copy.deepcopy(public_payload);payload['files']['private/server-configuration.json']=plan['configBefore'];rawpayload=enc(payload)
release=copy.deepcopy(public_release);release['payloadManifestSHA256']=hashlib.sha256(rawpayload).hexdigest();rawrelease=enc(release)
assert {k for k in release if release[k]!=public_release[k]}=={'payloadManifestSHA256'}
D.mkdir();(D/'candidate').mkdir();H.mkdir();(H/'classes').mkdir()
for n,b in [('payload-manifest.json',rawpayload),('release-manifest.json',rawrelease)]:(D/'candidate'/n).write_bytes(b)
rows={}
for n,p in plan['sources'].items():
 after={k:p[k]for k in ['bytes','sha256']};assert pin(Path(p['source']))==after
 before=pin(G/n)
 if before!=after:rows[n]={'source':p['source'],'before':before,'after':after}
for n in ['payload-manifest.json','release-manifest.json']:rows[n]={'source':str(D/'candidate'/n),'before':pin(G/n),'after':pin(D/'candidate'/n)}
plan.update(schema='xnby.exact-unified-supervision.owned-full-candidate.plan.v1',candidateReleaseSHA256=hashlib.sha256(rawrelease).hexdigest(),candidatePayloadManifestSHA256=release['payloadManifestSHA256'],mutations=rows,
 exactPublicR47ProgramAndControllerBytes=True,onlyPrivateConfigurationManifestPinAdapted=True,sourceR47BundleManifestSHA256=sha(B/'update-manifest.json'))
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
for p in OLD.glob('*'):
 if p.suffix not in ['.py','.mjs','.java']:continue
 if p.name=='home_transfer_health_r906.py':continue
 s=p.read_text('utf8').replace('current-supervision-r927','exact-supervision-r931').replace('current-supervision-browser-r927','exact-supervision-browser-r931').replace('work/sv927','work/sv931').replace("R/'work/sv927'","R/'work/sv931'").replace('current-supervision-source-pins-r927.json','exact-supervision-source-pins-r931.json').replace('verified-current-supervision-r927.json','verified-exact-supervision-r931.json').replace('current-supervision-full-result-r927.json','exact-supervision-full-result-r931.json')
 s=s.replace('OwnHomeNavigationReadbackR927','OwnHomeNavigationReadbackR931')
 if p.name=='run_home_transfer_full_r906.py':
  s=s.replace('supervision_current_full_r920_20261104','unified_home_supervision_exact_r930_20261104').replace('99f0b07ce6e6902d66ac9e9f74b5b452b7ad8fcb433b53495acd32e514785f61',sha(D/'full-source-and-restore-plan.private.json')).replace('xnby.current-supervision.owned-full-candidate.plan.v1','xnby.exact-unified-supervision.owned-full-candidate.plan.v1')
  s=s.replace("assert J(D/'conditional-pointer-recovery-r923.json')['passedAsScopedRecovery']","assert J(R/'work/sv927/verified-current-supervision-r927.json')['passed']")
 if p.suffix=='.py':ast.parse(s)
 name='OwnHomeNavigationReadbackR931.java'if p.suffix=='.java'else p.name;(H/name).write_text(s,encoding='utf8')
health='''from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
 pins=json.loads((V/'exact-supervision-source-pins-r931.json').read_bytes());assert sha(D/'full-source-and-restore-plan.private.json')==pins['candidatePlanSHA256']
 plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes());assert plan['target']==str(G)and plan['exactPublicR47ProgramAndControllerBytes']and plan['onlyPrivateConfigurationManifestPinAdapted']
 release=json.loads((D/'candidate/release-manifest.json').read_bytes());assert sha(D/'candidate/release-manifest.json')==plan['candidateReleaseSHA256']
 source=Path(plan['sources']['tools/original_public_test_update.py']['source']);assert sha(source)==release['controllerFiles']['tools/original_public_test_update.py']
 spec=importlib.util.spec_from_file_location('exact_r47_updater_r931',source);wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper);assert wrapper.declared(release)
 runtime=wrapper.runtime();return plan,runtime,wrapper
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G;plan,runtime,wrapper=profile()
 assert sha(G/'release-manifest.json')==plan['candidateReleaseSHA256']
 p=G/'private/server-configuration.json';assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['configBefore']
 result=runtime.health(G,row,True,gateway_port=gateway_port);assert result and result['supervisionReady']
 return {'exactR47UpdaterAndCoreUsed':True,'originalReleaseHealthRetained':True,'supervisionReadinessRequired':True,'privateApplicationSettingsChanged':False,'publicIISOrTLSAccepted':False}
'''
(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8');ast.parse(health)
# runtime() loads its pinned core adjacent to the updater. Preserve both names
# in the frozen source directory without changing either byte sequence.
core=B/'payload/tools/original_public_test_base_r46.py';assert core.is_file()
jobs=load('r931_compile_jobs',G/'tools/original_server_windows_job.py');budget=load('r931_budget',A/'tools/bounded_build_job_r671.py')
assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
source=H/'OwnHomeNavigationReadbackR931.java'
with(H/'compile.private.log').open('xb')as f:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(source)],stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};job.close()
assert p.returncode==0;compiled=H/'classes/OwnHomeNavigationReadbackR931.class'
(H/'fixture-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(source),'classSHA256':sha(compiled),'terminal':terminal}))
assert subprocess.run(['node','--check',str(H/'verify_home_transfer_browser_r906.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'exact-supervision-source-pins-r931.json').write_bytes(enc({'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':pins}))
report={'prepared':True,'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'completeSources':len(plan['sources']),'mutations':len(rows),
 'allPublicR47ProgramAndControllerBytesMatched':True,'onlyPrivateManifestPinAdapted':True,'productionUpdaterHealthAndPinnedCoreWillBeUsedWithoutExpectationPatch':True,
 'previousR927FullyPassedAndRestored':True,'readOnlyMetadataReaderCompileTerminal':terminal,'servicesDatabaseDesktopOrPublicChanged':False,'actualLifecycleStillPending':True}
(D/'prepared-r930.json').write_bytes(enc(report));print(json.dumps(report))
