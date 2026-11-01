from pathlib import Path
import hashlib,json,os,shutil,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T));B=R/'work/user_feedback_20261031';old=B/'emergency-workflow-source-r8';new=B/'emergency-workflow-source-r9';assert not new.exists()
P=R/'Application/work/tianjin_native_20261023/emergency_pc'
import original_business_result_compat as business
import original_duty_result_compat as duty
import original_confirmed_operation_compat as confirm
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
shutil.copytree(old/'source',new/'source',copy_function=os.link);meta=J(old/'source-closure.json');plans={}
rel=business.relative('emergency_pc');plans[rel]=(P/rel).read_bytes(),business.transform('emergency_pc',(P/rel).read_bytes())[0]
for kind in duty.PINS:
 rel=duty.relative(kind);raw=(P/rel).read_bytes();plans[rel]=raw,duty.transform(kind,raw)[0]
catalog=confirm.catalog()['kindResults']['emergency_pc'];rel=catalog['hook']['path'];raw=(P/rel).read_bytes();plans[rel]=raw,confirm.transform_hook(raw)
composition=[]
for rel,record in catalog['files'].items():
 raw=(P/rel).read_bytes();desired=confirm.transform_caller(raw,record);current=(old/'source'/rel).read_bytes()
 if current!=raw:
  # Two legitimate WF6/WF7 caller edits must survive; compose only the exact catalogued await statement.
  assert rel in ['src/views/emergencyResources/materials/index.vue','src/views/emergencyResponse/taskSend/index.vue']
  previous=current
  for call in record['calls']:
   patch=call['patch'];a=patch['originalText'].encode();b=patch['replacement'].encode();assert current.count(a)==1 and b not in current;current=current.replace(a,b,1)
  reverse=current
  for call in reversed(record['calls']):reverse=reverse.replace(call['patch']['replacement'].encode(),call['patch']['originalText'].encode(),1)
  assert reverse==previous;composition.append({'path':rel,'retainedWF6OrWF7EditsPreservedByteExactByInverse':True,'guardedCallCount':len(record['calls'])});plans[rel]=previous,current
 else:plans[rel]=raw,desired
rows=[]
for rel,(expected,updated)in plans.items():
 p=new/'source'/rel;assert p.read_bytes()==expected;p.unlink();p.write_bytes(updated)
 stored=T/'frontend/emergency-retained-operation-guards'/rel;stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(updated)
 meta['sourceFiles'][rel.removeprefix('src/')]={'source':str(stored),'sha256':sha(updated),'bytes':len(updated),'overlay':True}
 rows.append({'path':rel,'beforeSHA256':sha(expected),'afterSHA256':sha(updated)})
meta['fullRetainedOperationGuards']={'files':rows,'twoEditedCallersExactComposition':composition,'catalogSHA256':confirm.CATALOG_SHA256,'activeCalls':catalog['activeCallCount'],'existingWF6AndMaterialImportChangesPreserved':True}
(new/'source-closure.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
diff=[]
for p in(old/'source').rglob('*'):
 if p.is_file():
  rel=p.relative_to(old/'source').as_posix()
  if p.read_bytes()!=(new/'source'/rel).read_bytes():diff.append(rel)
assert set(diff)==set(plans)
(new/'retained-operation-source-proof.json').write_text(json.dumps({'onlyDeclaredGuardRestorationFilesChanged':True,'changedFiles':rows,'twoCallerComposition':composition,'oldThreeResourceGuardsRetained':True,'catalogueActiveCalls':9,'actualNativeRuntimePending':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
 p=T/name;s=p.read_text(encoding='utf-8');needle="'r6','r7','r8'";assert needle in s;s=s.replace(needle,"'r6','r7','r8','r9'");p.write_text(s,encoding='utf-8')
print(json.dumps({'revision':'r9','oldMissingOperationGuardFilesRestored':len(rows),'exactComposedCallers':len(composition),'activeConfirmationCalls':9,'WF6AndWF7ChangesPreserved':True}))
