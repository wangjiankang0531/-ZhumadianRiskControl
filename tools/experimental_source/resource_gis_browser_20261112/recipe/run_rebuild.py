from pathlib import Path
import json,os,subprocess,sys,time,hashlib
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_browser_20261112';W=R/'work/resource_gis_browser_20261112';D=R/'Document/Deployment/resource_gis_browser_20261112';sys.path.insert(0,str(A/'tools/experimental_source/production_fine_provider_20261106/candidate/tools'));from osgb_stdio_worker import OwnedWindowsJob
# Prepare uses no executable or resource copies; only exact source inputs.
subprocess.run([sys.executable,'-I','-B',str(P/'recipe/prepare_source.py'),str(W/'rebuild-source')],check=True)
gate="import sys,subprocess;assert sys.stdin.buffer.readline(100)==b'D176\\n';raise SystemExit(subprocess.call(sys.argv[1:]))";env=dict(os.environ,NODE_PATH=str(A/'web/node_modules'))
with(D/'clean-rebuild.log').open('xb')as log:
 child=subprocess.Popen([sys.executable,'-I','-B','-c',gate,'D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(W/'rebuild-source/web/build_scene_delivery.mjs'),'--outdir',str(W/'rebuild-delivery')],env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(child);child.stdin.write(b'D176\n');child.stdin.close();child.wait()
 while job.active_processes():time.sleep(.05)
 job.close();assert child.returncode==0 and job.final_active_processes==0
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();products={name:sha(W/'delivery02'/name)for name in ['viewer.js','source-gain-worker.js','index.html','source-config.html','scene-help.html']}
for name,pin in products.items():assert sha(W/'rebuild-delivery'/name)==pin
result={'passed':True,'newSourceReconstructionAndIndependentByteExactFullFiveProductRebuild':True,'sourcePins':312,'mainInputs':190,'rootExitCode':child.returncode,'originalJobBeforeClose':job.final_active_processes,'productsSHA256':products,'allOriginalRuntimeAndGISReadOnlyNotCopied':True};(D/'clean-rebuild.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
