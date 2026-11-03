from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_plan_submit_observation_r245_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()and all(not(C/n).exists()for n in ['r119','r120','prepared-r119','prepared-r120'])
assert J(C/'prepared-r117/history-runtime-restored.json')['passed']and J(C/'r117-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert sha(A/'release-manifest.json')==J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256']
names=['verify_full_controller_plan_exercise_r243_20261103.py','verify_native_plan_exercise_r243_20261103.mjs','plan_mapper_patch_r243.py']
for mode in ['baseline','candidate']:
 for group in ['personal_workflow_frontend','production_history_runtime']:
  names += [f'{verb}_{group}_r243_{mode}.py'for verb in ['prepare','restore']]
 names += [f'run_plan_exercise_r243_{mode}_20261103.py']
pins={}
for name in names:
 text=(T/name).read_text(encoding='utf-8').replace('r243','r245').replace('r117','r119').replace('r118','r120')
 if name.endswith('.mjs'):
  needle='let activeFormTitle=null,optionalJoinConsoleErrors=0;';assert text.count(needle)==1;text=text.replace(needle,'let activeFormTitle=null,optionalJoinConsoleErrors=0,optionalJoinDebuggerErrors=0;const debuggerObservations=[];')
  needle=" }else if(v.method==='Runtime.consoleAPICalled')";assert text.count(needle)==1
  block=""" }else if(v.method==='Debugger.paused'){
  const description=String(v.params.data?.description||v.params.data?.value||'');const optionalJoin=/join/.test(description)&&/undefined|TypeError/.test(description);
  if(optionalJoin)optionalJoinDebuggerErrors++;
  if(debuggerObservations.length<16)debuggerObservations.push({reason:v.params.reason,optionalJoinObserved:optionalJoin,topFunction:v.params.callFrames?.[0]?.functionName||''});
  await send('Debugger.resume',{},v.sessionId);
"""
  text=text.replace(needle,block+needle)
  old="e.textContent.trim()===${JSON.stringify(text)});e?.click();return!!e})()`);}";new="e.textContent.replace(/\\\\s/g,'')===${JSON.stringify(String(text).replace(/\\s/g,''))}&&!e.disabled);e?.click();return!!e})()`);}"
  assert text.count(old)==1;text=text.replace(old,new)
  needle="const beforeEmpty=exerciseCount();await modalClick('新增演练记录','.el-dialog__footer button','确定');";assert text.count(needle)==1
  replacement="""if(wire.baseline){await send('Debugger.enable',{},session);await send('Debugger.setPauseOnExceptions',{state:'all'},session);}
 const beforeEmpty=exerciseCount();
 const submitObservation=await evaluate(`(()=>{const d=${dialogTitle('新增演练记录')};return{dialogFound:!!d,footers:Array.from(d?.querySelectorAll('.el-dialog__footer button')||[]).map(e=>({text:e.textContent.trim(),disabled:e.disabled,visible:!!e.getClientRects().length})),errors:Array.from(d?.querySelectorAll('.el-form-item__error')||[]).map(e=>e.textContent.trim())}})()`);
 await fs.writeFile(O+'/before-exercise-submit.json',JSON.stringify(submitObservation,null,2));
 if(!await modalClick('新增演练记录','.el-dialog__footer button','确定'))throw Error('EXACT_VISIBLE_EXERCISE_SUBMIT_BUTTON_NOT_CLICKED');"""
  text=text.replace(needle,replacement)
  needle='optionalJoinConsoleErrors>0||exceptions.some';assert text.count(needle)==1;text=text.replace(needle,'optionalJoinConsoleErrors>0||optionalJoinDebuggerErrors>0||exceptions.some')
  needle='actualUndefinedJoinErrorObservedViaRuntimeOrConsole:true,';assert text.count(needle)==1
  text=text.replace(needle,"actualUndefinedJoinErrorObservedViaRuntimeOrConsole:optionalJoinConsoleErrors>0||exceptions.some(x=>/join|undefined/.test(x.description||'')),actualUndefinedJoinErrorObservedViaDebugger:optionalJoinDebuggerErrors>0,")
  needle="cases.push({case:'baseline-real-normal-page-optional-persons-trigger-undefined-join-before-save',passed:true});";assert text.count(needle)==1
  text=text.replace(needle,needle+"\n  await send('Debugger.setPauseOnExceptions',{state:'none'},session);await fs.writeFile(O+'/debugger-observations.json',JSON.stringify(debuggerObservations,null,2));")
  old="const dom=await send('DOM.getDocument',{depth:-1},session),input=await send('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'input[type=file]'},session);"
  new="""await send('DOM.getDocument',{depth:-1},session);const inputObject=await send('Runtime.evaluate',{expression:`(${dialogTitle('新增演练记录')})?.querySelector('input[type=file]')`,returnByValue:false},session);if(inputObject.exceptionDetails||!inputObject.result.objectId)throw Error('EXACT_EXERCISE_MODAL_FILE_INPUT_REQUIRED');const input=await send('DOM.requestNode',{objectId:inputObject.result.objectId},session);"""
  assert text.count(old)==1;text=text.replace(old,new)
  text=text.replace('const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads};','const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads,debuggerObservations};')
 dest=T/name.replace('r243','r245');assert not dest.exists();dest.write_text(text,encoding='utf-8');pins[dest.name]=sha(dest)
 if dest.suffix=='.py':ast.parse(text)
 else:
  q=subprocess.run(['node','--check',str(dest)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert q.returncode==0
D.mkdir(parents=True);proof={'prepared':True,'sources':pins,'baselineAttempt':'r119','candidateAttempt':'r120','sameProductFrontendAndBackendAsR117AndR224':True,'actualSubmitReturnMustBeTrue':True,'observesCaughtExceptionsViaDebuggerWithImmediateResume':True,'noProductHandlersOrDataPatchedToCreateException':True,'fileInputSelectedOnlyFromActiveExerciseDialog':True,'normalLoginAndAllPriorNativeBusinessAssertionsRetained':True,'publicFormalOrDesktopTouched':False,'actualRunPassed':False}
(D/'preparation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in proof.items()if k!='sources'}))
