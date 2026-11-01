"""Run the exact six-component controller using only the prepared synthetic fixture."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,socket,subprocess,sys,time,traceback

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');app=R/'_e/Application'
base=R/'work/event_delivery_consistency_20261030/full-controller-r123'
assert not(app.parent/'user-manual-protected.json').exists(),'USER_MANUAL_ROOT_MUST_NOT_BE_AUTOMATIC_TEST_FIXTURE'
parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='r1');parser.add_argument('--ui-phase',choices=['baseline','candidate'],default='baseline');parser.add_argument('--expect-empty-flow-rejection',action='store_true');parser.add_argument('--lists-only',action='store_true');parser.add_argument('--configure-task-form',action='store_true');parser.add_argument('--prepare-own-callback',action='store_true');parser.add_argument('--approve-once',action='store_true');parser.add_argument('--double-approve',action='store_true');parser.add_argument('--approval-resilience',action='store_true');parser.add_argument('--expect-state-label',action='store_true');parser.add_argument('--response-lost',action='store_true');parser.add_argument('--task-status-filter',action='store_true');parser.add_argument('--reconcile-read-failure',action='store_true');options=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',options.attempt)
assert not options.double_approve or options.approve_once
assert not options.approval_resilience or options.double_approve
assert not options.response_lost or options.approve_once and not options.approval_resilience
assert not options.reconcile_read_failure or options.response_lost
root=base/options.attempt;assert not root.exists();root.mkdir()
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,value):p.write_text(json.dumps(value,indent=2),encoding='utf-8')
prepared=read(base/'controller-fixture-ready.json');assert not prepared['wholeControllerActuallyStarted']
assert prepared['syntheticConfigurationAndIdentityOnly']and prepared['databasePreparedAndNormallyStopped']
assert sha(app/'release-manifest.json')==prepared['releaseSHA256']
for name,key in [('serve_original_server_release.py','controllerSHA256'),('original_server_windows_job.py','jobSHA256'),('original_public_test_update.py','updaterSHA256')]:assert sha(app/'tools'/name)==prepared[key]
spec=importlib.util.spec_from_file_location('exact_graceful_updater',app/'tools/original_public_test_update.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('exact_graceful_job',app/'tools/original_server_windows_job.py')
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','PYTHONHOME','PYTHONPATH','MYSQL_PWD','MYSQL_HOME']}
process=None;job=None;row=None;failure=None;checks={}
phase='created';http_observations=[]
original_http_check=m.http_check
def observed_http_check(port,path):
    status,body=original_http_check(port,path)
    stripped=body.lstrip();http_observations.append({'path':path,'status':status,'bytes':len(body),'jsonLike':stripped.startswith((b'{',b'[')),'htmlLike':stripped.lower().startswith((b'<!doctype',b'<html'))})
    dump(root/'http-response-metadata.json',http_observations)
    return status,body
m.http_check=observed_http_check
args=[str(app/'runtime/python/python.exe'),'-I','-B',str(app/'tools/serve_original_server_release.py'),
      '--application',str(app),'--release-manifest-sha256',prepared['releaseSHA256'],'--gateway-port',str(port),
      '--qa-seconds','600','--callback-overlay',str(app/'payload/callback-overlay/20261026-password-identity/manifest.json'),
      '--callback-overlay-sha256','91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb']
with (root/'controller.private.log').open('wb')as log:
    try:
        process=subprocess.Popen(args,cwd=app,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(process)
        dump(root/'controller-started.json',{'pid':process.pid,'gatewayPort':port,'exactCandidateControlBytes':True,
             'syntheticConfigurationAndDataOnly':True,'newJobLimitFlags':job.limit_flags})
        print('OWN_EXACT_SIX_COMPONENT_CONTROLLER_STARTED',flush=True)
        deadline=time.monotonic()+570;next_message=0
        while time.monotonic()<deadline:
            current=app/'UserData/OriginalServer/current-run.json'
            if current.exists():
                phase='reading-current-run';candidate=read(current)
                if candidate.get('controllerPID')==process.pid and candidate.get('ready'):
                    row=candidate;break
            assert process.poll()is None,'OWN_CONTROLLER_EXITED_BEFORE_READY'
            if time.monotonic()>next_message:
                print('OWN_CONTROLLER_WAITING_FOR_REAL_READY',flush=True);next_message=time.monotonic()+20
            time.sleep(.2)
        assert row is not None,'OWN_CONTROLLER_READY_TIMEOUT'
        assert set(row['children'])=={'store','mysql','redis','platform','business','gateway'}
        phase='checking-gateway-health';m.health(app,row,gateway_port=port)
        checks.update(actualSixComponentsReady=True,anonymousAuthenticationAndOriginalEightReportsPassed=True,
                      nativeSessionReportPassed=m.native_session_ready(app,row)is not None,
                      asyncMetadataReportPassed=m.async_ready(app,row)is not None)
        own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');assert own['credentialsSynthetic']
        config=read(app/'private/server-configuration.json');fake_password=config['seedRootPassword'];config=None
        if options.prepare_own_callback:
            callback_reader=read(base/'callback-reader.json');identity=read(app/'UserData/OriginalServer/installation.json')
            callback_result=subprocess.run([callback_reader['java'],'-Xmx128m','-cp',callback_reader['classpath'],'OwnWorkflowCallbackEndpointFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),str(row['businessPort'])],input=fake_password.encode(),capture_output=True,timeout=30,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert callback_result.returncode==0,'OWN_EXACT_CALLBACK_BINDING_FAILED'
            dump(root/'own-callback-binding.json',json.loads(callback_result.stdout.decode('utf-8')))
        browser_source=root/'workflow-browser-source.mjs';browser_source.write_bytes((R/'Application/tools/verify_native_approval_portal_browser_20261101.mjs').read_bytes())
        phase='real-native-workflow-pages'
        actors=[('operator','own_operator_a')]if options.expect_empty_flow_rejection else [('operator','own_operator_a'),('reviewer','own_reviewer_b')]
        if options.approve_once:
            assert not options.expect_empty_flow_rejection and not options.lists_only
            actors.append(('operator-readback','own_operator_a'))
        for actor,account in actors:
            wire={'base':'http://127.0.0.1:'+str(port),'actor':'operator'if actor=='operator-readback'else actor,'account':account,'password':fake_password,'expectedWirePassword':own['wirePassword'],'expectedUserId':own['accounts'][account]['id'],'syntheticNormalUser':True,'expectEmptyFlowRejection':options.expect_empty_flow_rejection,'listsOnly':options.lists_only,'configureTaskForm':options.configure_task_form,'approveOnce':options.approve_once and actor=='reviewer','readbackOnly':actor=='operator-readback','doubleClick':options.double_approve,'approvalResilience':options.approval_resilience and actor=='reviewer','expectStateLabel':options.expect_state_label,'responseLost':options.response_lost and actor=='reviewer','taskStatusFilter':options.task_status_filter and actor=='operator','reconcileReadFailure':options.reconcile_read_failure and actor=='reviewer'}
            with(root/('workflow-browser-'+actor+'.private.log')).open('wb')as browserlog:
                browser=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(browser_source),root.as_posix()],stdin=subprocess.PIPE,stdout=browserlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                browserjob=j.OwnedWindowsJob(browser);dump(root/('workflow-browser-'+actor+'-started.json'),{'pid':browser.pid,'syntheticNormalUser':True,'sourceSHA256':sha(browser_source)})
                browser.communicate(json.dumps(wire).encode('utf-8'));wire.clear()
                while browserjob.active_processes():time.sleep(.2)
                browserjob.close()
            assert browser.returncode==0,'REAL_NATIVE_WORKFLOW_UI_FAILED_'+actor
        fake_password=None;checks['emptyFlowRejectedBeforeBusinessSave'if options.expect_empty_flow_rejection else'realNativeOperatorAndReviewerWorkflowListsPassed'if options.lists_only else'realNativeOperatorAndReviewerWorkflowPagesPassed']=True
        if options.approve_once:checks['actualNativeUIApprovalCallbackAndInitiatorReadbackPassed']=True
        config=read(app/'private/server-configuration.json');password=config['seedRootPassword'];config=None
        reader=read(base/'schema-reader.json')
        identity=read(app/'UserData/OriginalServer/installation.json')
        result=subprocess.run([reader['java'],'-Xmx128m','-cp',reader['classpath'],'OwnControllerSchemaSnapshot',
                               str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),
                               str(base/'original-table-names.txt'),str(root/'schema-after.json')],
                              input=password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        password=None
        known=re.search(rb'OWN_SCHEMA_CHECK_FAILED:([A-Za-z0-9_]+)',result.stderr)
        dump(root/'schema-reader-outcome.json',{'exitCode':result.returncode,'stdoutBytes':len(result.stdout),'stderrBytes':len(result.stderr),'knownFailureClass':known[1].decode('ascii')if known else None,'classNotFound':b'ClassNotFoundException'in result.stderr,'memoryStartupFailure':b'OutOfMemoryError'in result.stderr or b'Could not reserve'in result.stderr,'rawLogOrCredentialExported':False})
        assert result.returncode==0,'OWN_CONTROLLER_SCHEMA_AFTER_FAILED'
        assert read(base/'schema-before.json')==read(root/'schema-after.json'),'ORIGINAL_398_MODELS_CHANGED'
        checks['original398DefinitionsUnchanged']=True
        dump(root/'ready-checks.json',checks)
        print('OWN_CONTROLLER_REAL_READY_HEALTH_TEN_REPORTS_AND_398_MODELS_PASSED',flush=True)
    except BaseException as error:
        failure=type(error).__name__
        dump(root/'failure.json',{'type':failure,'phase':phase,'message':str(error)if isinstance(error,AssertionError)else'OWN_CONTROLLER_CHECK_FAILED','frames':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}for f in traceback.extract_tb(error.__traceback__)]})
    finally:
        if process:
            # If ready was not reached, the controller still owns its startup/normal cleanup.
            current=app/'UserData/OriginalServer/current-run.json'
            if current.exists():
                candidate=read(current)
                if candidate.get('controllerPID')==process.pid:
                    run=Path(candidate['run']);assert run.parent==app/'UserData/OriginalServer/runs'
                    (run/'stop-requested.txt').write_text('OWN_NORMAL_STOP\n',encoding='ascii')
            while process.poll()is None:
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:print('OWN_CONTROLLER_NORMAL_SHUTDOWN_STILL_LIVE_NO_FORCE',flush=True)
            if job:
                while job.active_processes():
                    print('OWN_CONTROLLER_DESCENDANTS_STILL_LIVE_JOB_RETAINED',flush=True);time.sleep(2)
                job.close()
            dump(root/'controller-terminal.json',{'pid':process.pid,'exitCode':process.returncode,
                 'actualDescendantJobCountZeroBeforeClose':True,'forceTerminationUsed':False})
assert process is not None
receipts=[p for p in(app/'UserData/OriginalServer/runs').glob('j*/receipt.json')if read(p).get('controllerPID')==process.pid]
assert len(receipts)==1
receipt=read(receipts[0]);summary={k:receipt.get(k)for k in ['ready','failureType','failureStageMessage','normalOwnedShutdown',
    'allOwnedChildrenExited','exitCodesBeforeJobClose','forcedJobClosureComponents','jobAssignmentFailureComponents',
    'platformContextClosed','businessContextClosed']}
dump(root/'scoped-controller-receipt.json',summary)
if failure or process.returncode!=0:
    print(json.dumps({'passed':False,'checkFailure':failure,'controllerExitCode':process.returncode,'scopedReceipt':summary}))
    raise RuntimeError('WHOLE_CONTROLLER_NOT_PASSED')
assert receipt['normalOwnedShutdown']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']
assert not receipt['jobAssignmentFailureComponents']
assert set(receipt['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}
assert all(code==0 for code in receipt['exitCodesBeforeJobClose'].values())
assert receipt['platformContextClosed']and receipt['businessContextClosed']
proof={'schema':'xnby.r23.whole-graceful-controller-check.v1','allPassed':True,'exactCandidateControllerAndJobActuallyExecuted':True,
       'wholeSixComponentControllerActuallyExecuted':True,'allSixComponentsNormallyExitedZero':True,
       'controllerNormallyExitedZero':True,'allActualDescendantsExitedBeforeOuterJobClosed':True,'forceTerminationUsed':False,
       'actualTenReadinessChecksPassed':True,'checks':checks,'original398DefinitionsUnchanged':True,
       'syntheticConfigAndDataIdentityUsed':True,'actualPublicPrivateConfigIdentityOrIISOrTLSPassed':False,
       'controllerSHA256':prepared['controllerSHA256'],'jobSHA256':prepared['jobSHA256'],'updaterSHA256':prepared['updaterSHA256'],
       'normalLoggedInBrowserAndCompleteNangangBusinessAcceptancePassed':False,'publicOrFormalChanged':False}
dump(root/'result.json',proof);print(json.dumps(proof),flush=True)
