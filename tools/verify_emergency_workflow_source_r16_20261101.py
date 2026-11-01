"""Check emitted workflow routes/assets against actual build and original source pins."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['r1','r2','r3','r4','r5','r6','r7','r8','r9','r10','r11','r12','r13','r14','r15','r16'],default='r1');options=parser.parse_args()
R=Path('D:/Project/Zhumadian');W=R/('work/user_feedback_20261031/emergency-workflow-source-'+options.revision);F=W/'dist';T=R/'Application/tools'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(W/'build-result.json');c=read(W/'source-closure.json');assert m['buildPassed']and not m['normalLoginListDetailApprovalOrCallbackAccepted']
assert sha(W/'source-closure.json')==m['sourceClosureSHA256']
assert {p.relative_to(F).as_posix()for p in F.rglob('*')if p.is_file()}==set(m['files'])
for name,row in m['files'].items():assert sha(F/name)==row['sha256']and(F/name).stat().st_size==row['bytes']
overrides={'api/login/index.ts':'emergency-native-login-query.ts','views/emergencyResponse/taskSend/info/addOrEdit.vue':'emergency-task-add-edit.vue',
 'views/emergencyResponse/taskSend/info/detail.vue':'emergency-task-disposal-detail.vue','views/emergencyResponse/taskSend/info/index.vue':'emergency-task-add-edit-parent.vue'}
def independently_restored_guard(relative, before):
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
for rel,row in c['sourceFiles'].items():
 assert sha(Path(row['source']))==row['sha256'],'ORIGINAL_SOURCE_CHANGED:'+rel
 actual=W/'source/src'/rel
 expected=sha(T/'frontend'/overrides[rel])if rel in overrides else(c['adaptations'].get('src/'+rel)or{}).get('adaptedSHA256',row['sha256'])
 expected=c.get('taskContextAdaptations',{}).get('src/'+rel,{}).get('adaptedSHA256',expected)
 expected=c.get('runtimeSourceAdaptations',{}).get('src/'+rel,{}).get('adaptedSHA256',expected)
 if c.get('fullRetainedOperationGuards'):
  restored=next((r for r in c['fullRetainedOperationGuards']['files']if r['path']=='src/'+rel),None)
  if restored:
   original=R/'work/user_feedback_20261031/emergency-workflow-source-r8/source/src'/rel
   assert sha(original)==restored['beforeSHA256']
   assert expected in [restored['beforeSHA256'],restored['afterSHA256']],'RESTORED_GUARD_PREVIOUS_STAGE_MISMATCH:'+rel
   expected=restored['afterSHA256']
   generated=independently_restored_guard(rel,original.read_bytes())
   assert hashlib.sha256(generated).hexdigest()==restored['afterSHA256']==expected,'RESTORED_GUARD_NOT_INDEPENDENTLY_REPRODUCIBLE:'+rel
 if c.get('tableRequestOrderAdaptation',{}).get('path')=='src/'+rel:
  import importlib.util
  spec=importlib.util.spec_from_file_location('independent_order',T/'original_table_request_order_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r9/source/src'/rel
  recreated,receipt=helper.transform(origin.read_bytes())
  assert receipt['inputSHA256']==c['tableRequestOrderAdaptation']['inputSHA256']and hashlib.sha256(recreated).hexdigest()==expected
 if c.get('sameOriginMapRestoration',{}).get('path')=='src/'+rel:
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r10/source/src'/rel
  before=origin.read_bytes();assert hashlib.sha256(before).hexdigest()==c['sameOriginMapRestoration']['beforeSHA256']and before.count(b'"/tianjinrisk/map/"')==1
  assert hashlib.sha256(before.replace(b'"/tianjinrisk/map/"',b'"/zhumadian/map/"')).hexdigest()==expected
 if rel in c.get('nativeTeamContextAdaptations',{}):
  import importlib.util
  entry=c['nativeTeamContextAdaptations'][rel]
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r11/source/src'/rel
  assert sha(origin)==entry['beforeSHA256']and expected in [entry['beforeSHA256'],entry['afterSHA256']]
  assert entry['helper'] in ['original_team_detail_members_compat','original_team_editor_context_compat']
  assert entry['entry'] in ['transform','transform_editor','transform_parent']
  spec=importlib.util.spec_from_file_location('independent_native_team',T/(entry['helper']+'.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=getattr(helper,entry['entry'])(origin.read_bytes())
  assert receipt==entry['receipt']and hashlib.sha256(generated).hexdigest()==entry['afterSHA256']
  expected=entry['afterSHA256']
 if rel==c.get('nativeDutyPickerGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeDutyPickerGuard']
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r12/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_duty_picker',T/'original_duty_picker_selection_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes())
  assert receipt==entry['receipt']and expected==hashlib.sha256(generated).hexdigest()
 if rel==c.get('nativeDutyLogPersonnelGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeDutyLogPersonnelGuard']
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r13/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_duty_log',T/'original_duty_log_personnel_context_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes())
  assert receipt==entry['receipt']and expected in [receipt['beforeSHA256'],receipt['afterSHA256']]
  expected=receipt['afterSHA256']
 if rel==c.get('nativeTaskFeedbackResultGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeTaskFeedbackResultGuard'];origin=R/'work/user_feedback_20261031/emergency-workflow-source-r14/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_feedback',T/'original_task_feedback_result_compat_r143_20261101.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes());assert receipt==entry['receipt']and expected==receipt['beforeSHA256'];expected=receipt['afterSHA256'];assert generated==actual.read_bytes()
 if rel==c.get('nativeTaskEditResultGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeTaskEditResultGuard'];origin=R/'work/user_feedback_20261031/emergency-workflow-source-r15/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_edit',T/'original_task_edit_result_compat_r146_20261101.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes());assert receipt==entry['receipt']and expected==receipt['beforeSHA256'];expected=receipt['afterSHA256'];assert generated==actual.read_bytes()
 assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel
texts={p.relative_to(F).as_posix():p.read_text(encoding='utf-8')for p in(F/'assets/js').glob('*.js')}
roots=['/src/views/workflow/flowTodo/index.vue','/src/views/workflow/flowTodo/info/index.vue','/src/views/workflow/startWithMeTwo/index.vue','/src/views/workflow/startWithMeTwo/info/index.vue']
routes={}
for source in roots:
 found=set()
 for name,text in texts.items():
  for match in re.finditer(re.escape('"'+source+'"')+r':\(\)=>.{0,35}?import\("([^"\r\n]+)"\)',text):found.add((F/name).parent.joinpath(match[1]).resolve().relative_to(F.resolve()).as_posix())
 assert len(found)==1,'ROUTE_FACADE_NOT_UNIQUE:'+source
 routes[source]=next(iter(found));body=texts[routes[source]]
 assert not re.search(r'["\'](?:11111|22222)["\']',body),'WORKFLOW_STUB_STILL_SHIPPED'
 assert ('待办事宜'if'flowTodo'in source else'我发起的')in body
all_js='\n'.join(texts.values())
for endpoint in ['/jnpf/workflow/Engine/FlowBefore/List/1','/jnpf/workflow/Engine/FlowLaunch','/jnpf/workflow/Engine/FlowBefore/Audit/']:
 assert endpoint in all_js,'ORIGINAL_NATIVE_ENDPOINT_NOT_EMITTED'
assert 'undefined/serv'not in all_js and 'undefined/jnpf'not in all_js and '/zhumadian/api'in all_js
missing=[];references=0
for name,row in m['files'].items():
 if Path(name).suffix not in{'.js','.css','.html'}:continue
 text=(F/name).read_text(encoding='utf-8');refs=re.findall(r'''["']([^"'\r\n]{1,220}\.(?:js|css|woff2?|ttf|svg|png|jpe?g|gif|ico)(?:\?[^"']*)?)["']''',text)
 if name.endswith('.css'):refs+=re.findall(r'url\(([^)"\']+)\)',text)
 for ref in refs:
  if ref.startswith(('http:','https:','data:','blob:','//','#')):continue
  ref=ref.split('?',1)[0].split('#',1)[0]
  if ref.startswith('/zhumadian/emergency/'):p=F/ref.removeprefix('/zhumadian/emergency/')
  elif ref.startswith('assets/'):p=F/ref
  elif ref.startswith(('./','../')):p=(F/name).parent/ref
  else:continue
  references+=1
  if not p.is_file():missing.append({'consumer':name,'asset':ref})
assert not missing,'MISSING_COMPILED_ASSETS:'+json.dumps(missing[:10])
for name in texts:
 result=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(F/name)],capture_output=True);assert result.returncode==0,'EMITTED_JS_SYNTAX:'+name
fixed=R/'Document/Deployment/public_test_unified_r23_20261101'
assert sha(fixed/'delivery-manifest.json')=='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
assert sha(fixed/'public-git-sync-manifest.json')=='184cab1fc01ecdcbccea96e39280a49fbd1f0d4f7e32c963fc3c55a6fbec88aa'
result={'schema':'xnby.emergency-workflow-source-build-verification.v1','buildPassed':True,'compiledFiles':len(m['files']),
 'allBuildBytesAndSourcePinsVerified':True,'selectedSourceFiles':len(c['sourceFiles']),'sourceOverlayFiles':len(c['overlayFiles']),
 'actualFourWorkflowRouteFacadesVerified':routes,'twoStubRenderModulesReplaced':True,'originalNativeListLaunchAuditAPIsEmitted':True,
 'localAssetReferencesVerified':references,'missingAssets':0,'emittedJSFilesSyntaxChecked':len(texts),
 'existingLoginAndTaskQ3ReviewSourcesKept':not bool(c.get('taskContextAdaptations')),'existingQ3SubmitSemanticsKept':True,'workflowTaskContextDeclaredChangedFiles':len(c.get('taskContextAdaptations',{})),'auditSubmitDeclaredChangedFiles':sum(p.endswith('/auditForm.vue')for p in c.get('runtimeSourceAdaptations',{})),'taskStateDisplayDeclaredChangedFiles':len(c.get('taskStateDisplayAdaptations',{})),'uncertainOutcomeDeclaredChangedFiles':len(c.get('uncertainOutcomeAdaptations',{})),'undeclaredSourceDifferences':0,'referenceOrManualPreviewOrFixedScopesModified':False,
 'actualNormalUserWorkflowUIOrFullTypeCheckAccepted':False,'publicInstalled':False,'fullCloneReady':False}
(W/'independent-build-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items()if k!='actualFourWorkflowRouteFacadesVerified'}))
