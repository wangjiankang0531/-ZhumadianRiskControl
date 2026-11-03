"""Run the exact six-component controller using only the prepared synthetic fixture."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,socket,subprocess,sys,time,traceback

import ctypes
_own_memory=(ctypes.c_ulonglong*8)();_own_memory[0]=64
assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(_own_memory))
assert _own_memory[2]>4*1024**3,'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');app=R/'_g/Application'
schema_base=R/'work/event_delivery_consistency_20261030/full-controller-r131'
base=R/'work/event_delivery_consistency_20261030/full-controller-r163'
assert not(app.parent/'user-manual-protected.json').exists(),'USER_MANUAL_ROOT_MUST_NOT_BE_AUTOMATIC_TEST_FIXTURE'
parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='r1');parser.add_argument('--variant',choices=['original','candidate','combined'],default='original');parser.add_argument('--event-dictionaries',action='store_true');parser.add_argument('--closed-readback-only',action='store_true');parser.add_argument('--return-existing-pending',action='store_true');parser.add_argument('--resubmit-returned',action='store_true');parser.add_argument('--completed-addsign-readback',action='store_true');options=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',options.attempt)
root=base/options.attempt;assert not root.exists();root.mkdir(parents=True)
(root/'actual-host-source.py').write_bytes(Path(__file__).read_bytes())
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,value):p.write_text(json.dumps(value,indent=2),encoding='utf-8')
prepared_base=R/'work/event_delivery_consistency_20261030/full-controller-r135/candidate-install-r2'
if options.variant=='candidate':prepared_base=base/('prepared-'+options.attempt)
if options.variant=='combined':prepared_base=base/('prepared-'+options.attempt)
if options.closed_readback_only:prepared_base=base/'closed-readback-r1'
(root/'own-serial-definition.json').write_bytes((prepared_base/'own-serial-definition.json').read_bytes())
if options.closed_readback_only or options.return_existing_pending or options.resubmit_returned or options.completed_addsign_readback:(root/'workflow-context.private.json').write_bytes((prepared_base/'workflow-context.private.json').read_bytes())
prepared=read(prepared_base/'controller-fixture-ready.json');assert not prepared['wholeControllerActuallyStarted']
assert prepared['syntheticConfigurationAndIdentityOnly']and prepared['databasePreparedAndNormallyStopped']
assert sha(app/'release-manifest.json')==prepared['releaseSHA256']
history_scope=read(prepared_base/'history-runtime-scope.json');assert history_scope['onlyOwnedSyntheticG']
for n,pin in history_scope['newFiles'].items():
    if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']
frontend_scope=read(prepared_base/'frontend-scope.json')
for n,pin in frontend_scope['newFiles'].items():assert sha(app/n)==pin['sha256']
for name,key in [('serve_original_server_release.py','controllerSHA256'),('original_server_windows_job.py','jobSHA256'),('original_public_test_update.py','updaterSHA256')]:assert sha(app/'tools'/name)==prepared[key]
spec=importlib.util.spec_from_file_location('exact_graceful_updater',app/'tools/original_public_test_update.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('exact_graceful_job',app/'tools/original_server_windows_job.py')
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','PYTHONHOME','PYTHONPATH','MYSQL_PWD','MYSQL_HOME']}
process=None;job=None;row=None;failure=None;checks={};schema_process=None;schema_job=None;menu_visibility_requested=False;history_fault_requested=False
command="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='redis-server.exe' OR Name='minio.exe' OR Name='nginx.exe'\" | Where-Object { $_.ProcessId -ne "+str(os.getpid())+" -and ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
current_processes=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert current_processes.returncode==0 and current_processes.stdout.decode('utf-8-sig').strip()=='0','OWN_G_ALREADY_LIVE_DO_NOT_START_AGAIN'
def own_menu_visibility(mode):
    secret=read(app/'private/server-configuration.json')['seedRootPassword']
    args=[reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnPersonalWorkflowMenuVisibilityR201',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),mode,str(root)]
    completed=subprocess.run(args,input=secret.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);secret=None
    assert completed.returncode==0,'OWN_SYNTHETIC_MENU_VISIBILITY_'+mode.upper()+'_FAILED'
    result=json.loads(completed.stdout);assert result['passed']and not result['accountRoleOrGrantRowsChanged'];return result

def own_history_fault(mode):
    context=read(root/'workflow-context.private.json');assert context['syntheticDataOnly']
    secret=read(app/'private/server-configuration.json')['seedRootPassword']
    args=[reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnNativeHistoryFaultR201',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),str(root),mode,context['flowId'],context['taskId'],context['taskName']]
    completed=subprocess.run(args,input=secret.encode(),capture_output=True,timeout=45,env=env,creationflags=subprocess.CREATE_NO_WINDOW);secret=None
    if completed.returncode:dump(root/('own-history-fault-'+mode+'-diagnostic.json'),{'exitCode':completed.returncode,'codes':re.findall(r'OWN_HISTORY_FAULT_SQL:[0-9A-Z]+:[0-9]+',completed.stderr.decode('utf-8',errors='replace')),'rawStderrOrRowsExported':False})
    assert completed.returncode==0,'OWN_HISTORY_SQL_FAULT_'+mode.upper()+'_FAILED'
    result=json.loads(completed.stdout);assert result['passed']and result['onlyOwnSyntheticProcess']and not result['accountsOrSessionsRead'];return result

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
      '--callback-overlay-sha256',sha(app/'payload/callback-overlay/20261026-password-identity/manifest.json')]
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
        checks['actualR25MaterialRuntimePinsPassed']=m.material_ready(app,row) is not None
        checks['actualR26TeamMapperRuntimePinsPassed']=m.team_ready(app,row) is not None
        if options.variant=='combined':
            checks['actualRuntimePoolPolicyReady']=m.runtime_pool_ready(app,row) is not None
            assert checks['actualRuntimePoolPolicyReady']
        checks.update(actualSixComponentsReady=True,anonymousAuthenticationAndOriginalEightReportsPassed=True,
                      nativeSessionReportPassed=m.native_session_ready(app,row)is not None,
                      asyncMetadataReportPassed=m.async_ready(app,row)is not None)
        phase='verify-installed-native-history-hook'
        history_report=Path(row['platformRun'])/'before-addsign-history-ready.properties'
        history_properties=dict(line.split('=',1)for line in history_report.read_text(encoding='ascii').splitlines()if '='in line)
        assert history_properties['installed']=='true'and 1<=int(history_properties['factories'])<=4
        assert history_properties['originalEntityMapperAndServicePinned']=='true'and history_properties['originalTransactionAndConnectionUsed']=='true'
        assert history_properties['newDatasourceOrDDL']=='false'and history_properties['normalRoleUIAcceptanceProvenByStartup']=='false'
        dump(root/'native-history-ready.json',history_properties)
        checks['productionNativeServiceGateInstalled']=True
        phase='seed-only-own-resource-menus'
        own_config=read(app/'private/server-configuration.json');fake_password=own_config['seedRootPassword'];own_config=None
        reader=read(schema_base/'schema-reader.json');identity=read(app/'UserData/OriginalServer/installation.json')
        classes=root/'resource-fixture-classes';classes.mkdir();source=R/'Application/tools/java/duty_full_controller_r135/OwnDutyPortalMenusFixture.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_RESOURCE_MENU_COMPILE_FAILED'
        driver=next((app/'payload/business/lib').glob('mysql-connector-*.jar'))
        seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnDutyPortalMenusFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert seeded.returncode==0,'OWN_RESOURCE_MENU_SEED_FAILED'
        checks['onlyOwnNormalRoleDutyMenusPrepared']=True
        phase='only-own-workflow-menu-and-loopback-callback-fixtures'
        jackson=[]
        for prefix in ['jackson-core-','jackson-annotations-','jackson-databind-']:
            matches=list((app/'payload/business/lib').glob(prefix+'*.jar'));assert len(matches)==1;jackson.append(matches[0])
        cp=';'.join(map(str,[classes,driver,*jackson]))
        for class_name in ['OwnWorkflowPortalMenusFixture','OwnWorkflowCallbackEndpointFixture']:
            source=R/'Application/tools/java/workflow_serial_r154'/(class_name+'.java')
            compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(classes),str(source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_WORKFLOW_FIXTURE_COMPILE_FAILED'
            args=[reader['java'],'-Xmx128m','-cp',cp,class_name,str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')]
            if class_name=='OwnWorkflowCallbackEndpointFixture':args.append(str(row['businessPort']))
            seeded=subprocess.run(args,input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert seeded.returncode==0,'OWN_WORKFLOW_FIXTURE_SEED_FAILED'
        checks['onlyOwnWorkflowMenuAndPriorLoopbackCallbackPrepared']=True

        phase='seed-only-own-task-add-button-grants'
        add_source=R/'Application/tools/java/task_edit_full_controller_r146/OwnTaskEditPortalMenusFixture.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(add_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_TASK_ADD_MENU_COMPILE_FAILED'
        seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnTaskEditPortalMenusFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert seeded.returncode==0 and seeded.stdout.strip()==b'OWN_SYNTHETIC_TASK_ADD_MENU_AND_TWO_GROUPS_READY','OWN_TASK_ADD_MENU_SEED_FAILED'
        checks['onlyOwnSyntheticTaskAddButtonAndTwoRoleGrantsPrepared']=True

        phase='seed-only-own-sex-dictionary'
        dictionary_source=R/'Application/tools/java/team_full_controller_r133/OwnTeamDictionaryFixture.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(dictionary_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_TEAM_DICTIONARY_COMPILE_FAILED'
        seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnTeamDictionaryFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        if seeded.returncode:
            marker='OWN_DICTIONARY_DIAGNOSTIC:'
            for line in seeded.stdout.decode('utf-8',errors='replace').splitlines():
                if line.startswith(marker):dump(root/'dictionary-diagnostic.json',json.loads(line[len(marker):]))
        assert seeded.returncode==0,'OWN_TEAM_DICTIONARY_SEED_FAILED'
        checks['onlyFourOwnSexDictionaryRowsPrepared']=True

        phase='seed-only-own-duty-job-dictionary'
        duty_dictionary=R/'Application/tools/java/duty_full_controller_r135/OwnDutyDictionaryFixture.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(duty_dictionary)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_DUTY_JOB_DICTIONARY_COMPILE_FAILED'
        seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnDutyDictionaryFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        if seeded.returncode:
            marker='OWN_DICTIONARY_DIAGNOSTIC:'
            for line in seeded.stdout.decode('utf-8',errors='replace').splitlines():
                if line.startswith(marker):dump(root/'duty-dictionary-diagnostic.json',json.loads(line[len(marker):]))
        assert seeded.returncode==0,'OWN_DUTY_JOB_DICTIONARY_SEED_FAILED'
        checks['exactSyntheticRootAndOnlyTwoOwnDutyJobDictionaryRowsPrepared']=True
        if options.event_dictionaries:
            phase='seed-only-three-own-event-dictionaries'
            source=R/'Application/tools/java/duty_capacity_r136/OwnDutyEventDictionaryFixture.java'
            compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert compiled.returncode==0,'OWN_EVENT_DICTIONARY_COMPILE_FAILED'
            seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnDutyEventDictionaryFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            marker='OWN_EVENT_DICTIONARY_READY:';summaries=[json.loads(line[len(marker):])for line in seeded.stdout.decode('utf-8',errors='replace').splitlines()if line.startswith(marker)]
            if seeded.returncode:
                marker='OWN_DICTIONARY_DIAGNOSTIC:'
                for line in seeded.stdout.decode('utf-8',errors='replace').splitlines():
                    if line.startswith(marker):dump(root/'event-dictionary-diagnostic.json',json.loads(line[len(marker):]))
            assert seeded.returncode==0 and len(summaries)==1,'OWN_EVENT_DICTIONARY_SEED_FAILED'
            summary=summaries[0];assert set(summary)=={'typesCreated','typesReused','dataCreated'} and all(type(v)is int and 0<=v<=3 for v in summary.values()) and summary['typesCreated']+summary['typesReused']==3
            dump(root/'event-dictionary-fixture-counts.json',summary)
            checks['onlyThreeOwnEventDictionaryKindsPrepared']=True

        phase='reserve-own-readonly-schema-connection'
        schema_source=R/'Application/tools/java/duty_full_controller_r135/OwnDutySchemaSnapshot.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(schema_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_DUTY_SCHEMA_READER_COMPILE_FAILED'
        schema_process=subprocess.Popen([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnDutySchemaSnapshot',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),str(schema_base/'original-table-names.txt'),str(root/'schema-after.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        schema_job=j.OwnedWindowsJob(schema_process);schema_process.stdin.write(fake_password.encode());schema_process.stdin.flush()
        deadline=time.monotonic()+25
        while not(root/'schema-after.json.ready.json').exists():
            assert schema_process.poll()is None,'OWN_SCHEMA_OBSERVER_EXITED_BEFORE_READY'
            assert time.monotonic()<deadline,'OWN_SCHEMA_OBSERVER_READY_TIMEOUT'
            time.sleep(.05)
        assert schema_process.poll()is None
        dump(root/'schema-observer-started.json',{'pid':schema_process.pid,'readOnlyMetadataAndNumericCapacityOnly':True,'sourceSHA256':sha(schema_source),'captureAfterBrowser':True})
        phase='native-two-level-workflow-browsers'
        own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');assert own['credentialsSynthetic']
        browser_source=Path(__file__).parent/'verify_native_personal_workflow_r201_20261103.mjs'
        actual_browser=root/'actual-browser-source.mjs';actual_browser.write_bytes(browser_source.read_bytes());browser_passed=True
        assert options.attempt in ['r101'] and options.variant=='combined' and not(options.closed_readback_only or options.return_existing_pending or options.resubmit_returned)
        add_type='1'
        phases=[('operator','own_operator_a','operator',False,False),('operator-disposal','own_operator_a','operator',False,False),('reviewer-addsign','own_reviewer_b','reviewer',False,False),('operator-added','own_operator_a','reviewer',True,False)]
        if add_type=='1':phases.append(('reviewer-after-added','own_reviewer_b','reviewer',True,False))
        phases += [('reviewer-final','own_operator_a','reviewer',True,False),('reviewer-handled-readback','own_reviewer_b','reviewer',False,False),('operator-completed-readback','own_operator_a','operator',False,False)]
        if options.completed_addsign_readback:
            assert options.attempt=='r74'
            phases=[('operator-completed-readback','own_operator_a','operator',False,False)]
        state_source=R/'Application/tools/java/workflow_serial_r163/OwnReturnWorkflowReadback.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',str(driver),'-d',str(classes),str(state_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        assert compiled.returncode==0,'OWN_SERIAL_STATE_READER_COMPILE_FAILED'
        menu_source=Path(__file__).parent/'OwnPersonalWorkflowMenuVisibilityR201.java'
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(menu_source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_MENU_VISIBILITY_FIXTURE_COMPILE_FAILED'
        menu_visibility_requested=True;checks['onlyOwnWorkflowModulesHiddenBeforeNormalLogin']=own_menu_visibility('hide')['passed']
        compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(Path(__file__).parent/'OwnNativeHistoryFaultR201.java')],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW);assert compiled.returncode==0,'OWN_HISTORY_FAULT_HELPER_COMPILE_FAILED'
        for label,account,actor,audit,readback in phases:
            wire={'base':'http://127.0.0.1:'+str(port),'actor':actor,'phaseName':label,'account':account,'password':fake_password,'expectedWirePassword':own['wirePassword'],'expectedUserId':own['accounts'][account]['id'],'syntheticNormalUser':True,'configureTaskForm':label=='operator','approveOnce':audit,'rejectOnce':False,'addsignOnce':label=='reviewer-addsign','addsignType':add_type,'readbackOnly':readback,'expectedAfterAuditStatus':'1','requireMissingWorkflowMenus':True,'handledReadback':label=='reviewer-handled-readback'}
            wire['expectNativeHistorySQLFault']=label=='reviewer-addsign'
            if label=='reviewer-addsign':
                history_fault_requested=True;checks['ownHistorySQLTriggerArmedBeforeAssignedReviewerPost']=own_history_fault('arm')['passed']
            with(root/('workflow-browser-'+label+'.private.log')).open('wb')as browserlog:
                browser=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(actual_browser),root.as_posix()],stdin=subprocess.PIPE,stdout=browserlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                browserjob=j.OwnedWindowsJob(browser);dump(root/('workflow-browser-'+label+'-started.json'),{'pid':browser.pid,'sourceSHA256':sha(actual_browser),'syntheticNormalUser':True});browser.stdin.write(json.dumps(wire).encode());browser.stdin.close();wire.clear()
                deadline=time.monotonic()+180;fault_observed=False
                while browser.poll()is None:
                    if label=='reviewer-addsign'and not fault_observed and(root/'native-history-browser-fault-observed.json').exists():
                        observed=read(root/'native-history-browser-fault-observed.json');assert observed['oneFailedPost']and observed['opinionAndSelectedUserRetained']
                        checks['nativeSQLFaultAllEightScopedTableFingerprintsIdentical']=own_history_fault('verify-drop')['allScopedDataFingerprintsUnchanged'];fault_observed=True
                        dump(root/'native-history-fault-removed-retry-ready.json',{'passed':True,'onlyExactOwnTriggerRemoved':True,'nativeTransactionAndEngineRowsUnchanged':True})
                    assert time.monotonic()<deadline,'OWN_NATIVE_BROWSER_FAULT_HANDSHAKE_TIMEOUT'
                    time.sleep(.1)
                if label=='reviewer-addsign':assert fault_observed,'OWN_NATIVE_SQL_FAULT_NOT_OBSERVED'
                browser.wait()
                while browserjob.active_processes():time.sleep(.2)
                browserjob.close()
            terminal=read(root/('workflow-browser-'+label+'/browser-terminal.json'));assert terminal['normalBrowserClosed']and not terminal['forceTerminationUsed'],'OWN_SERIAL_WORKFLOW_BROWSER_ABNORMAL_EXIT'
            if browser.returncode!=0:browser_passed=False;break
            context=read(root/'workflow-context.private.json');definition=read(root/'own-serial-definition.json');observe=label in ['reviewer-addsign','operator-added','reviewer-after-added'];ended=None if observe else label in ['reviewer-final','reviewer-handled-readback','operator-completed-readback'];business_status='observe'if observe else('2'if label=='operator'else'1');pending_expected='observe'if observe else('0'if ended else'1');ended_expected='observe'if observe else('true'if ended else'false')
            state_args=[reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnReturnWorkflowReadback',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),context['flowId'],context['taskId'],definition['versionId'],context['taskName'],definition['templateBody']['enCode'],definition['templateId'],business_status,pending_expected,ended_expected]
            state_process=subprocess.Popen(state_args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW);state_job=j.OwnedWindowsJob(state_process);state_out,state_err=state_process.communicate(input=fake_password.encode())
            while state_job.active_processes():time.sleep(.1)
            state_job.close()
            if state_process.returncode:
                dump(root/('state-'+label+'-diagnostic.json'),{'exitCode':state_process.returncode,'codes':re.findall(r'OWN_(?:SQL_DIAGNOSTIC:[0-9A-Z]+:[0-9]+:[A-Z_]+|SERIAL_READBACK_SCOPE_REJECTED:[A-Z_]+)',state_err.decode('utf-8',errors='replace'))})
            assert state_process.returncode==0,'OWN_SERIAL_STATE_READER_FAILED'
            observation={}
            for line in state_out.decode('utf-8').splitlines():
                parts=line.split(':');assert len(parts)==3 and parts[0]=='OWN_PROOF';observation[parts[1]]=parts[2]=='true'if parts[2]in ['true','false']else int(parts[2])
            observation.update(phase=label,expectedBusinessStatus=business_status,expectedEngineEnded=ended,ownSyntheticOnly=True,readOnlyTransactionRolledBack=True,rawRowsOrCredentialsExported=False,normalReaderExitCode=0)
            dump(root/('state-'+label+'.json'),observation);assert observation['passed'],'OWN_SERIAL_BUSINESS_AND_ENGINE_CHECKPOINT_FAILED'

        fake_password=None;checks['actualCreateFeedbackAddsignAndNativeSequenceBrowsersPassed']=browser_passed and not options.closed_readback_only;checks['actualPreviouslyClosedAttachmentAndNativeAnchorBrowserReadbackPassed']=browser_passed and options.closed_readback_only
        phase='verify-original-398-models'
        _,schema_stderr=schema_process.communicate(input=b'C',timeout=40)
        if schema_process.returncode:
            marker='OWN_DUTY_SCHEMA_DIAGNOSTIC:'
            for line in schema_stderr.decode('utf-8',errors='replace').splitlines():
                if line.startswith(marker):dump(root/'schema-reader-diagnostic.json',json.loads(line[len(marker):]))
        assert schema_process.returncode==0,'OWN_CONTROLLER_SCHEMA_AFTER_FAILED'
        assert read(schema_base/'schema-before.json')==read(root/'schema-after.json'),'ORIGINAL_398_MODELS_CHANGED'
        checks['original398DefinitionsUnchanged']=True
        if options.variant in ['candidate','combined']:
            phase='verify-runtime-connection-capacity'
            capacity=read(root/'schema-after.json.capacity.json')
            assert capacity['Connection_errors_max_connections']==0,'OWN_CAPACITY_CONNECTION_REFUSALS_OBSERVED'
            budget=read(Path(row['run'])/'connection-budget.json')
            assert capacity['maxConnections']==budget['mysqlMaxConnections'],'OWN_ACTUAL_MYSQL_BUDGET_MISMATCH'
            dump(root/'actual-connection-budget.json',budget)
            fresh_password=read(app/'private/server-configuration.json')['seedRootPassword']
            fresh=subprocess.Popen([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnDutySchemaSnapshot',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data'),str(schema_base/'original-table-names.txt'),str(root/'schema-fresh-after.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            fresh_job=j.OwnedWindowsJob(fresh);fresh.communicate(input=fresh_password.encode()+b'C');fresh_password=None
            while fresh_job.active_processes():time.sleep(.1)
            fresh_job.close()
            assert fresh.returncode==0 and read(root/'schema-fresh-after.json')==read(schema_base/'schema-before.json'),'OWN_FRESH_METADATA_CONNECTION_FAILED'
            assert read(root/'schema-fresh-after.json.capacity.json')['Connection_errors_max_connections']==0
            checks.update(connectionCapacityWithoutRefusals=True,freshPostBrowserMetadataConnectionPassed=True)

        assert browser_passed,'OWN_NATIVE_SERIAL_WORKFLOW_BROWSER_FAILED'
        opinion=read(root/'workflow-browser-operator-completed-readback/addsign-sequence-and-opinion-observation.json')
        assert opinion['independentAddsignOpinionRetained']and opinion['exactlyOneTimedOriginalActorModeCorrectAddsignRecord']and not opinion['opinionRetentionGapRemains'],'NATIVE_BEFORE_ADDSIGN_INDEPENDENT_OPINION_NOT_RETAINED'
        checks['normalSeparateModuleOriginalServiceGateAndNativeRoleOpinionReadbackPassed']=True
        dump(root/'ready-checks.json',checks)
        print('OWN_CONTROLLER_REAL_READY_HEALTH_TEN_REPORTS_AND_398_MODELS_PASSED',flush=True)
    except BaseException as error:
        failure=type(error).__name__
        dump(root/'failure.json',{'type':failure,'phase':phase,'message':str(error)if isinstance(error,AssertionError)else'OWN_CONTROLLER_CHECK_FAILED','frames':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}for f in traceback.extract_tb(error.__traceback__)]})
    finally:
        if history_fault_requested:
            try:checks['ownHistoryFaultTriggerRemoved']=own_history_fault('cleanup')['triggerRemoved']
            except BaseException as trigger_error:
                failure=failure or 'OwnHistoryFaultCleanupFailed';dump(root/'own-history-trigger-cleanup-failed.json',{'failed':True,'type':type(trigger_error).__name__})
        if menu_visibility_requested:
            try:checks['originalOwnedMenuModuleMarkersRestored']=own_menu_visibility('restore')['passed']
            except BaseException as menu_error:
                failure=failure or 'OwnMenuRestoreFailed';dump(root/'own-menu-restore-failed.json',{'failed':True,'type':type(menu_error).__name__,'noPublicOrAccountRowsOperated':True})
        if schema_process:
            if schema_process.poll()is None:
                try:schema_process.communicate(input=b'X',timeout=30)
                except subprocess.TimeoutExpired:
                    while schema_process.poll()is None:
                        print('OWN_SCHEMA_OBSERVER_STILL_LIVE_NO_FORCE',flush=True);time.sleep(2)
            if schema_job:
                while schema_job.active_processes():time.sleep(.1)
                schema_job.close()
            dump(root/'schema-observer-terminal.json',{'exitCode':schema_process.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False})
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
current=read(app/'UserData/OriginalServer/current-run.json')
if current['controllerPID']==process.pid:run_path=Path(current['run'])
else:
    matches=[p for p in(app/'UserData/OriginalServer/runs').glob('j*/receipt.json')if read(p)['controllerPID']==process.pid]
    assert len(matches)==1,'EXACT_OWN_CONTROLLER_RECEIPT_REQUIRED';run_path=matches[0].parent
assert run_path.resolve()==run_path and run_path.parent==app/'UserData/OriginalServer/runs'
receipt=read(run_path/'receipt.json');assert receipt['controllerPID']==process.pid;summary={k:receipt.get(k)for k in ['ready','failureType','failureStageMessage','normalOwnedShutdown',
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
proof={'schema':'xnby.r201.native-before-addsign-real-sql-fault-retry.v1','allPassed':True,'actualExecutedNativeBrowserPhases':len(phases),'continuedSamePriorCreateFeedbackInstance':options.return_existing_pending,'actualNativeCreateUploadFeedbackAddsignAndTargetApprovalPassed':True,'normalAllSixControllerAndBrowsersExitZeroAndActualDescendantsZero':True,'original398ModelsUnchanged':True,'connectionCapacityWithoutRefusals':checks['connectionCapacityWithoutRefusals'],'productCodeChanged':False,'onlyOwnDeclaredSeparateHistoryModuleTemporarilyInstalled':True,'productionServiceGateNotSimulated':True,'independentBeforeAddsignOpinionRetained':True,'newDatasourceOrDDL':False,'publicFormalOrDesktopChanged':False,'onlyOwnSyntheticConfigurationAndDataUsed':True,'resubmissionNotExecuted':not options.resubmit_returned,'actualAddsignAndRemainingReviewsCompleted':not options.completed_addsign_readback,'onlyPreviouslyCompletedAddsignReadbackExecuted':options.completed_addsign_readback,'addsignType':add_type,'originalNangangTemplateOrWholeAcceptanceClaimed':False,'fullCloneReady':False}
dump(root/'result.json',proof);print(json.dumps(proof),flush=True)
