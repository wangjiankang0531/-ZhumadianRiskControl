from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
D=R/'Document/Deployment/original_task_attachment_candidate_r250_20261103'
assert not D.exists()
sources={}
def save(name,s):
 p=T/name;assert not p.exists()
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8',newline='\n');sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
def swap(s,a,b):
 assert s.count(a)==1,(a[:90],s.count(a));return s.replace(a,b)
for name in ['prepare_production_history_runtime_r218.py','restore_production_history_runtime_r218.py']:
 save(name.replace('r218','r250'),(T/name).read_text(encoding='utf-8').replace('r108','r121').replace('r218','r250'))
for name in ['prepare_personal_workflow_frontend_r245_candidate.py','restore_personal_workflow_frontend_r245_candidate.py']:
 save(name.replace('r245_candidate','r250'),(T/name).read_text(encoding='utf-8').replace('r120','r121').replace('r245_candidate','r250'))
save('configure_owned_parallel_gateway_r250.py',(T/'configure_owned_parallel_gateway_r218.py').read_text(encoding='utf-8').replace('r108','r121'))
browser=(T/'verify_native_parallel_gateway_r218_20261103.mjs').read_text(encoding='utf-8')
browser=swap(browser,'let uploadedPath=null,','let holdUpload=false,heldUpload=null,holdTaskSave=false,heldTaskSave=null,taskSavePaused=0;let uploadedPath=null,')
browser=swap(browser,"const u=new URL(v.params.request.url);if(u.origin===wire.base||['about:','data:'].includes(u.protocol))", "const u=new URL(v.params.request.url);if(u.origin===wire.base&&u.pathname.endsWith('/sys-file/upload')&&holdUpload){if(heldUpload)throw Error('ONE_OWN_HELD_UPLOAD');heldUpload=v.params.requestId;return;}if(u.origin===wire.base&&u.pathname.endsWith('/eventTask/save')&&holdTaskSave){taskSavePaused++;if(heldTaskSave)throw Error('DUPLICATE_TASK_SAVE_REQUEST');heldTaskSave=v.params.requestId;return;}if(u.origin===wire.base||['about:','data:'].includes(u.protocol))")
browser=swap(browser,"await send('DOM.setFileInputFiles',{nodeId:input,files:[filePath]},session);await until(()=>uploadedPath!==null);", """holdUpload=true;await send('DOM.setFileInputFiles',{nodeId:input,files:[filePath]},session);await until(()=>heldUpload!==null);const beforeHeldUploadTaskSaves=http.filter(x=>x.path.endsWith('/eventTask/save')).length;
   if(!await click('button','提交'))throw Error('TASK_SUBMIT_BUTTON_REQUIRED');await sleep(250);
   if(http.filter(x=>x.path.endsWith('/eventTask/save')).length!==beforeHeldUploadTaskSaves||!await evaluate("location.pathname.endsWith('/taskSend/add')")||await value('任务名称')!==name||uploadedPath!==null)throw Error('PENDING_UPLOAD_MUST_BLOCK_TASK_SUBMIT_AND_KEEP_INPUT');
   cases.push({case:'shared-candidate-uploader-held-before-network-blocks-task-submit-and-keeps-input',passed:true});
   holdUpload=false;const uploadRequest=heldUpload;heldUpload=null;await send('Fetch.continueRequest',{requestId:uploadRequest},session);await until(()=>uploadedPath!==null);""")
browser=swap(browser,"const count=http.filter(x=>x.path.endsWith('/eventTask/save')).length;if(!await click('button','提交'))throw Error('NATIVE_TASK_SUBMIT_REQUIRED');await until(()=>evaluate(\"location.pathname.endsWith('/emergencyResponse/taskSend')\"));", """const count=http.filter(x=>x.path.endsWith('/eventTask/save')).length;holdTaskSave=true;if(!await click('button','提交'))throw Error('NATIVE_TASK_SUBMIT_REQUIRED');await until(()=>heldTaskSave!==null);
   await click('button','提交');await sleep(250);if(taskSavePaused!==1||!await evaluate("location.pathname.endsWith('/taskSend/add')")||await value('任务名称')!==name)throw Error('TASK_DOUBLE_SUBMIT_MUST_KEEP_ONE_REQUEST_AND_FORM');
   cases.push({case:'shared-candidate-task-save-has-one-inflight-request-and-retains-form-until-confirmed',passed:true});holdTaskSave=false;const saveRequest=heldTaskSave;heldTaskSave=null;await send('Fetch.continueRequest',{requestId:saveRequest},session);await until(()=>evaluate("location.pathname.endsWith('/emergencyResponse/taskSend')"));""")
save('verify_native_task_attachment_r250_20261103.mjs',browser)
host=(T/'verify_full_controller_parallel_gateway_r218_20261103.py').read_text(encoding='utf-8').replace('verify_native_parallel_gateway_r218_20261103.mjs','verify_native_task_attachment_r250_20261103.mjs').replace("['r108']","['r121']")
host=swap(host,"'productCodeChanged':False,","'productCodeChanged':True,'candidateFrontendR224Installed':True,")
host=host.replace('xnby.r218.native-parallel-gateway-regression.v1','xnby.r250.task-attachment-candidate-regression.v1')
save('verify_full_controller_task_attachment_r250_20261103.py',host)
runner=(T/'run_parallel_gateway_r218_20261103.py').read_text(encoding='utf-8').replace('r108','r121').replace('verify_full_controller_parallel_gateway_r218','verify_full_controller_task_attachment_r250').replace('restore_personal_workflow_frontend_r218','restore_personal_workflow_frontend_r250').replace('restore_production_history_runtime_r218','restore_production_history_runtime_r250')
save('run_task_attachment_r250_20261103.py',runner)
check=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(T/'verify_native_task_attachment_r250_20261103.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert check.returncode==0
D.mkdir(parents=True);(D/'preparation.json').write_text(json.dumps({'sources':sources,'attempt':'r121','onlyOwnedSyntheticG':True,'actualCandidateFrontendR224':True,'normalNinePhaseOriginalParallelWorkflowKept':True,'newTaskUploadReadinessAndInflightSaveCases':2,'publicFormalOrDesktopChanged':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preparedSuiteSources':len(sources),'attempt':'r121','twoNewTaskAttachmentChecks':True,'productOrFixtureNotYetInstalled':True}))
