from pathlib import Path
import ast
V=Path(__file__).parent
def put(n,s):
 p=V/n;assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf8')
s=(V/'prepare_instances_scene_stage_r1716.py').read_text('utf8').replace('r1716','r1743').replace('r1715','r1736').replace('model-instances-receiver-r1714','scene-file-frontend-r1735');put('prepare_scene_files_stage_r1743.py',s)
for old,new in[('verify_instances_static_r1717.py','verify_scene_files_static_r1744.py'),('launch_instances_static_r1717.py','launch_scene_files_static_r1744.py')]:
 s=(V/old).read_text('utf8').replace('r1716','r1743').replace('r1717','r1744').replace('model-instances-receiver-r1714','scene-file-frontend-r1735').replace('verify_instances_static_r1744.py','verify_scene_files_static_r1744.py');put(new,s)
s=(V/'prepare_instances_original_parent_r1718.py').read_text('utf8').replace('r1718','r1745').replace('R1718','R1745').replace('r1716','r1743').replace('r1717','r1744').replace('r1715','r1736').replace('model-instances-receiver-r1714/support','scene-file-frontend-r1735/support').replace("'fineSourceProtocolContracts':819","'fineSourceProtocolContracts':827").replace("'sourceMainInputs':166","'sourceMainInputs':169")
needle="private=put('spatial-settings.private.json',enc(settings));assert sha(private)==sha(B/'spatial-settings.private.json')";assert s.count(needle)==1
replacement="""settings['sceneProjectsRoot']=str(R/'work/scene-files-original-r1745/cloud-scenes');settings['sceneModelCatalog']=str(G/'frontend/scene/model-library/catalog.json');settings['sceneModelCatalogSHA256']=sha(S/'payload/frontend/scene/model-library/catalog.json');assert 'a531000000000000000000000001d4c2'in settings['access']['writers'];private=put('spatial-settings.private.json',enc(settings))""";s=s.replace(needle,replacement)
needle="sources['payload-manifest.json']=put('payload/payload-manifest.json',enc(pm));";assert s.count(needle)==1
replacement="""backend=R/'work/scene-file-frontend-r1735/backend';old_code=release['spatialSync']['codeRoot'];new_code='extensions/spatial_sync_scene_files_r1745'
for n in list(sources):
 if n.startswith(old_code+'/'):sources.pop(n);pm['files'].pop(n,None);release['controllerFiles'].pop(n,None)
for p in backend.rglob('*'):
 if p.is_file():
  n=new_code+'/'+p.relative_to(backend).as_posix();sources[n]=p;pm['files'][n]=pin(p);release['controllerFiles'][n]=sha(p)
release['spatialSync']['codeRoot']=new_code;release['spatialSync']['packageManifestSHA256']=sha(backend/'package-manifest.json')
sources['payload-manifest.json']=put('payload/payload-manifest.json',enc(pm));""";s=s.replace(needle,replacement);put('prepare_scene_files_original_parent_r1745.py',s)
print('FULL_SCENE_FILE_ORIGINAL_PARENT_PREPARERS_READY')
