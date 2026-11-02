from pathlib import Path
import hashlib,json,re,sys
R=Path('D:/Project/Zhumadian');W=R/'work/user_feedback_20261031';ROOT=W/'avatar-full-r157';T=R/'Application/tools'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def files(root):return {p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in root.rglob('*')if p.is_file()}
old=J(ROOT/'security-baseline-source-capture/actual-retained-recipe-source-files.json');new=J(ROOT/'security_pc/actual-compiled-source-files.json');allowed={'src/layout/components/header-user.vue','src/utils/OriginalHeaderAvatarSource.ts'}
assert {n for n in set(old)|set(new)if old.get(n)!=new.get(n)}==allowed
assert J(ROOT/'security-baseline-source-capture/capture-result.json')['allContextsUnwoundAndSourceRestored']
assert J(ROOT/'security_pc/build/receipt.json')['exitCode']==0
safety=J(ROOT/'security_pc/candidate-result.json');assert safety['buildExitCode']==0 and safety['referenceAndOriginalSourceRestored']and safety['R18HomeCSSRetained']and safety['R21WorkplaceAndWorkflowSourcesRetained']
assert J(ROOT/'security_pc-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert J(ROOT/'emergency_pc-outer-terminal.json')['exitCode']==0 and J(ROOT/'emergency_pc-outer-terminal.json')['actualDescendantsZeroBeforeClose']
result={}
for role,dist,rows,base in [('security_pc',ROOT/'security_pc/build/dist',safety['fullFrontendFiles'],'/zhumadian/'),('emergency_pc',ROOT/'emergency_pc/dist',J(ROOT/'emergency_pc/full-build-result.json')['compiledFiles'],'/zhumadian/emergency/')]:
 assert files(dist)==rows
 texts={n:(dist/n).read_text(encoding='utf-8')for n in rows if n.endswith('.js')};all_js='\n'.join(texts.values());missing=[];count=0;runtime_tiles=[]
 for name in rows:
  if Path(name).suffix not in {'.js','.css','.html'}:continue
  text=(dist/name).read_text(encoding='utf-8');refs=re.findall(r'''["']([^"'\r\n]{1,220}\.(?:js|css|woff2?|ttf|svg|png|jpe?g|gif|ico)(?:\?[^"']*)?)["']''',text)
  if name.endswith('.css'):refs+=re.findall(r'''url\(([^)"']+)\)''',text)
  for ref in refs:
   if ref.startswith(('http:','https:','data:','blob:','//','#')):continue
   ref=ref.split('?',1)[0].split('#',1)[0]
   if ref=='/zhumadian/map/{z}/{x}/{y}.png':runtime_tiles.append({'consumer':name,'exactRuntimeTileTemplate':ref});continue
   if ref.startswith(base):p=dist/ref.removeprefix(base)
   elif ref.startswith('assets/'):p=dist/ref
   elif ref.startswith(('./','../')):p=(dist/name).parent/ref
   else:continue
   count+=1
   if not p.resolve().is_relative_to(dist.resolve())or not p.is_file():missing.append({'consumer':name,'reference':ref})
 assert not missing,missing[:5]
 assert '/zhumadian/api'in all_js and 'undefined/serv'not in all_js and 'undefined/jnpf'not in all_js
 assert '/api/file/'in all_js,'AVATAR_NORMALIZER_NOT_EMITTED'
 if role=='security_pc':
  html=(dist/'index.html').read_text(encoding='utf-8');assert html.count('data-xnby-home-viewport=')==1
  charts=[n for n,t in texts.items()if '事件总数'in t and 'maxWidth:420'in t];tasks=[n for n,t in texts.items()if '巡检任务清单'in t];stats=[n for n,t in texts.items()if all(s in t for s in ['巡检统计','隐患数量统计','隐患整改统计','事件统计'])]
  assert len(charts)==len(tasks)==len(stats)==1
  assert all(t in texts[tasks[0]]for t in ['"min-width":"132"','"min-width":"168"','width:"100"'])
  css='\n'.join((dist/n).read_text(encoding='utf-8')for n in rows if n.endswith('.css'));assert 'container-type:inline-size'in css and 'minmax(min(100%,270px),1fr)'in css
 else:
  for endpoint in ['/jnpf/workflow/Engine/FlowBefore/List/1','/jnpf/workflow/Engine/FlowLaunch','/jnpf/workflow/Engine/FlowBefore/Audit/']:assert endpoint in all_js
  for token in ['views/workflow/flowTodo/index.vue','views/workflow/flowTodo/info/index.vue','views/workflow/startWithMeTwo/index.vue','views/workflow/startWithMeTwo/info/index.vue']:assert token in all_js
 result[role]={'buildExitCode':0,'compiledFilesSHA256Verified':len(rows),'localAssetReferencesVerified':count,'declaredRuntimeMapTilesOutsideStaticFrontend':runtime_tiles,'missingAssets':0,'compiledAvatarNormalizerEmitted':True,'allPriorRecipeSourcesRetained':True,'actualFullCompiledBrowserPassed':False,'publicInstalled':False}
proof={'schema':'xnby.r157.full-avatar-build-graph.v1','passed':True,'roles':result,'independentSafetyCompilerBoundarySourceComparisonOnlyTwoDeclaredAvatarPaths':True,'safetyCompilerExitZeroButFirstOuterVerifierFailedAgainstUnadaptedSource':True,'originalFailedTerminalKept':True,'followupChecksUseActualPriorFullAdapterStackNotRelaxedGenericAllowance':True,'actualDescendantsZeroAfterBothBuilds':True,'wholeBusinessOrPublicAcceptanceClaimed':False,'fullCloneReady':False}
dump(ROOT/'independent-full-build-verification.json',proof);print(json.dumps(proof,ensure_ascii=False))
