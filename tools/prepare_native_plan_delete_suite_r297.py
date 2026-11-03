from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_delete_roundtrip_r297_20261103';assert not D.exists();D.mkdir()
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
assert not(C/'prepared-r133').exists()and not(C/'r133').exists()
pins={}
def put(name,text):
    p=T/name;assert not p.exists()
    if name.endswith('.py'):ast.parse(text,filename=name)
    p.write_text(text,encoding='utf-8',newline='\n');pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
def derive(name,newname):
    return (T/name).read_text(encoding='utf-8').replace('r131','r133').replace('r132','r134').replace('_r266','_r297')

for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend']:
    put(stem+'_r297.py',derive(stem+'_r266.py',stem+'_r297.py'))
put('mapper_observation_support_r297.py',derive('mapper_observation_support_r266.py','mapper_observation_support_r297.py'))
s=derive('mapper_product_patch_r266.py','mapper_product_patch_r297.py')
s=s.replace('original_public_test_update_mapper_runtime_r265.py','original_public_test_update_r38_mapper_preflight_r286.py')
s=s.replace("'runtimeAdapterOnlyChangesDeclarations':True","'runtimeAdapterOnlyChangesDeclarations':False,'fixedFinalRuntimeSourceUsedButTransportNotApplied':True")
put('mapper_product_patch_r297.py',s)

