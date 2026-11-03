from pathlib import Path
import ast,ctypes,hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103'
assert not D.exists()and not(C/'prepared-r141').exists()and not(C/'r141').exists()
assert hashlib.sha256((R/'_g/Application/release-manifest.json').read_bytes()).hexdigest()=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert json.loads((C/'prepared-r135/history-runtime-restored.json').read_bytes())['passed']
memory=(ctypes.c_ulonglong*8)();memory[0]=64
assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>6*1024**3,'SIX_GIB_ADMISSION_REQUIRED_BEFORE_MUTATION'
schema=R/'work/event_delivery_consistency_20261030/full-controller-r131'
assert(schema/'schema-reader.json').is_file()and(schema/'original-table-names.txt').is_file()

class Rewrite(ast.NodeTransformer):
    def visit_Constant(self,node):
        if not isinstance(node.value,str):return node
        v=node.value
        if v=='r135':v='r141'
        elif v=='prepared-r135':v='prepared-r141'
        elif v.startswith('r135/'):v='r141/'+v[5:]
        v=v.replace('_r304','_r325')
        v=v.replace('verify_native_plan_delete_r325_20261103.mjs','verify_native_parent_delete_r325_20261103.mjs')
        v=v.replace('verify_full_controller_plan_delete_r325.py','verify_full_controller_parent_delete_r325.py')
        return ast.copy_location(ast.Constant(v),node)

D.mkdir();pins={}
def save(src,dst):
    tree=Rewrite().visit(ast.parse((T/src).read_bytes()));ast.fix_missing_locations(tree)
    raw=(ast.unparse(tree)+'\n').encode();ast.parse(raw,filename=dst)
    target=T/dst;assert not target.exists();target.write_bytes(raw);pins[dst]=hashlib.sha256(raw).hexdigest()

for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend','mapper_product_patch','mapper_observation_support']:
    save(stem+'_r304.py',stem+'_r325.py')
save('verify_full_controller_plan_delete_r304.py','verify_full_controller_parent_delete_r325.py')
save('run_native_plan_delete_r304.py','run_native_parent_delete_r325.py')
runner=T/'run_native_parent_delete_r325.py'
raw=runner.read_text(encoding='utf-8').replace('r135','r141')
runner.write_text(raw,encoding='utf-8');pins[runner.name]=hashlib.sha256(runner.read_bytes()).hexdigest()
host=T/'verify_full_controller_parent_delete_r325.py';text=host.read_text(encoding='utf-8')
assert "schema_base = R / 'work/event_delivery_consistency_20261030/full-controller-r131'"in text
assert "options.attempt in ['r141']"in text
assert text.count("'baseline': options.attempt == 'r129'")==1
text=text.replace("'baseline': options.attempt == 'r129'","'baseline': options.attempt == 'r129', 'exerciseDepartmentBaseline': False")
assert text.count("len(browser_result['cases']) == 14")==1
text=text.replace("len(browser_result['cases']) == 14","len(browser_result['cases']) == 18")
ast.parse(text);host.write_text(text,encoding='utf-8');pins[host.name]=hashlib.sha256(host.read_bytes()).hexdigest()

