from pathlib import Path
import ast,json,hashlib,subprocess,sys

V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
J=lambda p:json.loads(p.read_bytes())
assert J(C/'r137-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert J(C/'prepared-r137/history-runtime-restored.json')['passed']
failure=J(C/'r137/plan-browser/failure.json')
assert failure['message']=='EXPECTED_LEGACY_DEPARTMENT_FILTER_REPRO_NOT_OBSERVED'
assert failure['http'][-1]['exerciseTotal']==1 and len(failure['cases'])==11

withdrawn=R/'Document/Deployment/exercise_department_frontend_candidate_r319_20261103/withdrawn-status-r320.json'
assert not withdrawn.exists()
withdrawn.write_text(json.dumps({'withdrawn':True,'candidateCompiled':False,'candidateInstalled':False,
 'reason':'Actual native filter returned one record; common SearchFormItem applies canonical column binding',
 'initialDefectHypothesisNotProven':True,'noProductFixClaimed':True,'preparedSourcesRetainedForTraceability':True},indent=2)+'\n',encoding='utf-8')

text=(V/'prepare_exercise_department_repro_r317.py').read_text(encoding='utf-8')
text=text.replace('native_exercise_department_filter_r317_20261103','native_exercise_department_filter_verified_r320_20261103')
text=text.replace('r137','r139').replace('_r317','_r320').replace('restore_exercise_department_prestart_r318.py','restore_exercise_department_prestart_r321.py')
text=text.replace("'exerciseDepartmentBaseline': True","'exerciseDepartmentBaseline': False")
text=text.replace("len(browser_result['cases']) == 15","len(browser_result['cases']) == 16")
text=text.replace("'expectedBrowserCases':15,'departmentFilterBaselineReproduction':True", "'expectedBrowserCases':16,'departmentFilterBehaviorVerification':True")
text=text.replace("||query.legacyDepartmentNonempty||!query.canonicalOrganizeDepartmentNonempty", "||!query.canonicalOrganizeDepartmentNonempty")
anchor="  if(wire.exerciseDepartmentBaseline){"
assert text.count(anchor)==1
text=text.replace(anchor,"  await fs.writeFile(O+'/department-filter-observed-before-assert.json',JSON.stringify({httpStatus:filtered.httpStatus,businessCode:filtered.businessCode,filteredRows:filtered.exerciseTotal,requestShape:query},null,2));\n"+anchor)
anchor="  activeFormTitle=null;\n'''"
assert text.count(anchor)==1
extra=r'''
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
'''
text=text.replace(anchor,extra+anchor)
ast.parse(text)
generated=V/'prepare_exercise_department_verified_generated_r320.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
completed=subprocess.run([sys.executable,str(generated)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
if completed.returncode:
    print(completed.stderr.decode('utf-8',errors='replace')[-1800:])
    raise RuntimeError('OWN_DEPARTMENT_VERIFIED_PREPARATION_REFUSED')
print(completed.stdout.decode('utf-8').strip())
