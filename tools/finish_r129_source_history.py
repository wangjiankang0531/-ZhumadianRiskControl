from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');W=R/'work/user_feedback_20261031/emergency-workflow-source-r9';T=R/'Application/tools';p=W/'source-closure.json';m=json.loads(p.read_bytes())
m['overlayFiles']=sorted(set(m['overlayFiles'])|{r['path'].removeprefix('src/')for r in m['preservedResourceResultGuards']['restoredSourceFiles']}|{r['path'].removeprefix('src/')for r in m['fullRetainedOperationGuards']['files']})
for row in m['fullRetainedOperationGuards']['files']:
 key=row['path'];previous=m.get('runtimeSourceAdaptations',{}).get(key)
 if previous:
  assert previous['adaptedSHA256']==row['beforeSHA256'];m.setdefault('runtimeBeforeRetainedOperationGuards',{})[key]=dict(previous);previous['adaptedSHA256']=row['afterSHA256'];previous['retainedOperationGuardsComposedAfterward']=True
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=T/'verify_emergency_workflow_source_20261101.py';s=p.read_text(encoding='utf-8');anchor="for rel,row in c['sourceFiles'].items():"
extra='''def independently_restored_guard(relative, before):
 import sys
 sys.path.insert(0,str(T))
 import original_business_result_compat as business
 import original_duty_result_compat as duty
 import original_confirmed_operation_compat as confirmed
 rel='src/'+relative
 if rel==business.relative('emergency_pc'):return business.transform('emergency_pc',before)[0]
 for kind in duty.PINS:
  if rel==duty.relative(kind):return duty.transform(kind,before)[0]
 catalogue=confirmed.catalog()['kindResults']['emergency_pc']
 if rel==catalogue['hook']['path']:return confirmed.transform_hook(before)
 row=catalogue['files'][rel]
 if hashlib.sha256(before).hexdigest()==row['originalSHA256']:return confirmed.transform_caller(before,row)
 assert rel in ['src/views/emergencyResources/materials/index.vue','src/views/emergencyResponse/taskSend/index.vue']
 result=before
 for call in row['calls']:
  a=call['patch']['originalText'].encode();b=call['patch']['replacement'].encode();assert result.count(a)==1 and b not in result;result=result.replace(a,b,1)
 return result
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor)
anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel"
extra=''' if c.get('fullRetainedOperationGuards'):
  restored=next((r for r in c['fullRetainedOperationGuards']['files']if r['path']=='src/'+rel),None)
  if restored:
   original=R/'work/user_feedback_20261031/emergency-workflow-source-r8/source/src'/rel
   assert sha(original)==restored['beforeSHA256']
   generated=independently_restored_guard(rel,original.read_bytes())
   assert hashlib.sha256(generated).hexdigest()==restored['afterSHA256']==expected,'RESTORED_GUARD_NOT_INDEPENDENTLY_REPRODUCIBLE:'+rel
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor);p.write_text(s,encoding='utf-8')
print(json.dumps({'sourceOverlayFiles':len(m['overlayFiles']),'selectedSourceFiles':len(m['sourceFiles']),'all14GuardsIndependentRegenerationRequired':True,'twoTaskImportChangesPreserved':True}))
