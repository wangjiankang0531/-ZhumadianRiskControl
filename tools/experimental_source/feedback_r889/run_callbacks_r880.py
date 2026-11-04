"""Actual G callback stage invoked by the future full original-manager parent.

No standalone service launch, public action, full-attempt creation or permission
grant. Parent must own full memory/health gates and retain all controller Jobs.
"""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';T=R/'Application/tools';ATTEMPT=R/'work/original-manager-full-lifecycle-r609';V=Path(__file__).resolve().parent
CHILDREN=[]
J=lambda p:json.loads(p.read_bytes())
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def children_exited():
    return all(x['process'].poll()is not None and x['job']is not None and x['job'].active_processes()==0 for x in CHILDREN)
def run_callback_setup(stage,attempt_id,release_sha256,*,gateway_port,controller_process):
    planner=load('actual_callback_plan_r666',V/'callback_plan_r880.py')
    planner.marker() # Refuse before plan files, compile or credentials if inactive.
    assert stage in ['first-start','normal-restart','after-submit-r889']and children_exited(),'OWN_CALLBACK_STAGE_AND_TERMINAL_CHILDREN_REQUIRED'
    memory=(ctypes.c_ulonglong*8)();memory[0]=64
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>1024**3,'ONE_GIB_POST_START_CALLBACK_PROBE_RESERVE_REQUIRED'
    proofRoot=R/'Document/Deployment/callback_runtime_entry_r668_20261104'
    proof=J(proofRoot/'verified-runtime-entry-r668.json');terminal=J(proofRoot/'terminal-r668.json')
    assert proof['passed']and proof['checks']==15 and proof['actualPinnedConnectorJInstantiatedWithoutConnection']
    assert sha(T/'owned_callback_runtime_plan_r663.py')==proof['planBuilderSHA256']
    assert sha(T/'OwnOriginalCallbackRuntimeR662.java')==proof['runtimeEntrySourceSHA256']
    names=['OwnedOriginalCallbacksR648.java','OwnedCallbackProvisioningJournalR658.java','OwnedOriginalCallbackProvisioningR659.java','OwnOriginalCallbackRuntimeR662.java']
    for name in names:assert sha(T/name)==terminal['sourcePins'][name],'CALLBACK_EXECUTION_SOURCE_DRIFT'
    payload=J(G/'payload-manifest.json')['files'];boot=G/'payload/platform/boot-loader.jar';connector=G/'payload/business/lib/mysql-connector-j-8.0.33.jar'
    for p in [boot,connector]:assert p.stat().st_size==payload[p.relative_to(G).as_posix()]['bytes']and sha(p)==payload[p.relative_to(G).as_posix()]['sha256']
    jobsPath=G/'tools/original_server_windows_job.py';assert sha(jobsPath)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
    jobs=load('actual_callback_jobs_r666',jobsPath);budget=load('task_callback_budget_r806',T/'bounded_build_job_r671.py')
    plan=planner.prepare_runtime_plan(stage,attempt_id,release_sha256,gateway_port=gateway_port,controller_process=controller_process)
    stageRoot=plan['attempt'];classes=stageRoot/'callback-chain-r776-classes';assert not classes.exists(),'EXISTING_CALLBACK_STAGE_NO_AUTOMATIC_RESTART'
    classes.mkdir();rows=[]
    env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
    def execute(label,command,wire=None):
        log=stageRoot/('callback-r777-'+label+'.private.log')
        with log.open('xb')as out:
            p=subprocess.Popen(command,cwd=ATTEMPT,env=env,stdin=subprocess.PIPE if wire is not None else subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            child={'process':p,'job':None};CHILDREN.append(child);interrupted=None
            try:child['job']=jobs.OwnedWindowsJob(p);child['budget']=budget.BoundedBuildJob(child['job'],1024**3);p.communicate(input=wire)
            except BaseException as e:
                interrupted=e
                if p.stdin is not None and not p.stdin.closed:
                    try:p.stdin.close()
                    except OSError:pass
                while p.poll()is None:
                    try:p.wait(timeout=15)
                    except subprocess.TimeoutExpired:print('OWN_CALLBACK_CHILD_STILL_LIVE_NO_RESTART_OR_RESTORE',flush=True)
            job=child['job']
            if job is None:raise RuntimeError('CALLBACK_JOB_EXIT_PROOF_MISSING_NO_RESTORE')from interrupted
            while job.active_processes():time.sleep(.1)
            memory=child['budget'].metrics();job.close()
        rows.append(dict(phase=label,exitCode=p.returncode,actualJobDescendantsZero=True,jobMemory=memory,forceTerminationUsed=False))
        (stageRoot/'callback-terminals-r777.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
        if interrupted is not None:raise interrupted
        return p.returncode
    jdk=G/'runtime/jdk17/bin'
    assert execute('compile',[str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',str(boot),'-d',str(classes),str(T/'OwnedOriginalCallbacksR648.java'),str(V/'OwnedCallbackProvisioningJournalR658.java'),str(T/'OwnedOriginalCallbackProvisioningR659.java'),str(T/'OwnedWindowsProcessArgumentsR747.java'),str(V/'OwnOriginalCallbackRuntimeR770.java')])==0,'CALLBACK_RUNTIME_COMPILE_FAILED'
    command=[str(jdk/'java.exe'),'-Dxnby.own.callback.port='+str(plan['databasePort']),'-Dxnby.owned.manager.stage='+stage,'-Xmx256m','-XX:ActiveProcessorCount=2','-cp',os.pathsep.join(map(str,[classes,boot,connector])),'OwnOriginalCallbackRuntimeR770']
    password=J(G/'private/server-configuration.json')['seedRootPassword'];assert len(password)==32 and all(c in'0123456789abcdef'for c in password)
    wire=(password+'\n').encode('ascii');password=None
    try:
        for mode in ['inspect','apply','verify-only']:
            code=execute(mode,command+[mode,'normal-restart',str(plan['plan']),plan['planSHA256']],wire)
            if code!=0:raise RuntimeError('CALLBACK_STAGE_FAILED_NO_AUTOMATIC_MUTATION_RETRY:'+mode)
    finally:wire=None
    assert children_exited()and plan['journal'].is_file()
    result=dict(passed=True,stage=stage,actualRuntimeEntryAndThreeModesPassed=True,actualJobDescendantsZero=True,
                mutationRetried=False,journalSHA256=sha(plan['journal']),normalBusinessOrHTTPCallbackAccepted=False)
    (stageRoot/'callback-r777-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result
