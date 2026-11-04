"""Normal synthetic login and read-only real pages; no business writes or callback rebinding."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time

R=Path('D:/Project/Zhumadian');G=R/'_g/Application';T=R/'Application/tools';V=Path(__file__).resolve().parent
W=R/'work/original-manager-full-lifecycle-r609/task-ui-r806'
P=R/'work/original-manager-full-lifecycle-r609/component-bootstrap-r850'
OUT=R/'work/bootstrap-browser-r850'
CHILDREN=[]
J=lambda p:json.loads(p.read_bytes())
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def props(p):return dict(line.split('=',1)for line in p.read_text('ascii').splitlines()if line and not line.startswith('#'))
def children_exited():return all(c['process'].poll()is not None and c['job']is not None and c['job'].active_processes()==0 for c in CHILDREN)

def run_probe(row,label,gateway_port,nonce,controller_process):
    assert label=='normal-restart' and children_exited() and not OUT.exists()
    health=load('component_probe_health_r822',V/'r45_original_backend_health_r849.py');plan,runtime,_=health.profile()
    assert runtime.owned_ready(G,plan['candidateReleaseSHA256'],gateway_port=gateway_port)==row
    assert controller_process.pid==row['controllerPID'] and controller_process.poll()is None
    assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
    seedRoot=R/'work/event_delivery_consistency_20261030/full-business-main-r114'
    seed=J(seedRoot/'normal-login-seed-result.json');identity=J(seedRoot/'own-normal-login.private.json')
    assert seed['ownCaptchaPolicyEnabled']is False and seed['administratorAccounts']==0 and seed['realAccountsImported']is False and identity['credentialsSynthetic']is True
    link=props(W/'snapshot-r810-submitted.properties');flight=props(W/'flight.private.properties')
    assert flight['nonce']==nonce
    definitions=J(R/'work/original-manager-http-definitions-r615/native-definitions.private.json')['definitions'][0]
    assert definitions['code']=='tj_eventTask'
    wire={'base':'http://127.0.0.1:'+str(gateway_port),'account':'own_operator_a',
        'password':J(G/'private/server-configuration.json')['seedRootPassword'],
        'expectedUserId':identity['accounts']['own_operator_a']['id'],'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True,
        'mode':'completed-readonly','opinion':flight['approval'],'approveLabel':definitions['expectedGraph']['childNode']['properties'].get('auditBtnText','通过'),
        'versionId':definitions['versionId'],**{k:link[k]for k in ['taskId','instanceId','operatorId','engineTaskId']}}
    source=G/'tools/original_server_windows_job.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
    jobs=load('component_probe_jobs_r822',source);budget=load('component_probe_budget_r822',T/'bounded_build_job_r671.py')
    stage=P/label;stage.mkdir()
    env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','NODE_EXTRA_CA_CERTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
    with(stage/'browser.private.log').open('xb')as out:
        process=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(V/'verify_r45_original_backend_browser_r850.mjs')],
            stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        child={'process':process,'job':None};CHILDREN.append(child);error=None
        try:
            child['job']=jobs.OwnedWindowsJob(process);cap=budget.BoundedBuildJob(child['job'],1024**3)
            process.communicate(input=(json.dumps(wire)+'\n').encode())
        except BaseException as e:
            error=e
            if process.stdin is not None and not process.stdin.closed:process.stdin.close()
            while process.poll()is None:
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:print('SAME_COMPONENT_PROBE_HANDLE_LIVE_NO_RESTART',flush=True)
        finally:wire.clear()
        assert child['job']is not None
        while child['job'].active_processes():time.sleep(.1)
        metrics=cap.metrics();child['job'].close()
    terminal=dict(exitCode=process.returncode,actualJobDescendantsZero=True,budget=metrics,forceTerminationUsed=False)
    (stage/'browser-job-terminal.json').write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf8')
    if error is not None:raise error
    assert process.returncode==0,'ACTUAL_COMPONENT_BOOTSTRAP_BROWSER_FAILED'
    result=J(OUT/'result.json');assert result['passed']and result['approvalRequests']==0 and not result['APIsMocked']
    assert J(OUT/'browser-terminal.json')['normalBrowserClosed']
    proof=dict(passed=True,actualCompiledApplicationAndOriginalSDK=True,normalNonadminLogin=True,
        anonymousFullInstallerNotFetched=True,completeOriginalGlobalComponentsAvailableAfterLogin=True,
        originalBusinessListsAndExistingCompletedDetailPassed=True,actualUICases=len(result['cases']),
        businessWritesOrCallbackRebindingPerformed=False,publicOrDesktopTouched=False,fullCloneReady=False)
    static=load('r45_static_gateway_probe',V/'probe_r45_original_gateway_r850.py').run_probe(row,label,gateway_port,nonce)
    assert static['passed'];proof['actualGatewayGzipCacheAndDecodedSHAValidated']=True
    (stage/'business-result-r850.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    return proof
