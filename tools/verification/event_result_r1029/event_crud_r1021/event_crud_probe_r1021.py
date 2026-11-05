from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application';V=Path(__file__).resolve().parent
Z=R/'work/ev1021';CHILDREN=[]
J=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def children_exited():return all(c['process'].poll()is not None and c['job']is not None and c['job'].active_processes()==0 for c in CHILDREN)
def run_probe(row,label,gateway_port,nonce,controller_process):
 assert label in ['first-start','normal-restart']and children_exited()and controller_process.poll()is None and controller_process.pid==row['controllerPID']
 plan,runtime,_=load('event_health_r1021',V/'home_transfer_health_r906.py').profile()
 assert runtime.owned_ready(G,plan['candidateReleaseSHA256'],gateway_port=gateway_port)==row
 for source,pin in J(V/'event-source-pins-r1021.json')['files'].items():assert sha(Path(source))==pin
 identity=J(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json')
 seed=J(R/'work/event_delivery_consistency_20261030/full-business-main-r114/normal-login-seed-result.json')
 assert identity['credentialsSynthetic']and not seed['ownCaptchaPolicyEnabled']and seed['administratorAccounts']==0 and not seed['realAccountsImported']
 password=J(G/'private/server-configuration.json')['seedRootPassword'];assert len(password)==32
 wire={'base':'http://127.0.0.1:'+str(gateway_port),'account':'own_operator_a','password':password,'expectedUserId':identity['accounts']['own_operator_a']['id'],'phase':label,'nonce':nonce,'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True}
 password=None;identity=None
 jobs=load('event_original_jobs_r1021',G/'tools/original_server_windows_job.py');budget=load('event_budget_r1021',A/'tools/bounded_build_job_r671.py')
 assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','NODE_EXTRA_CA_CERTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
 with(Z/(label+'-browser.private.log')).open('xb')as out:
  p=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(V/'verify_event_crud_r1021.mjs')],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
  child={'process':p,'job':None};CHILDREN.append(child)
  try:
   child['job']=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(child['job'],1024**3)
   p.communicate(input=(json.dumps(wire,ensure_ascii=False)+'\n').encode())
  finally:
   wire.clear()
   if p.stdin is not None and not p.stdin.closed:p.stdin.close()
   while p.poll()is None:
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:print('SAME_OWN_EVENT_BROWSER_STILL_LIVE_NO_FORCE',flush=True)
  assert child['job']is not None
  while child['job'].active_processes():time.sleep(.1)
  terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};child['job'].close()
  (Z/(label+'-browser-terminal.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf8')
 assert p.returncode==0,'ORIGINAL_EVENT_UI_FAILED_INSPECT_SAME_CONTEXT_NO_RECREATE'
 result=J(Z/'browser'/label/'result.json');browser=J(Z/'browser'/label/'browser-terminal.json')
 assert result['passed']and not result['APIsMocked']and browser['normalBrowserClosed']and browser['exitCode']==0
 assert result['eventCreatesObserved']==(1 if label=='first-start'else 0)
 return {'passed':True,'phase':label,'cases':result['cases'],'eventCreatesObserved':result['eventCreatesObserved'],'APIsMocked':False,'allMutationsThroughNormalOriginalUI':True,'normalBrowserAndActualDescendantsExited':True,'fullCloneReady':False}
