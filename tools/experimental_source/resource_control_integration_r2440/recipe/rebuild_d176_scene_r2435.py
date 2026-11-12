"""Rebuild a fixed 319-file D176 source closure without touching its producers."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
S=A/'tools/experimental_source/resource_control_merge_r2433';W=R/'work/resource-scene-control-r2435'
INDEX='74a891864b22f2223b2efca0b9cb40bd44a7557b2555bd33fe6aeb90202e645a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def dump(p,x):
 with p.open('x',encoding='utf8')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def checked():
 assert sha(S/'scene-source-index.json')==INDEX
 value=j(S/'scene-source-index.json');assert len(value['files'])==319
 shared={'../shared/'+n for n in('business_reference_type_cases.json','business_source_snapshot_cases.json','cloud_feature_merge_cases.json','native_http_sources_cases.json','project_account_identity_cases.json','spatial_types.json')}
 for n,row in value['files'].items():
  assert not Path(n).is_absolute()and '\\'not in n and('..'not in Path(n).parts or n in shared)
  source=(A/row['source']).resolve();assert source.is_relative_to(A/'tools/experimental_source/resource_no_gis_workspace_20261112')or source.is_relative_to(A/'tools/experimental_source/resource_gis_browser_20261112')
  assert source.is_file()and not source.is_symlink()and not source.lstat().st_file_attributes&1024
  assert source.stat().st_size==row['bytes']and sha(source)==row['sha256']
 return value
def worker():
 assert not W.exists();value=checked();total=sum(row['bytes']for row in value['files'].values());assert total==5595971
 W.mkdir();dump(W/'storage-plan.json',{'sourceFiles':319,'sourceBytes':total,'GISCopied':False,'sharedDependenciesWritten':False})
 source=W/'source/web'
 for n,row in value['files'].items():
  dest=source/n;assert dest.resolve().is_relative_to((W/'source').resolve());dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb')as f:f.write((A/row['source']).read_bytes())
 node=Path('D:/Program Files/nodejs/node.exe');assert sha(node)=='91ec09dda8f20556f366110859f106ab189d45f8f6a2bd092e6785174ad4a0fa'
 env={k:v for k,v in os.environ.items()if k.upper()not in('NODE_OPTIONS','NODE_PATH','BROWSER')};env['NODE_PATH']=str(A/'web/node_modules');env['BROWSER']='none'
 p=subprocess.Popen([str(node),'--max-old-space-size=512',str(source/'build_scene_delivery.mjs'),'--outdir',str(W/'products')],cwd=source,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
 p.wait();assert p.returncode==0,'ACTUAL_SCENE_BUILD_FAILED_KEEP_ATTEMPT'
 receipt=j(W/'products/rebuild-receipt.json');assert receipt['passed']and receipt['allFiveOutputsMatchPinnedSources']and not receipt['allFiveOutputsByteIdenticalToDeliveredPackage']
 for n,row in value['expectedOutputs'].items():
  p=W/'products'/n;assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 assert value==checked()
 assert all(sha(source/n)==row['sha256']for n,row in value['files'].items())
 result={'passed':True,'sourceFiles':319,'sourceBytes':total,'sourceIndexSHA256':INDEX,'sourceManifestSHA256':value['manifestSHA256'],
  'allFiveOutputsMatchFixedD176Pins':True,'outputs':value['expectedOutputs'],'sourceInputs':receipt['sourceInputs'],'mainInputs':receipt['mainInputs'],
  'sharedSourcesVendorAndCopiedSourceClosureUnchanged':True,'GISOrRuntimeCopied':False,'publicR51Or252Changed':False,'productionLoginOrRenderingAccepted':False}
 dump(W/'verification.json',result);print(json.dumps({k:v for k,v in result.items()if k!='outputs'}),flush=True)
def main():
 if sys.argv[1:]==['worker']:
  assert sys.stdin.buffer.readline()==b'OWN_D176_SCENE_R2435\n';worker();return
 assert sys.argv[1:]==[]and not W.exists()
 jp=R/'_g/Application/tools/original_server_windows_job.py';assert sha(jp)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 jobs=load('scene2435jobs',jp);bounds=load('scene2435bounds',A/'tools/bounded_build_job_r671.py');memory=bounds.memory_snapshot();assert memory['availablePhysicalBytes']>4*1024**3 and memory['availableCommitBytes']>3*1024**3
 with(V/'d176-scene-r2435.private.log').open('xb')as f:p=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),'worker'],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 try:job=jobs.OwnedWindowsJob(p);budget=bounds.BoundedBuildJob(job,1024**3)
 except BaseException:p.stdin.close();p.wait();raise
 p.stdin.write(b'OWN_D176_SCENE_R2435\n');p.stdin.flush();p.stdin.close();print(json.dumps({'originalPID':p.pid,'jobAssignedBeforeGate':True}),flush=True)
 while p.poll()is None:
  try:p.wait(10)
  except subprocess.TimeoutExpired:print(json.dumps({'sameHandleLive':True,'metrics':budget.metrics()}),flush=True)
 while job.active_processes():time.sleep(.05)
 result={'rootExitCode':p.returncode,'actualJobBeforeClose':job.active_processes(),'metrics':budget.metrics(),'forceTerminationUsed':False,'sourceSHA256':sha(Path(__file__))};job.close()
 dump(V/'d176-scene-r2435-outer-terminal.json',result);print(json.dumps(result),flush=True);assert p.returncode==0
if __name__=='__main__':main()
