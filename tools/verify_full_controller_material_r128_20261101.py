"""Run the exact six-component controller using only the prepared synthetic fixture."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,socket,subprocess,sys,time,traceback

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');app=R/'_f/Application'
prepared_base=R/'work/event_delivery_consistency_20261030/full-controller-r127'
base=R/'work/event_delivery_consistency_20261030/full-controller-r128';base.mkdir(exist_ok=True)
assert not(app.parent/'user-manual-protected.json').exists(),'USER_MANUAL_ROOT_MUST_NOT_BE_AUTOMATIC_TEST_FIXTURE'
parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='r1');parser.add_argument('--variant',choices=['original','candidate'],default='original');options=parser.parse_args()
schema_base=prepared_base
if options.variant=='candidate':prepared_base=base/'candidate-install-r1'
assert re.fullmatch(r'r[1-9][0-9]{0,3}',options.attempt)
root=base/options.attempt;assert not root.exists();root.mkdir()
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,value):p.write_text(json.dumps(value,indent=2),encoding='utf-8')
prepared=read(prepared_base/'controller-fixture-ready.json');assert not prepared['wholeControllerActuallyStarted']
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
      '--qa-seconds','480','--callback-overlay',str(app/'payload/callback-overlay/20261026-password-identity/manifest.json'),
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
        checks['actualR24WorkflowGuardRuntimePinsPassed']=m.workflow_ready(app,row) is not None
        if options.variant=='candidate':
            own_candidate=read(base/'material-excel-candidate-r1/candidate.json')
            for relative,pin in own_candidate['classFiles'].items():
                m.check_file(Path(row['run'])/'b/classes',relative,pin['sha256'],pin['bytes'])
            checks['allThreeMaterialControllerAndHelperRuntimeClassesPinned']=True

        checks.update(actualSixComponentsReady=True,anonymousAuthenticationAndOriginalEightReportsPassed=True,
                      nativeSessionReportPassed=m.native_session_ready(app,row)is not None,
                      asyncMetadataReportPassed=m.async_ready(app,row)is not None)
        config=read(app/'private/server-configuration.json');fake_password=config['seedRootPassword'];config=None
        reader=read(schema_base/'schema-reader.json');identity=read(app/'UserData/OriginalServer/installation.json')
        if options.attempt=='r1':
            classes=root/'material-classes';classes.mkdir();javac=app/'runtime/jdk17/bin/javac.exe'
            java_source=R/'Application/tools/java/material_full_controller_r1/OwnMaterialPortalMenusFixture.java'
            compiled=subprocess.run([str(javac),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(java_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert compiled.returncode==0,'OWN_MATERIAL_MENU_COMPILE_FAILED'
            driver=next((app/'payload/business/lib').glob('mysql-connector-*.jar'))
            seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnMaterialPortalMenusFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert seeded.returncode==0,'OWN_MATERIAL_MENU_SEED_FAILED'
        else:
            prior=read(base/'r1/material-browser/failure.json')
            assert any(x.get('ownUserMatched')and x.get('materialMenuReturned')for x in prior['http']),'OWN_MENUS_NOT_PREPARED'
        own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');assert own['credentialsSynthetic']
        wire={'base':'http://127.0.0.1:'+str(port),'account':'own_operator_a','password':fake_password,'expectedUserId':own['accounts']['own_operator_a']['id'],'syntheticNormalUser':True,'variant':options.variant}
        phase='actual-normal-role-material-browser'
        browser_source=R/'Application/tools/verify_full_controller_material_browser_r128_20261101.mjs'
        with(root/'material-browser.private.log').open('wb')as browserlog:
            browser=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(browser_source),root.as_posix()],stdin=subprocess.PIPE,stdout=browserlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            browserjob=j.OwnedWindowsJob(browser);dump(root/'material-browser-started.json',{'pid':browser.pid,'sourceSHA256':sha(browser_source)})
            browser.communicate(json.dumps(wire).encode());wire.clear()
            while browserjob.active_processes():time.sleep(.2)
            browserjob.close()
        fake_password=None
        assert browser.returncode==0,'OWN_FULL_MATERIAL_BROWSER_FAILED'
        checks['actualNormalRoleMaterialBrowserPassed']=True
        config=read(app/'private/server-configuration.json');password=config['seedRootPassword'];config=None
        reader=read(schema_base/'schema-reader.json')
        identity=read(app/'UserData/OriginalServer/installation.json')
        result=subprocess.run([reader['java'],'-Xmx128m','-cp',reader['classpath'],'OwnControllerSchemaSnapshot',
                               str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),
                               str(schema_base/'original-table-names.txt'),str(root/'schema-after.json')],
                              input=password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        password=None
        assert result.returncode==0,'OWN_CONTROLLER_SCHEMA_AFTER_FAILED'
        assert read(schema_base/'schema-before.json')==read(root/'schema-after.json'),'ORIGINAL_398_MODELS_CHANGED'
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
proof={'schema':'xnby.r128.full-controller-material.v1','allPassed':True,'exactCandidateControllerAndJobActuallyExecuted':True,
       'wholeSixComponentControllerActuallyExecuted':True,'allSixComponentsNormallyExitedZero':True,
       'controllerNormallyExitedZero':True,'allActualDescendantsExitedBeforeOuterJobClosed':True,'forceTerminationUsed':False,
       'actualTenReadinessChecksPassed':True,'checks':checks,'original398DefinitionsUnchanged':True,
       'syntheticConfigAndDataIdentityUsed':True,'actualPublicPrivateConfigIdentityOrIISOrTLSPassed':False,
       'controllerSHA256':prepared['controllerSHA256'],'jobSHA256':prepared['jobSHA256'],'updaterSHA256':prepared['updaterSHA256'],
       'normalLoggedInBrowserAndCompleteNangangBusinessAcceptancePassed':False,'publicOrFormalChanged':False}
dump(root/'result.json',proof);print(json.dumps(proof),flush=True)
