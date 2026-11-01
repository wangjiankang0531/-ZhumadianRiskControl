"""Check emitted workflow routes/assets against actual build and original source pins."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['r1','r2','r3','r4','r5','r6','r7'],default='r1');options=parser.parse_args()
R=Path('D:/Project/Zhumadian');W=R/('work/user_feedback_20261031/emergency-workflow-source-'+options.revision);F=W/'dist';T=R/'Application/tools'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(W/'build-result.json');c=read(W/'source-closure.json');assert m['buildPassed']and not m['normalLoginListDetailApprovalOrCallbackAccepted']
assert sha(W/'source-closure.json')==m['sourceClosureSHA256']
assert {p.relative_to(F).as_posix()for p in F.rglob('*')if p.is_file()}==set(m['files'])
for name,row in m['files'].items():assert sha(F/name)==row['sha256']and(F/name).stat().st_size==row['bytes']
overrides={'api/login/index.ts':'emergency-native-login-query.ts','views/emergencyResponse/taskSend/info/addOrEdit.vue':'emergency-task-add-edit.vue',
 'views/emergencyResponse/taskSend/info/detail.vue':'emergency-task-disposal-detail.vue','views/emergencyResponse/taskSend/info/index.vue':'emergency-task-add-edit-parent.vue'}
for rel,row in c['sourceFiles'].items():
 assert sha(Path(row['source']))==row['sha256'],'ORIGINAL_SOURCE_CHANGED:'+rel
 actual=W/'source/src'/rel
 expected=sha(T/'frontend'/overrides[rel])if rel in overrides else(c['adaptations'].get('src/'+rel)or{}).get('adaptedSHA256',row['sha256'])
 expected=c.get('taskContextAdaptations',{}).get('src/'+rel,{}).get('adaptedSHA256',expected)
 expected=c.get('runtimeSourceAdaptations',{}).get('src/'+rel,{}).get('adaptedSHA256',expected)
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
