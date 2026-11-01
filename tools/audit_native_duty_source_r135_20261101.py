from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';P=R/'Application/work/tianjin_native_20261023/emergency_pc/src';W=R/'work/user_feedback_20261031/emergency-workflow-source-r12/source/src';D=R/'Document/Deployment/emergency_duty_native_r135_20261101';D.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('duty_save_guard',T/'original_duty_result_compat.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sha=lambda raw:hashlib.sha256(raw).hexdigest();checks=[]
for kind in ['dutyPersonnel','dutySchedule','dutyLog']:
    paths=['api/dutyManage/'+kind+'/index.ts']+['views/dutyManage/'+kind+'/'+suffix for suffix in ['index.vue','info/index.vue','info/detail.vue','info/addOrEdit.vue']]
    for rel in paths:
        raw=(P/rel).read_bytes();actual=(W/rel).read_bytes();method='whole-original-byte-equal'
        if rel.endswith('/info/addOrEdit.vue'):expected,receipt=module.transform(kind,raw);assert expected==actual;method='exact-original-plus-declared-save-result-guard'
        elif rel.endswith(kind+'/index.vue')and kind!='dutySchedule':
            a='  await useHandleData(removeById, { id: row.id }, "删除");';b='  if (!(await useHandleData(removeById, { id: row.id }, "删除"))) return;';original=raw.decode('utf-8').replace('\r\n','\n');current=actual.decode('utf-8').replace('\r\n','\n');assert original.count(a)==1 and original.replace(a,b)==current;method='exact-original-plus-declared-cancel-result-guard'
        else:assert raw==actual,rel
        checks.append({'path':rel,'comparison':method,'originalSHA256':sha(raw),'currentSHA256':sha(actual)})
for rel in ['views/dutyManage/dutySchedule/info/personList.vue','views/dutyManage/dutyLog/components/eventList.vue']:
    raw=(P/rel).read_bytes();actual=(W/rel).read_bytes();assert raw==actual;checks.append({'path':rel,'comparison':'whole-original-byte-equal','originalSHA256':sha(raw),'currentSHA256':sha(actual)})
info=(W/'views/dutyManage/dutySchedule/info/index.vue').read_text(encoding='utf-8');detail=(W/'views/dutyManage/dutySchedule/info/detail.vue').read_text(encoding='utf-8');picker=(W/'views/dutyManage/dutySchedule/info/personList.vue').read_text(encoding='utf-8');calendar=(W/'views/dutyManage/dutySchedule/index.vue').read_text(encoding='utf-8')
observations={'scheduleDetailComponentCommentedOutInOriginalInfoWrapper':'<!-- <Detail v-else /> -->'in info and '// import Detail'in info,'unenabledScheduleDetailUsesStaticRows':'const data = ['in detail,'nativeCalendarEventOpensEdit':'path: "/dutyManage/dutySchedule/edit"'in calendar,'originalPickerDirectlyDestructuresMaybeMissingRow':'= nowRow;'in picker and 'const nowRow ='in picker and 'if (!nowRow)'not in picker,'runtimeDefectReproductionNotClaimedBySourceAudit':True,'hardcodedExampleRowValuesNotExported':True}
result={'schema':'xnby.r135.original-duty-source-audit.v1','passed':True,'filesCompared':len(checks),'checks':checks,'observations':observations,'allDeclaredGuardsOnly':True,'sourceOrProductOrPublicModified':False,'realNangangRolesOrWholeModuleAccepted':False};(D/'original-duty-source-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k!='checks'}))
