"""Actual G-only apply_update/recover/rollback; IIS binding is local HTTP only."""
from pathlib import Path
import copy
import functools
import hashlib
import http.client
import importlib.util
import json
import os
import subprocess
import sys
import time
import types

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
V=Path(__file__).resolve().parent;W=R/'work/ua1049'
D=R/'Document/Deployment/r48_static_bridge_full_apply_r1049_20261105'
PLAN_SHA='8e72519fc20fd85a2e628f65f9b6468fd6b56a2ded770bf29f983f406c51c933'

def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def enc(value):return(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def referenced():
    query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode==0,'PROCESS_QUERY_FAILED_NOT_ZERO'
    return int(p.stdout.decode('utf-8-sig').strip())

def main():
    assert sys.argv[1:]==['--run'],'EXPLICIT_REVIEWED_RUN_REQUIRED'
    plan_path=W/'prepared-plan.private.json';assert sha(plan_path)==PLAN_SHA
    plan=read(plan_path)
    assert plan['target']==str(G)and plan['onlyExistingOwnedSyntheticFixture']
    assert read(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
    assert not(W/'run-started.json').exists(),'DO_NOT_RESTART_PREVIOUS_ATTEMPT'
    memory=load('real_apply_memory_r1049',A/'tools/bounded_build_job_r671.py')
    snapshot=memory.memory_snapshot()
    assert min(snapshot['availablePhysicalBytes'],snapshot['availableCommitBytes'])>plan['minimumFreePhysicalAndCommitBytes'],'SEVEN_GIB_RESOURCE_GATE'
    assert referenced()==0,'OWN_G_ACTIVE_NO_START'
    code=load('real_apply_code_r1049',A/'tools/owned_candidate_code_transaction_r543.py')
    assert sha(G/'release-manifest.json')==plan['originalGReleaseSHA256']
    assert all(code.pin(G/name)==row for name,row in plan['protectedPins'].items())
    assert all(code.pin(G/name)==row for name,row in plan['initialMetadata'].items())
    for name,row in plan['mutations'].items():assert code.pin(G/name)==row['before']and code.pin(Path(row['source']))==row['after']
    sys.path.insert(0,str(A/'tools'))
    from owned_run_pointer_r717 import OwnedRunPointerSnapshot
    processes=[];checks=[];terminals=[];runtimes={};attempts=set();failure=None;phase='prepare'
    code_restored=False;pointer_restored=False;metadata_restored=False
    port=plan['gatewayPort'];current_pointer=G/'UserData/OriginalServer/current-run.json'
    def save(name,data):code.atomic(W/name,enc(data))
    def invariant():assert all(code.pin(G/name)==row for name,row in plan['protectedPins'].items()),'PROTECTED_DATA_IDENTITY_DRIFT'
    def exited():return all(row['process'].poll()is not None for row in processes)and referenced()==0
    transaction=code.CodeTransaction(G,W/'base-before',plan['mutations'],processes_exited=exited)
    pointer=OwnedRunPointerSnapshot(G,W/'pointer-before',plan['pointerBefore'],processes_exited=exited)
    def resource_gate():
        row=memory.memory_snapshot();assert min(row['availablePhysicalBytes'],row['availableCommitBytes'])>2*1024**3,'TWO_GIB_REMAINING_HEADROOM_REQUIRED'
    def track_popen(*args,**kwargs):
        command=args[0]if args else kwargs['args']
        assert command[0]==str(G/'runtime/python/python.exe')and command[3]==str(G/'tools/serve_original_server_release.py'),'ONLY_EXPECTED_CONTROLLER_COMMAND'
        resource_gate();invariant()
        p=subprocess.Popen(*args,**kwargs)
        pin=command[command.index('--release-manifest-sha256')+1]
        item={'process':p,'pin':pin,'row':None,'log':str(kwargs['stdout'].name),'terminal':False}
        processes.append(item)
        save('controller-handles.private.json',[{'pid':x['process'].pid,'releaseSHA256':x['pin'],'log':x['log']}for x in processes])
        print(json.dumps({'phase':phase,'controllerPID':p.pid,'actualProcessSpawned':True}),flush=True)
        return p
    def http_binding(address,path):
        assert address=='owned-loopback-http-not-iis'
        assert path in ['/zhumadian/home','/zhumadian/h5/','/zhumadian/api/jnpf/oauth/getLoginConfig','/zhumadian/api/serv/checkInventory/page?current=1&size=1']
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
        try:
            conn.request('GET',path,headers={'Connection':'close'});response=conn.getresponse();body=response.read(4*1024**2+1);assert len(body)<=4*1024**2
            return response.status,body
        finally:conn.close()
    def bind(scenario):
        source=Path(scenario['runtimeSource']);assert sha(source)==scenario['runtimeSHA256']
        wrapper=load('real_apply_runtime_'+scenario['label'].replace('-','_'),source);m=wrapper.runtime()
        m.R48_BASES={plan['oldReleaseSHA256']:copy.deepcopy(plan['binding'])}
        m.R48_PLAN_COMMON={**m.R48_PLAN_COMMON,'targetApplication':G.as_posix(),'gatewayPort':port}
        raw_loader=m.load_bundle;raw_ready=m.owned_ready
        m.load_bundle=functools.partial(raw_loader,expected_target=G.as_posix(),expected_port=port)
        def bound_ready(app,pin,*,gateway_port=port):
            row=raw_ready(app,pin,gateway_port=gateway_port)
            matched=[item for item in processes if item['process'].pid==row['controllerPID']]
            assert len(matched)==1,'ONLY_THIS_TEST_CONTROLLER'
            matched[0]['row']=row
            return row
        m.owned_ready=bound_ready
        m.launch=functools.partial(m.launch,gateway_port=port)
        m.health=functools.partial(m.health,gateway_port=port)
        attributes={name:getattr(subprocess,name)for name in dir(subprocess)if not name.startswith('__')}
        attributes['Popen']=track_popen;m.subprocess=types.SimpleNamespace(**attributes)
        def ingress(app,checked,report):
            assert app==G and checked['gatewayPort']==port
            assert http_binding('owned-loopback-http-not-iis','/zhumadian/home')[0]==200
            return types.SimpleNamespace(tls_local=http_binding),'owned-loopback-http-not-iis'
        m.ingress_preflight=ingress
        runtimes[scenario['label']]=m
        return m
    def terminal(item):
        if item['terminal']:return
        p=item['process']
        while p.poll()is None:
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:print('OWN_CONTROLLER_STILL_LIVE_NO_RESTART_OR_RESTORE',flush=True)
        receipts=[]
        for path in (G/'UserData/OriginalServer/runs').glob('j*/receipt.json'):
            value=read(path)
            if value.get('controllerPID')==p.pid:receipts.append(value)
        assert len(receipts)==1,'EXACT_CONTROLLER_TERMINAL_RECEIPT_REQUIRED'
        receipt=receipts[0]
        assert p.returncode==0 and receipt['normalOwnedShutdown']is True and receipt['allOwnedChildrenExited']is True
        assert set(receipt['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}
        assert all(value==0 for value in receipt['exitCodesBeforeJobClose'].values())
        assert not receipt.get('forcedJobClosureComponents')and not receipt.get('jobAssignmentFailureComponents')
        item['terminal']=True
        terminals.append({'controllerPID':p.pid,'controllerExitCode':p.returncode,'normalOwnedShutdown':True,
            'allSixChildrenExitedZero':True,'forceTerminationUsed':False})
        save('controller-terminals.json',terminals)
    def finalize_stopped():
        for item in processes:
            if item['process'].poll()is not None:terminal(item)
    def stop_all(m):
        for item in processes:
            p=item['process']
            if p.poll()is None:
                if item['row']is not None:m.normal_stop(G,item['pin'],item['row'])
                else:
                    while p.poll()is None:
                        if current_pointer.exists():
                            row=read(current_pointer)
                            if row.get('controllerPID')==p.pid:
                                run=Path(row['run']);assert run.parent==G/'UserData/OriginalServer/runs'
                                code.atomic(run/'stop-requested.txt',b'owned-normal-stop\n');break
                        print('OWN_STARTING_CONTROLLER_WAIT_NO_FORCE_NO_RESTORE',flush=True);time.sleep(2)
            terminal(item)
    def own_pending():
        p=G/'UserData/OriginalPublicUpdates/pending.json'
        if not p.exists():return None
        value=read(p)
        assert value.get('updateId')=='20261105-r48-event-results-from-r45'and value.get('oldReleaseSHA256')==plan['oldReleaseSHA256']
        assert value.get('newReleaseSHA256')in {row['newReleaseSHA256']for row in plan['scenarios']}
        attempt=Path(value['attempt']);assert attempt.parent==G/'UserData/OriginalPublicUpdates'
        attempts.add(str(attempt))
        return value
    save('run-started.json',{'preparedPlanSHA256':PLAN_SHA,'actualApplyCoreFunctionBodyUnmodified':True,'publicIISOrTLSAcceptanceClaimed':False})
    active_meta=G/'UserData/OriginalDeployment/active-deployment.private.json'
    try:
        phase='prepare-owned-base-code';transaction.prepare();pointer.prepare();transaction.apply();invariant()
        assert sha(G/'release-manifest.json')==plan['oldReleaseSHA256']
        code.atomic(active_meta,enc({'schema':'xnby.owned-test-deployment.v1','releaseId':read(G/'release-manifest.json')['releaseId'],'ownerMarker':'real-apply-bridge-r1049'}))
        for scenario in plan['scenarios']:bind(scenario)
        broken=runtimes['original-failure'];fixed=runtimes['repaired']
        phase='start-actual-old-r45';folder=W/'start-old';folder.mkdir()
        old=broken.launch(G,plan['oldReleaseSHA256'],folder);broken.health(G,old)
        checks.append({'case':'actual-old-six-components-ready','passed':True})
        phase='actual-original-apply-failure'
        scenario=plan['scenarios'][0]
        try:broken.apply_update(G,Path(scenario['bundle']),scenario['planSHA256'])
        except ValueError as exc:
            assert str(exc)=='R37_EXACT_STATIC_CONTROLS_AND_RETAINED_ALL_OTHER_CONTROLS_REQUIRED'
        else:raise AssertionError('ORIGINAL_APPLY_DID_NOT_FAIL_AT_EXPECTED_CONNECTION')
        pending=own_pending();finalize_stopped()
        assert pending['oldNormalShutdownCompleted']and pending['mutationStarted']and pending['codeApplied']and not pending['ready']
        assert sha(G/'release-manifest.json')==scenario['newReleaseSHA256']and not(Path(pending['attempt'])/'launch-state.json').exists()
        checks.append({'case':'real-old-stop-replace-static-failure-before-new-start','passed':True})
        phase='actual-failed-update-recovery';broken.recover_pending(G);invariant()
        assert own_pending()['recovered']and sha(G/'release-manifest.json')==plan['oldReleaseSHA256']
        old=broken.owned_ready(G,plan['oldReleaseSHA256']);broken.health(G,old)
        checks.append({'case':'real-recover-pending-restores-and-starts-old-code','passed':True})
        phase='actual-repaired-apply';scenario=plan['scenarios'][1]
        fixed.apply_update(G,Path(scenario['bundle']),scenario['planSHA256']);invariant();finalize_stopped()
        pending=own_pending();latest=read(G/'UserData/OriginalPublicUpdates/latest.json')
        assert latest['ready']and pending['completed']and latest['newReleaseSHA256']==scenario['newReleaseSHA256']
        assert sha(G/'release-manifest.json')==scenario['newReleaseSHA256']
        row=fixed.owned_ready(G,scenario['newReleaseSHA256']);fixed.health(G,row)
        checks.append({'case':'real-repaired-stop-replace-static-check-start-health-and-anonymous-http','passed':True})
        phase='actual-rollback-latest';fixed.rollback_latest(G);invariant();finalize_stopped()
        assert sha(G/'release-manifest.json')==plan['oldReleaseSHA256']
        row=fixed.owned_ready(G,plan['oldReleaseSHA256']);fixed.health(G,row)
        checks.append({'case':'real-successful-update-rollback-and-old-six-components-ready','passed':True})
    except BaseException as exc:
        failure={'phase':phase,'type':type(exc).__name__,'message':str(exc)[:400]}
        save('failure.private.json',failure)
    finally:
        if processes:
            m=runtimes.get('repaired')or runtimes['original-failure']
            stop_all(m)
        pending=own_pending()
        if pending and pending.get('mutationStarted')and not pending.get('recovered')and sha(G/'release-manifest.json')!=plan['oldReleaseSHA256']:
            assert pending.get('failureType')and not pending.get('ready'),'UNKNOWN_SUCCESS_OR_DRIFT_NO_AUTOMATIC_RECOVERY'
            matching=[row for row in plan['scenarios']if row['newReleaseSHA256']==pending['newReleaseSHA256']]
            assert len(matching)==1
            m=runtimes[matching[0]['label']];m.recover_pending(G);stop_all(m)
        assert exited(),'ALL_OWNED_PROCESSES_MUST_BE_GONE'
        invariant()
        # Restore only metadata created in this owned attempt; untouched absent
        # before-images are retained as a separate proof, never a broad directory deletion.
        for name,before in plan['initialMetadata'].items():
            assert before is None
            path=G/name
            if not path.exists():continue
            value=read(path);expected=code.pin(path)
            if name.endswith('active-deployment.private.json'):
                assert value.get('ownerMarker')=='real-apply-bridge-r1049'
                assert value.get('controllerPID')in {item['process'].pid for item in processes}
            else:
                assert value.get('updateId')=='20261105-r48-event-results-from-r45'and value.get('attempt')in attempts
            assert code.pin(path)==expected
            path.unlink()
        metadata_restored=True
        if current_pointer.exists()and code.pin(current_pointer)!=plan['pointerBefore']:
            last=[item for item in processes if item['row']and item['row']['controllerPID']==read(current_pointer).get('controllerPID')]
            assert len(last)==1
            pointer.restore(expected_current=code.pin(current_pointer),owned_ready_row=last[0]['row'])
        else:pointer.restore(expected_current=code.pin(current_pointer),owned_ready_row=None)
        pointer_restored=True
        state=transaction.state()
        if state['phase']!='restored':transaction.restore()
        code_restored=all(code.pin(G/name)==row['before']for name,row in plan['mutations'].items())
        invariant()
        report={'passed':failure is None and len(checks)==5,'failure':failure,'checks':checks,'terminals':terminals,
            'actualApplyUpdateBodyAndCodeMutationsUsed':True,'originalFailureAndRecoverPendingActuallyRun':True,
            'repairedApplyAndRollbackActuallyRun':failure is None,
            'realIISOrPublicTLSAccepted':False,'ingressBinding':'actual loopback HTTP, not IIS/TLS',
            'normalAuthenticatedUIAccepted':False,'newBusinessRowsSubmitted':False,
            'codeRestored':code_restored,'pointerRestored':pointer_restored,'metadataRestored':metadata_restored,
            'protectedConfigurationAndInstallationPinsKept':True,'successfulCIMOwnedGReferences':referenced(),
            'allOwnedControllerHandlesTerminal':all(item['process'].poll()is not None for item in processes),
            'publicChanged':False,'fullCloneReady':False}
        save('verified-real-apply-r1049.json',report);code.atomic(D/'verified-real-apply-r1049.json',enc(report))
        print(json.dumps(report),flush=True)
    if failure:raise RuntimeError('REAL_APPLY_TEST_FAILED_AND_RECORDED')

if __name__=='__main__':main()
