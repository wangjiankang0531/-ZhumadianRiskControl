"""Independent closed-file audit; reads original code only, never starts the application."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,re,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
W=R/'work/resource-complete-control-r2438';B=W/'bundle';H=R/'_h/Application'
OLD=R/'work/public-same-window-r2330';F=R/'work/hazard-management-full-r2434'
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def j(p):return json.loads(p.read_bytes())
def enc(x):return(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def own_name(n):
 p=PurePosixPath(n);assert p.as_posix()==n and not p.is_absolute()and '..'not in p.parts and '\\'not in n
def functions(raw):
 t=ast.parse(raw);result={}
 for node in t.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):result[node.name]=ast.dump(node,include_attributes=False)
  elif isinstance(node,ast.ClassDef):
   for member in node.body:
    if isinstance(member,(ast.FunctionDef,ast.AsyncFunctionDef)):result[node.name+'.'+member.name]=ast.dump(member,include_attributes=False)
 return result
def main():
 report=W/'independent-graph-verification.json';assert not report.exists()
 plan=j(B/'update-manifest.json');payload=j(B/'payload/payload-manifest.json');release=j(B/'payload/release-manifest.json')
 files=payload['files'];assert len(files)==16227 and len(plan['files'])==602
 assert sha(B/'payload/release-manifest.json')==plan['newReleaseSHA256']
 assert sha(B/'payload/payload-manifest.json')==plan['newPayloadManifestSHA256']==release['payloadManifestSHA256']
 total=0;read_count=0;protected=0
 original=j(OLD/'bundle/payload/payload-manifest.json')['files']
 for n,v in files.items():
  own_name(n);assert set(v)=={'bytes','sha256'}and type(v['bytes'])is int and v['bytes']>=0 and re.fullmatch('[a-f0-9]{64}',v['sha256'])
  if n.startswith(('private/','UserData/','seed/','Assets/')):
   assert original.get(n)==v;protected+=1;continue
  p=(B/'payload'/n)if n in plan['files']else H/n
  assert p.is_file()and not p.is_symlink()and not p.is_junction()and not p.lstat().st_file_attributes&0x400,n
  assert p.stat().st_size==v['bytes']and sha(p)==v['sha256'],n
  total+=v['bytes'];read_count+=1
 for n,v in plan['files'].items():
  own_name(n);assert not n.startswith(('private/','UserData/','seed/','Assets/','runtime/'))
  p=B/'payload'/n;assert sha(p)==v['SHA256']and p.stat().st_size==v['bytes']
 expected=set(plan['files']);actual={p.relative_to(B/'payload').as_posix()for p in(B/'payload').rglob('*')if p.is_file()};assert actual==expected
 for n,h in release['controllerFiles'].items():
  if n in files:assert files[n]['sha256']==h
  else:
   assert j(OLD/'bundle/payload/release-manifest.json')['controllerFiles'][n]==h
   assert sha(H/n)==h
 package=release['spatialSync']['codeRoot'];pm=B/'payload'/package/'package-manifest.json'
 assert sha(pm)==release['spatialSync']['packageManifestSHA256'];package_rows=j(pm)['inputs'];assert len(package_rows)==44
 for n,v in package_rows.items():assert files[package+'/'+n]==v and sha(B/'payload'/package/n)==v['sha256']
 proxies=['iis/App_Code/XnbyReferenceProxy.cs','deploy/iis_original/App_Code/XnbyReferenceProxy.cs']
 assert(B/'payload'/proxies[0]).read_bytes()==(B/'payload'/proxies[1]).read_bytes()
 for n in proxies:assert release['staticInitialLoadPerformance']['files'][n]==files[n]
 static=release['sceneStatic'];sm=B/'payload'/static['manifestPath'];assert sha(sm)==static['manifestSHA256'];scene=j(sm)['files']
 for n,v in scene.items():assert files['frontend/scene/'+n]==v
 old=functions((OLD/'runtime/tools/original_offline_scene_profile_r2191.py').read_bytes())
 new=functions((W/'runtime/tools/original_offline_scene_profile_r2191.py').read_bytes());assert old==new
 old=functions((R/'work/public-offline-entry-r2306/bundle/payload/tools/original_spatial_sync_release_support.py').read_bytes())
 new=functions((B/'payload/tools/original_spatial_sync_release_support.py').read_bytes())
 changed={n for n in old if old[n]!=new.get(n)}
 assert changed=={'preflight','SpatialRuntime.start','SpatialRuntime.configure_gateway','SpatialRuntime.verify_gateway'}
 assert set(new)-set(old)=={'checked_client_resources'}
 prior=j(R/'work/hazard-management-full-r2322/actual-compiled-source-files.json');current=j(F/'actual-compiled-source-files.json')
 changed_compiler={n for n in set(prior)|set(current)if prior.get(n)!=current.get(n)}
 source_map=j(R/'Application/tools/experimental_source/resource_control_merge_r2433/source-map.json')['inputs']
 assert changed_compiler=={v['destination']for v in source_map}and len(current)==3737
 for v in source_map:assert current[v['destination']]['sha256']==v['newSHA256']
 source=j(F/'source-restoration.json');assert source['originalProjectUnchanged']and source['isolatedCopyRestoredToOriginal']and source['failure']is None
 assert all(source['receipts'][key]['sourceRestored']for key in('resourceWorkspace','modeNavigation','publicSceneEntry','statistics','editor','sceneHost'))
 assert source['receipts']['avatar']['originalSourcesRestored']
 private=V/'public-offline-entry-private-r2306';oldp=private/'spatial-sync-settings.private.json';newp=private/'spatial-sync-settings.client-resources-r2438.private.json'
 assert sha(oldp)=='286aef3fa30d953d3037f36dc5dc2fadb3771a5cd229226ee2b117e5d1ff83f3'and sha(newp)==release['spatialSync']['settingsSHA256']
 config=j(newp);assert {k:v for k,v in config.items()if k!='clientResources'}==j(oldp)
 assert release['spatialSync']['settingsPath']=='private/spatial-sync-settings.client-resources-r2438.private.json'
 assert j(OLD/'bundle/payload/release-manifest.json')['spatialSync']['settingsPath']=='private/spatial-sync-settings.private.json'
 assert len(config['clientResources']['allowedInstallations'])==2
 r51=R/'Document/Deployment/public_home_same_window_r51_20261112/prepared-manifest.json'
 assert sha(r51)=='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
 result={'passed':True,'completeGraphRows':len(files),'actualProgramFilesRead':read_count,'actualProgramLogicalBytes':total,'protectedRowsKeptByExactPriorMetadataNotRead':protected,'actualSparseFilesRead':len(actual),'resourceWorkerSources':44,'sceneStaticRows':len(scene),'sameWindowOnlyCompilerInputRetained':True,'changedInputsFromR51':sorted(changed_compiler),'allOriginalProfileFunctionASTUnchanged':True,'changedOriginalSupportFunctions':sorted(changed),'newPrivateConfigurationProposalValidatedNotApplied':True,'oldPrivateAccountAccessAndEveryOtherSettingUnchanged':True,'fixedR51TransportManifestUnchanged':True,'installedCodeOrDatabaseOrGISModified':False,'applicationOrGISProcessesStarted':0,'actualLifecycleOrNormalUserOrPublic250252Accepted':False}
 with report.open('x',encoding='utf8')as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
