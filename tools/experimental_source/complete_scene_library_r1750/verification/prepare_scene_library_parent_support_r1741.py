from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/scene-file-frontend-r1735';p=W/'support/original_spatial_sync_release_support.py';s=p.read_text('utf8');before=s;package=hashlib.sha256((W/'backend/package-manifest.json').read_bytes()).hexdigest()
def sub(s,a,b):assert s.count(a)==1,a[:100];return s.replace(a,b)
s=sub(s,"PACKAGE_PIN='986ee1c0e3412ec4b63e1659e757a890d2f79ffb626697a328afba51260ec8cb'","PACKAGE_PIN='"+package+"'");s=sub(s,"len(manifest.get('inputs',{}))==34","len(manifest.get('inputs',{}))==35")
s=sub(s,"'developmentLoopbackOrigin','fineSource'}","'developmentLoopbackOrigin','fineSource','sceneProjectsRoot','sceneModelCatalog','sceneModelCatalogSHA256'}")
anchor='    fine=fine_preflight(app,release,value.get(\'fineSource\'))';extra='''    scene_library=None;scene_keys={'sceneProjectsRoot','sceneModelCatalog','sceneModelCatalogSHA256'}
    if scene_keys&set(value):
        need(scene_keys<=set(value),'COMPLETE_SCENE_LIBRARY_SETTINGS_REQUIRED')
        need(all(isinstance(value[k],str)and Path(value[k]).is_absolute()for k in ['sceneProjectsRoot','sceneModelCatalog']),'ABSOLUTE_SCENE_LIBRARY_PATHS_REQUIRED')
        root=plain(value['sceneProjectsRoot']);catalog=plain(value['sceneModelCatalog'])
        need(not root.is_relative_to(app)and not app.is_relative_to(root),'PRIVATE_SCENE_LIBRARY_OUTSIDE_APPLICATION_REQUIRED')
        for other in [data,projects,catalog]:need(not root.is_relative_to(other)and not other.is_relative_to(root),'DISTINCT_SCENE_LIBRARY_ROOT_REQUIRED')
        need(isinstance(value['sceneModelCatalogSHA256'],str)and re.fullmatch('[0-9a-f]{64}',value['sceneModelCatalogSHA256']),'PINNED_SCENE_LIBRARY_CATALOG_REQUIRED')
        catalog_raw=read(catalog,262144);need(digest(catalog_raw)==value['sceneModelCatalogSHA256'],'SCENE_LIBRARY_CATALOG_CHANGED');document=loads(catalog_raw)
        need(isinstance(document,dict)and document.get('schema')=='xnby.scene-model-library.v1'and isinstance(document.get('models'),list)and len(document['models'])<=64,'SCENE_LIBRARY_CATALOG_INVALID')
        ids=set()
        for row in document['models']:
            need(isinstance(row,dict)and isinstance(row.get('id'),str)and re.fullmatch('[-a-z0-9]{1,80}',row['id'])and row['id']not in ids and isinstance(row.get('sha256'),str)and re.fullmatch('[0-9a-f]{64}',row['sha256']),'SCENE_LIBRARY_CATALOG_ROW_INVALID');ids.add(row['id'])
        need(scene_rows is not None and any(row['route']=='/zhumadian/scene/model-library/catalog.json'and row['file']==catalog for row in scene_rows),'SCENE_LIBRARY_CATALOG_MUST_MATCH_DISPLAYED_PROJECT_MODELS')
        scene_library={k:value[k]for k in scene_keys}
''';s=sub(s,anchor,extra+anchor);s=sub(s,"return {'fineSource':fine,","return {'sceneLibrary':scene_library,'fineSource':fine,")
anchor="        if value.get('developmentLoopbackOrigin',False):worker_config['gatewayOrigin']='http://127.0.0.1:'+str(self.gateway_port)";s=sub(s,anchor,anchor+"\n        if self.settings['sceneLibrary']is not None:worker_config.update(self.settings['sceneLibrary'])")
s=sub(s,"sys.argv[4],project_files=True))","sys.argv[4],project_files=True,project_scenes=sys.argv[5]=='1'))")
s=sub(s,"str(self.worker['port']),nonce],stdin=","str(self.worker['port']),nonce,'1'if self.settings['sceneLibrary']is not None else'0'],stdin=")
s=sub(s,"        for path in ['/zhumadian/api/spatial-sync/v2/project/layers','/zhumadian/api/spatial-sync/v2/project/files']:","        paths=['/zhumadian/api/spatial-sync/v2/project/layers','/zhumadian/api/spatial-sync/v2/project/files']\n        if self.settings['sceneLibrary']is not None:paths.append('/zhumadian/api/spatial-sync/v2/project/scenes')\n        for path in paths:")
ast.parse(s)
def functions(value):
 out={}
 def walk(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
   elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[prefix+n.name]=ast.dump(n,include_attributes=False)
 walk(ast.parse(value).body);return out
old,new=functions(before),functions(s);changed={n for n in old if old[n]!=new[n]};assert changed=={'preflight','SpatialSyncRuntime.start','SpatialSyncRuntime.configure_gateway','SpatialSyncRuntime.verify_gateway'},changed
p.write_text(s,encoding='utf8');(W/'parent-support-r1741.json').write_text(json.dumps({'candidatePackageSHA256':package,'changedFunctions':sorted(changed),'allStopWaitRecoveryAndJobFunctionsASTUnchanged':True,'sceneRootCatalogPreflightReadOnlyBeforeStart':True,'publicUpdated':False},indent=2)+'\n',encoding='utf8');print('ORIGINAL_PARENT_SCENE_LIBRARY_GUARDS_CONFIG_AND_GATEWAY_PREPARED')
