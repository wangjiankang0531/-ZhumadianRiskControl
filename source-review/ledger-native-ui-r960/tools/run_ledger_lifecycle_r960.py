"""Prepare original models/callbacks using one actual owned full-candidate lifecycle.

--run requires six GiB physical and commit headroom before allocation.
An inherited three-GiB controller Job and one-GiB probe Job bound private commit.
The original six-GiB entry and candidate bytes remain unchanged. The new complete frontend is checked through normal synthetic login, read-only business lists and the existing completed task detail. Only this new owned ledger fixture is created and supervised through the normal API/UI; metadata is prepared in the exact G namespace. No public business write, account/role change, schema change, task approval or callback rebinding is performed.
No public service, desktop, original data clone or forced termination is used.
"""
from pathlib import Path
import argparse,ctypes,hashlib,importlib.util,json,os,secrets,shutil,socket,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent;T=A/'tools'
D=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104';O=R/'work/original-manager-full-lifecycle-r609';W=O/'task-ui-r806';P=O/'ledger-ui-r941';Z=R/'work/ledgerfull-r960'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
budget=load('bounded_integrated_budget_r688',T/'bounded_build_job_r671.py')
REQUIRED=7*1024**3
CONTROLLER_BUDGET=4*1024**3
GATE=b'XNBY_OWN_BOUNDED_CONTROLLER_R688\n'
GATE_CODE="import sys,runpy; expected=b'XNBY_OWN_BOUNDED_CONTROLLER_R688\\n'; got=sys.stdin.buffer.readline(128); assert got==expected,'UNOPENED_OWN_CONTROLLER_GATE'; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
def available():return budget.memory_snapshot()['availablePhysicalBytes']
def resources():
 snap=budget.memory_snapshot();return snap['availablePhysicalBytes']>REQUIRED and snap['availableCommitBytes']>REQUIRED
def referenced():
 query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
 p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0;return int(p.stdout.decode('utf-8-sig').strip())

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
assert J(R/'work/sv931/verified-exact-supervision-r931.json')['passed']
latest=J(R/'work/sv925/verified-current-supervision-r925.json');assert latest['codeRestored']and latest['privateConfigurationUnchanged']and latest['originalCurrentPointerRestored']
ready_observer=load('ready_observer_r924',V/'owned_ready_observation_r924.py')
assert sha(D/'full-source-and-restore-plan.private.json')=='a44203be5562ea30a565752e9b4ec2081b2f5b9d577f7455bc7497a348a9fc7d','EXACT_INTEGRATED_PLAN_PIN_REQUIRED'
plan=J(D/'full-source-and-restore-plan.private.json')
assert plan['schema']=='xnby.exact-unified-supervision.owned-full-candidate.plan.v1'and plan['target']==str(G)and plan['onlyExistingOwnedSyntheticFixture']
assert plan['minimumAvailableMemoryBeforeApplyOrStart']==6*1024**3
assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly'] and not(G.parent/'user-manual-protected.json').exists()
assert W.is_dir()and P.is_dir()and (P/'own-ledger-ui.marker').read_bytes()==b'own-ledger-ui-r941\n'and not(P/'resume-r960').exists()and not Z.exists(),'EXACT_EXISTING_METADATA_NEW_RESUME_REQUIRED'
prior=J(R/'work/hf912/verified-home-transfer-r912.json')
assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
assert 'phase=restored'in(W/'resume-r810/manager-directory.private.properties').read_text('ascii').splitlines()
for source,pin in J(V/'ledger-source-pins-r960.json')['files'].items():assert sha(Path(source))==pin,'COMPONENT_BOOTSTRAP_SOURCE_DRIFT'
memory=available()
if not args.run or not resources():
 proof={'started':False,'reason':'EXPLICIT_RUN_REQUIRED'if not args.run else'UNCHANGED_SIX_GIB_PHYSICAL_AND_COMMIT_REQUIRED',
 'availableMemoryBytes':memory,'requiredMemoryBytes':REQUIRED,'controllerJobLimitBytes':CONTROLLER_BUDGET,'probeJobLimitBytes':1024**3,'startupReserveBytes':1024**3,'attemptAllocated':False,'GCodeChanged':False,'servicesStarted':False,'actualLifecycleAccepted':False}
 (V/'r45-backend-not-started-r850.json').write_bytes(enc(proof));print(json.dumps(proof));raise SystemExit(0 if not args.run else 2)
