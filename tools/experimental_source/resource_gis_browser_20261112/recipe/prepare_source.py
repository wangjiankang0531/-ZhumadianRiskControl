from pathlib import Path
import hashlib,json,shutil,sys
R=Path('D:/Project/Zhumadian');P=R/'Application/tools/experimental_source/resource_gis_browser_20261112';BASE=R/'Application/tools/experimental_source/resource_no_gis_workspace_20261112';target=Path(sys.argv[1]).absolute();assert not target.exists(),'New source output only'
shutil.copytree(BASE/'web',target/'web');shutil.copytree(BASE/'portal',target/'portal')
manifest=json.loads((P/'recipe/scene_delivery_sources.json').read_text(encoding='utf-8'))
for name in manifest['sourcePins']:
 if not name.startswith('../shared/'):continue
 source=(BASE/'web'/name).resolve();destination=(target/'web'/name).resolve();assert source.is_relative_to(BASE.resolve())and destination.is_relative_to(target.resolve());destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
for name in ['resource_management_client.js','resource_management_topic.js','client_resource_transport.js']:shutil.copyfile(P/'web/src'/name,target/'web/src'/name)
for name in ['scene_delivery_sources.json','layer_editor_delivery_manifest.json']:shutil.copyfile(P/'recipe'/name,target/'web'/name)
for name,pin in manifest['sourcePins'].items():assert hashlib.sha256((target/'web'/name).read_bytes()).hexdigest()==pin,name
print(json.dumps({'sourcePinsMatched':len(manifest['sourcePins']),'copiedGISOrRuntime':False,'source':str(target)}))
