"""One original-SDK lifecycle in the existing owned G, code/metadata restored.

Only a new spatial SQLite/JSON fixture may be written; no original business,
account/grant, task, upload or callback transaction is created or replayed.
"""
from pathlib import Path
import copy,hashlib,http.client,importlib.util,json,os,socket,subprocess,sys,time,traceback
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).parent;W=R/'work/su1746';D=R/'Document/Deployment/fine_browser_original_r1745_20261107';PLAN=R/'work/fine-browser-parent-r1745/prepared-plan.private.json'
sys.dont_write_bytecode=True;sys.path.insert(0,str(A/'tools'))
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
code=load('spatial_own_code_r1455',A/'tools/owned_candidate_code_transaction_r543.py');budget=load('spatial_own_budget_r1455',A/'tools/bounded_build_job_r671.py');jobs=load('spatial_own_jobs_r1455',G/'tools/original_server_windows_job.py')
from owned_run_pointer_r717 import OwnedRunPointerSnapshot
receipt=load('spatial_own_receipt_r1455',A/'tools/owned_run_terminal_r709.py')
J=lambda p:json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):code.atomic(W/name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def referenced():
    query="$ErrorActionPreference='Stop';(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')}|Measure-Object).Count"
    p=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode==0,'SUCCESSFUL_G_PROCESS_QUERY_REQUIRED';return int(p.stdout.decode('utf-8-sig').strip())
assert W.is_dir()and set(p.name for p in W.iterdir())=={'harness-r1746.private.log','parent-started-r1746.json'};plan=J(PLAN);assert sha(PLAN)=='244ce85ac28ce4da083e7f530d55473b76cbf58cd63dd2e34586682a4d20e09b'
resource=J(R/'work/fine-browser-parent-r1745/resource-and-reconciliation.json');assert sha(R/'work/fine-browser-parent-r1745/resource-and-reconciliation.json')=='5750bf622263202c01a03fb4dd49c3e39a4fb55cfdbc9d2a37cf2fbb3d98fc95' and resource['priorActualParentTerminalAndRestored']and resource['priorSuccessfulUIWritesConfirmed']and not resource['saveReplayAllowed']
assert not(W/'harness-started-r1746.json').exists()and J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>=resource['minimumAvailablePhysicalAndCommitBytes']
assert referenced()==0 and sha(G/'release-manifest.json')==plan['ownedBaseReleaseSHA256']
resume=J(R/'Document/Deployment/spatial_origin_config_r1516_20261106/readonly-resume-scope-r1525.json');assert resume['priorConfirmedIconAndJSONSaves'] and not resume['saveReplayAllowed'] and sha(R/'work/su1522/expected-document.private.json')==resume['expectedDocumentSHA256'];assert J(R/'work/si1460/project-files/原SDK网页工程_r1522.json')==J(R/'work/su1522/expected-document.private.json')
assert sha(Path(plan['privateOwnedFrontendBeforePinSource']))==plan['privateOwnedFrontendBeforePinSourceSHA256']
for n,p in plan['protectedPins'].items():assert code.pin(G/n)==p
for n,row in plan['mutations'].items():assert code.pin(G/n)==row['before'] and(row['after']is None or code.pin(row['source'])==row['after'])
assert not(G/plan['privateSettingsPath']).exists()and code.pin(plan['privateSettingsSource'])==plan['privateSettingsAfter']
callback=R/'work/original-manager-full-lifecycle-r609/attachment-r1072/resume-r1095/normal-restart/callback-normal-restart-journal.private.properties';assert sha(callback)==plan['callbackJournalSHA256']
max_length=max(len(str((W/'b/before'/n).with_name('.'+Path(n).name+'.own-'+'0'*32+'.tmp')))for n,r in plan['mutations'].items()if r['before']is not None);assert max_length<260,'ALL_BACKUP_ATOMIC_PATHS_MUST_FIT'
processes=[];probe_processes=[];checks=[];terminals=[];phase='prepare';failure=None;code_restored=False;pointer_restored=False;private_created=False;current_owned=None
save('harness-started-r1746.json',{'sourceSHA256':sha(__file__),'planSHA256':sha(PLAN),'publicChanged':False,'businessOrTaskReplayAllowed':False})
def exited():return all(r['process'].poll()is not None and(r['job']is None or r['job'].active_processes()==0)for r in processes+probe_processes)and referenced()==0
tx=code.CodeTransaction(G,W/'b',plan['mutations'],processes_exited=exited)
pointer=OwnedRunPointerSnapshot(G,W/'p',plan['pointerBefore'],processes_exited=exited)
def invariant():
    for n,p in plan['protectedPins'].items():assert code.pin(G/n)==p,'PROTECTED_G_IDENTITY_OR_CONFIGURATION_DRIFT'
    assert sha(callback)==plan['callbackJournalSHA256'],'COMPLETED_CALLBACK_JOURNAL_CHANGED_NO_REPLAY'
def check(value,name):
    checks.append({'case':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def process_wait(row):
    p=row['process']
    while p.poll()is None:
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:print(json.dumps({'sameOwnedProcessHandleStillLive':True,'phase':phase,'noForceOrReplacement':True}),flush=True)
    if row['job']:
        while row['job'].active_processes():time.sleep(.1)
def start(label):
    invariant();assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>=15*1024**3
    folder=W/label;folder.mkdir()
    with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    assert port not in (8767,18891,18892)
    old=J(R/'work/ue1378/plan-copy.private.json');overlay=G/old['callbackOverlay'];assert sha(overlay)==old['callbackOverlaySHA256']
    gate=b'OWN_SPATIAL_PARENT_R1455\n';bootstrap="import sys,runpy;assert sys.stdin.buffer.readline(128)==b'OWN_SPATIAL_PARENT_R1455\\n';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
    command=[str(G/'runtime/python/python.exe'),'-I','-B','-c',bootstrap,str(G/'tools/serve_original_server_release.py'),'--application',str(G),'--release-manifest-sha256',plan['candidateReleaseSHA256'],'--gateway-port',str(port),'--callback-overlay',str(overlay),'--callback-overlay-sha256',old['callbackOverlaySHA256']]
    before_runs={p.name for p in (G/'UserData/OriginalServer/runs').iterdir()};out=(folder/'controller.private.log').open('xb');p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    row={'process':p,'job':None,'out':out,'label':label,'gatewayPort':port,'ready':None,'runDirsBefore':before_runs};processes.append(row)
    try:row['job']=jobs.OwnedWindowsJob(p);row['budget']=budget.BoundedBuildJob(row['job'],5*1024**3)
    except BaseException:p.stdin.write(b'cancel\n');p.stdin.close();process_wait(row);raise
    p.stdin.write(gate);p.stdin.flush();p.stdin.close()
    save('controller-handles.private.json',[{'pid':r['process'].pid,'label':r['label']}for r in processes]);print(json.dumps({'phase':phase,'actualControllerStarted':True,'label':label}),flush=True)
    last=time.monotonic()
    while p.poll()is None:
        path=G/'UserData/OriginalServer/current-run.json'
        if path.exists():
            ready=J(path)
            if ready.get('controllerPID')==p.pid and ready.get('ready')is True:
                row['ready']=ready;return row
        if time.monotonic()-last>15:print(json.dumps({'phase':phase,'sameOriginalControllerStillStarting':True}),flush=True);last=time.monotonic()
        time.sleep(.2)
    process_wait(row);raise RuntimeError('ORIGINAL_PARENT_EXITED_BEFORE_READY')
def stop(row):
    if row['process'].poll()is None:
        ready=row.get('ready')
        if ready is None:
            path=G/'UserData/OriginalServer/current-run.json'
            if path.exists():
                value=J(path)
                if value.get('controllerPID')==row['process'].pid and value.get('ready')is True:ready=value;row['ready']=value
        if ready is not None:
            folder=Path(ready['run']);assert folder.parent==G/'UserData/OriginalServer/runs';(folder/'stop-requested.txt').write_bytes(b'own-spatial-parent-stop\n')
    process_wait(row);row['out'].close()
    if row.get('ready')is not None:run=Path(row['ready']['run'])
    else:
        events=[json.loads(x)for x in (W/row['label']/'controller.private.log').read_text('utf8',errors='replace').splitlines()if x.startswith('{')and'"stopped"'in x]
        if not events:
            assert {p.name for p in (G/'UserData/OriginalServer/runs').iterdir()}==row['runDirsBefore']and code.pin(G/'UserData/OriginalServer/current-run.json')==plan['pointerBefore'],'EARLY_EXIT_WITHOUT_RECEIPT_MUST_NOT_HAVE_ALLOCATED_RUN'
            row['terminal']={'earlyExitBeforeRunAllocation':True};terminals.append({'label':row['label'],'controllerExitCode':row['process'].returncode,'earlyExitBeforeRunAllocation':True,'componentExitCodes':{},'normalOwnedShutdown':False,'actualJobZero':row['job']is not None and row['job'].active_processes()==0});save('actual-controller-terminals.private.json',terminals);return
        assert len(events)==1;run=Path(events[0]['run'])
    _,value=receipt.receipt_for_run(G,run,row['process'].pid,row.get('ready'))
    row['terminal']=value;terminals.append({'label':row['label'],'controllerExitCode':row['process'].returncode,'componentExitCodes':value['exitCodesBeforeJobClose'],'allOwnedChildrenExited':value['allOwnedChildrenExited'],'normalOwnedShutdown':value['normalOwnedShutdown'],'spatialShutdown':value.get('spatialSyncShutdown'),'actualJobZero':row['job']is not None and row['job'].active_processes()==0})
    save('actual-controller-terminals.private.json',terminals)
def login(row,label):
    original=J(G/'private/server-configuration.json');secret=original['seedRootPassword'];assert len(secret)==32 and all(c in'0123456789abcdef'for c in secret);original.clear()
    second=J(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');assert second['credentialsSynthetic']is True
    wire={'base':'http://127.0.0.1:'+str(row['gatewayPort']),'account':'own_statistics_reader_e','password':secret,'expectedUserId':f'a531{120002:028x}','credentialsSynthetic':True,'phase':label,'secondAccount':'own_operator_a','secondExpectedUserId':second['accounts']['own_operator_a']['id']};secret=''
    helper=V/'original_configuration_lifecycle_r1746.mjs';args=['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(helper),(W/('ui-'+label)).as_posix()]
    err=(W/('ui-'+label+'.stderr.private.log')).open('xb');p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True);record={'process':p,'job':None};probe_processes.append(record)
    try:record['job']=jobs.OwnedWindowsJob(p);record['budget']=budget.BoundedBuildJob(record['job'],resource['browserLimitBytes'])
    except BaseException:p.stdin.close();process_wait(record);raise
    raw=(json.dumps(wire)+'\n').encode();wire.clear();first=True
    while True:
        try:out,_=p.communicate(input=raw if first else None,timeout=15);break
        except subprocess.TimeoutExpired:first=False;raw=b'';print(json.dumps({'phase':phase,'sameNormalLoginBrowserOwnerLive':True}),flush=True)
    raw=b'';process_wait(record);err.close();value=json.loads(out);out=b'';save('normal-login-'+label+'-proof.json',value['proof']);assert p.returncode==0,'ACTUAL_ORIGINAL_SCENE_UI_FAILED'
    assert value['proof']['passed']and value['proof']['normalCompiledLogin']and value['proof']['currentUserMatchedKnownSyntheticNonAdmin'];save('normal-login-'+label+'-proof.json',value['proof']);return value
def probe(row,label):
    ready=row['ready'];check(J(Path(ready['run'])/'spatial-sync/server.private.json')['gatewayOrigin']=='http://127.0.0.1:'+str(row['gatewayPort']),'actual-single-original-loopback-origin-bound-'+label);check(ready['spatialSync']['platformPort']==ready['platformPort']and ready['spatialSync']['originalGatewayRoutesVerified']and ready['spatialSync']['sceneStaticConfigured'],'actual-original-platform-and-scene-static-binding-'+label)
    check(set(ready['children'])=={'store','mysql','redis','platform','business','gateway'},'original-six-component-ready-map-preserved-'+label)
    value=login(row,label);proof=value['proof'];check(proof['originalGetTokenHostUsed']and not proof['authorizationExportedToParent'],'normal-original-host-UI-through-original-token-provider-'+label)
    checks.extend({'case':c['case']+'-'+label,'passed':c['passed']}for c in proof['checks'])
    intent=J(R/'work/su1522/ui-write-intent.private.json');check(intent['iconConfirmed']and intent['fileConfirmed'],'known-UI-spatial-saves-confirmed-no-blind-retry-'+label)
    document=J(R/'work/su1522/expected-document.private.json');saved=J(R/'work/si1460/project-files/原SDK网页工程_r1522.json');check(saved==document,'real-server-owned-JSON-file-matches-UI-snapshot-'+label)
    invariant()
try:
    phase='apply-owned-code';tx.prepare();pointer.prepare();tx.apply();invariant()
    private=G/plan['privateSettingsPath'];assert not private.exists()
    with private.open('xb')as f:f.write(Path(plan['privateSettingsSource']).read_bytes())
    private_created=True
    for label in ['restart']:
        phase='start-'+label;row=start(label);current_owned=row['ready'];phase='normal-original-sdk-'+label;probe(row,label);phase='normal-stop-'+label;stop(row)
        last=terminals[-1];check(last['controllerExitCode']==0 and last['normalOwnedShutdown']and all(v==0 for v in last['componentExitCodes'].values())and set(last['componentExitCodes'])=={'store','mysql','redis','platform','business','gateway','spatial-sync','fine-source'},'actual-eight-component-parent-normal-shutdown-'+label)
        check(last['spatialShutdown']['actualWorkerHandleTerminal']and last['spatialShutdown']['workerExitCode']==0,'actual-spatial-worker-native-exit-code-'+label)
    fine=terminals[-1]['spatialShutdown']['fineSourceShutdown'];check(fine['providerExitCode']==0 and fine['nativeExitCode']==0 and fine['actualJobZero']and fine['normalStopAccepted']and fine['protectedWrites']==0,'actual-fine-native-provider-normal-parent-stop-and-zero-writes')
    phase='complete'
except BaseException as error:
    failure={'phase':phase,'class':type(error).__name__,'message':str(error)[:180]if isinstance(error,(AssertionError,ValueError,RuntimeError))else None,'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno}for f in traceback.extract_tb(error.__traceback__)]};save('failure-safe.json',failure);print(json.dumps({'failed':True,'phase':phase,'class':type(error).__name__}),flush=True)
finally:
    for row in processes:
        if 'terminal'not in row:stop(row)
    for row in probe_processes:process_wait(row)
    assert exited(),'ACTUAL_HANDLES_AND_FRESH_G_QUERY_REQUIRED_BEFORE_RESTORE';invariant()
    current=code.pin(G/'UserData/OriginalServer/current-run.json')
    pointer.restore(expected_current=current,owned_ready_row=current_owned);pointer_restored=True
    tx.restore();code_restored=True
    if private_created:
        path=G/plan['privateSettingsPath'];assert code.pin(path)==plan['privateSettingsAfter'];path.unlink()
    invariant();assert sha(G/'release-manifest.json')==plan['ownedBaseReleaseSHA256']
    metrics=[]
    for row in processes+probe_processes:
        if row['job']:metrics.append(row['budget'].metrics());row['job'].close()
    result={'schema':'xnby.spatial.original-host-ui.v1','passed':failure is None,'phase':phase,'failure':failure,'checks':checks,'controllerRuns':len(processes),'actualTerminals':terminals,'originalCodeRestored':code_restored,'originalPointerRestored':pointer_restored,'newPrivateSettingsRemoved':not(G/plan['privateSettingsPath']).exists(),'protectedConfigurationInstallationStoreAndCallbackPinsRetained':True,'allActualJobsZeroBeforeClose':True,'jobMetrics':metrics,'actualOriginalLoginAndCurrentUserUsed':any((W/('normal-login-'+label+'-proof.json')).exists()and J(W/('normal-login-'+label+'-proof.json')).get('normalCompiledLogin',False)for label in ['first','restart']),'syntheticCurrentUserHTTPUsed':False,'realPublicUserOrIIS_TLS252Accepted':False,'noOriginalBusinessTaskUploadOrGrantReplay':True,'fullBusinessRowDigestAuditPerformed':False,'forceTerminationUsed':False,'publicChanged':False}
    save('verified-result.json',result);print(json.dumps({'passed':result['passed'],'phase':phase,'controllerRuns':len(processes),'codeRestored':code_restored,'pointerRestored':pointer_restored,'failure':failure}),flush=True)
if failure:raise SystemExit(1)