js=(T/'verify_native_plan_exercise_r245_20261103.mjs').read_text(encoding='utf-8')
needle='let holdUpload=false,heldUpload=null,holdExercise=false,heldExercise=null,exercisePaused=0,injectExerciseFalse=false;'
assert js.count(needle)==1;js=js.replace(needle,needle+'\nlet deleteTargetId="",injectPlanDeleteFalse=false;')
needle="  const disallowed=!u||u.origin!==wire.base"
assert js.count(needle)==1
guard='''  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyPlan/removeById')){
   if(request.method!=='GET'||!deleteTargetId||u.searchParams.get('id')!==deleteTargetId)throw Error('ONLY_THIS_OWN_DELETE_TARGET_ALLOWED');
   if(injectPlanDeleteFalse){injectPlanDeleteFalse=false;await send('Fetch.fulfillRequest',{requestId:v.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Cache-Control',value:'no-store'}],body:Buffer.from(JSON.stringify({code:0,data:false,msg:'OWN_CLIENT_DELETE_FALSE_INJECTION'})).toString('base64')},v.sessionId);return;}
  }
'''
js=js.replace(needle,guard+needle)
needle="  if(exceptions.length)throw Error('CANDIDATE_ORIGINAL_UI_EXCEPTION');"
assert js.count(needle)==1
extra=r'''
  stage='close-own-exercise-details-and-create-delete-target';
  for(const title of ['演练记录详情','演练记录']){
   if(!await evaluate(`(()=>{const d=${dialogTitle(title)},b=d?.querySelector('.el-dialog__headerbtn');b?.click();return!!b})()`))throw Error('OWN_MODAL_CLOSE_'+title);
   await until(()=>evaluate(`!(${dialogTitle(title)})`));
  }
  activeFormTitle=null;
  const deletionName=name+'_DELETE_ONLY';writes=count('save');
  if(!await click('.table-box button','新增'))throw Error('DELETE_TARGET_ADD');
  await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
  await fill('应急预案名称',deletionName);await fill('指挥长','OWN_DELETE_COMMANDER');await fill('指挥长电话','13800000000');
  if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('DELETE_TARGET_FILINGS');
  await fill('处置措施','OWN_DELETE_ONLY_NO_CHILDREN');await click('button','提交');await until(()=>count('save')>writes);
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  const deletePage=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName));
  if(Number(deletePage.total)!==1||deletePage.records[0].id===id)throw Error('DISTINCT_OWN_DELETE_TARGET_REQUIRED');
  deleteTargetId=String(deletePage.records[0].id);
  const ownTargetExercises=await ownAPI('emergencyExercise','getPage?current=1&size=5&emergencyPlanId='+encodeURIComponent(deleteTargetId));
  if(Number(ownTargetExercises.total)!==0)throw Error('DELETE_TARGET_MUST_HAVE_NO_CHILDREN');
  if(await value('应急预案名称')===null)await click('.table-search button','更多');await fill('应急预案名称',deletionName);
  let searches=count('getPage');await click('.table-search button','搜索');await until(()=>count('getPage')>searches);
  async function deleteOwnTarget(){
   if(!await evaluate(`(()=>{const r=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(deletionName)}));const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_DELETE_ROW_BUTTON');
   await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("是否删除"))'));
  }
  stage='native-delete-cancel-does-not-send-request';
  const beforeCancel=count('removeById');await deleteOwnTarget();
  if(!await click('.el-message-box__btns button','取消'))throw Error('OWN_DELETE_CANCEL');
  await until(()=>evaluate('!Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length)'));await sleep(200);
  if(count('removeById')!==beforeCancel)throw Error('CANCEL_SENT_DELETE');
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==1)throw Error('CANCEL_REMOVED_PLAN');
  cases.push({case:'native-plan-delete-cancel-no-request-record-kept',passed:true});
  stage='native-delete-false-response-keeps-record-no-success';injectPlanDeleteFalse=true;
  await deleteOwnTarget();if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_DELETE_FALSE_CONFIRM');
  await until(()=>count('removeById')===beforeCancel+1);
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message--error")).some(e=>e.getClientRects().length&&e.textContent.includes("删除未完成"))'));
  if(http.filter(x=>x.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==false)throw Error('FALSE_DELETE_NOT_OBSERVED');
  if(await evaluate('Array.from(document.querySelectorAll(".el-message--success")).some(e=>e.getClientRects().length&&e.textContent.includes("删除成功"))'))throw Error('FALSE_DELETE_REPORTED_SUCCESS');
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==1)throw Error('INJECTED_FALSE_DELETE_CHANGED_SERVER');
  cases.push({case:'native-plan-delete-browser-false-no-server-write-keeps-record-and-reports-failure',passed:true,realSQLFailureClaimed:false});
  stage='native-delete-real-confirm-once-and-control-record-retained';
  const beforeReal=count('removeById');await deleteOwnTarget();if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_DELETE_REAL_CONFIRM');
  await until(()=>count('removeById')===beforeReal+1);
  if(http.filter(x=>x.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==true)throw Error('REAL_DELETE_NOT_CONFIRMED');
  await until(()=>evaluate(`!Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(deletionName)}))`));
  if(Number((await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(deletionName))).total)!==0)throw Error('REAL_DELETE_NOT_PERSISTED');
  const control=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id));
  const controlExercise=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  if(control.emergencyPlanName!==name||control.disposalMeasures!=='OWN_PLAN_REVISED_R222'||controlExercise.emergencyPlanId!==id||controlExercise.fileList?.length!==1||controlExercise.participants?.split(',').length!==2)throw Error('UNRELATED_CONTROL_PLAN_EXERCISE_OR_ATTACHMENT_CHANGED');
  cases.push({case:'native-plan-delete-real-confirm-once-parent-disappears-unrelated-plan-exercise-and-file-kept',passed:true});
'''
js=js.replace(needle,extra+'\n'+needle)
put('verify_native_plan_delete_r297_20261103.mjs',js)
host=derive('verify_full_controller_mapper_product_r266.py','verify_full_controller_plan_delete_r297.py')
host=host.replace('verify_native_plan_exercise_r245_20261103.mjs','verify_native_plan_delete_r297_20261103.mjs')
host=host.replace("len(browser_result['cases'])>=6","len(browser_result['cases'])==14")
put('verify_full_controller_plan_delete_r297.py',host)
runner=derive('run_mapper_product_r266.py','run_native_plan_delete_r297.py').replace('verify_full_controller_mapper_product_r297.py','verify_full_controller_plan_delete_r297.py')
put('run_native_plan_delete_r297.py',runner)
node_check=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(T/'verify_native_plan_delete_r297_20261103.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert node_check.returncode==0,'NEW_BROWSER_SOURCE_SYNTAX_FAILED'
report={'prepared':True,'attempt':'r133','sourcePins':pins,'actualFinalRuntimeSource':'original_public_test_update_r38_mapper_preflight_r286.py',
 'normalRoleExpectedCases':14,'newDeleteCases':3,'falseResponseInjectionNotSQLFailure':True,
 'onlyOneNewOwnNoChildPlanMayBeDeleted':True,'unrelatedOwnPlanExerciseAndFileMustRemain':True,
 'currentCompiledConfirmationHookAlreadyCorrectNotNewProductFix':True,
 'newProductCodeOrPublicDeploymentChanged':False,'fixturePreparedOrRuntimeStarted':False}
(D/'preparation-r297.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preparedSources':len(pins),'attempt':'r133','browserExpectedCases':14,'newDeleteCases':3,'runtimeStarted':False}))
