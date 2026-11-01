from pathlib import Path
import ast,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';B=W/'emergency-workflow-source-r14';N=W/'emergency-workflow-source-r15';relative='src/views/emergencyResponse/taskSend/info/detail.vue';before=(B/'source'/relative).read_bytes();pin=hashlib.sha256(before).hexdigest()
# Candidate preparation cannot be confused with observed failure or deployed acceptance.
helper='''"""Preserve native task disposal input when the original update API saved no row."""
import hashlib
BEFORE_SHA256=__PIN__
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF14_TASK_DISPOSAL_SOURCE_REQUIRED')
 nl=b'\\r\\n'if b'\\r\\n'in raw else b'\\n'
 old=b'    await updateById(fieldJudge.value);'
 new=("    const result = await updateById(fieldJudge.value);\\n"
      "    if (result.data !== true) {\\n"
      "      ElMessage.error(\\"任务未保存，请刷新核对后重试\\");\\n"
      "      return false;\\n"
      "    }").encode('utf-8').replace(b'\\n',nl)
 if raw.count(old)!=1:raise ValueError('ONE_NATIVE_TASK_DISPOSAL_UPDATE_REQUIRED')
 out=raw.replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalBooleanSaveResultChecked':True,'falseResultKeepsFeedbackAndDoesNotNavigateOrReportSuccess':True,'normalTrueResultValidationBusyAndNavigationKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
'''.replace('__PIN__',repr(pin));ast.parse(helper);ns={};exec(compile(helper,'candidate_task_feedback_guard','exec'),ns);after,receipt=ns['transform'](before)
path=T/'original_task_feedback_result_compat_r143_20261101.py';path.write_bytes(helper.encode());overlay=T/'frontend/emergency-task-feedback-result'/relative;overlay.parent.mkdir(parents=True,exist_ok=True);overlay.write_bytes(after)
assert not N.exists();N.mkdir();shutil.copytree(B/'source',N/'source',ignore=shutil.ignore_patterns('node_modules','dist','.git','.vite','.cache'))
(N/'source'/relative).write_bytes(after);c=json.loads((B/'source-closure.json').read_bytes());c['nativeTaskFeedbackResultGuard']={'path':relative.removeprefix('src/'),'receipt':receipt,'storedSource':str(overlay)};c['publicInstalled']=False;(N/'source-closure.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
builder=(T/'build_emergency_workflow_source_20261101.mjs').read_text(encoding='utf-8').replace("'r13','r14']","'r13','r14','r15']");assert builder!=(T/'build_emergency_workflow_source_20261101.mjs').read_text(encoding='utf-8');(T/'build_emergency_workflow_source_r15_20261101.mjs').write_bytes(builder.encode())
v=(T/'verify_emergency_workflow_source_20261101.py').read_text(encoding='utf-8').replace("'r13','r14']","'r13','r14','r15']")
anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert v.count(anchor)==1
addition=""" if rel==c.get('nativeTaskFeedbackResultGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeTaskFeedbackResultGuard'];origin=R/'work/user_feedback_20261031/emergency-workflow-source-r14/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_feedback',T/'original_task_feedback_result_compat_r143_20261101.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes());assert receipt==entry['receipt']and expected==receipt['beforeSHA256'];expected=receipt['afterSHA256'];assert generated==actual.read_bytes()
"""
v=v.replace(anchor,addition+anchor);ast.parse(v);(T/'verify_emergency_workflow_source_r15_20261101.py').write_bytes(v.encode())
count=0
for p in(B/'source').rglob('*'):
 if p.is_file():
  other=N/'source'/p.relative_to(B/'source');assert other.exists();count+=other.read_bytes()!=p.read_bytes()
assert count==1
(N/'candidate-result-guard.json').write_text(json.dumps({'sourceChangedFiles':1,'receipt':receipt,'baselineFailureObserved':False,'actualRuntimeAccepted':False,'publicInstalled':False,'fullCloneReady':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'oneSourceCandidatePrepared':True,'inputSHA256':pin,'actualFailureAndRuntimeAcceptanceStillPending':True,'publicInstalled':False}))
