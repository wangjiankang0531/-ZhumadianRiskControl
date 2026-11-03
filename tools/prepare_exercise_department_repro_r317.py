from pathlib import Path
import ast,ctypes,hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_exercise_department_filter_r317_20261103'
assert not D.exists()and not(C/'prepared-r137').exists()and not(C/'r137').exists()
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
        if v=='r135':v='r137'
        elif v=='prepared-r135':v='prepared-r137'
        elif v.startswith('r135/'):v='r137/'+v[5:]
        v=v.replace('_r304','_r317')
        v=v.replace('verify_native_plan_delete_r317_20261103.mjs','verify_native_exercise_filter_r317_20261103.mjs')
        v=v.replace('verify_full_controller_plan_delete_r317.py','verify_full_controller_exercise_filter_r317.py')
        return ast.copy_location(ast.Constant(v),node)

D.mkdir();pins={}
def save(src,dst):
    tree=Rewrite().visit(ast.parse((T/src).read_bytes()));ast.fix_missing_locations(tree)
    raw=(ast.unparse(tree)+'\n').encode();ast.parse(raw,filename=dst)
    target=T/dst;assert not target.exists();target.write_bytes(raw);pins[dst]=hashlib.sha256(raw).hexdigest()

for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend','mapper_product_patch','mapper_observation_support']:
    save(stem+'_r304.py',stem+'_r317.py')
save('verify_full_controller_plan_delete_r304.py','verify_full_controller_exercise_filter_r317.py')
save('run_native_plan_delete_r304.py','run_native_exercise_filter_r317.py')
runner=T/'run_native_exercise_filter_r317.py'
raw=runner.read_text(encoding='utf-8').replace('r135','r137')
runner.write_text(raw,encoding='utf-8');pins[runner.name]=hashlib.sha256(runner.read_bytes()).hexdigest()
host=T/'verify_full_controller_exercise_filter_r317.py';text=host.read_text(encoding='utf-8')
assert "schema_base = R / 'work/event_delivery_consistency_20261030/full-controller-r131'"in text
assert "options.attempt in ['r137']"in text
assert text.count("'baseline': options.attempt == 'r129'")==1
text=text.replace("'baseline': options.attempt == 'r129'","'baseline': options.attempt == 'r129', 'exerciseDepartmentBaseline': True")
assert text.count("len(browser_result['cases']) == 14")==1
text=text.replace("len(browser_result['cases']) == 14","len(browser_result['cases']) == 15")
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
  if(wire.exerciseDepartmentBaseline){
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==2||!query.legacyDepartmentNonempty||query.canonicalOrganizeDepartmentNonempty)throw Error('EXPECTED_LEGACY_DEPARTMENT_FILTER_REPRO_NOT_OBSERVED');
  }else{
   if(filtered.httpStatus!==200||filtered.businessCode!==0||filtered.exerciseTotal!==1||query.legacyDepartmentNonempty||!query.canonicalOrganizeDepartmentNonempty)throw Error('CORRECT_ORGANIZE_DEPARTMENT_FILTER_NOT_OBSERVED');
  }
  await fs.writeFile(O+'/department-filter-evidence.json',JSON.stringify({reproducedLegacyKeyIgnored:!!wire.exerciseDepartmentBaseline,unfilteredRows:2,filteredRows:filtered.exerciseTotal,requestShape:query,actualOriginalBackendAndCompiledPage:true,onlyOwnSyntheticRecords:true,businessRowsChangedByFilter:false},null,2));
  cases.push({case:wire.exerciseDepartmentBaseline?'native-exercise-department-legacy-key-reproduces-two-unfiltered-rows':'native-exercise-organize-department-filters-two-records-to-one',passed:true,defectReproduced:!!wire.exerciseDepartmentBaseline});
  activeFormTitle=null;
'''
js=js.replace(anchor,extra+'\n'+anchor)
anchor="  for(const title of ['演练记录详情','演练记录']){"
assert js.count(anchor)==1;js=js.replace(anchor,"  for(const title of ['演练记录']){")
out=T/'verify_native_exercise_filter_r317_20261103.mjs';assert not out.exists();out.write_text(js,encoding='utf-8');pins[out.name]=hashlib.sha256(out.read_bytes()).hexdigest()
node=subprocess.run(['node','--check',str(out)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert node.returncode==0
restore=(V/'restore_plan_delete_prestart_r305.py').read_text(encoding='utf-8').replace('r135','r137').replace('_r304','_r317')
ast.parse(restore);rp=V/'restore_exercise_department_prestart_r318.py';assert not rp.exists();rp.write_text(restore,encoding='utf-8')
steps=[['prepare_owned_return_serial_r163_20261102.py','--attempt','r137'],['prepare_production_history_runtime_r317.py'],
 ['mapper_product_patch_r317.py','prepare','--attempt','r137'],['mapper_observation_support_r317.py','prepare','--attempt','r137'],['prepare_personal_workflow_frontend_r317.py']]
results=[]
for args in steps:
    done=subprocess.run([sys.executable,str(T/args[0]),*args[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if done.returncode:
        (D/'prepare-failure.json').write_text(json.dumps({'step':args[0],'exitCode':done.returncode},indent=2)+'\n',encoding='utf-8')
        raise RuntimeError('OWN_DEPARTMENT_PREPARATION_REFUSED:'+args[0])
    results.append({'step':args[0],'result':json.loads(done.stdout)})
proof={'prepared':True,'attempt':'r137','sourcePins':pins,'admissionAvailableBytes':memory[2],
 'fixedSchemaReaderPreserved':True,'expectedBrowserCases':15,'departmentFilterBaselineReproduction':True,
 'steps':results,'servicesStarted':False,'onlyOwnSyntheticFixture':True,'publicFormalOrDesktopChanged':False}
(D/'prepared-result-r317.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'attempt':'r137','sources':len(pins),'memoryGiB':round(memory[2]/1024**3,2),'servicesStarted':False}))
