"""Retain exact frontend/backend/support inputs without claiming original-host acceptance."""
from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;W=R/'work/scene-file-frontend-r1735';S=A/'tools/experimental_source/complete_scene_library_r1750'
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
files=[]
def put(n,raw):
 p=A/n;p.parent.mkdir(parents=True,exist_ok=True)
 raw.decode('utf8')
 if p.suffix=='.py':ast.parse(raw)
 with p.open('xb')as f:f.write(raw)
 files.append(n);return p
assert not S.exists()
build=J(R/'Document/Deployment/scene_model_visibility_build_r1736_20261107/qualified-build-r1736.json');assert build['passed']and build['nodeTests']['pass']==827 and build['sourceInputs']==266
old={x['input']:x for x in J(A/'tools/experimental_source/model_instances_receiver_r1721/source-closure.json')['closure']}
m=J(W/'source/web/scene_delivery_sources.json');closure=[];changed=[]
for n,h in m['sourcePins'].items():
 src=(W/'source/web'/n).resolve();assert src.is_relative_to((W/'source').resolve())and sha(src)==h
 if n in old and old[n]['sha256']==h:target=A/old[n]['retainedSource'];assert sha(target)==h
 else:target=(S/'frontend/web'/n).resolve();assert target.is_relative_to((S/'frontend').resolve());put(target.relative_to(A).as_posix(),src.read_bytes());changed.append(n)
 closure.append({'input':n,'sha256':h,'retainedSource':target.relative_to(A).as_posix()})
target=put((S/'frontend/web/scene_delivery_sources.json').relative_to(A).as_posix(),(W/'source/web/scene_delivery_sources.json').read_bytes());closure.append({'input':'scene_delivery_sources.json','sha256':sha(target),'retainedSource':target.relative_to(A).as_posix()})
for p in(R/'work/scene-catalog-parent-r1747/support').glob('*.py'):
 n='support/'+p.name
 if old.get(n,{}).get('sha256')==sha(p):row=old[n];assert sha(A/row['retainedSource'])==row['sha256']
 else:target=put((S/n).relative_to(A).as_posix(),p.read_bytes());row={'input':n,'sha256':sha(p),'retainedSource':target.relative_to(A).as_posix()}
 closure.append(row)
assert len(closure)==272 and len({r['input']for r in closure})==272
put((S/'source-closure.json').relative_to(A).as_posix(),enc({'sourceInputs':266,'changedInputs':changed,'closure':closure,'requiresOriginalSDKAndDependencies':True,'standaloneCleanPublicBuildClaimed':False,'originalHostAcceptanceNotImplied':True}))
backend=J(W/'backend/package-manifest.json');assert len(backend['inputs'])==35
for n,pin in backend['inputs'].items():assert sha(W/'backend'/n)==pin['sha256']and(W/'backend'/n).stat().st_size==pin['bytes']
for p in(W/'backend').rglob('*'):
 if p.is_file():put((S/'backend'/p.relative_to(W/'backend')).relative_to(A).as_posix(),p.read_bytes())
scripts=['scene_file_contract_r1734.js','prepare_scene_file_frontend_r1734.py','prepare_scene_file_frontend_r1735.py','scene_file_client_tests_r1736.mjs','prepare_scene_file_build_r1736.py','build_scene_file_frontend_r1736.py','discover_fine_scene_r1736.mjs','rebase_scene_library_original_package_r1737.py','check_scene_schema_r1739.mjs','test_scene_original_package_r1739.py','run_scene_original_package_r1739.py','scene_library_component_r1740.js','build_scene_library_component_r1740.mjs','scene_library_browser_server_r1740.py','drive_scene_library_component_r1740.mjs','test_scene_library_component_r1740.py','run_scene_library_component_r1740.py','prepare_scene_library_parent_support_r1741.py','prepare_scene_library_parent_support_r1742.py','prepare_scene_files_original_pipeline_r1743.py','prepare_scene_files_stage_r1743.py','verify_scene_files_static_r1744.py','launch_scene_files_static_r1744.py','prepare_scene_files_original_parent_r1745.py','prepare_scene_files_original_browser_r1746.py','original_configuration_lifecycle_r1746.mjs','run_original_configuration_lifecycle_r1746.py','launch_original_configuration_lifecycle_r1746.py','prepare_scene_catalog_parent_r1747.py','prepare_scene_files_original_parent_r1748.py','prepare_original_scene_retry_r1749.py','original_configuration_lifecycle_r1749.mjs','run_original_configuration_lifecycle_r1749.py','launch_original_configuration_lifecycle_r1749.py','snapshot_complete_scene_sources_r1750.py']
for n in scripts:put((S/'verification'/n).relative_to(A).as_posix(),(V/n).read_bytes())
out={'applicationFiles':files,'sourceClosureEntries':272,'changedFrontendInputs':changed,'qualifiedBackendInputs':35,'qualifiedBackendManifestSHA256':sha(W/'backend/package-manifest.json'),'exactOriginalSourceSnapshotsOnly':True,'originalHostAccepted':False,'publicUpdated':False,'publicPushed':False}
put((S/'snapshot.json').relative_to(A).as_posix(),enc(out));print(json.dumps({'snapshotReady':True,'applicationFiles':len(files),'closureEntries':272,'changedFrontendInputs':changed,'publicPushed':False}))
