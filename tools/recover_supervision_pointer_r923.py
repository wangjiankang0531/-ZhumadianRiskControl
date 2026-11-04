"""Restore only the captured owned pointer after the R921 process observation timeout.

No process launch/retry, no data/code overwrite and no guessed pointer state.
"""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/supervision_current_full_r920_20261104';Z=R/'work/sv921'
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
plan=J(D/'full-source-and-restore-plan.private.json');assert sha(D/'full-source-and-restore-plan.private.json')=='99f0b07ce6e6902d66ac9e9f74b5b452b7ad8fcb433b53495acd32e514785f61'
assert not(D/'conditional-pointer-recovery-r923.json').exists()
terminal=J(Z/'controller-terminals.json');assert len(terminal)==1
t=terminal[0];assert t['controllerExitCode']==0 and t['actualJobDescendantsZero']and not t['forceTerminationUsed']and set(t['exitCodes'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in t['exitCodes'].values())
assert J(Z/'code-transaction/journal.json')['phase']=='restored'
sys.path.insert(0,str(A/'tools'));code=load('r923_code',A/'tools/owned_candidate_code_transaction_r543.py');ptr=load('r923_pointer',A/'tools/owned_run_pointer_r717.py');receipt=load('r923_receipt',A/'tools/owned_run_terminal_r709.py')
rows={**plan['mutations'],**{n:{'before':p,'after':None}for n,p in plan['retiredKnownFrontendPaths'].items()},**{n:{'before':p,'after':None}for n,p in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items()}}
assert all(code.pin(G/n)==p['before']for n,p in rows.items())and sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
assert code.pin(G/'private/server-configuration.json')==plan['configBefore']and code.pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
snapshot=J(Z/'pointer-snapshot/snapshot.private.json');assert snapshot['phase']=='captured'
pointer=G/'UserData/OriginalServer/current-run.json';observed=code.pin(pointer);row=J(pointer)
assert row['controllerPID']==43964 and row['ready']is True and Path(row['run']).absolute()==G/'UserData/OriginalServer/runs/j189'
assert J(Z/'controller-handles.private.json')['pids']==[43964]and J(Z/'controller-handles.private.json')['candidateReleaseSHA256']==plan['candidateReleaseSHA256']
_,r=receipt.receipt_for_run(G,Path(row['run']),43964,row);assert r['normalOwnedShutdown']and r['allOwnedChildrenExited']and all(v==0 for v in r['exitCodesBeforeJobClose'].values())
events=[json.loads(line)for line in(Z/'normal-restart/controller.private.log').read_text('utf8').splitlines()if line.startswith('{')]
assert any(e.get('ready')is True and e.get('run')==row['run']and e.get('releaseId')==row['releaseId']for e in events)
assert any(e.get('stopped')is True and e.get('run')==row['run']and e.get('allOwnedChildrenExited')is True for e in events)
def exited():
 query="@(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') }).Count"
 p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0;return int(p.stdout.decode('utf-8-sig').strip())==0
assert exited(),'LIVE_G_REFERENCE_REFUSE_RECOVERY'
transaction=ptr.OwnedRunPointerSnapshot(G,Z/'pointer-snapshot',snapshot['before'],processes_exited=exited)
transaction.restore(expected_current=observed,owned_ready_row=row)
assert code.pin(pointer)==snapshot['before']and all(code.pin(G/n)==p['before']for n,p in rows.items())and exited()
proof={'schema':'xnby.current-supervision.r921-conditional-recovery.v1','passedAsScopedRecovery':True,'originalTestPassed':False,
 'failure':'controller-ownership-query-TimeoutExpired-then-missing-observed-ready-for-pointer-restore','allSixComponentsStartedAndNormallyExited':True,
 'actualControllerExitCode':0,'actualJobDescendantsZero':True,'controllerPeakJobBytes':t['jobMemoryBudget']['reportedPeakJobMemoryBytes'],
 'originalCodeAndPrivateConfigurationAndInstallationIdentityRestored':True,'durableOriginalPointerBeforeImageRestored':True,
 'currentRunReceiptReadyAndControllerStdoutBoundBeforeRestore':True,'noActiveGProcessReferencesBeforeOrAfter':True,
 'processesRestartedOrBusinessDataWrittenOrDesktopPublicTouched':False,'originalUIAndPDFChecksAccepted':False,'fullCloneReady':False}
(D/'conditional-pointer-recovery-r923.json').write_bytes(enc(proof));print(json.dumps(proof))
