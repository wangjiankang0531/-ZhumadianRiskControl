from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;H=V/'event_crud_r1010';R=Path('D:/Project/Zhumadian');A=R/'Application';D=R/'Document/Deployment/event_crud_native_r1010_20261105'
J=lambda p:json.loads(Path(p).read_bytes());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not(H/'event-source-pins-r1010.json').exists()
assert J(H/'configuration-tests-r1010.json')['passed']and J(V/'browser-expressions-passed-r1010.json')['passed']
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_event_crud_r1010.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
files=dict(J(V/'ledger_native_r960/ledger-source-pins-r960.json')['files'])
for p in H.iterdir():
 if p.is_file()and p.suffix in {'.py','.mjs'}:files[str(p)]=sha(p)
for n in ['owned_candidate_code_transaction_r543.py','owned_run_terminal_r709.py','owned_run_pointer_r717.py','bounded_build_job_r671.py','owned_task_configuration_r637.py']:
 p=A/'tools'/n;files[str(p)]=sha(p)
for n in ['original_public_test_update.py','original_public_test_base_r46.py']:
 p=R/'Document/Deployment/event_result_runtime_r1000_20261105/source'/n;files[str(p)]=sha(p)
pins={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':files,'actualPostFixRuntimeAccepted':False,'exactPreparedR48SourceBytes':True}
(H/'event-source-pins-r1010.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
(D/'prepared-sources-r1011.json').write_text(json.dumps({'passedAsSourcePreparation':True,'frozenSourcePins':len(files),'browserExpressionChecks':J(V/'browser-expressions-passed-r1010.json')['checkedLiteralOrTemplateEvaluationExpressions'],'configurationFaultChecks':13,'actualLifecycleOrBusinessAccepted':False,'newR48SparseLoaderFullFileValidationAccepted':False},indent=2)+'\n',encoding='utf8');print(json.dumps({'prepared':True,'sourcePins':len(files),'postFixRuntimeAccepted':False}))
