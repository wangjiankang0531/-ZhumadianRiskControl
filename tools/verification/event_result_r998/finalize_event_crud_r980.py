from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;H=V/'event_crud_r979';R=Path('D:/Project/Zhumadian');A=R/'Application'
D=R/'Document/Deployment/event_crud_native_r979_20261104'
J=lambda p:json.loads(Path(p).read_bytes());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (H/'event-source-pins-r979.json').exists()
assert J(H/'configuration-tests-r979.json')['passed']
p=H/'run_event_crud_r979.py';s=p.read_text('utf8');end=s.index('"""',3)+3
s='"""Exact owned R47 candidate: one fresh event, ordinary edit, restart, native second-tab delete and original editor false-save. Six own loopback notification URLs use a separate exact configuration transaction, restored before original code. No public/desktop/account/schema/model writes or forced shutdown."""'+s[end:]
s=s.replace('# This original-backend candidate never changes private application configuration.','# Restore this attempt\'s six loopback URL values and both manifest pins before the outer code restore.')
s=s.replace('UNCHANGED_SIX_GIB_PHYSICAL_AND_COMMIT_REQUIRED','SEVEN_GIB_PHYSICAL_AND_COMMIT_REQUIRED')
p.write_text(s,encoding='utf8')
for f in H.glob('*.py'):ast.parse(f.read_text('utf8'))
r=subprocess.run(['node','--check',str(H/'verify_event_crud_r979.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
old=J(V/'ledger_native_r960/ledger-source-pins-r960.json')
files=dict(old['files'])
for f in H.glob('*'):
 if f.is_file()and f.suffix in {'.py','.mjs'}:files[str(f)]=sha(f)
for n in ['owned_candidate_code_transaction_r543.py','owned_run_terminal_r709.py','owned_run_pointer_r717.py','bounded_build_job_r671.py','owned_task_configuration_r637.py']:
 f=A/'tools'/n;files[str(f)]=sha(f)
out={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':files,'configurationFaultChecks':len(J(H/'configuration-tests-r979.json')['checks']),'started':False,'actualNativeUIOrLifecycleAccepted':False}
(H/'event-source-pins-r979.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
(D/'prepared-r980.json').write_text(json.dumps({'passedAsPreparationOnly':True,'actualRunAccepted':False,'normalRoleEventUICasesPrepared':True,'oneFreshOwnEventAcrossTwoNormalLifecycles':True,'allBusinessMutationsThroughOriginalUI':True,'allSixDockURLsFreshOwnLoopbackOnly':True,'configurationFaultTests':13,'resourceBeforeRunPhysicalAndCommitBytes':7*1024**3,'controllerJobBytes':4*1024**3,'browserJobBytes':1024**3,'noWholeEventChainRepeat':True,'CIMUnprivilegedAccessDeniedNotAcceptedAsZero':True,'subsequentPrivilegedCIMZeroVerifiedBeforePreparation':True},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'sourcePins':len(files),'configurationFaultChecks':13,'runtimeAccepted':False}))
