from pathlib import Path
import ctypes,hashlib,json,os,subprocess,sys,time
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';W=R/'work/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112/build02';web=W/'source/web';sys.path.insert(0,str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools'));from osgb_stdio_worker import OwnedWindowsJob
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();env=dict(os.environ,NODE_PATH=str(A/'web/node_modules'));rows=[];node='D:/Program Files/nodejs/node.exe'
class Memory(ctypes.Structure):_fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),('total',ctypes.c_ulonglong),('available',ctypes.c_ulonglong),('commitTotal',ctypes.c_ulonglong),('commitAvailable',ctypes.c_ulonglong),('virtualTotal',ctypes.c_ulonglong),('virtualAvailable',ctypes.c_ulonglong),('extended',ctypes.c_ulonglong)]
def run(label,args):
 memory=Memory();memory.length=ctypes.sizeof(memory);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory));assert min(memory.available,memory.commitAvailable)>3*1024**3,'Need actual3GiB before small frontend build'
 gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D176\\n';raise SystemExit(subprocess.call(sys.argv[1:]))"
 with(D/(label+'.log')).open('xb')as log:
  child=subprocess.Popen([sys.executable,'-I','-B','-c',gate,*args],cwd=web,env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(child);child.stdin.write(b'D176\n');child.stdin.close();print(json.dumps({'phase':label,'originalPID':child.pid}),flush=True)
  while child.poll()is None:
   try:child.wait(10)
   except subprocess.TimeoutExpired:print(json.dumps({'phase':label,'sameOriginalHandleLive':True}),flush=True)
  while job.active_processes():time.sleep(.05)
  job.close();rows.append({'phase':label,'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes});(D/'build-original-roots.json').write_text(json.dumps(rows,indent=2)+'\n');assert child.returncode==0 and job.final_active_processes==0,label+' inspect preserved original log'
m=json.loads((web/'scene_delivery_sources.json').read_text(encoding='utf-8'));delta=json.loads((D.parent/'prepared-inputs.json').read_text());changed={v['path']for v in delta['changedWebInputs']}
for name,pin in m['sourcePins'].items():
 if name not in changed:assert sha(web/name)==pin,name
for name in changed:m['sourcePins'][name]=sha(web/name)
assert sha(W/'fixture-parent03.js')==json.loads((D.parent/'actual-vue-fixture-build03.json').read_text())['parentBundleSHA256']
run('new-full-scene-discovery',[node,'--max-old-space-size=256',str(P/'recipe/discover.mjs')])
discovered=json.loads((W/'discovered.json').read_text());assert set(discovered['mainInputs'])==set(m['mainInputs']);meta=web/'layer_editor_delivery_manifest.json';value=json.loads(meta.read_text(encoding='utf-8'));value.update(state='private-D176-compact-GIS-controls-not-published',sourceBase='a1d2e68f4ee3e39e3e72e7107c4de105743d5a33',outputs=discovered['products'],mainInputs=discovered['mainInputs']);meta.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');m['sourcePins']['layer_editor_delivery_manifest.json']=sha(meta);m.update(pinKind='candidate',expectedOutputs=discovered['products'],mainInputs=discovered['mainInputs'],deliveryManifestSHA256=sha(meta));(web/'scene_delivery_sources.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
run('canonical-full-five-products',[node,'--max-old-space-size=256',str(web/'build_scene_delivery.mjs'),'--outdir',str(W/'delivery02')])
for name in ['source-gain-worker.js','index.html','source-config.html','scene-help.html']:assert sha(W/'delivery02'/name)==sha(R/'work/resource_no_gis_workspace_20261112/delivery03'/name)
result={'passed':True,'fullFiveProductsBuilt':True,'sourcePinCount':len(m['sourcePins']),'mainInputs':len(m['mainInputs']),'onlyD175ThreeJSChangedBeforeDerivedMetadata':sorted(changed),'bothOriginalVueComponentsCompiled':True,'originalFourNonViewerProductsByteIdentical':True,'products':discovered['products'],'originalRootsAndJobsZero':True,'actualBrowserStillPending':True,'publicAnd252Changed':False};(D/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='products'}),flush=True)
