from pathlib import Path
import ast,hashlib,importlib.util,json,stat,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';D=R/'Document/Deployment/public_test_duty_layout_r28_20261101';B=W/'r28-duty-layout-candidate-r1/bundle';G=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r139'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest();manifest=J(D/'delivery-manifest.json');prep=J(D/'preparation-result.json');delivery=D/'delivery'
assert sha(D/'delivery-manifest.json')==prep['manifestSHA256'] and(D/'delivery-manifest.json').read_bytes()==(delivery/'delivery-manifest.json').read_bytes()
assert {p.name for p in delivery.iterdir()}==set(manifest['files'])|{'delivery-manifest.json'}and len(manifest['files'])==7
for name,pin in manifest['files'].items():p=delivery/name;assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400 and p.stat().st_size==pin['bytes']and sha(p)==pin['sha256']
source=T/'original_public_test_update_r28_20261101.py';spec=importlib.util.spec_from_file_location('independent_fixed_r27',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
updater='tools/original_public_test_update.py';prefix='frontend/emergency_pc/';archive=delivery/'Zhumadian_Duty_Layout_20261101_R28.zip'
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None and len(z.namelist())==len(set(z.namelist()))
 plan=json.loads(z.read('update-manifest.json'));assert digest(z.read('update-manifest.json'))==manifest['updateManifestSHA256']
 assert set(z.namelist())=={'web.config','update-manifest.json'}|{'payload/'+n for n in plan['files']}
 for item in z.infolist():assert not item.filename.startswith(('/','\\'))and '..'not in Path(item.filename).parts and stat.S_IFMT(item.external_attr>>16)not in [stat.S_IFLNK,stat.S_IFDIR]
 for name,pin in plan['files'].items():raw=z.read('payload/'+name);assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']and raw==(B/'payload'/name).read_bytes()
 q=json.loads(z.read('payload/payload-manifest.json'));r=json.loads(z.read('payload/release-manifest.json'))
 assert digest(z.read('payload/payload-manifest.json'))==r['payloadManifestSHA256']==plan['newPayloadManifestSHA256']and digest(z.read('payload/release-manifest.json'))==plan['newReleaseSHA256']==manifest['newReleaseSHA256']
 assert z.read('payload/'+updater)==source.read_bytes()==(delivery/'r28_update_runtime.py').read_bytes()and sha(source)==manifest['newUpdaterSHA256']
 for n,pin in m.R27_POOL_PINS.items():assert z.read('payload/'+n)==(T/'connection-budget-r139'/Path(n).name).read_bytes()==(G/n).read_bytes()and plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']}
old=J(W/'r26-team-native-candidate-r1/bundle/payload/release-manifest.json');oldq=J(W/'r26-team-native-candidate-r1/bundle/payload/payload-manifest.json');assert set(plan['acceptedOldReleases'])=={'8350e8c4543788f560a6b51e1787722ba782bf76a21051ba39f4bc0eee180c35'}
changed={updater,*m.R27_POOL_PINS};assert {n:h for n,h in old['controllerFiles'].items()if n not in changed}=={n:h for n,h in r['controllerFiles'].items()if n not in changed}and len(r['controllerFiles'])==20
legal={'release-manifest.json','payload-manifest.json',*changed}|{n for n in q['files']if n.startswith(prefix)};assert set(plan['files'])<=legal and len(plan['files'])==178
assert {n:p for n,p in oldq['files'].items()if not n.startswith(prefix)}=={n:p for n,p in q['files'].items()if not n.startswith(prefix)}
for n in oldq['files']:
 if not n.startswith(prefix):assert n not in plan['files']and n not in plan['removedFrontendFiles']
obsolete={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldq['files'].items()if n.startswith(prefix)and n not in q['files']};assert plan['removedFrontendFiles']==obsolete and len(obsolete)==172
build=J(W/'emergency-workflow-source-r14/build-result.json');assert {n.removeprefix(prefix):p for n,p in q['files'].items()if n.startswith(prefix)}==build['files']and len(build['files'])==339
assert r[m.R27_POOL_FIELD]==m.R27_POOL_POLICY and r[m.R24_WORKFLOW_FIELD]==m.R27_POOL_WORKFLOW_CONTRACT
defs=lambda p:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};before=defs(T/'original_public_test_update_r26_20261101.py');after=defs(source)
assert {n for n in before if before[n]!=after[n]}=={'team_bundle_contract','material_declared','material_bundle_contract','workflow_declared','workflow_bundle_contract','workflow_ready','load_bundle','async_bundle_contract','async_ready','health','apply_update'}
assert set(after)-set(before)=={'runtime_pool_declared','workflow_contract_for','parameter_pin_for','controller_pin_for','runtime_pool_bundle_contract','runtime_pool_ready','candidate_runtime_pool_preflight'}
for n in ['normal_stop','replace_code','restore_code','backup_code','rollback_latest','recover_pending']:assert before[n]==after[n]

newtree=ast.parse(source.read_text(encoding='utf-8'))
apply=next(n for n in newtree.body if isinstance(n,ast.FunctionDef)and n.name=='apply_update')
expected_assign=ast.parse('candidate_pool = candidate_runtime_pool_preflight(app, bundle, plan)').body[0]
guard_text="if candidate_pool is not None:\n    require(sha(regular(app, 'private/server-configuration.json')) == candidate_pool['configurationSHA256'],\n            'CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP')"
expected_guard=ast.parse(guard_text).body[0]
same=lambda a,b:ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
assigns=[n for n in apply.body if same(n,expected_assign)];assert len(assigns)==1;apply.body.remove(assigns[0])
guards=[(n,b)for n in apply.body if isinstance(n,ast.Try)for b in n.body if same(b,expected_guard)];assert len(guards)==1;guards[0][0].body.remove(guards[0][1])
assert ast.dump(apply,include_attributes=False)==before['apply_update']
wrapper_ast=ast.parse((delivery/'deploy_duty_layout_r28.py').read_text(encoding='utf-8'))
main=next(n for n in wrapper_ast.body if isinstance(n,ast.FunctionDef)and n.name=='main')
calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='candidate_runtime_pool_preflight'];assert len(calls)==1

for n in ['deploy_duty_layout_r28.py','r28_update_runtime.py']:ast.parse((delivery/n).read_text(encoding='utf-8'))
assert 'EXACT_R26'in(delivery/'deploy_duty_layout_r28.py').read_text(encoding='utf-8')and manifest['oldUpdaterSHA256']=='6307a61826e4d77b4b5381e10f97ecff0d6ec76f54d90fa01e2a9ff4915b2f5a'
whole=J(C/'r4/result.json');ui=J(C/'r4/duty-browser/result.json');assert whole['allPassed']and whole['updaterSHA256']==sha(source)and whole['checks']['actualRuntimePoolPolicyReady']and ui['passed']and len(ui['cases'])==18 and not ui['exceptions']
proof={'schema':'xnby.r28.independent-fixed-delivery.v1','passed':True,'transportFiles':8,'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),'exactArchivedProgramPathsAndCRCVerified':178,'exactObsoleteEmergencyFiles':172,'exactWF14FrontendFiles':339,'other17ControlsOriginalJarsAndEveryNonEmergencyPayloadRetained':True,'normalStopBackupReplaceRestoreRollbackRecoverASTUnchanged':True,'exactActualControllerSourcesAndNativeDutyParallelProofMatched':True,'publicUploadedDeployedOrGitPushed':False,'fullCloneReady':False};assert proof['transportBytes']==prep['transportBytesIncludingManifest'];(D/'independent-fixed-delivery-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
