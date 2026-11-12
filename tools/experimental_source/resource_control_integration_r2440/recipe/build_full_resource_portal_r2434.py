"""Build original portal navigation, view/edit links and local GIS error messages."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
W=R/'work/hazard-management-full-r2434'
sys.path.insert(0,str(T));sys.path.insert(0,str(V))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def inventory(root):
 rows={}
 for folder,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if n not in ['node_modules','.git','dist','.vite']]
  for name in names:
   if name=='node_modules':continue
   p=Path(folder)/name
   assert not p.is_symlink() and not p.is_junction() and p.resolve()==p
   rows[p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
 return rows
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

RESOURCE_SOURCE=A/'tools/experimental_source/resource_control_merge_r2433'
RESOURCE_MAP_PIN='48ec119a116c8e63fd52fd1e063bd94e45328351c97a58d04822cf2894dcc4dc'
RESOURCE_DESTINATIONS={
 'src/views/sceneViewer/index.vue','src/views/sceneEditor/index.vue',
 'src/views/sceneEditor/project_scene_host.js','src/views/sceneEditor/http_json.js',
 'src/views/sceneEditor/resource_project_host.js','src/views/sceneEditor/client_resource_transport.js',
 'src/views/sceneEditor/scene_topic_navigation.js'}
EXPECTED_RESOURCE_DIFF=RESOURCE_DESTINATIONS|{'src/views/home/index.vue'}

@contextmanager
def resource_overlay(project):
 map_file=RESOURCE_SOURCE/'source-map.json'
 assert sha(map_file)==RESOURCE_MAP_PIN
 rows=j(map_file)['inputs'];assert len(rows)==7 and {r['destination']for r in rows}==RESOURCE_DESTINATIONS
 changes=[]
 for row in rows:
  src=RESOURCE_SOURCE/row['source'];new=src.read_bytes();assert hashlib.sha256(new).hexdigest()==row['newSHA256']
  path=project/row['destination'];old=path.read_bytes()if path.exists()else None
  if 'expectedOriginalBeforeSHA256'in row:
   assert old is not None and hashlib.sha256(old).hexdigest()==row['expectedOriginalBeforeSHA256'],'EXACT_BASE_COMPILER_SOURCE_REQUIRED:'+row['destination']
  else:assert row['addOnlyOrIdentical']is True and(old is None or old==new),'UNKNOWN_ADD_ONLY_COMPILER_SOURCE:'+row['destination']
  changes.append((path,old,new,row))
 receipt={'fixedSevenInputMapSHA256':RESOURCE_MAP_PIN,'actualFinalInputSHA256':{r['destination']:r['newSHA256']for r in rows},'sourceRestored':False}
 applied=[]
 try:
  for path,old,new,row in changes:
   assert path.parent.is_dir();path.write_bytes(new);applied.append((path,old,new))
   target=W/'actual-resource-compiler-inputs'/row['destination'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(new)
   if row['destination']=='src/views/sceneViewer/index.vue':(W/'actual-sceneViewer-compiler-source.vue').write_bytes(new)
   if row['destination']=='src/views/sceneEditor/index.vue':(W/'actual-sceneEditor-compiler-source.vue').write_bytes(new)
  yield receipt
 finally:
  for path,old,new in reversed(applied):
   assert path.read_bytes()==new,'RESOURCE_COMPILER_SOURCE_CHANGED_BEFORE_RESTORE'
   if old is None:path.unlink()
   else:path.write_bytes(old)
  receipt['sourceRestored']=all((not p.exists())if old is None else p.read_bytes()==old for p,old,new,row in changes)
  assert receipt['sourceRestored']

def main():
 assert not W.exists(),'DO_NOT_RESTART_EXISTING_ATTEMPT'
 from original_scene_model_host_overlay_r1796 import scene_host_override,HOSTS,ROUTE
 from original_header_avatar_compat import header_avatar_override,HEADER,EXTRA
 from original_hazard_statistics_overlay_r1118 import hazard_statistics_override,REL,AFTER
 from original_hazard_editor_submit_overlay_r1178 import hazard_editor_override,PINS as EDITOR_PINS
 import original_public_login_query_compat_20261101 as login
 import build_risk_frontend_r22_r2_20261101 as recipe
 previous=R/'work/hazard-management-full-r1181/actual-compiled-source-files.json'
 old_actual=j(previous)
 assert old_actual[REL]['sha256']==AFTER and all(old_actual[n]['sha256']==p['after'] for n,p in EDITOR_PINS.items())
 assert j(R/'work/user_feedback_20261031/avatar-full-r157/independent-full-build-verification.json')['passed']
 cfg=j(R/'Document/Deployment/confirmed_operations_20261029/security-build-r2-config.json')
 origin=Path(cfg['project']);before=inventory(origin)
 old_login=login.published_login_query_override;old_run=subprocess.run;captured={};receipts={}
 @contextmanager
 def combined(project,reference):
  with old_login(project,reference) as original,header_avatar_override(project) as avatar,hazard_statistics_override(project) as stats,hazard_editor_override(project) as editor,scene_host_override(project) as host:
   receipts['avatar']=avatar;receipts['statistics']=stats;receipts['editor']=editor;receipts['sceneHost']=host;yield original
 def intercept(command,*args,**kwargs):
  if isinstance(command,list) and any(str(x).endswith('vite.js') for x in command):
   assert not captured,'EXACT_SINGLE_SAFETY_COMPILER_BOUNDARY_REQUIRED'
   home=Path(kwargs['cwd'])/'src/views/home/index.vue';raw=home.read_bytes()
   old=b'window.open("http://127.0.0.1:8767/?topic=emergency&mode=command", "_blank", "noopener,noreferrer");'
   new=b'void sceneRouter.push("/sceneViewer");'
   assert raw.count(old)==1 and raw.count(b'if (item.enCode == "mjyjzh")')==1
   router_old=b'const { currentRoute } = useRouter();'
   router_new=b'const sceneRouter = useRouter();\nconst { currentRoute } = sceneRouter;'
   assert raw.count(router_old)==1
   changed=raw.replace(old,new,1).replace(router_old,router_new,1)
   assert changed.count(b'void sceneRouter.push("/sceneViewer");')==1
   assert b'window.open("/zhumadian/sceneViewer"'not in changed
   assert (b'?t=$'+b'{token}&user=')not in changed and b'127.0.0.1:8767'not in changed
   receipts['publicSceneEntry']={'path':'src/views/home/index.vue','beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(changed).hexdigest(),'target':'/sceneViewer','originalRouterBaseKept':True,'sameTabSessionStorageKept':True,'sameOriginOriginalLoginGuardAndHost':True,'noCredentialQueryOrNewDebugPort':True,'sourceRestored':False}
   home.write_bytes(changed)
   mode_sources={}
   local_messages={
    'LOCAL_GIS_UNAVAILABLE':'未能连接本机三维服务，请确认服务已启动并允许此站点访问本机网络后重连',
    'LOCAL_GIS_VERSION_MISMATCH':'本机三维资源版本不匹配，请更新本机三维组件后重连',
    'LOCAL_GIS_GRANT_REJECTED':'本机三维授权已失效，请重新连接',
    'LOCAL_GIS_GRANT_UNAVAILABLE':'三维授权服务暂不可用，请稍后重连',
    'LOCAL_GIS_SESSION_REQUIRED':'本机三维会话已结束，请重新连接',
    'LOCAL_GIS_SOURCE_CHANGED':'本机地景资源已切换，请重新连接',
    'LOCAL_GIS_RENEWAL_FAILED':'三维会话续期失败，请重新连接',
    'LOCAL_GIS_ABORTED':'三维连接已中断，请重新连接'}
   for view,target,label,pin in [
    ('sceneViewer','/sceneEditor','编辑图层与场景','fbdad8131aeb2efad9c7bfac5b9675b7e2b9b88ddc1efff09b4458f09ea4006e'),
    ('sceneEditor','/sceneViewer','返回三维查看','abce37ba42471ac46b737903486e1e94e7ac412730c333e71c9939dd529db9bf')]:
    relative='src/views/'+view+'/index.vue';file=Path(kwargs['cwd'])/relative;old_bytes=file.read_bytes();assert hashlib.sha256(old_bytes).hexdigest()==pin
    text=old_bytes.decode('utf-8');anchor='<span>{{ statusText }}</span>';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n      <router-link class="scene-mode-link" to="'+target+'">'+label+'</router-link>',1)
    anchor='const statusText=computed(';assert text.count(anchor)==1
    text=text.replace(anchor,'Object.assign(messages,'+json.dumps(local_messages,ensure_ascii=False,separators=(',',':'))+');\n'+anchor,1)
    assert text.count('</style>')==1;text=text.replace('</style>','.scene-mode-link{color:#b9e1ff;text-decoration:underline;white-space:nowrap}.scene-'+('viewer'if view=='sceneViewer'else'editor')+'-status{flex-wrap:wrap}</style>')
    new_bytes=text.encode('utf-8');mode_sources[relative]=(old_bytes,new_bytes);file.write_bytes(new_bytes)
    (W/('actual-'+view+'-compiler-source.vue')).write_bytes(new_bytes)
   receipts['modeNavigation']={'files':{n:{'beforeSHA256':hashlib.sha256(old).hexdigest(),'afterSHA256':hashlib.sha256(new).hexdigest()}for n,(old,new)in mode_sources.items()},'backendACLAndOriginalLoginKept':True,'sourceRestored':False}
   try:
    with resource_overlay(Path(kwargs['cwd'])) as resources:
     receipts['resourceWorkspace']=resources
     actual=inventory(Path(kwargs['cwd']));captured.update(actual)
     prior=j(R/'work/hazard-management-full-r1815/actual-compiled-source-files.json')
     diff={n for n in set(prior)|set(actual)if prior.get(n)!=actual.get(n)}
     assert diff==EXPECTED_RESOURCE_DIFF,'ONLY_HOME_PLUS_SEVEN_RESOURCE_COMPILER_INPUTS_REQUIRED:'+str(sorted(diff))
     assert actual[REL]['sha256']==AFTER and all(actual[n]['sha256']==p['after']for n,p in EDITOR_PINS.items())
     dump(W/'actual-compiled-source-files.json',actual)
     dump(W/'compiler-boundary-proof.json',{'comparedTo':'work/hazard-management-full-r1815/actual-compiled-source-files.json','changedCompilerInputs':sorted(diff),'allOtherPriorAdaptersPreserved':True,'actualSourceFiles':len(actual),'normalOriginalLoginAndBackendACLKept':True,'notRuntimePatchOfBuiltJavaScript':True})
     (W/'actual-home-compiler-source.vue').write_bytes(changed)
     kwargs.pop('timeout',None);kwargs['env']['VITE_SCENE_HOST_DEVELOPMENT']='false'
     command=[command[0],'--max-old-space-size=1536',*command[1:]]
     p=subprocess.Popen(command,*args,**kwargs);p.wait();return subprocess.CompletedProcess(command,p.returncode)
   finally:
    assert home.read_bytes()==changed
    for relative,(old_bytes,new_bytes)in mode_sources.items():
     file=Path(kwargs['cwd'])/relative;assert file.read_bytes()==new_bytes;file.write_bytes(old_bytes)
    receipts['modeNavigation']['sourceRestored']=True
    home.write_bytes(raw);receipts['publicSceneEntry']['sourceRestored']=home.read_bytes()==raw
  return old_run(command,*args,**kwargs)
 recipe.STAGE=W;login.published_login_query_override=combined;subprocess.run=intercept
 failure=None
 try:recipe.main()
 except BaseException as e:failure={'kind':type(e).__name__,'message':str(e)};raise
 finally:
  subprocess.run=old_run;login.published_login_query_override=old_login
  if W.exists():dump(W/'source-restoration.json',{'originalProjectUnchanged':inventory(origin)==before,'isolatedCopyRestoredToOriginal':inventory(W/'source')==before if(W/'source').exists()else None,'receipts':receipts,'failure':failure})
 assert {n for n in set(captured)|set(j(R/'work/hazard-management-full-r1815/actual-compiled-source-files.json'))if captured.get(n)!=j(R/'work/hazard-management-full-r1815/actual-compiled-source-files.json').get(n)}==EXPECTED_RESOURCE_DIFF,'ONLY_ORIGINAL_HOME_DELTA_FROM_QUALIFIED_PRODUCTION_REQUIRED'
 previous_model_host=j(R/'work/hazard-management-full-r1673/actual-compiled-source-files.json');assert {n for n in set(captured)|set(previous_model_host)if captured.get(n)!=previous_model_host.get(n)}==EXPECTED_RESOURCE_DIFF,'ONLY_NEW_MODEL_HOST_SOURCE_DELTA_REQUIRED'
 assert receipts['resourceWorkspace']['sourceRestored']
 assert receipts['modeNavigation']['sourceRestored']
 assert receipts['statistics']['sourceRestored'] and receipts['editor']['sourceRestored'] and receipts['avatar']['originalSourcesRestored'] and receipts['sceneHost']['sourceRestored']
 assert inventory(origin)==before and inventory(W/'source')==before
 result=j(W/'candidate-result.json');assert result['buildExitCode']==0 and result['referenceAndOriginalSourceRestored']
 files=inventory(W/'build/dist');assert files==result['fullFrontendFiles']
 previous_host=j(R/'work/hazard-management-full-r1475/actual-compiled-source-files.json');assert {n for n in set(captured)|set(previous_host)if captured.get(n)!=previous_host.get(n)}==EXPECTED_RESOURCE_DIFF,'ONLY_D122_HOST_QUERY_DELTA_FROM_VERIFIED_LOCAL_BUILD_REQUIRED';assert captured['src/views/sceneEditor/project_scene_host.js']['sha256']=='a4fc03fcde3c8ed18cba9f60217616830f0475a404f152c5d341f982f668d46f'
 text='\n'.join((W/'build/dist'/n).read_text('utf8') for n in files if n.endswith('.js'))
 assert '保存未完成，请保留当前内容并重试。'in text and '详情未取得，请返回列表刷新后重试。'in text and '以下仍为上次成功结果' in text and 'undefined/serv' not in text and 'undefined/jnpf' not in text
 dump(W/'full-build-result.json',{'passed':True,'completeSafetyFrontendFiles':len(files),'compiledBytes':sum(v['bytes']for v in files.values()),'actualCompilerInputs':len(captured),'changedCompilerInputs':sorted(EXPECTED_RESOURCE_DIFF),'statisticsSourceSHA256':AFTER,'allPriorSafetyAdaptersAndAvatarRetained':True,'sharedAndIsolatedSourcesRestored':True,'actualFullBrowserOrOriginalBackendOrPublicAccepted':False,'loopbackHostDevelopmentBuild':False,'productionFrontendCompilerOutput':True,'FineSourceEarlyHostIncluded':True,'originalHomeCommandTargetsSameOriginSceneViewer':True,'originalHomeUsesSameWindowRouter':True,'noTokenStorageOrPermissionChanges':True,'onlyHomeAndSevenResourceInputsChangedFromQualifiedR1815':True,'sevenResourceCompilerSourcesRestored':receipts['resourceWorkspace']['sourceRestored'],'formalViewEditLinksIncluded':True,'localGISErrorMessagesIncluded':True,'productionBrowserAndIISVerificationPending':True,'publicDeployed':False})
 print(json.dumps(j(W/'full-build-result.json')))
if __name__=='__main__':main()