assert shutil.disk_usage(R).free>2*1024**3+256*1024**2,'CODE_BACKUP_AND_TWO_RUNS_256MIB_ESTIMATE_PLUS_2GIB_RESERVE'
assert referenced()==0,'OWN_G_ALREADY_ACTIVE_NO_DUPLICATE_START'
code=load('owned_code_r545',T/'owned_candidate_code_transaction_r543.py')
test=J(R/'Document/Deployment/supervision_full_application_r538_20261104/verified-code-transactions-r544.json');assert test['passed']and test['sourceSHA256']==sha(T/'owned_candidate_code_transaction_r543.py')
health=load('owned_full_health_r545',V/'home_transfer_health_r906.py');_,runtime,helper=health.profile()
jobSource=G/'tools/original_server_windows_job.py';assert sha(jobSource)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('owned_jobs_r545',jobSource)
assert code.pin(G/'private/server-configuration.json')==plan['configBefore']and code.pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
for n,row in plan['sources'].items():assert code.pin(Path(row['source']))=={'bytes':row['bytes'],'sha256':row['sha256']},'CANDIDATE_SOURCE_DRIFT:'+n
rows=dict(plan['mutations'])
for n,p in plan['retiredKnownFrontendPaths'].items():assert n not in rows;rows[n]={'before':p,'after':None}
for n,p in plan['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():assert n not in rows;rows[n]={'before':p,'after':None}
for n,row in rows.items():assert code.pin(G/n)==row['before'],'OWN_BASE_CODE_DRIFT:'+n
backupAtomicLengths=[len(str((Z/'code-transaction/before'/n).with_name('.'+Path(n).name+'.own-'+'0'*32+'.tmp')))for n,r in rows.items()if r['before']is not None]
needMax=max(backupAtomicLengths);assert needMax<260,'ALL_ACTUAL_BACKUP_ATOMIC_PATHS_MUST_FIT_BEFORE_ALLOCATION'
# All owned-file runtime paths are checked by the pinned controller. Keep caller
# preimages in this attempt only, never in public evidence or the Git scope.
pointer=G/'UserData/OriginalServer/current-run.json';pointerBefore=code.pin(pointer);pointerBytes=pointer.read_bytes()if pointerBefore else None
terminal_helper=load('manager_exact_terminal_r745',T/'owned_run_terminal_r709.py')
dataPins={p.relative_to(G).as_posix():code.pin(p)for p in [G/'private/server-configuration.json',G/'UserData/OriginalServer/installation.json',G/'UserData/OriginalServer/store-credentials.private.json']}
assert all(p is not None for p in dataPins.values())
business_probe=load('owned_normal_supervision_probe_r600',V/'home_transfer_probe_r906.py')
assert callable(business_probe.children_exited)and callable(business_probe.run_probe),'NORMAL_BUSINESS_PROBE_INTERFACE_REQUIRED'
fixture_nonce=hashlib.sha256(str(P).encode('utf8')).hexdigest()[:32]
assert len(fixture_nonce)==32 and all(c in'0123456789abcdef'for c in fixture_nonce)
(P/'resume-r960').mkdir()

processes=[];phase='preparing';failure=None;codeRestored=False;pointerRestored=False;terminals=[];checks=[];probeChecks=[]
def exited():return all(x['process'].poll()is not None and x['job']is not None and x['job'].active_processes()==0 for x in processes)and business_probe.children_exited()and referenced()==0
tx=code.CodeTransaction(G,Z/'code-transaction',rows,processes_exited=exited)
sys.path.insert(0,str(T))
from owned_run_pointer_r717 import OwnedRunPointerSnapshot
pointerTx=OwnedRunPointerSnapshot(G,Z/'pointer-snapshot',pointerBefore,processes_exited=exited)
expectedConfig=plan['configBefore'];taskRestored=True
with socket.socket()as gateway_reservation:gateway_reservation.bind(('127.0.0.1',0));port=gateway_reservation.getsockname()[1]
assert port not in {18891,18892,8767}
def save(name,value):code.atomic(Z/name,enc(value))
def invariant():
 for name,pin in dataPins.items():
  if name!='private/server-configuration.json':assert code.pin(G/name)==pin,'PRIVATE_INSTALLATION_OR_STORE_IDENTITY_DRIFT_NO_RESTORE'
def configuration_invariant():
 invariant();assert code.pin(G/'private/server-configuration.json')==expectedConfig,'TASK_CONFIGURATION_PHASE_DRIFT_NO_START'

def start(label):
 assert resources(),'RESOURCE_DROPPED_BEFORE_OWN_CONTROLLER_START'
 configuration_invariant();folder=Z/label;folder.mkdir();manifest=plan['candidateReleaseSHA256'];overlay=plan['callbackOverlay']
 assert sha(G/'release-manifest.json')==manifest
 command=[str(G/'runtime/python/python.exe'),'-I','-B','-c',GATE_CODE,str(G/'tools/serve_original_server_release.py'),'--application',str(G),'--release-manifest-sha256',manifest,'--gateway-port',str(port),
          '--callback-overlay',overlay['path'],'--callback-overlay-sha256',overlay['sha256']]
 with(folder/'controller.private.log').open('xb')as out:
  proc=subprocess.Popen(command,cwd=G,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
 record={'process':proc,'job':None,'row':None,'label':label,'receiptChecked':False};processes.append(record)
 save('controller-handles.private.json',{'pids':[p['process'].pid for p in processes],'candidateReleaseSHA256':manifest,'forceTerminationUsed':False})
 try:
  record['job']=jobs.OwnedWindowsJob(proc)
  record['budget']=budget.BoundedBuildJob(record['job'],CONTROLLER_BUDGET)
  record['budget'].metrics()
  proc.stdin.write(GATE);proc.stdin.flush()
 finally:
  proc.stdin.close()
 print(json.dumps({'phase':label,'controllerPID':proc.pid,'onlyOwnedG':True}),flush=True)
 nextProgress=0
 while True:
  if proc.poll()is not None:raise RuntimeError('OWN_CANDIDATE_EXITED_BEFORE_READY')
  record['budget'].metrics()
  if pointer.exists():
   row=J(pointer)
   if row.get('controllerPID')==proc.pid and row.get('ready')is True:
    record['row']=ready_observer.observe_ready(runtime,G,manifest,record,lambda value:save(label+'/observed-ready.private.json',value),gateway_port=port);return record
  if time.monotonic()>=nextProgress:print('OWN_CONTROLLER_HANDLE_STILL_LIVE_WAITING_FOR_READY_NO_RESTART',flush=True);nextProgress=time.monotonic()+15
  time.sleep(.5)

def stop(record):
 proc=record['process'];job=record['job']
 if record['receiptChecked']:return
 if proc.poll()is None:
  if record['row']is not None:
   managerJournal=W/'manager-directory.private.properties'
   while managerJournal.exists()and 'phase=restored'not in managerJournal.read_text('ascii').splitlines():
    print('OWN_MANAGER_PREIMAGE_NOT_RESTORED_DATABASE_KEPT_LIVE_NO_FORCE',flush=True);time.sleep(10)
   runtime.normal_stop(G,plan['candidateReleaseSHA256'],record['row'])
  else:
   # A current pointer is authoritative only if this exact owned controller wrote it.
   if pointer.exists():
    row=J(pointer)
    if row.get('controllerPID')==proc.pid:
     run=Path(row['run']).absolute();assert run.parent==G/'UserData/OriginalServer/runs';code.atomic(run/'stop-requested.txt',b'own-normal-stop\n')
  while proc.poll()is None:
   try:proc.wait(timeout=15)
   except subprocess.TimeoutExpired:print('OWN_CONTROLLER_STILL_LIVE_NO_FORCE_NO_RESTORE',flush=True)
 assert job is not None,'MISSING_OUTER_JOB_PROOF_NO_CODE_RESTORE'
 while job.active_processes():print('OWN_DESCENDANTS_STILL_LIVE_NO_RESTORE',flush=True);time.sleep(2)
 if record['row']is not None:
  receiptPath,receipt=terminal_helper.receipt_for_run(G,Path(record['row']['run']),proc.pid,record['row'])
 else:
  events=[json.loads(line)for line in (Z/record['label']/'controller.private.log').read_text('utf8').splitlines()if line.startswith('{')]
  stopped=[x for x in events if x.get('stopped')is True];assert len(stopped)==1,'THIS_CONTROLLER_STDOUT_RUN_REQUIRED'
  receiptPath,receipt=terminal_helper.receipt_for_run(G,Path(stopped[0]['run']),proc.pid,record.get('observedReady'))
 assert receipt['allOwnedChildrenExited']and not receipt.get('forcedJobClosureComponents')and not receipt.get('jobAssignmentFailureComponents')
 if record['row']is not None:
  assert proc.returncode==0 and receipt['normalOwnedShutdown']and set(receipt['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 budgetResult=record['budget'].metrics()if record.get('budget')is not None else None
 terminal={'jobMemoryBudget':budgetResult,'phase':record['label'],'controllerExitCode':proc.returncode,'allOwnedChildrenExited':True,'actualJobDescendantsZero':True,'normalOwnedShutdown':receipt.get('normalOwnedShutdown'),'exitCodes':receipt.get('exitCodesBeforeJobClose'),'forceTerminationUsed':False}
 terminals.append(terminal);job.close();record['receiptChecked']=True;save('controller-terminals.json',terminals)

try:
 phase='backup-original-code';tx.prepare();phase='durable-pointer-before';pointerTx.prepare();phase='apply-full-candidate';assert resources(),'RESOURCE_DROPPED_BEFORE_CODE_APPLY';tx.apply();configuration_invariant()
 for label in ['first-start','normal-restart']:
  phase=label;record=start(label);result=health.health(G,record['row'],gateway_port=port);checks.append({'phase':label,**result});save('health-results.json',checks)
  phase='normal-original-model-setup-'+label;probeChecks.append(business_probe.run_probe(record['row'],label,port,fixture_nonce,record['process']));save('normal-supervision-results.json',probeChecks)
  phase='stop-'+label;stop(record);invariant()
except BaseException as error:
 failure={'phase':phase,'type':type(error).__name__};print(json.dumps({'failed':True,**failure,'normalCleanupRequired':True}),flush=True)
finally:
 # No restore can occur before every real process handle and descendant is terminal.
 for record in processes:stop(record)
 invariant();assert exited(),'LIVE_OR_FOREIGN_G_REFERENCE_NO_CODE_RESTORE'
 observedPointer=code.pin(pointer)
 if observedPointer!=pointerBefore:
  assert pointer.exists()and J(pointer).get('controllerPID')in {p['process'].pid for p in processes},'FOREIGN_CURRENT_POINTER_REFUSE_ALL_RESTORE'
 # This original-backend candidate never changes private application configuration.
 assert code.pin(G/'private/server-configuration.json')==plan['configBefore'];taskRestored=True
 expectedConfig=plan['configBefore'];configuration_invariant()
 if tx.journal.exists():
  state=tx.state()
  if state['phase']in {'prepared','applying','applied','restoring'}:tx.restore();codeRestored=True
  elif state['phase']=='backup-in-progress':
   assert all(code.pin(G/n)==r['before']for n,r in rows.items());codeRestored=True
 if pointerTx.journal.exists():
  assert code.pin(pointer)==observedPointer,'CURRENT_POINTER_DRIFT_DURING_CODE_RESTORE'
  ownedRow=(processes[-1]['row']or processes[-1].get('observedReady'))if processes else None
  pointerTx.restore(expected_current=observedPointer,owned_ready_row=ownedRow)
 else:assert code.pin(pointer)==pointerBefore,'NO_DURABLE_POINTER_BEFORE_NO_WRITE'
 pointerRestored=code.pin(pointer)==pointerBefore
 configuration_invariant();assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']and pointerRestored
 assert all(code.pin(G/n)==r['before']for n,r in rows.items()),'RESTORED_FULL_CODE_PREIMAGE_REQUIRED'
 proof={'passed':failure is None and len(checks)==2 and len(probeChecks)==2 and taskRestored and codeRestored and pointerRestored,'failure':failure,'actualTwoSixComponentLifecycles':len(checks)==2,
 'health':checks,'terminals':terminals,'codeRestored':codeRestored,'privateConfigurationUnchanged':taskRestored,'originalCurrentPointerRestored':pointerRestored,
 'originalPrivateConfigurationAndInstallationIdentityRestored':True,'dataDirectoriesNeverClonedOrReplaced':True,
 'actualOriginalLedgerUIAndNormalRestart':len(probeChecks)==2,'businessChecks':probeChecks,'normalOriginalLedgerPreviewDownloadAndRestartAccepted':failure is None and len(probeChecks)==2,'actualIISTLSOrPublicAccepted':False,
 'maxActualBackupAtomicPathCharacters':needMax,'boundedControllerPrivateCommitBytes':CONTROLLER_BUDGET,'startupPhysicalAndCommitRequirementBytes':REQUIRED,'completeCompiledOnlineFrontendUsed':bool(checks),
 'durablePointerBeforeSnapshotUsed':True,'exactRunOwnerReceiptSelectionUsed':True,'desktopUsed':False,'fullCloneReady':False}
 save('verified-ledger-ui-r960.json',proof);(V/'ledger-ui-full-result-r960.json').write_bytes(enc(proof))
print(json.dumps({'passed':proof['passed'],'failure':failure,'codeRestored':codeRestored,'actualOriginalLedgerUIAndNormalRestart':proof['actualOriginalLedgerUIAndNormalRestart']}))
raise SystemExit(0 if proof['passed']else 1)
