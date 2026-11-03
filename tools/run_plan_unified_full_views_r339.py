from pathlib import Path
import hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
scope=json.loads((D/'full-preflight-sources-r339.json').read_bytes());results=[]
assert not(D/'full-preflight-driver-r339.json').exists()
for row in scope['sources']:
    source=V/row['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
    print('OWN_COMPLETE_PROGRAM_PREFLIGHT_START_'+row['variant'],flush=True)
    log=D/row['variant'].lower()/'full-preflight-driver-r339.log';assert not log.exists()
    with log.open('xb')as output:
        done=subprocess.run([sys.executable,str(source)],stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    if done.returncode:
        (D/'full-preflight-driver-failure-r339.json').write_text(json.dumps({'variant':row['variant'],'exitCode':done.returncode,'sourceSHA256':row['sha256'],'servicesStarted':False},indent=2)+'\n',encoding='utf-8')
        raise RuntimeError('OWN_COMPLETE_PROGRAM_PREFLIGHT_FAILED:'+row['variant'])
    proof=json.loads((D/row['variant'].lower()/'full-program-preflight.json').read_bytes())
    assert proof['allPassed']and proof['candidatePlanClassContractAndTransportPassed']
    results.append({'variant':row['variant'],'passed':True,'programFiles':proof['fullProgramFilesVerified'],
      'oldControls':proof['oldDeclaredControls'],'newControls':proof['newDeclaredControls'],
      'writes':proof['candidateInstallPaths'],'removals':proof['obsoleteEmergencyFrontendRemovals'],
      'allChangePaths':proof['allChangePaths'],'sourceProgramsUnchanged':proof['sourceProgramsUnchanged']})
    print(json.dumps(results[-1]),flush=True)
(D/'full-preflight-driver-r339.json').write_text(json.dumps({'passed':True,'variants':results,'servicesStarted':False,
 'actualServerPreflightOrIISOrPublicDeploymentPassed':False},indent=2)+'\n',encoding='utf-8')
print('OWN_BOTH_EXACT_BASES_COMPLETE_PROGRAM_PREFLIGHT_PASSED',flush=True)
