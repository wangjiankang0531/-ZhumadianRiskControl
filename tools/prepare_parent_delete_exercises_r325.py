from pathlib import Path
import ast,json,subprocess,sys

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
J=lambda p:json.loads(p.read_bytes())
assert J(C/'r139-outer-terminal.json')['exitCode']==0
assert J(C/'r139-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert J(C/'prepared-r139/history-runtime-restored.json')['passed']
text=(V/'prepare_exercise_department_verified_generated_r320.py').read_text(encoding='utf-8')
text=text.replace('native_exercise_department_filter_verified_r320_20261103','native_parent_delete_with_exercises_r325_20261103')
text=text.replace('r139','r141').replace('_r320','_r325')
text=text.replace('verify_full_controller_exercise_filter_r325','verify_full_controller_parent_delete_r325')
text=text.replace('verify_native_exercise_filter_r325','verify_native_parent_delete_r325')
text=text.replace('run_native_exercise_filter_r325','run_native_parent_delete_r325')
text=text.replace('restore_exercise_department_prestart_r321.py','restore_parent_delete_prestart_r326.py')
text=text.replace('prepared-result-r317.json','prepared-result-r325.json')
text=text.replace("len(browser_result['cases']) == 16","len(browser_result['cases']) == 18")
text=text.replace("'expectedBrowserCases':16,'departmentFilterBehaviorVerification':True", "'expectedBrowserCases':18,'parentDeleteWithExercisesCharacterization':True")

parent_cases=r'''
  stage='create-unrelated-control-before-parent-with-exercises-delete';
  const keepName=name+'_KEEP_AFTER_PARENT_DELETE';writes=count('save');
  if(!await click('.table-box button','新增'))throw Error('PARENT_DELETE_CONTROL_ADD');
  await until(()=>evaluate('location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")'));
  await fill('应急预案名称',keepName);await fill('指挥长','OWN_PARENT_DELETE_CONTROL');await fill('指挥长电话','13800000000');
  if(!await evaluate('(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()'))throw Error('PARENT_DELETE_CONTROL_FILINGS');
  await fill('处置措施','OWN_UNRELATED_KEEP_AFTER_PARENT_DELETE');await click('button','提交');await until(()=>count('save')>writes);
  await until(()=>evaluate('location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")'));
  const keepPage=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(keepName));
  if(Number(keepPage.total)!==1||String(keepPage.records[0].id)===String(id))throw Error('DISTINCT_OWN_KEEP_CONTROL_REQUIRED');
  const keepId=String(keepPage.records[0].id),keepBefore=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(keepId));
  const exercisesBefore=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  if(Number(exercisesBefore.total)!==2||!exercisesBefore.records.some(r=>r.id===exercise.id))throw Error('TWO_OWN_EXERCISES_BEFORE_PARENT_DELETE_REQUIRED');
  const fileExerciseBefore=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  if(fileExerciseBefore.fileList?.length!==1||fileExerciseBefore.participants?.split(',').length!==2)throw Error('CHILD_FILE_AND_PEOPLE_BEFORE_PARENT_DELETE_REQUIRED');
  stage='actual-original-parent-delete-with-two-existing-exercises';
  await filterOwn();deleteTargetId=String(id);
  if(!await evaluate(`(()=>{const r=Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).find(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(name)})&&!e.textContent.includes(${JSON.stringify(keepName)}));const b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_PARENT_WITH_EXERCISES_DELETE_BUTTON');
  await until(()=>evaluate('Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("是否删除"))'));
  const parentDeleteBefore=count('removeById');
  if(!await click('.el-message-box__btns button','确定'))throw Error('OWN_PARENT_WITH_EXERCISES_DELETE_CONFIRM');
  await until(()=>count('removeById')===parentDeleteBefore+1);
  if(http.filter(r=>r.path.endsWith('/emergencyPlan/removeById')).at(-1).saved!==true)throw Error('PARENT_DELETE_DID_NOT_COMPLETE');
  const removedParent=await ownAPI('emergencyPlan','getPage?current=1&size=5&emergencyPlanName='+encodeURIComponent(name));
  if(removedParent.records.some(r=>String(r.id)===String(id)))throw Error('PARENT_STILL_IN_ORIGINAL_LIST');
  if(await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(id))!==null)throw Error('DELETED_PARENT_DETAILS_NOT_NULL');
  const exercisesAfter=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  const fileExerciseAfter=await ownAPI('emergencyExercise','getById?id='+encodeURIComponent(exercise.id));
  const keepAfter=await ownAPI('emergencyPlan','getById?id='+encodeURIComponent(keepId));
  if(Number(exercisesAfter.total)!==2||JSON.stringify(exercisesAfter.records.map(r=>String(r.id)).sort())!==JSON.stringify(exercisesBefore.records.map(r=>String(r.id)).sort()))throw Error('ORIGINAL_CHILD_EXERCISE_RETENTION_CHANGED');
  if(JSON.stringify(fileExerciseAfter)!==JSON.stringify(fileExerciseBefore)||JSON.stringify(keepAfter)!==JSON.stringify(keepBefore))throw Error('CHILD_DETAILS_OR_UNRELATED_PLAN_CHANGED');
  await until(()=>evaluate(`!Array.from(document.querySelectorAll('.el-table__body-wrapper tbody tr')).some(r=>r.getClientRects().length&&r.textContent.includes(${JSON.stringify(name)})&&!r.textContent.includes(${JSON.stringify(keepName)}))`));
  cases.push({case:'native-parent-with-two-exercises-delete-retains-original-child-details-and-unrelated-plan',passed:true,originalBehaviorCharacterization:true,childCascadeDeletionClaimed:false});
  stage='exercise-attachment-object-still-readable-after-parent-delete';
  const childObject=new URL(currentLink.href);
  if(childObject.origin!==wire.base)throw Error('OWN_CHILD_ATTACHMENT_ORIGIN_REQUIRED');
  const objectResponse=await fetch(childObject.href,{headers:{Authorization:token,'User-Agent':await evaluate('navigator.userAgent')},redirect:'error',signal:AbortSignal.timeout(15000)});
  if(objectResponse.status!==200)throw Error('OWN_CHILD_OBJECT_NOT_READABLE_AFTER_PARENT_DELETE');
  const objectBytes=Buffer.from(await objectResponse.arrayBuffer());
  if(!objectBytes.equals(png))throw Error('OWN_CHILD_OBJECT_BYTES_CHANGED_AFTER_PARENT_DELETE');
  cases.push({case:'native-child-attachment-metadata-and-real-object-bytes-kept-after-parent-delete',passed:true,objectStoreCascadeDeletionClaimed:false});
  await fs.writeFile(O+'/parent-delete-with-exercises-evidence.json',JSON.stringify({passed:true,parentDeleteRequests:1,parentAbsentFromListAndDetails:true,childExercisesBefore:2,childExercisesAfter:2,childDetailsPeopleAndFileMetadataUnchanged:true,realChildAttachmentHTTP:objectResponse.status,realChildAttachmentBytesIdentical:true,unrelatedOwnPlanExactDetailsUnchanged:true,actualOriginalServiceAndNormalRoleUI:true,onlyOwnSyntheticRecords:true,originalBehaviorCharacterizedNotNewCascadeRule:true,allSixResourceRelationsPopulatedOrVerifiedByThisCase:false},null,2));
'''
anchor="out=T/'verify_native_parent_delete_r325_20261103.mjs';"
assert text.count(anchor)==1
case_anchor="  cases.push({case:'native-plan-delete-real-confirm-once-parent-disappears-unrelated-plan-exercise-and-file-kept',passed:true});"
insertion="parent_case_anchor="+repr(case_anchor)+"\nassert js.count(parent_case_anchor)==1\njs=js.replace(parent_case_anchor,parent_case_anchor+'\\n'+"+repr(parent_cases)+",1)\n"
text=text.replace(anchor,insertion+anchor)
ast.parse(text)
generated=V/'prepare_parent_delete_exercises_generated_r325.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
done=subprocess.run([sys.executable,str(generated)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
if done.returncode:
    print(done.stderr.decode('utf-8',errors='replace')[-1800:]);raise RuntimeError('OWN_PARENT_DELETE_PREPARATION_REFUSED')
print(done.stdout.decode('utf-8').strip())
