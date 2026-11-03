from pathlib import Path
from unittest.mock import patch
import contextlib,ctypes,hashlib,http.client,importlib.util,json,os,socket,subprocess,sys,time,traceback

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools'
O=R/'work/plan-six-relations-typed-r390';D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103/lifecycle-r390'
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
    root=R/'work/event_delivery_consistency_20261030/full-controller-r163/r151'
    assert not root.exists() and m.native_plan_runtime_ready(A,row)['installedAndRuntimeClassCopyMatched']
    root.mkdir();dump(root/'controller-started.json',{'gatewayPort':port,'onlyOwnedSyntheticG':True})
    source=Path(__file__).resolve().parent/'verify_native_plan_six_relations_typed_r390.mjs'
    assert sha(source)=='651b39eb27ec1894d15dd9d6d00cdc3e7779ec6135dc2571de8d1ad7f817a937'
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
            expected=scope['desiredBaseline'].get(name,'unchanged-original')
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

dump(O/'run-started.json',{'started':True,'baselineApplied':False,'gatewayPort':port,'realIISTLSWillNotBeAsserted':True})
try:
    unchanged_private()
    for name,original in scope['originalBefore'].items():assert pin(A/name)==original,'ORIGINAL_FIXTURE_DRIFT'
    phase='apply-owned-R37-code-baseline'
    for name,value in scope['desiredBaseline'].items():
        target=A/name;assert_plain(target)
        if value is None:
            if target.exists():target.unlink()
        else:
            src=Path(value['source']);assert pin(src)=={k:value[k]for k in ['bytes','sha256']};atomic(target,src.read_bytes())
    baseline_applied=True
    bundle=O/'bundle';manifest=scope['bundleManifestSHA256'];assert sha(bundle/'update-manifest.json')==manifest
    with patch.object(m,'load_bundle',local_load),patch.object(m,'owned_ready',local_owned),patch.object(m,'health',local_health),patch.object(m,'launch',local_launch),patch.object(m,'ingress_preflight',local_ingress),patch.object(subprocess,'Popen',observed_popen):
        phase='actual-adapted-full-load-bundle'
        plan,old,changes=m.load_bundle(A,bundle,manifest);assert old==scope['baselineAdaptedR37SHA256']and len(changes)==364
        assert m.candidate_runtime_pool_preflight(A,bundle,plan)['originalMapperPreflight']['passed']
        boot=O/'baseline-boot';boot.mkdir()
        phase='start-real-baseline-six-components';row=m.launch(A,old,boot);m.health(A,row)
        assert m.native_plan_runtime_ready(A,row)is None,'BASELINE_MUST_NOT_HAVE_PLAN_OVERRIDE'
        assert not(A/m.R39_PLAN_CLASS).exists()
        phase='baseline-398-schema-snapshot';schema_before=schema_snapshot('before-update',row)
        print('OWN_REAL_BASELINE_SIX_AND_398_SCHEMA_READY',flush=True)
        phase='actual-apply-update-six-component-transaction'
        with(O/'actual-updater-transactions.private.log').open('w',encoding='utf-8')as trace,contextlib.redirect_stdout(trace):m.apply_update(A,bundle,manifest)
        latest=J(A/'UserData/OriginalPublicUpdates/latest.json');assert latest['ready']and latest['newReleaseSHA256']==scope['candidateAdaptedR39SHA256']
        row=m.owned_ready(A,scope['candidateAdaptedR39SHA256']);m.health(A,row)
        native_plan=m.native_plan_runtime_ready(A,row)
        assert native_plan['installedAndRuntimeClassCopyMatched']and native_plan['candidatePlanClassSHA256']==m.R39_PLAN_ROW['sha256']
        dump(O/'candidate-plan-runtime-ready.json',native_plan)
        phase='candidate-398-schema-snapshot';assert schema_snapshot('after-update',row)==schema_before
        phase='actual-candidate-gzip-static';static=verify_candidate_static()
        dump(O/'candidate-static-HTTP.json',{'passed':True,'checks':static,'actualOwnedGatewayHTTP':True,'actualIISTLS':False})
        print('OWN_ACTUAL_UPDATE_SIX_COMPONENTS_398_SCHEMA_AND_GZIP_PASSED',flush=True)
        phase='actual-candidate-normal-role-six-relations-29-cases'
        native_ui_failure=None
        try:
            native_ui=verify_native_candidate(row)
            print('OWN_FINAL_R40_NATIVE_29_CASES_WITH_ALL_SIX_RELATIONS_AND_DELETED_DETAIL_PASSED',flush=True)
        except BaseException as error:
            native_ui_failure={'type':type(error).__name__,'message':str(error)if isinstance(error,AssertionError)else'OWN_BROWSER_FAILED_SEE_SCOPED_DIAGNOSTIC'}
            dump(O/'candidate-native-ui-failure.json',native_ui_failure)
            print('OWN_NATIVE_UI_FAILED_PROCEEDING_TO_ACTUAL_ROLLBACK_AND_NORMAL_STOP',flush=True)
        phase='actual-rollback-latest-six-component-transaction'
        with(O/'actual-updater-transactions.private.log').open('a',encoding='utf-8')as trace,contextlib.redirect_stdout(trace):m.rollback_latest(A)
        assert sha(A/'release-manifest.json')==old
        row=m.owned_ready(A,old);m.health(A,row,guarded=False)
        assert m.native_plan_runtime_ready(A,row)is None and not(A/m.R39_PLAN_CLASS).exists(),'ROLLBACK_MUST_RESTORE_PLAN_CLASS_ABSENCE'
        phase='rollback-398-schema-snapshot';assert schema_snapshot('after-rollback',row)==schema_before
        print('OWN_ACTUAL_ROLLBACK_SIX_COMPONENTS_AND_398_SCHEMA_PASSED',flush=True)
        phase='final-normal-stop';normal_stop_every_owned_process()
        assert len(processes)==3 and len(terminal)==3
        for item in terminal:
            assert item['controllerExitCode']==0 and item['receipt']['normalOwnedShutdown']
            assert set(item['receipt']['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}
            assert all(code==0 for code in item['receipt']['exitCodesBeforeJobClose'].values())
        phase='restore-original-G-code-and-pointers';restore_original();restored=True
        assert native_ui_failure is None,'OWN_NATIVE_UI_FAILED_AFTER_SAFE_ACTUAL_ROLLBACK_AND_RESTORE'
except BaseException as error:
    failure={'type':type(error).__name__,'phase':phase,
      'message':str(error)if isinstance(error,(AssertionError,ValueError))else'OWN_LIFECYCLE_FAILED_INSPECT_SCOPED_STATE',
      'frames':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}for f in traceback.extract_tb(error.__traceback__)]}
    dump(O/'failure.json',failure)
