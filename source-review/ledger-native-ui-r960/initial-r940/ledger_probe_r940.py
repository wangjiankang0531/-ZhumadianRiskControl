"""Original nonadmin ledger UI on the exact owned R47 candidate, with durable fixture intent."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941';OUT=R/'work/ledger-browser-r941'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
CHILDREN=[]
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def children_exited():return all(c['process'].poll()is not None and c['job']is not None and c['job'].active_processes()==0 for c in CHILDREN)
def props(p):return dict(s.split('=',1)for s in p.read_text('ascii').splitlines()if s and not s.startswith('#'))
def run_probe(row,label,gateway_port,nonce,controller_process):
 assert label in ['first-start','normal-restart']and children_exited()and controller_process.poll()is None and controller_process.pid==row['controllerPID']
 assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
 health=load('ledger_actual_r47_health',V/'home_transfer_health_r906.py');plan,runtime,_=health.profile()
 assert runtime.owned_ready(G,plan['candidateReleaseSHA256'],gateway_port=gateway_port)==row
 for source,pin in J(V/'ledger-source-pins-r941.json')['files'].items():assert sha(Path(source))==pin
 assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 jobs=load('ledger_jobs_r940',G/'tools/original_server_windows_job.py');budget=load('ledger_budget_r940',T/'bounded_build_job_r671.py')
 seedRoot=R/'work/event_delivery_consistency_20261030/full-business-main-r114';seed=J(seedRoot/'normal-login-seed-result.json');identity=J(seedRoot/'own-normal-login.private.json')
 assert not seed['ownCaptchaPolicyEnabled']and seed['administratorAccounts']==0 and not seed['realAccountsImported']and identity['credentialsSynthetic']
 password=J(G/'private/server-configuration.json')['seedRootPassword'];assert len(password)==32
 stage=P/label;stage.mkdir();terminals=[]
 env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','NODE_EXTRA_CA_CERTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
 def execute(name,command,stdin,capbytes):
  with(stage/(name+'.private.log')).open('xb')as out:
   proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
   child={'process':proc,'job':None};CHILDREN.append(child);error=None
   try:
    child['job']=jobs.OwnedWindowsJob(proc);limit=budget.BoundedBuildJob(child['job'],capbytes);proc.communicate(input=stdin)
   except BaseException as caught:
    error=caught
    if proc.stdin is not None and not proc.stdin.closed:proc.stdin.close()
    while proc.poll()is None:
     try:proc.wait(timeout=15)
     except subprocess.TimeoutExpired:print('SAME_LEDGER_CHILD_HANDLE_LIVE_NO_FORCE_OR_RESTORE',flush=True)
   assert child['job']is not None,'ACTUAL_LEDGER_CHILD_JOB_REQUIRED'
   while child['job'].active_processes():time.sleep(.1)
   terminal={'phase':name,'exitCode':proc.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};child['job'].close();terminals.append(terminal)
  (stage/'probe-terminals.json').write_bytes(enc(terminals))
  if error is not None:raise error
  return proc.returncode
 compiled=V/'classes/OwnLedgerMetadataR940.class';compileproof=J(V/'metadata-compile-proof.json');assert compileproof['passed']and sha(compiled)==compileproof['classSHA256']
 connector=G/'payload/business/lib/mysql-connector-j-8.0.33.jar';assert {'bytes':connector.stat().st_size,'sha256':sha(connector)}==J(G/'payload-manifest.json')['files'][connector.relative_to(G).as_posix()]
 mode='prepare'if label=='first-start'else'readback'
 command=[str(G/'runtime/jdk17/bin/java.exe'),'-Xmx128m','-cp',str(compiled.parent)+os.pathsep+str(connector),'OwnLedgerMetadataR940',str(row['databasePort']),row['databaseUUID'],str(G/'UserData/OriginalServer/database/data'),str(P),mode]
 assert execute('metadata-'+mode,command,(password+'\n').encode('ascii'),512*1024**2)==0,'EXACT_OWN_LEDGER_METADATA_FAILED'
 metadata=props(P/('metadata-'+mode+'.private.properties'));assert metadata['phase']=='committed-readback-verified'and metadata['usersRolesAccountsBusinessRowsAndSchemaWritten']=='false'and metadata['persistentWritesIssued']==str(mode=='prepare').lower()
 wire={'base':'http://127.0.0.1:'+str(gateway_port),'account':'own_operator_a','password':password,'expectedUserId':identity['accounts']['own_operator_a']['id'],
  'mode':'create'if label=='first-start'else'readback','nonce':nonce,'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True}
 password=None;identity=None
 try:assert execute('original-ledger-browser',['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(V/'verify_ledger_ui_r940.mjs')],enc(wire),1024**3)==0,'ORIGINAL_LEDGER_UI_FAILED'
 finally:wire.clear()
 result=J(OUT/label/'result.json');browser=J(OUT/label/'browser-terminal.json');assert result['passed']and not result['APIsMocked']and browser['normalBrowserClosed']and browser['exitCode']==0
 expected=1 if label=='first-start'else 0;assert result['generationRequests']==expected and result['fixtureRecordsCreated']==expected
 summary={'passed':True,'phase':label,'cases':result['cases'],'metadataRowsVerified':int(metadata['verifiedMetadataRows']),'metadataOnlyPreparedOnFirstStart':True,
  'actualOriginalNonadminLoginLedgerSupervisionPreviewAndDownloadUI':True,'actualCompiledOriginalSDK':True,'generationRequests':result['generationRequests'],'fixtureRecordsCreated':result['fixtureRecordsCreated'],
  'authNotReplacedAndPreviewDownloadHeadersNotInjected':True,'normalBrowserAndActualJobDescendantsExited':True,'publicOrDesktopTouched':False,'fullCloneReady':False}
 (stage/'ledger-ui-result.json').write_bytes(enc(summary));return summary
