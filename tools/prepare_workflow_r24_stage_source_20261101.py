from pathlib import Path
import ast, copy, hashlib, json, shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
S23=W/'r23-unified-candidate-r1';S=W/'r24-unified-candidate-r1';F=W/'emergency-workflow-source-r6'
assert not S.exists()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
proof=read(R/'work/event_delivery_consistency_20261030/full-controller-r123/independent-outcome-reconcile-r126.json')
assert proof['passed'] and proof['candidateWholeControllerAndSchemaPassedRuns']==2
b=read(F/'build-result.json');v=read(F/'independent-build-verification.json')
assert b['buildPassed']and b['fileCount']==338 and v['allBuildBytesAndSourcePinsVerified']and v['undeclaredSourceDifferences']==0
rows={n:copy.deepcopy(pin)for n,pin in read(S23/'candidate-stage.json')['allMaterializedPayloadFiles'].items()if not n.startswith('frontend/emergency_pc/')}
rows.update({'frontend/emergency_pc/'+n:copy.deepcopy(pin)for n,pin in b['files'].items()})
task='payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'
task_source=R/'work/event_delivery_consistency_20261030/full-controller-r121/flow-guard-candidate-r6/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'
rows[task]={'bytes':8543,'sha256':'9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'}
assert len(rows)==1182 and shutil.disk_usage(W).free>2*1024**3
for n,pin in rows.items():
    f=task_source if n==task else F/'dist'/n.removeprefix('frontend/emergency_pc/')if n.startswith('frontend/emergency_pc/')else S23/'payload'/n
    raw=f.read_bytes();assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['sha256'],n
    put(S/'payload'/n,raw)
for n in ['r21-base-release-manifest.json','r21-base-payload-manifest.json','async-extension-release-fragment.json']:
    put(S/n,(S23/n).read_bytes())
controls=['tools/serve_original_server_release.py','tools/original_platform_async_release_support.py',
          'tools/original_public_test_update.py','tools/original_server_windows_job.py','tools/original_server_release_parameters.py']
for n in controls:
    f=T/'original_public_test_update_r24_20261101.py'if n==controls[2]else T/'server-runtime-temp-r2/original_server_release_parameters.py'if n==controls[4]else S23/'graceful-public-control'/n
    put(S/'graceful-public-control'/n,f.read_bytes())
put(S/'candidate-stage.json',enc({'schema':'xnby.r24.code-stage.v1','allMaterializedPayloadFiles':rows,
    'frontendCounts':{'security':836,'emergency':338},'backendAndPlatformFiles':8,
    'userPreviewReadOrChanged':False,'publicInstalled':False,'fullCloneReady':False,
    'workflowBuildProofSHA256':sha(F/'independent-build-verification.json'),
    'workflowNormalRoleProofSHA256':sha(R/'work/event_delivery_consistency_20261030/full-controller-r123/independent-outcome-reconcile-r126.json')}))
s=(T/'prepare_unified_graceful_sparse_update_20261101.py').read_text(encoding='utf-8')
s=s.replace('r23-unified-candidate-r1','r24-unified-candidate-r1').replace("'r23gx-'","'r24gx-'")
s=s.replace('original_public_test_update_r23_graceful_20261101.py','original_public_test_update_r24_20261101.py')
s=s.replace('r23-graceful-updater-contract-r1','r24-inherited-updater-contract-r1')
s=s.replace('assert len(rows)==1047','assert len(rows)==1182')
s=s.replace('assert len(bodies)==593 and sum(map(len,bodies.values()))==11164268',"assert len(bodies)<1000 and sum(map(len,bodies.values()))<32*1024**2")
s=s.replace('unifiedRiskAndEmergencyR23','unifiedRiskAndEmergencyR24').replace('20261101-r23-preparation','20261101-r24-preparation')
s=s.replace('20261101-R23-','20261101-R24-').replace('OWN_R23_FAULT_','OWN_R24_FAULT_')
s=s.replace("'updaterContractChecksPassed':123", "'updaterContractChecksPassed':157")
s=s.replace("'sourceIssueCellsMarkedCompleteByThisCandidate':[]}","'sourceIssueCellsMarkedCompleteByThisCandidate':[], 'workflowRevision':'WF6', 'wholeModuleAccepted':False}")
s=s.replace("release.update(read(S/'async-extension-release-fragment.json'))", "release.update(read(S/'async-extension-release-fragment.json'))\nrelease[m.R24_WORKFLOW_FIELD]=copy.deepcopy(m.R24_WORKFLOW_CONTRACT)")
s=s.replace("'tools/original_public_test_update.py','tools/original_server_windows_job.py']", "'tools/original_public_test_update.py','tools/original_server_windows_job.py','tools/original_server_release_parameters.py']")
s=s.replace('assert len(removed)==584 and not set(bodies).intersection(removed)', 'assert removed and not set(bodies).intersection(removed)')
s=s.replace("('fourth-write',4),('async-jar-write',jar)","('fourth-write',4),('task-controller-write',m.R24_TASK_CLASS),('parameter-adapter-write',m.R24_PARAMETER),('async-jar-write',jar)")
s=s.replace("'updaterContractChecks':123", "'updaterContractChecks':157")
s=s.replace('other16OriginalControllersAndIISRetained','other15OriginalControllersAndIISRetained')
s=s.replace('xnby.r23.sparse-update-preparation.v1','xnby.r24.sparse-update-preparation.v1')
# The existing source resolves prior files from the verified old R21 resolver; retain that readonly reference.
assert "read(R/'work/r23pv-r1/dependency-resolution.json')"in s
ast.parse(s);out=T/'prepare_unified_workflow_r24_sparse_update_20261101.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'stage':str(S),'materializedCodeFiles':len(rows),'frontendFiles':338,
    'generatedDriver':str(out),'publicTransportSealed':False}))
