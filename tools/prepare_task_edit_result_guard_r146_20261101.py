from pathlib import Path
import ast,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';B=W/'emergency-workflow-source-r15';N=W/'emergency-workflow-source-r16';C=R/'work/event_delivery_consistency_20261030/full-controller-r145/r2';J=lambda p:json.loads(p.read_bytes())
failure=J(C/'task-edit-browser/failure.json');proof=J(C/'task-edit-browser/false-edit-response-proof.json');assert failure['message']=='FALSE_TASK_EDIT_LOST_INPUT_OR_REPORTED_SUCCESS'and proof['actualCodeZeroDataFalse']and proof['successMessage']and not proof['stayed'];assert J(C/'controller-terminal.json')['exitCode']==0 and J(C/'controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']and J(C/'task-edit-browser/browser-terminal.json')['chromeExitCode']==0
relative='src/views/emergencyResponse/taskSend/info/addOrEdit.vue';raw=(B/'source'/relative).read_bytes();pin=hashlib.sha256(raw).hexdigest()
helper='''"""Keep the original task editor open unless its real API saved a row."""
import hashlib
BEFORE_SHA256=__PIN__
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF15_TASK_EDIT_SOURCE_REQUIRED')
 nl=b'\\r\\n'if b'\\r\\n'in raw else b'\\n'
 old=b'    await api({ ...field.value, uploadUrl });'
 new=("    const result = await api({ ...field.value, uploadUrl });\\n"
      "    if (result.data !== true) {\\n"
      "      ElMessage.error(\\"任务未保存，请刷新核对后重试\\");\\n"
      "      return false;\\n"
      "    }").encode('utf-8').replace(b'\\n',nl)
 if raw.count(old)!=1:raise ValueError('ONE_ORIGINAL_TASK_SAVE_REQUIRED')
 out=raw.replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalBooleanSaveResultChecked':True,'falseResultKeepsEditorAndDoesNotNavigateOrReportSuccess':True,'normalTrueResultValidationBusyAndNavigationKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
'''.replace('__PIN__',repr(pin));ast.parse(helper);ns={};exec(compile(helper,'own_task_edit_result','exec'),ns);after,receipt=ns['transform'](raw);p=T/'original_task_edit_result_compat_r146_20261101.py';assert not p.exists();p.write_bytes(helper.encode());overlay=T/'frontend/emergency-task-edit-result'/relative;overlay.parent.mkdir(parents=True,exist_ok=True);overlay.write_bytes(after)
assert not N.exists();N.mkdir();shutil.copytree(B/'source',N/'source',ignore=shutil.ignore_patterns('node_modules','dist','.git','.vite','.cache'));(N/'source'/relative).write_bytes(after);c=J(B/'source-closure.json');c['nativeTaskEditResultGuard']={'path':relative.removeprefix('src/'),'receipt':receipt,'storedSource':str(overlay)};c['publicInstalled']=False;(N/'source-closure.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for basename in ['build_emergency_workflow_source_r15_20261101.mjs','verify_emergency_workflow_source_r15_20261101.py']:
 s=(T/basename).read_text(encoding='utf-8');new=s.replace("'r14','r15']","'r14','r15','r16']");assert new!=s
 if basename.endswith('.py'):
  anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert new.count(anchor)==1
  addition=""" if rel==c.get('nativeTaskEditResultGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeTaskEditResultGuard'];origin=R/'work/user_feedback_20261031/emergency-workflow-source-r15/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_edit',T/'original_task_edit_result_compat_r146_20261101.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes());assert receipt==entry['receipt']and expected==receipt['beforeSHA256'];expected=receipt['afterSHA256'];assert generated==actual.read_bytes()
""";new=new.replace(anchor,addition+anchor);ast.parse(new)
 (T/basename.replace('_r15_','_r16_')).write_bytes(new.encode())
assert sum(p.read_bytes()!=(N/'source'/p.relative_to(B/'source')).read_bytes()for p in(B/'source').rglob('*')if p.is_file())==1
(N/'candidate-result-guard.json').write_text(json.dumps({'sourceChangedFiles':1,'receipt':receipt,'baselineFailureActuallyObserved':True,'actualCandidateRuntimeAccepted':False,'publicInstalled':False,'pendingR29And47FilesKept':True,'fullCloneReady':False},indent=2)+'\n',encoding='utf-8');print('OWN_WF16_ONE_SOURCE_TASK_EDIT_CANDIDATE_PREPARED')
