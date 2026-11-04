"""Restore only R885's exact code/pointer after its bound run has fully exited."""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';T=R/'Application/tools';V=Path(__file__).resolve().parent;Z=R/'work/ep885'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 assert not(Z/'verified-recovery-r886.json').exists()
 handles=json.loads((Z/'controller-handles.private.json').read_bytes());assert handles['pids']==[47704]
 helper=load('exact_terminal_r886',T/'owned_run_terminal_r709.py')
 run=G/'UserData/OriginalServer/runs/j182';ready=json.loads((run/'ready.json').read_bytes())
 receiptPath,receipt=helper.receipt_for_run(G,run,47704,ready)
 assert receipt['allOwnedChildrenExited'] and not receipt.get('forcedJobClosureComponents') and not receipt.get('jobAssignmentFailureComponents')
 assert receipt['exitCodesBeforeJobClose']=={'store':0,'mysql':0,'redis':0,'platform':0,'business':1,'gateway':0}
 assert not receipt['normalOwnedShutdown'] and receipt['mysqlAdminStopExitCode']==0
 pids=[47704,*ready['children'].values()];assert all(type(n)is int and 0<n<2**32 for n in pids)
 last=[0.0,None]; observations=[]
 def stopped(fresh=False):
  if not fresh and last[1] is not None and time.monotonic()-last[0]<2:return last[1]
  ids=' OR '.join('ProcessId='+str(n)for n in sorted(set(pids)))
  query="$live=(Get-CimInstance Win32_Process -Filter '"+ids+"'|Measure-Object).Count; $refs=(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count; [pscustomobject]@{oldPIDsStillLive=$live;ownedGReferences=$refs}|ConvertTo-Json -Compress"
  p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
  assert p.returncode==0,'ACTUAL_TERMINAL_OBSERVATION_REQUIRED_NO_RESTORE'
  value=json.loads(p.stdout.decode('utf-8-sig'));observations.append(value);last[:]=[time.monotonic(),value['oldPIDsStillLive']==value['ownedGReferences']==0]
  return last[1]
 assert stopped(True),'LIVE_OR_REUSED_PID_NO_RESTORE'
 planPath=R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json'
 assert sha(planPath)=='204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09'
 plan=json.loads(planPath.read_bytes());rows=dict(plan['mutations'])
 for n,pin in plan['retiredKnownFrontendPaths'].items():assert n not in rows;rows[n]={'before':pin,'after':None}
 for n,pin in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():assert n not in rows;rows[n]={'before':pin,'after':None}
 sys.path.insert(0,str(T));from owned_candidate_code_transaction_r543 import CodeTransaction,pin
 from owned_run_pointer_r717 import OwnedRunPointerSnapshot
 tx=CodeTransaction(G,Z/'code-transaction',rows,processes_exited=stopped)
 assert tx.state()['phase']=='applied' and sha(G/'release-manifest.json')==plan['candidateReleaseSHA256']
 assert pin(G/'private/server-configuration.json')==plan['configBefore'] and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
 snap=json.loads((Z/'pointer-snapshot/snapshot.private.json').read_bytes());assert snap['phase']=='captured'
 pointer=G/'UserData/OriginalServer/current-run.json';current=pin(pointer)
 actual=json.loads(pointer.read_bytes())
 for key in ['schema','controllerPID','run','ownerId','releaseId','startedAt','children']:assert actual[key]==ready[key]
 native=run/'b/hs_err_pid20916.log';head=native.read_bytes()[:16384].decode('utf8','replace')
 assert 'There is insufficient memory for the Java Runtime Environment to continue.' in head
 allocation=re.search(r'failed to allocate ([0-9,]+) bytes',head)
 tx.restore();assert all(pin(G/n)==row['before']for n,row in rows.items())
 assert stopped(True) and pin(pointer)==current
 pointerTx=OwnedRunPointerSnapshot(G,Z/'pointer-snapshot',snap['before'],processes_exited=stopped)
 pointerTx.restore(expected_current=current,owned_ready_row=ready)
 assert stopped(True) and sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256'] and pin(pointer)==snap['before']
 proof={'schema':'xnby.owned-event-picker.recovery.v1','passed':True,'failedRunOwnerAndReadyReceiptMatched':True,
  'allOriginalPIDsAndOwnedReferencesAbsent':True,'terminalObservations':observations,'observationCacheMaximumSeconds':2,
  'originalExitCodes':receipt['exitCodesBeforeJobClose'],'normalSixComponentExitClaimed':False,
  'businessNativeAllocationFailureObserved':True,'failedAllocationBytes':int(allocation.group(1).replace(',',''))if allocation else None,
  'hsErrorSHA256':sha(native),'receiptSHA256':sha(receiptPath),'codeRestored':True,'originalCurrentPointerRestored':True,
  'privateConfigurationAndInstallationIdentityUnchanged':True,'databaseDataRestoredReplacedOrWritten':False,
  'servicesRestarted':False,'forceTerminationUsed':False,'publicOrDesktopTouched':False,'fullCloneReady':False}
 (Z/'verified-recovery-r886.json').write_bytes(enc(proof));print(json.dumps(proof,ensure_ascii=False))
if __name__=='__main__':main()
