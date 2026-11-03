from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
browser=(V/'verify_native_plan_six_relations_typed_r390.mjs').read_text(encoding='utf-8')
start=browser.index(' async function removeResourceA(kind){');end=browser.index(' function checkRelations(',start)
browser=browser[:start]+r'''
 const resourceDeletionSteps=[];
 const boxVisible="Array.from(document.querySelectorAll('.el-message-box')).filter(e=>e.getClientRects().length)";
 async function removeResourceA(kind){
  stage='resource-'+kind.entity+'-enter-tab';await resourceTab(kind);
  await until(()=>evaluate(`(${boxVisible}).length===0`));
  async function remove(action){
   stage='resource-'+kind.entity+'-open-'+action;
   if(!await evaluate(`(()=>{const p=${pane()},r=Array.from(p?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).find(e=>e.textContent.includes(${JSON.stringify(kind.ownA)})),b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_RESOURCE_REMOVE_BUTTON');
   await until(()=>evaluate(`(${boxVisible}).length===1&&(${boxVisible})[0].textContent.includes('确认删除')`));
   resourceDeletionSteps.push({kind:kind.entity,phase:action+'-opened'});
  }
  async function action(text){
   if(!await evaluate(`(()=>{const boxes=${boxVisible};if(boxes.length!==1)return false;const b=Array.from(boxes[0].querySelectorAll('.el-message-box__btns button')).find(e=>e.textContent.trim()===${JSON.stringify(text)}&&!e.disabled);b?.click();return!!b})()`))throw Error('OWN_EXACT_ONE_RESOURCE_CONFIRMATION_BUTTON');
   await until(()=>evaluate(`(${boxVisible}).length===0`));
  }
  await remove('cancel');stage='resource-'+kind.entity+'-cancel-and-close';await action('取消');
  await until(async()=>await selectedResourceCount()===2);resourceDeletionSteps.push({kind:kind.entity,phase:'cancel-kept-two-and-dialog-closed'});
  await remove('confirm');stage='resource-'+kind.entity+'-confirm-and-close';await action('确定');
  await until(async()=>await selectedResourceCount()===1);
  if(!await evaluate(`(${pane()})?.textContent.includes(${JSON.stringify(kind.ownB)})===true`))throw Error('OWN_RESOURCE_REMOVE_RETAIN_B');
  resourceDeletionSteps.push({kind:kind.entity,phase:'confirm-kept-B-and-dialog-closed'});
 }
'''+browser[end:]
browser=browser.replace("const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads,debuggerObservations};","const diagnostic={stage,message:failed,cases,http,blocked,exceptions,downloads,debuggerObservations};try{diagnostic.resourceDeletionSteps=resourceDeletionSteps;diagnostic.visibleBoxes=await evaluate(`(${boxVisible}).map(e=>({text:e.innerText,buttons:Array.from(e.querySelectorAll('button')).map(b=>({text:b.textContent,disabled:b.disabled}))}))`)}catch{}")
# The lexical diagnostics above are inside try; retain stage even if they are unavailable in catch.
bf=V/'verify_native_plan_six_relations_dialog_r394.mjs';assert not bf.exists();bf.write_text(browser,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
s=(V/'plan_typed_run_r390.py').read_text(encoding='utf-8');prefix=s.split("dump(O/'run-started.json'",1)[0]
prefix=prefix.replace('plan-six-relations-typed-r390','plan-six-relations-ui-r394').replace('lifecycle-r390','lifecycle-r394')
prefix=prefix.replace("full-controller-r163/r151'","full-controller-r163/r153'")
prefix=prefix.replace('verify_native_plan_six_relations_typed_r390.mjs',bf.name).replace('651b39eb27ec1894d15dd9d6d00cdc3e7779ec6135dc2571de8d1ad7f817a937',sha(bf))
prefix=prefix.replace("scope['desiredBaseline'].get(name,'unchanged-original')","scope['desiredCandidate'].get(name,'unchanged-original')")
suffix=r'''
dump(O/'run-started.json',{'started':True,'normalUIIterationOnly':True,'newApplyOrRollbackNotClaimed':True})
installed=False
try:
    unchanged_private()
    for n,value in scope['originalBefore'].items():assert pin(A/n)==value,'ORIGINAL_PREIMAGE_DRIFT'
    phase='install-owned-exact-candidate-code-for-UI-iteration'
    for n,value in scope['desiredCandidate'].items():
        p=A/n;assert_plain(p)
        if value is None:
            if p.exists():p.unlink()
        else:
            source=Path(value['source']);assert pin(source)=={k:value[k]for k in ['bytes','sha256']};atomic(p,source.read_bytes())
    installed=True
    with patch.object(m,'owned_ready',local_owned),patch.object(m,'health',local_health),patch.object(m,'launch',local_launch),patch.object(subprocess,'Popen',observed_popen):
        plan=J(O/'bundle/update-manifest.json')
        assert sha(A/'release-manifest.json')==scope['candidateAdaptedR39SHA256']
        assert m.candidate_runtime_pool_preflight(A,O/'bundle',plan)['originalMapperPreflight']['passed']
        phase='normal-launch-one-real-candidate-controller';boot=O/'candidate-boot';boot.mkdir()
        row=m.launch(A,scope['candidateAdaptedR39SHA256'],boot);m.health(A,row)
        phase='candidate-models-before-UI';before=schema_snapshot('before-ui',row)
        phase='actual-current-entry-gzip';static=verify_candidate_static();dump(O/'candidate-static-HTTP.json',{'passed':True,'checks':static,'actualIISTLS':False})
        phase='normal-role-29-case-UI-iteration';ui=verify_native_candidate(row)
        phase='candidate-models-after-UI';assert schema_snapshot('after-ui',row)==before
        print('OWN_ALL_SIX_RELATIONS_NORMAL_ROLE_29_CASES_PASSED',flush=True)
except BaseException as error:
    failure={'type':type(error).__name__,'phase':phase,'message':str(error)if isinstance(error,(AssertionError,ValueError))else'OWN_UI_ITERATION_FAILED_INSPECT_SCOPED_RESULT'}
    dump(O/'failure.json',failure)
finally:
    normal_stop_every_owned_process()
    if installed:
        try:restore_original();restored=True
        except BaseException as e:dump(O/'restore-refused.json',{'type':type(e).__name__,'message':str(e),'noForce':True})
    dump(O/'terminal.json',{'failure':failure,'allOwnedControllerHandlesTerminal':all(v['process'].poll()is not None for v in processes),
       'controllers':terminal,'originalGCodeAndPointersRestored':restored,'forceTerminationUsed':False,'newApplyOrRollbackNotClaimed':True})
assert failure is None and restored
assert len(terminal)==1 and terminal[0]['controllerExitCode']==0 and terminal[0]['actualJobDescendantsZero']
dump(D/'verified-native-r394.json',{'passed':True,'actualNormalRoleCases':29,'normalOneControllerUIIteration':True,'newApplyOrRollbackNotClaimed':True,
 'priorR390ActualApplyAndRollbackEvidenceSeparate':True,'original398ModelsBeforeAfterUIMatched':True,'normalControllerChromeAndActualDescendantsZero':True,
 'originalGCodeConfigurationAndPointersRestored':True,'actualIISHTTPSOrPublicVerified':False,'fullCloneReady':False})
'''
out=V/'plan_relation_ui_r394.py';assert not out.exists();ast.parse(prefix+suffix);out.write_text(prefix+suffix,encoding='utf-8')
report={'preparedOnly':True,'browserSHA256':sha(bf),'driverSHA256':sha(out),'sameR40ProductCandidate':True,
 'eachCancelAndConfirmWaitsForNoVisibleMessageBox':True,'exactSingleVisibleMessageBoxButtonScoped':True,
 'native29Pending':True,'newApplyRollbackNotClaimedByThisIteration':True}
(D/'ui-iteration-prepared-r393.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