js=(T/'verify_native_plan_delete_r304_20261103.mjs').read_text(encoding='utf-8')
anchor="let deleteTargetId=\"\",injectPlanDeleteFalse=false;"
assert js.count(anchor)==1;js=js.replace(anchor,anchor+'\nconst exerciseFilterRequests=[];')
anchor="  const disallowed=!u||u.origin!==wire.base"
assert js.count(anchor)==1;js=js.replace(anchor,"  if(u?.origin===wire.base&&u.pathname.endsWith('/emergencyExercise/getPage'))exerciseFilterRequests.push({legacyDepartmentNonempty:!!u.searchParams.get('department'),canonicalOrganizeDepartmentNonempty:!!u.searchParams.get('organizeDepartment')});\n"+anchor)
anchor="   row.businessCode=b.code;"
assert js.count(anchor)==1;js=js.replace(anchor,"   if(row.path.endsWith('/emergencyExercise/getPage'))row.exerciseTotal=Number(b.data?.total);\n"+anchor)
anchor="  stage='close-own-exercise-details-and-create-delete-target';"
assert js.count(anchor)==1
extra=r'''
  stage='exercise-organize-department-filter-baseline-or-fixed';
  if(!await evaluate(`(()=>{const d=${dialogTitle('演练记录详情')},b=d?.querySelector('.el-dialog__headerbtn');b?.click();return!!b})()`))throw Error('EXERCISE_DETAIL_CLOSE_FOR_SEARCH');
  await until(()=>evaluate(`!(${dialogTitle('演练记录详情')})`));
  activeFormTitle='演练记录';
  const unfiltered=await ownAPI('emergencyExercise','getPage?current=1&size=20&emergencyPlanId='+encodeURIComponent(id));
  if(Number(unfiltered.total)!==2||!unfiltered.records.some(r=>r.id===exercise.id&&r.organizeDepartment)||!unfiltered.records.some(r=>r.id!==exercise.id&&!r.organizeDepartment))throw Error('TWO_OWN_DEPARTMENT_DISTINCT_EXERCISES_REQUIRED');
  const searchDepartmentVisible=()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')};return Array.from(d?.querySelectorAll('.table-search .el-form-item')||[]).some(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()==='组织部门')})()`);
  if(!await searchDepartmentVisible()){
   if(!await modalClick('演练记录','.table-search button','更多'))throw Error('EXERCISE_SEARCH_MORE');
   await until(searchDepartmentVisible);
  }
  if(!await evaluate(`(()=>{const d=${dialogTitle('演练记录')},f=Array.from(d.querySelectorAll('.table-search .el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()==='组织部门');const e=f?.querySelector('.el-select__wrapper,.el-input__wrapper');e?.click();return!!e})()`))throw Error('EXERCISE_SEARCH_DEPARTMENT_FIELD');
  await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-tree-node__content')).some(e=>e.getClientRects().length&&e.textContent.trim()===${JSON.stringify(department)})`));
  if(!await click('.el-tree-node__content',department))throw Error('EXERCISE_SEARCH_DEPARTMENT_CHOICE');
  const beforeFilter=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length;
  if(!await modalClick('演练记录','.table-search button','搜索'))throw Error('EXERCISE_SEARCH_BUTTON');
  await until(()=>http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length>beforeFilter);
  const filtered=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).at(-1),query=exerciseFilterRequests.at(-1);
  await fs.writeFile(O+'/department-filter-observed-before-assert.json',JSON.stringify({httpStatus:filtered.httpStatus,businessCode:filtered.businessCode,filteredRows:filtered.exerciseTotal,requestShape:query},null,2));
  if(wire.exerciseDepartmentBaseline){
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==2||!query.legacyDepartmentNonempty||query.canonicalOrganizeDepartmentNonempty)throw Error('EXPECTED_LEGACY_DEPARTMENT_FILTER_REPRO_NOT_OBSERVED');
  }else{
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==1||!query.canonicalOrganizeDepartmentNonempty)throw Error('CORRECT_ORGANIZE_DEPARTMENT_FILTER_NOT_OBSERVED');
  }
  await fs.writeFile(O+'/department-filter-evidence.json',JSON.stringify({reproducedLegacyKeyIgnored:!!wire.exerciseDepartmentBaseline,unfilteredRows:2,filteredRows:filtered.exerciseTotal,requestShape:query,actualOriginalBackendAndCompiledPage:true,onlyOwnSyntheticRecords:true,businessRowsChangedByFilter:false},null,2));
  cases.push({case:wire.exerciseDepartmentBaseline?'native-exercise-department-legacy-key-reproduces-two-unfiltered-rows':'native-exercise-organize-department-filters-two-records-to-one',passed:true,defectReproduced:!!wire.exerciseDepartmentBaseline});

  await until(()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')},rows=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(r=>r.getClientRects().length);return rows.length===1&&rows[0].textContent.includes(${JSON.stringify(exerciseName+'_FILE')})&&!rows[0].textContent.includes(${JSON.stringify(exerciseName+'_EMPTY')})})()`));
  stage='exercise-organize-department-reset-restores-parent-scoped-two-records';
  const beforeReset=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length;
  if(!await modalClick('演练记录','.table-search button','重置'))throw Error('EXERCISE_FILTER_RESET_BUTTON');
  await until(()=>http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).length>beforeReset);
  const reset=http.filter(r=>r.path.endsWith('/emergencyExercise/getPage')).at(-1),resetQuery=exerciseFilterRequests.at(-1);
  if(reset.httpStatus!==200||reset.businessCode!==0||reset.exerciseTotal!==2||resetQuery.canonicalOrganizeDepartmentNonempty)throw Error('EXERCISE_RESET_DID_NOT_CLEAR_CANONICAL_FILTER');
  await until(()=>evaluate(`(()=>{const d=${dialogTitle('演练记录')},rows=Array.from(d?.querySelectorAll('.el-table__body-wrapper tbody tr')||[]).filter(r=>r.getClientRects().length);return rows.length===2&&rows.some(r=>r.textContent.includes(${JSON.stringify(exerciseName+'_FILE')}))&&rows.some(r=>r.textContent.includes(${JSON.stringify(exerciseName+'_EMPTY')}))})()`));
  await fs.writeFile(O+'/department-filter-reset-evidence.json',JSON.stringify({passed:true,filteredRows:1,resetRows:2,requestShape:query,resetRequestShape:resetQuery,actualVisibleRowsMatchedBothResponses:true,actualOriginalBackendAndCompiledPage:true,onlyOwnSyntheticRecords:true,businessRowsChangedByFilterOrReset:false},null,2));
  cases.push({case:'native-exercise-department-reset-restores-both-parent-scoped-records',passed:true});
  activeFormTitle=null;
'''
js=js.replace(anchor,extra+'\n'+anchor)
anchor="  for(const title of ['演练记录详情','演练记录']){"
assert js.count(anchor)==1;js=js.replace(anchor,"  for(const title of ['演练记录']){")
parent_case_anchor="  cases.push({case:'native-plan-delete-real-confirm-once-parent-disappears-unrelated-plan-exercise-and-file-kept',passed:true});"
assert js.count(parent_case_anchor)==1
js=js.replace(parent_case_anchor,parent_case_anchor+'\n'+'\n  stage=\'create-unrelated-control-before-parent-with-exercises-delete\';\n  const keepName=name+\'_KEEP_AFTER_PARENT_DELETE\';writes=count(\'save\');\n  if(!await click(\'.table-box button\',\'新增\'))throw Error(\'PARENT_DELETE_CONTROL_ADD\');\n  await until(()=>evaluate(\'location.pathname.endsWith("/structured/add")&&!!document.querySelector(".info-title")\'));\n  await fill(\'应急预案名称\',keepName);await fill(\'指挥长\',\'OWN_PARENT_DELETE_CONTROL\');await fill(\'指挥长电话\',\'13800000000\');\n  if(!await evaluate(\'(()=>{const f=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="是否备案");const e=Array.from(f?.querySelectorAll(".el-radio")||[]).find(e=>e.textContent.trim()==="否");e?.click();return!!e})()\'))throw Error(\'PARENT_DELETE_CONTROL_FILINGS\');\n  await fill(\'处置措施\',\'OWN_UNRELATED_KEEP_AFTER_PARENT_DELETE\');await click(\'button\',\'提交\');await until(()=>count(\'save\')>writes);\n  await until(()=>evaluate(\'location.pathname.endsWith("/emergencyPlans/structured")&&!!document.querySelector(".table-search")\'));\n  const keepPage=await ownAPI(\'emergencyPlan\',\'getPage?current=1&size=5&emergencyPlanName=\'+encodeURIComponent(keepName));\n  if(Number(keepPage.total)!==1||String(keepPage.records[0].id)===String(id))throw Error(\'DISTINCT_OWN_KEEP_CONTROL_REQUIRED\');\n  const keepId=String(keepPage.records[0].id),keepBefore=await ownAPI(\'emergencyPlan\',\'getById?id=\'+encodeURIComponent(keepId));\n  const exercisesBefore=await ownAPI(\'emergencyExercise\',\'getPage?current=1&size=20&emergencyPlanId=\'+encodeURIComponent(id));\n  if(Number(exercisesBefore.total)!==2||!exercisesBefore.records.some(r=>r.id===exercise.id))throw Error(\'TWO_OWN_EXERCISES_BEFORE_PARENT_DELETE_REQUIRED\');\n  const fileExerciseBefore=await ownAPI(\'emergencyExercise\',\'getById?id=\'+encodeURIComponent(exercise.id));\n  if(fileExerciseBefore.fileList?.length!==1||fileExerciseBefore.participants?.split(\',\').length!==2)throw Error(\'CHILD_FILE_AND_PEOPLE_BEFORE_PARENT_DELETE_REQUIRED\');\n  stage=\'actual-original-parent-delete-with-two-existing-exercises\';\n  await filterOwn();deleteTargetId=String(id);\n  if(!await evaluate(`(()=>{const r=Array.from(document.querySelectorAll(\'.el-table__body-wrapper tbody tr\')).find(e=>e.getClientRects().length&&e.textContent.includes(${JSON.stringify(name)})&&!e.textContent.includes(${JSON.stringify(keepName)}));const b=Array.from(r?.querySelectorAll(\'button\')||[]).find(e=>e.textContent.trim()===\'删除\');b?.click();return!!b})()`))throw Error(\'OWN_PARENT_WITH_EXERCISES_DELETE_BUTTON\');\n  await until(()=>evaluate(\'Array.from(document.querySelectorAll(".el-message-box")).some(e=>e.getClientRects().length&&e.textContent.includes("是否删除"))\'));\n  const parentDeleteBefore=count(\'removeById\');\n  if(!await click(\'.el-message-box__btns button\',\'确定\'))throw Error(\'OWN_PARENT_WITH_EXERCISES_DELETE_CONFIRM\');\n  await until(()=>count(\'removeById\')===parentDeleteBefore+1);\n  if(http.filter(r=>r.path.endsWith(\'/emergencyPlan/removeById\')).at(-1).saved!==true)throw Error(\'PARENT_DELETE_DID_NOT_COMPLETE\');\n  const removedParent=await ownAPI(\'emergencyPlan\',\'getPage?current=1&size=5&emergencyPlanName=\'+encodeURIComponent(name));\n  if(removedParent.records.some(r=>String(r.id)===String(id)))throw Error(\'PARENT_STILL_IN_ORIGINAL_LIST\');\n  if(await ownAPI(\'emergencyPlan\',\'getById?id=\'+encodeURIComponent(id))!==null)throw Error(\'DELETED_PARENT_DETAILS_NOT_NULL\');\n  const exercisesAfter=await ownAPI(\'emergencyExercise\',\'getPage?current=1&size=20&emergencyPlanId=\'+encodeURIComponent(id));\n  const fileExerciseAfter=await ownAPI(\'emergencyExercise\',\'getById?id=\'+encodeURIComponent(exercise.id));\n  const keepAfter=await ownAPI(\'emergencyPlan\',\'getById?id=\'+encodeURIComponent(keepId));\n  if(Number(exercisesAfter.total)!==2||JSON.stringify(exercisesAfter.records.map(r=>String(r.id)).sort())!==JSON.stringify(exercisesBefore.records.map(r=>String(r.id)).sort()))throw Error(\'ORIGINAL_CHILD_EXERCISE_RETENTION_CHANGED\');\n  if(JSON.stringify(fileExerciseAfter)!==JSON.stringify(fileExerciseBefore)||JSON.stringify(keepAfter)!==JSON.stringify(keepBefore))throw Error(\'CHILD_DETAILS_OR_UNRELATED_PLAN_CHANGED\');\n  await until(()=>evaluate(`!Array.from(document.querySelectorAll(\'.el-table__body-wrapper tbody tr\')).some(r=>r.getClientRects().length&&r.textContent.includes(${JSON.stringify(name)})&&!r.textContent.includes(${JSON.stringify(keepName)}))`));\n  cases.push({case:\'native-parent-with-two-exercises-delete-retains-original-child-details-and-unrelated-plan\',passed:true,originalBehaviorCharacterization:true,childCascadeDeletionClaimed:false});\n  stage=\'exercise-attachment-object-still-readable-after-parent-delete\';\n  const childObject=new URL(currentLink.href);\n  if(childObject.origin!==wire.base)throw Error(\'OWN_CHILD_ATTACHMENT_ORIGIN_REQUIRED\');\n  const objectResponse=await fetch(childObject.href,{headers:{Authorization:token,\'User-Agent\':await evaluate(\'navigator.userAgent\')},redirect:\'error\',signal:AbortSignal.timeout(15000)});\n  if(objectResponse.status!==200)throw Error(\'OWN_CHILD_OBJECT_NOT_READABLE_AFTER_PARENT_DELETE\');\n  const objectBytes=Buffer.from(await objectResponse.arrayBuffer());\n  if(!objectBytes.equals(png))throw Error(\'OWN_CHILD_OBJECT_BYTES_CHANGED_AFTER_PARENT_DELETE\');\n  cases.push({case:\'native-child-attachment-metadata-and-real-object-bytes-kept-after-parent-delete\',passed:true,objectStoreCascadeDeletionClaimed:false});\n  await fs.writeFile(O+\'/parent-delete-with-exercises-evidence.json\',JSON.stringify({passed:true,parentDeleteRequests:1,parentAbsentFromListAndDetails:true,childExercisesBefore:2,childExercisesAfter:2,childDetailsPeopleAndFileMetadataUnchanged:true,realChildAttachmentHTTP:objectResponse.status,realChildAttachmentBytesIdentical:true,unrelatedOwnPlanExactDetailsUnchanged:true,actualOriginalServiceAndNormalRoleUI:true,onlyOwnSyntheticRecords:true,originalBehaviorCharacterizedNotNewCascadeRule:true,allSixResourceRelationsPopulatedOrVerifiedByThisCase:false},null,2));\n',1)
out=T/'verify_native_parent_delete_r325_20261103.mjs';assert not out.exists();out.write_text(js,encoding='utf-8');pins[out.name]=hashlib.sha256(out.read_bytes()).hexdigest()
node=subprocess.run(['node','--check',str(out)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert node.returncode==0
restore=(V/'restore_plan_delete_prestart_r305.py').read_text(encoding='utf-8').replace('r135','r141').replace('_r304','_r325')
ast.parse(restore);rp=V/'restore_parent_delete_prestart_r326.py';assert not rp.exists();rp.write_text(restore,encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r141'],['prepare_production_history_runtime_r325.py'],
 ['mapper_product_patch_r325.py','prepare','--attempt','r141'],['mapper_observation_support_r325.py','prepare','--attempt','r141'],['prepare_personal_workflow_frontend_r325.py']]
results=[]
for args in steps:
    done=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if done.returncode:
        (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':done.returncode},indent=2)+'\n',encoding='utf-8')
        raise RuntimeError('OWN_DEPARTMENT_PREPARATION_REFUSED:'+args[0])
    results.append({'step':args[0],'result':json.loads(done.stdout)})
proof={'prepared':True,'attempt':'r141','sourcePins':pins,'admissionAvailableBytes':memory[2],
 'fixedSchemaReaderPreserved':True,'expectedBrowserCases':18,'parentDeleteWithExercisesCharacterization':True,
 'steps':results,'servicesStarted':False,'onlyOwnSyntheticFixture':True,'publicFormalOrDesktopChanged':False}
(D/'prepared-result-r325.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r141','sources':len(pins),'memoryGiB':round(memory[2]/1024**3,2),'servicesStarted':False}))
