"""Resume rollback only from the exact applied/stopped R1049 candidate."""
from pathlib import Path
import functools
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
import types

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
V=Path(__file__).resolve().parent;W=R/'work/ua1049';S=W/'resume-r1053'
D=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'
PLAN_SHA='8e72519fc20fd85a2e628f65f9b6468fd6b56a2ded770bf29f983f406c51c933'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def encode(data):return(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def referenced():
    query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode==0,'CIM_QUERY_FAILURE_NOT_ZERO';return int(p.stdout.decode('utf-8-sig').strip())

def main():
    assert sys.argv[1:]==['--run']
    assert sha(W/'prepared-plan.private.json')==PLAN_SHA
    plan=read(W/'prepared-plan.private.json');scenario=plan['scenarios'][1]
    assert read(W/'failure.private.json')=={'phase':'actual-repaired-apply','type':'KeyError','message':"'completed'"}
    parent=read(W/'actual-parent-terminal-r1049.json')
    assert parent['harnessExitCode']==1 and parent['actualJobDescendantsZero']and not parent['forceTerminationUsed']
    prior_terminals=read(W/'controller-terminals.json')
    assert len(prior_terminals)==3 and all(x['controllerExitCode']==0 and x['allSixChildrenExitedZero']for x in prior_terminals)
    assert referenced()==0,'PREVIOUS_HANDLES_NOT_TERMINAL_NO_RESUME'
    budget=load('resume_memory_r1053',A/'tools/bounded_build_job_r671.py');memory=budget.memory_snapshot()
    assert min(memory['availablePhysicalBytes'],memory['availableCommitBytes'])>7*1024**3
    assert sha(G/'release-manifest.json')==scenario['newReleaseSHA256']
    latest_path=G/'UserData/OriginalPublicUpdates/latest.json'
    pending_path=G/'UserData/OriginalPublicUpdates/pending.json'
    latest=read(latest_path);pending=read(pending_path)
    assert latest['ready']is True and not latest.get('rolledBack')and pending['ready']is True
    assert latest['newReleaseSHA256']==pending['newReleaseSHA256']==scenario['newReleaseSHA256']
    assert latest['oldReleaseSHA256']==pending['oldReleaseSHA256']==plan['oldReleaseSHA256']
    assert latest['attempt']==pending['attempt']and latest['updateId']==pending['updateId']=='20261105-r48-event-results-from-r45'
    attempt=Path(latest['attempt']);assert attempt.parent==G/'UserData/OriginalPublicUpdates'
    code=load('resume_code_r1053',A/'tools/owned_candidate_code_transaction_r543.py')
    assert all(code.pin(G/name)==row for name,row in plan['protectedPins'].items())
    assert sha(Path(scenario['runtimeSource']))==scenario['runtimeSHA256']
    helper=load('resume_actual_fixed_runtime_r1053',Path(scenario['runtimeSource']));m=helper.runtime()
    # Check every target/before pin before starting any controller. An absent
    # completed field is never treated as success evidence; actual result,
    # runtime health and terminal receipts establish each completed stage.
    changes=read(attempt/'changes.json')
    for name,row in changes.items():
        if row['after']is None:assert not(G/name).exists()
        else:m.check_file(G,name,row['after'])
        if row['before']is not None:m.check_file(attempt/'before',name,row['before'])
    successful_apply=read(attempt/'result.json')
    assert successful_apply['ready']is True and successful_apply['codeApplied']is True and successful_apply['serverLocalTLSVerified']is True
    old_attempts=[]
    for directory in (G/'UserData/OriginalPublicUpdates').iterdir():
        if directory.is_dir()and(directory/'recovery-result.json').is_file():
            result=read(directory/'recovery-result.json')
            if result.get('updateId')=='20261105-r48-event-results-from-r45'and result.get('newReleaseSHA256')==plan['scenarios'][0]['newReleaseSHA256']:
                old_attempts.append((directory,result))
    assert len(old_attempts)==1 and old_attempts[0][1]['recovered']is True
    original_failure=read(old_attempts[0][0]/'result.json')
    assert original_failure['failure']=='R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED'
    assert original_failure['oldNormalShutdownCompleted']and original_failure['mutationStarted']and original_failure['codeApplied']
    assert not S.exists();S.mkdir()
    port=plan['gatewayPort'];processes=[];terminals=[];failure=None;restored=False;metadata_restored=False;pointer_restored=False
    def save(name,value):code.atomic(S/name,encode(value))
    def invariant():assert all(code.pin(G/name)==row for name,row in plan['protectedPins'].items())
    def track(*args,**kwargs):
        command=args[0]if args else kwargs['args'];assert command[0]==str(G/'runtime/python/python.exe')and command[3]==str(G/'tools/serve_original_server_release.py')
        invariant();p=subprocess.Popen(*args,**kwargs)
        item={'process':p,'pin':command[command.index('--release-manifest-sha256')+1],'row':None,'terminal':False};processes.append(item)
        save('handles.private.json',[{'pid':x['process'].pid,'pin':x['pin']}for x in processes])
        print(json.dumps({'actualResumeControllerPID':p.pid}),flush=True);return p
    attributes={name:getattr(subprocess,name)for name in dir(subprocess)if not name.startswith('__')};attributes['Popen']=track;m.subprocess=types.SimpleNamespace(**attributes)
    raw_ready=m.owned_ready
    def ready(app,pin,*,gateway_port=port):
        row=raw_ready(app,pin,gateway_port=gateway_port);matches=[x for x in processes if x['process'].pid==row['controllerPID']]
        assert len(matches)==1;matches[0]['row']=row;return row
    m.owned_ready=ready;m.health=functools.partial(m.health,gateway_port=port);m.launch=functools.partial(m.launch,gateway_port=port)
    def terminal(item):
        if item['terminal']:return
        p=item['process']
        while p.poll()is None:
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:print('ACTUAL_RESUME_HANDLE_LIVE_NO_FORCE',flush=True)
        matches=[]
        for path in (G/'UserData/OriginalServer/runs').glob('j*/receipt.json'):
            value=read(path)
            if value.get('controllerPID')==p.pid:matches.append(value)
        assert len(matches)==1;value=matches[0]
        assert p.returncode==0 and value['normalOwnedShutdown']and value['allOwnedChildrenExited']
        assert set(value['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}and all(x==0 for x in value['exitCodesBeforeJobClose'].values())
        assert not value.get('forcedJobClosureComponents')and not value.get('jobAssignmentFailureComponents')
        item['terminal']=True;terminals.append({'controllerPID':p.pid,'controllerExitCode':0,'normalOwnedShutdown':True,'allSixChildrenExitedZero':True,'forceTerminationUsed':False});save('controller-terminals.json',terminals)
    def stop_all():
        for item in processes:
            p=item['process']
            if p.poll()is None:
                if item['row']:m.normal_stop(G,item['pin'],item['row'])
                else:
                    while p.poll()is None:
                        pointer=G/'UserData/OriginalServer/current-run.json'
                        if pointer.exists():
                            row=read(pointer)
                            if row.get('controllerPID')==p.pid:
                                run=Path(row['run']);assert run.parent==G/'UserData/OriginalServer/runs';code.atomic(run/'stop-requested.txt',b'owned-normal-stop\n');break
                        time.sleep(2)
            terminal(item)
    def exited():return all(x['process'].poll()is not None for x in processes)and referenced()==0
    sys.path.insert(0,str(A/'tools'))
    from owned_run_pointer_r717 import OwnedRunPointerSnapshot
    transaction=code.CodeTransaction(G,W/'base-before',plan['mutations'],processes_exited=exited)
    pointer=OwnedRunPointerSnapshot(G,W/'pointer-before',plan['pointerBefore'],processes_exited=exited)
    try:
        row=m.launch(G,scenario['newReleaseSHA256'],S);m.health(G,row)
        assert read(latest_path)==latest,'FOREIGN_UPDATE_RECORD_DRIFT'
        m.rollback_latest(G);invariant()
        assert sha(G/'release-manifest.json')==plan['oldReleaseSHA256']
        old=m.owned_ready(G,plan['oldReleaseSHA256']);m.health(G,old)
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc)[:400]};save('failure.private.json',failure)
    finally:
        stop_all();assert exited(),'RESUME_PROCESSES_STILL_LIVE_NO_RESTORE';invariant()
        if failure is None:
            assert read(attempt/'rollback-result.json')['rolledBack']is True
            all_pids={row['controllerPID']for row in prior_terminals+terminals}
            for name in plan['initialMetadata']:
                path=G/name
                if not path.exists():continue
                value=read(path);expected=code.pin(path)
                if name.endswith('active-deployment.private.json'):assert value.get('ownerMarker')=='real-apply-bridge-r1049'and value.get('controllerPID')in all_pids
                else:assert value.get('attempt')in {str(attempt),str(old_attempts[0][0])}and value.get('updateId')=='20261105-r48-event-results-from-r45'
                assert code.pin(path)==expected;path.unlink()
            metadata_restored=True
            matches=[item for item in processes if item['row']and item['row']['controllerPID']==read(G/'UserData/OriginalServer/current-run.json').get('controllerPID')]
            assert len(matches)==1
            pointer.restore(expected_current=code.pin(G/'UserData/OriginalServer/current-run.json'),owned_ready_row=matches[0]['row']);pointer_restored=True
            transaction.restore();restored=all(code.pin(G/name)==row['before']for name,row in plan['mutations'].items());invariant()
        report={'passed':failure is None and restored and metadata_restored and pointer_restored,'failure':failure,
            'checks':[{'case':name,'passed':failure is None}for name in ['actual-old-six-components-ready','real-old-stop-replace-static-failure-before-new-start','real-recover-pending-restores-and-starts-old-code','real-repaired-stop-replace-static-check-start-health-and-anonymous-http','real-successful-update-rollback-and-old-six-components-ready']],
            'terminals':prior_terminals+terminals,'initialHarnessKeyErrorRetained':True,
            'continuedFromExactSuccessfullyAppliedNormallyStoppedCandidate':True,'applyUpdateNotRepeated':True,
            'actualApplyUpdateBodyAndCodeMutationsUsed':True,'originalFailureAndRecoverPendingActuallyRun':True,
            'repairedApplyAndRollbackActuallyRun':failure is None,'realIISOrPublicTLSAccepted':False,
            'ingressBinding':'R1049 actual loopback HTTP, not IIS/TLS','normalAuthenticatedUIAccepted':False,
            'newBusinessRowsSubmitted':False,'codeRestored':restored,'pointerRestored':pointer_restored,'metadataRestored':metadata_restored,
            'protectedConfigurationAndInstallationPinsKept':True,'successfulCIMOwnedGReferences':referenced(),
            'allOwnedControllerHandlesTerminal':all(x['process'].poll()is not None for x in processes),'publicChanged':False,'fullCloneReady':False}
        save('verified-real-apply-resume-r1053.json',report);code.atomic(W/'verified-real-apply-r1049.json',encode(report));code.atomic(D/'verified-real-apply-resume-r1053.json',encode(report))
        print(json.dumps(report),flush=True)
    if failure:raise RuntimeError('ACTUAL_ROLLBACK_RESUME_FAILED')

if __name__=='__main__':main()
