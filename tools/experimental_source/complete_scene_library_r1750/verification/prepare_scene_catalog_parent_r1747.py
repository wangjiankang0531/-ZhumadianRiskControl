"""Correct string/Path comparison after a verified pre-run rejection, new candidate only."""
from pathlib import Path
import ast,hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent
old=R/'work/scene-file-frontend-r1735/support';W=R/'work/scene-catalog-parent-r1747';D=R/'Document/Deployment/scene_catalog_parent_r1747_20261107'
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(raw)
assert not W.exists()and not D.exists()
prior=J(R/'work/su1746/verified-result.json');terminal=J(R/'Document/Deployment/fine_browser_original_r1745_20261107/actual-parent-terminal-r1746.json')
assert not prior['passed']and prior['originalCodeRestored']and prior['originalPointerRestored']and prior['allActualJobsZeroBeforeClose']and terminal['actualOuterJobZero']
assert prior['actualTerminals'][0]['earlyExitBeforeRunAllocation']and not(R/'work/su1746/scene-file-write-intent.private.json').exists()
target='original_spatial_sync_release_support.py';before=(old/target).read_text('utf8')
a="row['file']==catalog";b="plain(row['file'])==catalog";assert before.count(a)==1
after=before.replace(a,b);ast.parse(after)
oldtree=ast.parse(before);newtree=ast.parse(after)
assert [(n.name,ast.dump(n))for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name!='preflight']==[(n.name,ast.dump(n))for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name!='preflight']
for p in old.iterdir():
 assert p.is_file()
 put(W/'support'/p.name,after.encode('utf8')if p.name==target else p.read_bytes())
stage=R/'work/scene-fine-auth-stage-r1743'
spec=importlib.util.spec_from_file_location('scene_static_r1747',stage/'payload/tools/original_scene_static_routes.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=m.preflight(stage/'payload',J(stage/'scene-descriptor.json'),J(stage/'scene-readonly-assets.private.json'))
catalog=stage/'payload/frontend/scene/model-library/catalog.json';route='/zhumadian/scene/model-library/catalog.json'
assert len([r for r in rows if r['route']==route])==1
assert not any(r['route']==route and r['file']==catalog for r in rows)
def match(rs):return any(r['route']==route and m.plain(r['file'])==catalog for r in rs)
assert match(rows)
assert not match([dict(r,file=str(catalog.with_name('other.json')))if r['route']==route else r for r in rows])
assert not match([dict(r,route=route+'.foreign')if r['route']==route else r for r in rows])
proof={'passed':True,'priorOriginalParentRefusedBeforeAnyRunOrWrite':True,'actualStaticRows':len(rows),'actualOriginalRowStringPathMismatchReproduced':True,'canonicalSameCatalogAccepted':True,'differentCatalogAndRouteRejected':True,'allOtherFunctionAndClassASTsUnchanged':True,'beforeSHA256':sha(old/target),'afterSHA256':sha(W/'support'/target),'sceneSchemaBackendFrontendAndLifecycleChanged':False,'publicChanged':False}
put(D/'path-comparison-proof-r1747.json',(json.dumps(proof,indent=2)+'\n').encode())
s=(V/'prepare_scene_files_original_parent_r1745.py').read_text('utf8').replace('r1745','r1748').replace('R1745','R1748').replace("support=R/'work/scene-file-frontend-r1735/support'","support=R/'work/scene-catalog-parent-r1747/support'")
ast.parse(s);put(V/'prepare_scene_files_original_parent_r1748.py',s.encode())
print(json.dumps(proof))