finally:
    if not restored:
        # Never restore code under a running controller. If apply did not finish
        # rolling code back, retain the baseline/attempt and report it explicitly.
        normal_stop_every_owned_process()
        if baseline_applied:
            try:restore_original();restored=True
            except BaseException as e:dump(O/'restore-refused.json',{'type':type(e).__name__,'message':str(e),'runningProcessesTerminated':False})
    dump(O/'terminal.json',{'failure':failure,'allOwnedControllerHandlesTerminal':all(v['process'].poll()is not None for v in processes),
      'controllers':terminal,'originalGCodeAndPointersRestored':restored,'forceTerminationUsed':False,
      'actualEvents':actual_events,'actualIISTLSNotTested':True})
assert failure is None and restored,'OWN_UNIFIED_LIFECYCLE_NOT_PASSED'
proof={'baselineVariant':'R37','candidatePlanClassInstalledAndActualRuntimeBytesMatched':True,'rollbackRestoredPlanClassAbsence':True,'passed':True,'candidateUpdaterSourceSHA256':sha(S),'actualApplyUpdateFunctionExecuted':True,
 'actualRollbackLatestFunctionExecuted':True,'realSixComponentControllersStarted':3,
 'allThreeNormalZeroAndActualDescendantsZero':True,'original398ModelsUnchangedAcrossUpdateAndRollback':True,
 'candidateGatewayGzipAndDecodedSHAActualPassed':True,'loopbackHTTPIngressAdapterUsed':True,
 'loadBundleOnlyTargetAndGatewayAndPrivateManifestPointersAdapted':True,
 'identityHealthNormalStopLaunchBackupReplaceRestoreAndRollbackBodiesNotStubbed':True,
 'actualIISHTTPSOrPublicVerified':False,'actualNormalRolePlanSixRelationsExerciseAndDeletedDetail29CasesPassed':True,
 'updaterReceiptTLSLabelNotAcceptedAsTLSProof':True,'originalGCodeConfigurationAndPointersRestored':True,
 'databaseCopiedOrReplaced':False,'publicFormal18891Scene8767OrDesktopTouched':False,'fullCloneReady':False}
dump(D/'verified-lifecycle-r374.json',proof);print(json.dumps(proof),flush=True)
