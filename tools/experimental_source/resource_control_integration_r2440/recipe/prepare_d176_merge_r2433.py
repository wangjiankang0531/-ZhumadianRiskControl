"""Compose fixed D170 parent inputs with D176 controls; leave public R51 unchanged."""
from pathlib import Path
import copy,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application'
BASE=A/'tools/experimental_source/resource_no_gis_workspace_20261112'
NEW=A/'tools/experimental_source/resource_gis_browser_20261112'
S=A/'tools/experimental_source/resource_control_merge_r2433'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def enc(x):return(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(raw)
def main():
 assert not S.exists()
 receipt=j(R/'Document/Deployment/resource_gis_browser_received_r2432_20261112/source-receipt.json');assert receipt['received']and receipt['sourceFiles']==26
 source_map=BASE/'source-map.json';assert sha(source_map)=='202d2e8ee6096ea480b51c7a77a4e6dad6a3932629923327f3085e75a74bce0a'
 mapping=j(source_map);assert len(mapping['inputs'])==7
 rows=copy.deepcopy(mapping['inputs']);changes=[]
 for row in rows:
  src=BASE/row['source'];assert sha(src)==row['newSHA256']
  if row['destination']=='src/views/sceneEditor/client_resource_transport.js':
   src=NEW/'web/src/client_resource_transport.js';assert sha(src)=='2717b1561aba141c19fefaf23b8f186bf9d359ba658468fa2ee10d7244c0f90b'
   changes.append({'destination':row['destination'],'beforeSHA256':row['newSHA256'],'afterSHA256':sha(src)});row['newSHA256']=sha(src)
  put(S/row['source'],src.read_bytes())
 assert len(changes)==1;mapping['inputs']=rows;put(S/'source-map.json',enc(mapping))
 manifest=NEW/'recipe/scene_delivery_sources.json';assert sha(manifest)=='4ded0cfeab1146c68536c38fb76ac48744769578314d4aa8122b4c2fd5f0a321'
 m=j(manifest);pins={'scene_delivery_sources.json':sha(manifest)}
 for group in('sourcePins','vendorPins','mainInputs'):
  for name,pin in m[group].items():assert name not in pins or pins[name]==pin;pins[name]=pin
 def source(name):
  if name=='scene_delivery_sources.json':return manifest
  if name=='layer_editor_delivery_manifest.json':return NEW/'recipe'/name
  if name in('src/resource_management_client.js','src/resource_management_topic.js','src/client_resource_transport.js'):return NEW/'web'/name
  return BASE/'web'/name
 index={}
 for name,pin in pins.items():
  src=source(name).resolve();assert src.is_relative_to(BASE)or src.is_relative_to(NEW)
  assert src.is_file()and not src.is_symlink()and not src.lstat().st_file_attributes&1024 and sha(src)==pin
  index[name]={'source':src.relative_to(A).as_posix(),'bytes':src.stat().st_size,'sha256':pin}
 assert len(index)==319
 put(S/'scene-source-index.json',enc({'schema':'xnby.fixed.scene-source-index.v1','manifestSHA256':sha(manifest),'files':index,'expectedOutputs':m['expectedOutputs']}))
 result={'prepared':True,'publicBase':'R51 b3649166','parentCompilerInputs':7,'parentChangesAgainstD170':changes,
  'parentCompilerMapSHA256':sha(S/'source-map.json'),'sceneSourceFiles':319,'sceneSourceBytes':sum(v['bytes']for v in index.values()),
  'sceneManifestSHA256':sha(manifest),'allInputsQualifiedAgainstFixedD170AndD176':True,'qualifiedBackendD175OwnManifestStillBdf6d7e1':True,
  'publicOr252OrPrivateConfigOrRegistryChanged':False,'fullPortalBuildAndSceneRebuildStillPending':True}
 put(S/'prepared.json',enc(result));print(json.dumps(result))
if __name__=='__main__':main()
