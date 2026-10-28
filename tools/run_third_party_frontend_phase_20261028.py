from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,zipfile
W=Path(__file__).resolve().parent;A=Path('D:/Project/Zhumadian/Application');R=A.parent
sys.path.insert(0,str(W));sys.path.insert(1,str(A/'tools'))
from original_third_party_frontend_compat import transform,RELATIVE,PIN
from run_original_inventory_ownership_probe import state
from original_server_windows_job import OwnedWindowsJob
ROOT=R/'work/third_party_frontend_20261028_r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,value):
    assert not p.exists();p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(tag,cmd,seconds,extra=None):
    assert not (ROOT/(tag+'-started.json')).exists();env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','NODE_OPTIONS','PYTHONPATH')};env.update(TMP=str(ROOT/'tmp'),TEMP=str(ROOT/'tmp'),PYTHONPATH=str(W)+';'+str(A/'tools'));env.update(extra or {})
    p=subprocess.Popen(list(map(str,cmd)),cwd=W,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    dump(ROOT/(tag+'-started.json'),{'PID':p.pid,'maximumSeconds':seconds});job=None;timed=False
    try:
        job=OwnedWindowsJob(p)
        try:out,err=p.communicate(timeout=seconds)
        except subprocess.TimeoutExpired:timed=True;job.close();out,err=p.communicate(timeout=10)
    finally:
        if job:job.close()
        if p.poll() is None:p.kill();p.wait(timeout=5)
    (ROOT/(tag+'.stdout.log')).write_bytes(out);(ROOT/(tag+'.stderr.log')).write_bytes(err);dump(ROOT/(tag+'-process.json'),{'exitCode':p.returncode,'timedOut':timed})
    if timed or p.returncode:raise RuntimeError(tag+': '+err.decode('utf-8',errors='replace')[-2200:])
def main():
    assert not ROOT.exists();oldstate=state();assert oldstate['controllerPID']==35292 and Path(oldstate['run']).name=='j41'
    with zipfile.ZipFile(R/'Document/Deployment/original_inspection_filter_20261027/execution-evidence.private.zip') as z:config=json.loads(z.read('executed-sources/inspection-filter-build-config.json'))
    project=Path(config['project']);reference=Path(config['reference']);node=Path(config['node']);assert project.is_dir() and reference.is_dir() and node.is_file()
    manifest=Path(config['manifest']);assert sha(manifest)=='8d3c51186ceede7547cf7dbb62bab1433e253793596be0c6df103e26efcede98' and sha(node)=='91ec09dda8f20556f366110859f106ab189d45f8f6a2bd092e6785174ad4a0fa'
    origin=reference/RELATIVE;raw=origin.read_bytes();assert sha(origin)==PIN and (project/RELATIVE).read_bytes()==raw
    ROOT.mkdir();(ROOT/'tmp').mkdir();candidate=ROOT/'FormDialog.candidate.vue';candidate.write_bytes(transform(raw)[0])
    files=[W/'original_third_party_frontend_compat.py',W/'test_original_third_party_frontend_compat.py',W/'check_original_third_party_frontend.mjs',W/'build_original_business_result_frontend.py',Path(__file__)]
    dump(ROOT/'prepared.private.json',{'at':datetime.datetime.now().astimezone().isoformat(),'sourcePins':{str(p):sha(p) for p in files},'referenceFileSHA256':sha(origin),'typescriptSHA256':sha(project/'node_modules/typescript/lib/typescript.js'),'nodeSHA256':sha(node),'manifestSHA256':sha(manifest),'controllerPID':oldstate['controllerPID'],'currentRuntimeUnchanged':True,'runtimeInstallationAllowed':False})
    python=Path('D:/Zqa20261025/Application/runtime/python/python.exe')
    run('adapter-tests',[python,'-B','-m','unittest','test_original_third_party_frontend_compat'],35,{'ORIGINAL_THIRD_PARTY_REFERENCE':str(reference)})
    run('component-tests',[node,W/'check_original_third_party_frontend.mjs',origin,candidate,project,ROOT/'component-result.json'],30)
    config['output']=str(ROOT/'pc-candidate');dump(ROOT/'build-config.private.json',config)
    run('full-pc-build',[python,'-B',W/'build_original_business_result_frontend.py','--config',ROOT/'build-config.private.json','--business-result','--inspection-filter','--third-party-credentials'],300)
    receipt=json.loads((ROOT/'pc-candidate/receipt.json').read_text('utf-8'));assert receipt['exitCode']==0 and receipt['sourceFilesUnchanged'] and receipt['originalReferenceUnchanged'] and receipt['thirdPartyCredentialsCompatibility']['sourceFileRestored']
    assert receipt['businessResultCompatibility'] and receipt['inspectionPointNameCompatibility'] and receipt['approvalRetryCompatibility'] and receipt['workflowRequestCompatibility']
    assert state()['controllerPID']==oldstate['controllerPID'] and sha(origin)==PIN and (project/RELATIVE).read_bytes()==raw
    result={'at':datetime.datetime.now().astimezone().isoformat(),'adapterChecks':9,'componentControlCases':json.loads((ROOT/'component-result.json').read_text('utf-8'))['caseCount'],'fullOriginalFrontendBuilt':True,'referenceAndBuildCopyRestored':True,'allPriorDeploymentAndBusinessAdaptersRetained':True,'outputBytes':receipt['bytes'],'outputFiles':receipt['fileCount'],'runtimeInstalledOrRestarted':False,'realBrowserLengthValidationPassed':False,'publicDeployed':False,'fullCloneReady':False}
    dump(ROOT/'result.json',result);print(json.dumps(result))
if __name__=='__main__':main()
