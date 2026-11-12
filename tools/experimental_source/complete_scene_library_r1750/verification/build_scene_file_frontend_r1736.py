"""Freeze actual D125+auth inputs, discover bytes, then canonical rebuild and tests."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;W=R/'work/scene-file-frontend-r1735';web=W/'source/web';D=R/'Document/Deployment/scene_model_visibility_build_r1736_20261107'
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not D.exists();received=J(R/'Document/Deployment/fine_parent_integration_r1584_20261106/D125-receiver-rebase-r1594.json')
baseline=J(R/'work/model-instances-receiver-r1714/source/web/scene_delivery_sources.json');assert J(W/'prepared.json')['preparedOnly']
for n,h in baseline['sourcePins'].items():
 if n not in {'src/landscape_editor_ui.js', 'src/cloud_editor_panel.js', 'src/cloud_layer_client.js', 'src/scene_model_overlay.js', 'src/viewer.js', 'src/landscape_editor.js'}:assert sha(web/n)==h
assert (web/'tests/model_source_visibility.test.mjs').is_file()
D.mkdir();manifest=web/'scene_delivery_sources.json';before=manifest.read_bytes();m=J(manifest);assert 'scene_delivery_sources.json'not in m['sourcePins']and len(m['mainInputs'])==167
for n in list(m['sourcePins']):m['sourcePins'][n]=sha(web/n)
for n in ['src/original_scene_source_session.js','tests/original_scene_source_session.test.mjs','tests/model_source_visibility.test.mjs','tests/model_source_coverage.test.mjs','src/scene_identity_retirement.js','tests/scene_identity_retirement.test.mjs','tests/original_scene_configuration.test.mjs','src/original_scene_asset_loader.js','tests/original_scene_asset_loader.test.mjs','tests/original_asset_encoding.test.mjs','src/scene_model_resources.js','tests/scene_model_resources.test.mjs','tests/scene_instances.test.mjs','src/scene_file_contract.js','src/scene_file_library_ui.js','tests/scene_file_client.test.mjs']:m['sourcePins'][n]=sha(web/n)
for n in list(m['mainInputs']):m['mainInputs'][n]=sha(web/n)
m['mainInputs']['src/original_scene_source_session.js']=sha(web/'src/original_scene_source_session.js');m['mainInputs']['src/scene_identity_retirement.js']=sha(web/'src/scene_identity_retirement.js');m['mainInputs']['src/original_scene_asset_loader.js']=sha(web/'src/original_scene_asset_loader.js');m['mainInputs']['src/scene_model_resources.js']=sha(web/'src/scene_model_resources.js');m['mainInputs']['src/scene_file_contract.js']=sha(web/'src/scene_file_contract.js');m['mainInputs']['src/scene_file_library_ui.js']=sha(web/'src/scene_file_library_ui.js');m['pinKind']='candidate';m['deliveryManifestSHA256']=hashlib.sha256(enc({'parentD125Archive':received['sourceArchiveSHA256'],'sourcePins':m['sourcePins'],'mainInputs':m['mainInputs']})).hexdigest()
manifest.write_bytes(enc(m));(D/'upstream-build-manifest-before.json').write_bytes(before)
dependency=A/'web/node_modules/esbuild';binary=dependency/'node_modules/@esbuild/win32-x64/esbuild.exe';assert binary.is_file()and J(dependency/'package.json')['version']=='0.25.10';dependency_pins={str(p):sha(p)for p in [dependency/'package.json',dependency/'lib/main.js',binary]}
link=web/'node_modules/esbuild';assert not link.exists();r=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',"New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(dependency)+"' | Out-Null"],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and link.is_junction()and link.resolve()==dependency.resolve()
assert sha(R/'_g/Application/tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22';jobs=load('fine_scene_jobs1598',R/'_g/Application/tools/original_server_windows_job.py');budget=load('fine_scene_budget1598',A/'tools/bounded_build_job_r671.py');terminals=[]
def execute(name,args,limit=1024**3):
 assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>3*1024**3
 bootstrap="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'FINE_SCENE_BUILD_R1736\\n';raise SystemExit(subprocess.call(sys.argv[1:]))";log=D/(name+'.private.log')
 with log.open('xb')as f:p=subprocess.Popen(['D:/Python/Python313/python.exe','-I','-B','-c',bootstrap,*args],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,ESBUILD_BINARY_PATH=str(binary)),creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,limit);p.stdin.write(b'FINE_SCENE_BUILD_R1736\n');p.stdin.close()
 while p.poll()is None:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameBuildHandleLive':True,'phase':name,'metrics':cap.metrics()}),flush=True)
 while job.active_processes():time.sleep(.05)
 t={'phase':name,'exitCode':p.returncode,'actualJobZero':True,'metrics':cap.metrics(),'forceTerminationUsed':False};job.close();terminals.append(t);(D/'actual-terminals-r1736.json').write_bytes(enc(terminals));assert p.returncode==0,'SOURCE_BUILD_OR_TEST_FAILED_PRESERVE_SAME_ATTEMPT';return log
node='D:/Program Files/nodejs/node.exe'
discovery=D/'discovered-outputs-unqualified-r1736.json';execute('discovery-only',[node,'--max-old-space-size=256',str(V/'discover_fine_scene_r1736.mjs'),str(web),str(discovery)])
discovered=J(discovery);assert discovered['qualifiedBuild']is False and len(discovered['mainInputs'])==169
m=J(manifest);m['expectedOutputs']=discovered['outputs'];manifest.write_bytes(enc(m));(D/'fixed-build-manifest-r1736.json').write_bytes(manifest.read_bytes())
out=W/'delivery-fine-auth-r1736';execute('canonical-pinned-rebuild',[node,'--max-old-space-size=256',str(web/'build_scene_delivery.mjs'),'--outdir',str(out)])
receipt=J(out/'rebuild-receipt.json');assert receipt['passed']and receipt['allFiveOutputsMatchPinnedSources']and receipt['mainInputs']==169
for n,pin in m['expectedOutputs'].items():assert sha(out/n)==pin['sha256']and(out/n).stat().st_size==pin['bytes']
tests=sorted((web/'tests').glob('*.test.mjs'));assert len(tests)>50
log=execute('all-scene-contracts',[node,'--max-old-space-size=256','--test','--test-concurrency=2','--test-reporter=tap',*[str(p)for p in tests]],2*1024**3)
text=log.read_text('utf8');import re
counts={k:int(re.search(r'^# '+k+r' ([0-9]+)$',text,re.M)[1])for k in ['tests','pass','fail','cancelled','skipped']};assert counts['fail']==counts['cancelled']==counts['skipped']==0 and counts['tests']==counts['pass']and counts['tests']>=725
for n,pin in dependency_pins.items():assert sha(Path(n))==pin
for n,h in m['sourcePins'].items():assert sha(web/n)==h
proof={'passed':True,'parentD125ArchiveSHA256':received['sourceArchiveSHA256'],'actualMainInputs':169,'sourceInputs':len(m['sourcePins']),'fiveOutputs':m['expectedOutputs'],'nodeTests':counts,'testFiles':len(tests),'allActualJobsZero':True,'sharedDependenciesBytesUnchanged':True,'modelOrGISCopied':False,'actualOriginalSDKBrowserAccepted':False,'publicUpdated':False};(D/'qualified-build-r1736.json').write_bytes(enc(proof));print(json.dumps(proof))
