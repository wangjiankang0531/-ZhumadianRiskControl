from pathlib import Path
import ast,hashlib,json,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';B=W/'emergency-workflow-source-r16';N=W/'emergency-workflow-source-r17';P=R/'work/event_delivery_consistency_20261030/full-controller-r147/r2';J=lambda p:json.loads(p.read_bytes());before=J(P/'task-picker-browser/empty-event-confirm-proof.json');assert J(P/'task-picker-browser/failure.json')['message']=='EMPTY_TASK_EVENT_CONFIRM_NOT_GUARDED'and not before['warning'];assert not before['dialogOpen'];assert J(P/'controller-terminal.json')['exitCode']==0 and J(P/'controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']and J(P/'task-picker-browser/browser-terminal.json')['chromeExitCode']==0
relative='src/views/emergencyResponse/taskSend/info/list.vue';raw=(B/'source'/relative).read_bytes();pin=hashlib.sha256(raw).hexdigest();helper='''"""Validate the original event picker before emitting its selected record."""
import hashlib
BEFORE_SHA256=__PIN__
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF16_TASK_EVENT_PICKER_SOURCE_REQUIRED')
 nl=b'\\r\\n'if b'\\r\\n'in raw else b'\\n'
 old=b'  emit("check", nowRow);'
 active=b'// import { ElMessage } from "element-plus";'
 if raw.count(old)!=1 or raw.count(active)!=1:raise ValueError('ONE_ORIGINAL_EVENT_PICKER_AND_IMPORT_REQUIRED')
 new=("  if (!nowRow) {\\n"
      "    ElMessage.warning(\\"请先选择一条事件信息\\");\\n"
      "    return;\\n"
      "  }\\n"
      "  emit(\\"check\\", nowRow);").encode('utf-8').replace(b'\\n',nl)
 out=raw.replace(active,b'import { ElMessage } from "element-plus";',1).replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalPickerValidatesCurrentVisibleSelectedRow':True,'emptyOrInvalidatedChoiceWarnsAndKeepsDialogWithoutEmittingUndefined':True,'confirmedEventFilterOriginalRadioAndSuccessfulSelectionKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
'''.replace('__PIN__',repr(pin));ast.parse(helper);ns={};exec(compile(helper,'event_picker_guard','exec'),ns);after,receipt=ns['transform'](raw);p=T/'original_task_event_picker_compat_r148_20261101.py';assert not p.exists();p.write_bytes(helper.encode());overlay=T/'frontend/emergency-task-event-picker'/relative;overlay.parent.mkdir(parents=True,exist_ok=True);overlay.write_bytes(after);assert not N.exists();N.mkdir();shutil.copytree(B/'source',N/'source',ignore=shutil.ignore_patterns('node_modules','dist','.git','.vite','.cache'));(N/'source'/relative).write_bytes(after);c=J(B/'source-closure.json');c['nativeTaskEventPickerGuard']={'path':relative.removeprefix('src/'),'receipt':receipt,'storedSource':str(overlay)};c['publicInstalled']=False;(N/'source-closure.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_r16_20261101.mjs','verify_emergency_workflow_source_r16_20261101.py']:
 s=(T/name).read_text(encoding='utf-8');v=s.replace("'r15','r16']","'r15','r16','r17']");assert v!=s
 if name.endswith('.py'):
  anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert v.count(anchor)==1
  addition=""" if rel==c.get('nativeTaskEventPickerGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeTaskEventPickerGuard'];origin=R/'work/user_feedback_20261031/emergency-workflow-source-r16/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_picker',T/'original_task_event_picker_compat_r148_20261101.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes());assert receipt==entry['receipt']and expected==receipt['beforeSHA256'];expected=receipt['afterSHA256'];assert generated==actual.read_bytes()
""";v=v.replace(anchor,addition+anchor);ast.parse(v)
 (T/name.replace('_r16_','_r17_')).write_bytes(v.encode())
assert sum(p.read_bytes()!=(N/'source'/p.relative_to(B/'source')).read_bytes()for p in(B/'source').rglob('*')if p.is_file())==1;(N/'candidate-result-guard.json').write_text(json.dumps({'sourceChangedFiles':1,'receipt':receipt,'baselineEmptySelectionSilentlyClosesObserved':True,'actualCandidateRuntimeAccepted':False,'publicInstalled':False,'pendingR29And47FilesKept':True,'fullCloneReady':False},indent=2)+'\n',encoding='utf-8');print('OWN_WF17_SINGLE_PICKER_SOURCE_CANDIDATE_PREPARED')
