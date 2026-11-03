from pathlib import Path
from unittest.mock import patch
import contextlib,ctypes,hashlib,http.client,importlib.util,json,os,socket,subprocess,sys,time,traceback

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools'
O=R/'work/plan-six-relations-ui-r394';D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103/lifecycle-r394'
S=T/'original_public_test_update_r40_resource_cancel_r385.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
scope=J(O/'scope.json');assert scope['onlyOwnedSyntheticG']and not(O/'run-started.json').exists()
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
assert sha(S)==scope['candidateUpdaterSourceSHA256']
memory=(ctypes.c_ulonglong*8)();memory[0]=64;assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>6*1024**3
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
check=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert check.returncode==0 and check.stdout.decode('utf-8-sig').strip()=='0'
port=scope['gatewayPort']
with socket.socket()as probe:probe.bind(('127.0.0.1',port))
spec=importlib.util.spec_from_file_location('actual_snapshot_updater',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('owned_job',A/'tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
def dump(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(enc(value))
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.exists()else None
def unchanged_private():
    assert pin(A/'private/server-configuration.json')==scope['privateConfigurationPin']
    assert sha(A/'UserData/OriginalServer/installation.json')==scope['installationSHA256']
def atomic(p,raw):m.atomic(p,raw)
def assert_plain(p):
    assert p.absolute().is_relative_to(A)
    for parent in [p,*p.parents]:
        if parent==A.parent:break
        if parent.exists():assert not parent.is_symlink()and not getattr(parent.lstat(),'st_file_attributes',0)&0x400

phase='checking-original-preimages';failure=None;baseline_applied=False;restored=False
processes=[];jobs=[];rows=[];terminal=[];actual_events=[];snapshot_checks=[]
original_popen=subprocess.Popen
def observed_popen(args,*a,**kw):
    p=original_popen(args,*a,**kw)
    if isinstance(args,(list,tuple))and str(A/'tools/serve_original_server_release.py')in list(map(str,args)):
        current_pin=str(args[list(map(str,args)).index('--release-manifest-sha256')+1])
        processes.append({'process':p,'pin':current_pin});jobs.append(j.OwnedWindowsJob(p))
        print('OWN_REAL_CONTROLLER_STARTED_PID_'+str(p.pid),flush=True)
        dump(O/'owned-controller-handles.json',{'pids':[v['process'].pid for v in processes],'forceTerminationUsed':False})
    return p

real_load=m.load_bundle;real_owned=m.owned_ready;real_health=m.health;real_launch=m.launch
def local_load(app,bundle,pin_value,**kw):
    assert app==A
    return real_load(app,bundle,pin_value,expected_target=A,expected_port=port)
def local_owned(app,pin_value,*,gateway_port=port):
    assert app==A and gateway_port==port
    return real_owned(app,pin_value,gateway_port=port)
def local_health(app,row,guarded=True,*,gateway_port=port):
    assert app==A and gateway_port==port
    return real_health(app,row,guarded,gateway_port=port)
def local_launch(app,pin_value,folder,overlay=None,*,gateway_port=port):
    assert app==A and gateway_port==port
    result=real_launch(app,pin_value,folder,overlay,gateway_port=port);rows.append(result)
    actual_events.append({'stage':'actual-six-ready','releaseSHA256':pin_value,'controllerPID':result['controllerPID']})
    return result
class OwnedHTTPIngress:
    def tls_local(self,address,path):
        assert address=='own-loopback-http-fixture'
        return m.http_check(port,path)
def local_ingress(app,plan,report):
    assert app==A
    # This is explicitly an HTTP fixture adapter, never IIS or TLS evidence.
    actual_events.append({'stage':'explicit-owned-HTTP-ingress-adapter','actualIISTLS':False})
    return OwnedHTTPIngress(),'own-loopback-http-fixture'

def normal_stop_every_owned_process():
    for record,job in zip(processes,jobs):
        if record.get('jobClosed'):continue
        p=record['process']
        if p.poll()is None:
            current=A/'UserData/OriginalServer/current-run.json'
            assert current.is_file(),'LIVE_OWN_CONTROLLER_WITHOUT_POINTER_NO_RESTORE'
            row=J(current);assert row.get('controllerPID')==p.pid,'LIVE_OWN_CONTROLLER_POINTER_MISMATCH_NO_RESTORE'
            run=Path(row['run']);assert run.parent==A/'UserData/OriginalServer/runs'
            if row.get('ready'):m.normal_stop(A,record['pin'],row)
            else:atomic(run/'stop-requested.txt',b'own-normal-stop\n')
            while p.poll()is None:
                try:p.wait(timeout=20)
                except subprocess.TimeoutExpired:print('OWN_CONTROLLER_NORMAL_EXIT_STILL_LIVE_NO_FORCE',flush=True)
        while job.active_processes():
            print('OWN_CONTROLLER_DESCENDANTS_STILL_LIVE_NO_RESTORE_OR_FORCE',flush=True);time.sleep(2)
        p.wait();job.close();record['jobClosed']=True
        receipts=[q for q in(A/'UserData/OriginalServer/runs').glob('j*/receipt.json')if J(q).get('controllerPID')==p.pid]
        assert len(receipts)<=1
        if receipts:
            receipt=J(receipts[0]);assert receipt['allOwnedChildrenExited']and not receipt.get('forcedJobClosureComponents')and not receipt.get('jobAssignmentFailureComponents')
            summary={k:receipt.get(k)for k in ['normalOwnedShutdown','allOwnedChildrenExited','exitCodesBeforeJobClose','platformContextClosed','businessContextClosed']}
        else:
            summary={'normalOwnedShutdown':False,'startupExitedBeforeReceipt':True,'actualHandleAndDescendantsTerminal':True}
        terminal.append({'pid':p.pid,'controllerExitCode':p.returncode,'actualJobDescendantsZero':True,'receipt':summary})

def schema_snapshot(label,row):
    reader=J(R/'work/event_delivery_consistency_20261030/full-controller-r131/schema-reader.json')
    names=R/'work/event_delivery_consistency_20261030/full-controller-r131/original-table-names.txt'
    assert len([n for n in names.read_text(encoding='utf-8').splitlines()if n.strip()])==398
    identity=J(A/'UserData/OriginalServer/installation.json');cfg=J(A/'private/server-configuration.json')
    output=O/(label+'-398-models.private.json')
    args=[reader['java'],'-Xmx128m','-cp',reader['classpath'],'OwnControllerSchemaSnapshot',str(row['databasePort']),identity['databaseUUID'],str(A/'UserData/OriginalServer/database/data'),str(names),str(output)]
    p=original_popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    job=j.OwnedWindowsJob(p)
    out,err=p.communicate(input=cfg['seedRootPassword'].encode());cfg=None;identity=None
    while job.active_processes():time.sleep(.1)
    job.close();assert p.returncode==0,'OWN_SCHEMA_SNAPSHOT_FAILED'
    return J(output)

def verify_candidate_static():
    wrapper=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2/delivery/deploy_unified_mappers_r38.py'
    ns={'__file__':str(wrapper),'__name__':'owned_static_checks'};exec(compile(wrapper.read_bytes(),str(wrapper),'exec'),ns)
    # Bind the test to actual compiled entry names; preserve strict decoded hashes.
    import re
    entry=(O/'bundle/payload/frontend/emergency_pc/index.html').read_text(encoding='utf-8')
    scripts=re.findall(r'<script[^>]+src="(/zhumadian/emergency/assets/js/[^"<>]+)"',entry)
    styles=re.findall(r'<link[^>]+href="(/zhumadian/emergency/assets/css/[^"<>]+)"',entry)
    assert len(scripts)==len(styles)==1
    expected={n:p for n,p in ns['STATIC_EXPECTED'].items()if not n.startswith('/zhumadian/emergency/')}
    for original in scripts+styles:
        rel='frontend/emergency_pc/'+original.split('/zhumadian/emergency/',1)[1]
        pin=m.R38_FRONTEND_ROWS[rel]
        expected[original.replace('/zhumadian/emergency/','/zhumadian/emergency/branding-20261025/',1)]={'decodedBytes':pin['bytes'],'decodedSHA256':pin['sha256']}
    assert len(expected)==4
    ns['STATIC_EXPECTED']=expected
    result=[]
    for path in ns['STATIC_EXPECTED']:
        client=http.client.HTTPConnection('127.0.0.1',port,timeout=20)
        try:
            client.request('GET',path,headers={'Host':'www.joinlinksmart.com','Accept-Encoding':'gzip','Connection':'close'})
            response=client.getresponse();body=response.read(4*1024**2+1);headers={k.lower():v for k,v in response.getheaders()}
            checked=ns['validate_static_response'](path,'gzip',response.status,headers,body)
            result.append({'resource':path,**checked})
        finally:client.close()
    return result


def verify_native_candidate(row):
    # All state and credentials here belong to the separately marked synthetic clone.
    root=R/'work/event_delivery_consistency_20261030/full-controller-r163/r153'
    assert not root.exists() and m.native_plan_runtime_ready(A,row)['installedAndRuntimeClassCopyMatched']
    root.mkdir();dump(root/'controller-started.json',{'gatewayPort':port,'onlyOwnedSyntheticG':True})
    source=Path(__file__).resolve().parent/'verify_native_plan_six_relations_dialog_r394.mjs'
    assert sha(source)=='bbc40e5a9c5f75d041b2da4850837cf5fc5250ddcc6b2a85ce6b73f74560ebe6'
    actual=root/'actual-browser-source.mjs';actual.write_bytes(source.read_bytes())
    classes=root/'resource-fixture-classes';classes.mkdir()
    reader=J(R/'work/event_delivery_consistency_20261030/full-controller-r131/schema-reader.json')
    identity=J(A/'UserData/OriginalServer/installation.json');cfg=J(A/'private/server-configuration.json')
    secret=cfg['seedRootPassword'];assert len(secret)==32
    drivers=list((A/'payload/business/lib').glob('mysql-connector-*.jar'));assert len(drivers)==1
    cp=str(classes)+';'+str(drivers[0])
    env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','PYTHONHOME','PYTHONPATH','MYSQL_PWD','MYSQL_HOME']}
    fixture_rows=[]
    for fixture in ['OwnPlanPortalMenusR222','OwnPlanDictionaryR226']:
        source=T/(fixture+'.java')
        compile_args=[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)]
        p=original_popen(compile_args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);out,err=p.communicate()
        while job.active_processes():time.sleep(.1)
        job.close();assert p.returncode==0,'OWN_PLAN_SEED_COMPILE_FAILED'
        args=[reader['java'],'-Xmx128m','-cp',cp,fixture,str(row['databasePort']),identity['databaseUUID'],str(A/'UserData/OriginalServer/database/data')]
        p=original_popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);out,err=p.communicate(input=secret.encode())
        while job.active_processes():time.sleep(.1)
        job.close();assert p.returncode==0,'OWN_PLAN_SEED_EXACT_REUSE_FAILED'
        fixture_rows.append({'fixture':fixture,'sourceSHA256':sha(source),'exitCode':0,'actualDescendantsZero':True})
    wire={'base':'http://127.0.0.1:'+str(port),'account':'own_operator_a','password':secret,'expectedUserId':'a531'+format(100,'028x'),'syntheticNormalUser':True,'baseline':False,'exerciseDepartmentBaseline':False}
    with(root/'plan-browser.private.log').open('wb')as trace:
        p=original_popen(['D:/Program Files/nodejs/node.exe',str(actual),root.as_posix()],stdin=subprocess.PIPE,stdout=trace,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(p);dump(root/'browser-started.json',{'pid':p.pid,'sourceSHA256':sha(actual),'syntheticOnly':True})
        p.communicate(input=enc(wire));wire.clear();secret=None;cfg=None;identity=None
        while job.active_processes():time.sleep(.1)
        job.close()
    dump(root/'browser-outer-terminal.json',{'exitCode':p.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False})
    bt=J(root/'plan-browser/browser-terminal.json');assert bt['chromeExitCode']==0 and bt['normalBrowserClose']and not bt['forceTerminationUsed']
    assert p.returncode==0,'OWN_UNIFIED_PLAN_NATIVE_UI_FAILED'
    result=J(root/'plan-browser/result.json');assert result['passed']and len(result['cases'])==29 and not result['exceptions']
    deleted=J(root/'plan-browser/deleted-detail-navigation-evidence.json');assert deleted['passed']
    summary={'passed':True,'cases':29,'javascriptExceptions':0,'normalRoleAndOriginalController':True,
      'allSixPlanRelationsActuallyCreatedEditedAndRenderedReadonly':True,'exactR40ResourceCancelCandidateRuntime':True,'planDeleteAndExercisePeopleAttachmentRetained':True,
      'deletedOldDetailNavigationRetryRefreshFriendlyState':True,'fixtures':fixture_rows,
      'browserAndActualDescendantsNormalZero':True,'publicOrFormalOrDesktopTouched':False}
    dump(D/'candidate-native-ui-r374.json',summary)
    return summary

def restore_original():
    assert all(v['process'].poll()is not None for v in processes)
    unchanged_private()
    current=A/'UserData/OriginalServer/current-run.json'
    if current.exists()and pin(current)!=scope['originalBefore'].get('UserData/OriginalServer/current-run.json'):
        assert J(current).get('controllerPID')in {v['process'].pid for v in processes},'FOREIGN_CURRENT_POINTER_REFUSE_RESTORE'
    for name in ['UserData/OriginalPublicUpdates/latest.json','UserData/OriginalPublicUpdates/pending.json']:
        path=A/name
        if path.exists()and pin(path)!=scope['originalBefore'].get(name):
            assert J(path).get('updateId')==J(O/'bundle/update-manifest.json')['updateId'],'FOREIGN_UPDATE_POINTER_REFUSE_RESTORE'
    active=A/'UserData/OriginalDeployment/active-deployment.private.json'
    if active.exists()and pin(active)!=scope['originalBefore'].get('UserData/OriginalDeployment/active-deployment.private.json'):
        state=J(active);assert state.get('ownedSyntheticLifecycleFixture')is True
        assert 'controllerPID'not in state or state['controllerPID']in {v['process'].pid for v in processes},'FOREIGN_DEPLOYMENT_POINTER_REFUSE_RESTORE'
    for name,original in scope['originalBefore'].items():
        target=A/name;assert_plain(target)
        # Code after successful rollback must be either the prepared baseline or
        # its absent state. Any unexpected code is retained for manual inspection.
        if not name.startswith('UserData/'):
            expected=scope['desiredCandidate'].get(name,'unchanged-original')
            if expected=='unchanged-original':expected=original
            elif expected is not None:expected={k:expected[k]for k in ['bytes','sha256']}
            assert pin(target)==expected,'FOREIGN_OR_UNRESTORED_CODE_REFUSE_ORIGINAL_RESTORE:'+name
    for name,original in scope['originalBefore'].items():
        target=A/name
        if original is None:
            if target.exists():target.unlink()
        else:
            before=O/'original-before'/name;assert pin(before)==original;atomic(target,before.read_bytes())
    assert all(pin(A/name)==value for name,value in scope['originalBefore'].items())
    unchanged_private()
    assert sha(A/'release-manifest.json')==scope['baseOriginalGReleaseSHA256']


dump(O/'run-started.json',{'started':True,'normalUIIterationOnly':True,'newApplyOrRollbackNotClaimed':True})
installed=False
try:
    unchanged_private()
    for n,value in scope['originalBefore'].items():assert pin(A/n)==value,'ORIGINAL_PREIMAGE_DRIFT'
    phase='install-owned-exact-candidate-code-for-UI-iteration'
    for n,value in scope['desiredCandidate'].items():
        if value is not None:assert pin(Path(value['source']))=={k:value[k]for k in ['bytes','sha256']}
    installed=True
    for n,value in scope['desiredCandidate'].items():
        p=A/n;assert_plain(p)
        if value is None:
            if p.exists():p.unlink()
        else:
            source=Path(value['source']);assert pin(source)=={k:value[k]for k in ['bytes','sha256']};atomic(p,source.read_bytes())
    installed=True
    with patch.object(m,'owned_ready',local_owned),patch.object(m,'health',local_health),patch.object(m,'launch',local_launch),patch.object(subprocess,'Popen',observed_popen):
        plan=J(O/'bundle/update-manifest.json')
        assert sha(A/'release-manifest.json')==scope['candidateAdaptedR39SHA256']
        assert m.candidate_runtime_pool_preflight(A,O/'bundle',plan)['originalMapperPreflight']['passed']
        phase='normal-launch-one-real-candidate-controller';boot=O/'candidate-boot';boot.mkdir()
        row=m.launch(A,scope['candidateAdaptedR39SHA256'],boot);m.health(A,row)
        phase='candidate-models-before-UI';before=schema_snapshot('before-ui',row)
        phase='actual-current-entry-gzip';static=verify_candidate_static();dump(O/'candidate-static-HTTP.json',{'passed':True,'checks':static,'actualIISTLS':False})
        phase='normal-role-29-case-UI-iteration';ui=verify_native_candidate(row)
        phase='candidate-models-after-UI';assert schema_snapshot('after-ui',row)==before
        print('OWN_ALL_SIX_RELATIONS_NORMAL_ROLE_29_CASES_PASSED',flush=True)
except BaseException as error:
    failure={'type':type(error).__name__,'phase':phase,'message':str(error)if isinstance(error,(AssertionError,ValueError))else'OWN_UI_ITERATION_FAILED_INSPECT_SCOPED_RESULT'}
    dump(O/'failure.json',failure)
finally:
    normal_stop_every_owned_process()
    if installed:
        try:restore_original();restored=True
        except BaseException as e:dump(O/'restore-refused.json',{'type':type(e).__name__,'message':str(e),'noForce':True})
    dump(O/'terminal.json',{'failure':failure,'allOwnedControllerHandlesTerminal':all(v['process'].poll()is not None for v in processes),
       'controllers':terminal,'originalGCodeAndPointersRestored':restored,'forceTerminationUsed':False,'newApplyOrRollbackNotClaimed':True})
assert failure is None and restored
assert len(terminal)==1 and terminal[0]['controllerExitCode']==0 and terminal[0]['actualJobDescendantsZero']
dump(D/'verified-native-r394.json',{'passed':True,'actualNormalRoleCases':29,'normalOneControllerUIIteration':True,'newApplyOrRollbackNotClaimed':True,
 'priorR390ActualApplyAndRollbackEvidenceSeparate':True,'original398ModelsBeforeAfterUIMatched':True,'normalControllerChromeAndActualDescendantsZero':True,
 'originalGCodeConfigurationAndPointersRestored':True,'actualIISHTTPSOrPublicVerified':False,'fullCloneReady':False})
