"""One original upload/create/failing edit; read-only old-row digests and restart."""
from pathlib import Path
import importlib.util,json,os,subprocess,time,hashlib
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent;P=R/'work/hazard-transaction-probe-r1212';D=R/'Document/Deployment/hazard_attachment_transaction_r1212_20261106';CHILDREN=[]
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def props(p):return dict(line.split('=',1)for line in p.read_text('ascii').splitlines()if line and not line.startswith('#'))
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def children_exited():return all(x['process'].poll()is not None and x['job'].active_processes()==0 for x in CHILDREN)
def run_probe(row,label,gateway_port,unused_nonce,controller_process):
 assert label in ['mainflow','normal-restart']and children_exited()and controller_process.pid==row['controllerPID']and controller_process.poll()is None
 plan,runtime,_=load('hazard_attachment_health',V/'hazard_health_r1212.py').profile();assert runtime.owned_ready(G,plan['candidateReleaseSHA256'],gateway_port=gateway_port)==row
 assert j(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
 flight=j(D/'flight.private.json');nonce=flight['nonce'];assert len(nonce)==32 and all(c in'0123456789abcdef'for c in nonce)
 stage=P/label;stage.mkdir();classes=P/'classes';jobs=load('hazard_attachment_jobs',G/'tools/original_server_windows_job.py');budget=load('hazard_attachment_budget',A/'tools/bounded_build_job_r671.py');terminals=[]
 connector=G/'payload/business/lib/mysql-connector-j-8.0.33.jar';pin=j(G/'payload-manifest.json')['files'][connector.relative_to(G).as_posix()];assert connector.stat().st_size==pin['bytes']and sha(connector)==pin['sha256']
 env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','NODE_EXTRA_CA_CERTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
 def secret():
  s=j(G/'private/server-configuration.json')['seedRootPassword'];assert len(s)==32 and all(c in'0123456789abcdef'for c in s);return s
 def execute(name,command,wire=None):
  with(stage/(name+'.private.log')).open('xb')as out:p=subprocess.Popen(command,stdin=subprocess.PIPE if wire is not None else subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
  job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,1024**3);CHILDREN.append({'process':p,'job':job})
  try:p.communicate(input=wire)
  finally:
   while p.poll()is None:
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:print('SAME_OWN_ATTACHMENT_CHILD_LIVE_NO_RESTART',flush=True)
   while job.active_processes():time.sleep(.1)
   metrics=cap.metrics();job.close();terminals.append({'name':name,'exitCode':p.returncode,'actualJobDescendantsZero':True,'metrics':metrics,'forceTerminationUsed':False});(stage/'child-terminals.json').write_text(json.dumps(terminals,indent=2)+'\n',encoding='utf8')
  assert p.returncode==0,'ORIGINAL_HAZARD_ATTACHMENT_CHILD_FAILED:'+name
 jdk=G/'runtime/jdk17/bin';cp=str(classes)+os.pathsep+str(connector)
 if not classes.exists():
  classes.mkdir();execute('compile',[str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(V/'OwnHazardCrudReadR1212.java'),str(V/'OwnHazardStatisticsMenuFixtureR1172.java'),str(V/'OwnHazardFormMetadataR1212.java')])
 def sql(name,phase):
  out=stage/(name+'.private.properties');execute(name,[str(jdk/'java.exe'),'-Xmx128m','-cp',cp,'OwnHazardCrudReadR1212',str(row['databasePort']),row['databaseUUID'],phase,nonce,str(out),f'a531{120002:028x}',flight['ownId']],(secret()+'\n').encode('ascii'));return props(out)
 def metadata(name):
  out=stage/(name+'.private.properties');execute(name,[str(jdk/'java.exe'),'-Xmx128m','-cp',cp,'OwnHazardFormMetadataR1212',str(row['databasePort']),row['databaseUUID'],'verify',str(out)],(secret()+'\n').encode('ascii'));assert props(out)['passed']=='true'
 metadata('verify-existing-own-eleven-metadata')
 if label=='mainflow':
  before=sql('business-before','before');(P/'original-business-before.private.json').write_text(json.dumps(before)+'\n',encoding='utf8')
 else:before=j(P/'original-business-before.private.json')
 mode='mainflow'if label=='mainflow'else'reopen';wire={'ownId':flight['ownId'],'base':'http://127.0.0.1:'+str(gateway_port),'account':'own_statistics_reader_e','password':secret(),'expectedUserId':f'a531{120002:028x}','credentialsSynthetic':True,'nonce':nonce,'mode':mode}
 try:execute('original-hazard-attachment-'+mode,['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(V/'hazard_transaction_browser_r1212.mjs')],(json.dumps(wire)+'\n').encode('utf8'))
 finally:wire.clear()
 ui=j(P/('ui-'+mode)/'result.json');assert ui['passed']and j(P/('ui-'+mode)/'terminal.json')['chromeExitCode']==0
 after=sql('business-after','after-mainflow'if label=='mainflow'else'after-restart');assert before['originalHazardRowsFingerprint']==after['originalHazardRowsFingerprint']and before['originalBaseFilesFingerprint']==after['originalBaseFilesFingerprint'],'PREEXISTING_BUSINESS_ROWS_CHANGED'
 assert int(after['ownAttachmentCount'])==ui['attachmentCountAfter']and after['ownRecordSoftDeleted']=='false','SQL_AND_ACTUAL_UI_MATCH'
 if label=='mainflow':
  assert ui['attachmentAtomicityPreserved'] and ui['normalRetryAccepted'] and ui['failedEditPreservedMainRow'];assert after['ownAttachmentId']==ui['attachmentAfter'][0]['id'];assert j(P/'ui-mainflow/verified-png.json')['passed'];(P/'own-after-mainflow.private.json').write_text(json.dumps(after)+'\n',encoding='utf8')
 else:
  prior=j(P/'own-after-mainflow.private.json');assert all(after[k]==prior[k]for k in ['ownRecordFingerprint','ownAttachmentFingerprint','ownAttachmentCount']),'OWN_ROW_OR_RELATION_CHANGED_ACROSS_RESTART'
 metadata('verify-existing-metadata-after-ui')
 proof={'passed':True,'phase':label,'scopedCandidateAcceptanceOnly':True,'actualOriginalSDKAndOrdinaryUI':True,'actualUICases':len(ui['cases']),'sameExistingOwnRecordNoCreate':True,'repairAndFailedKeepAndValidRetryAndFailedRemove':label=='mainflow','allPreExistingHazardAndBaseFileRowsFingerprintUnchanged':True,'mainRowUnchangedByFailedEdit':True,'attachmentRelationRetainedAfterFailedEdit':int(after['ownAttachmentCount'])==1,'attachmentAtomicityDefectObserved':int(after['ownAttachmentCount'])==0,'normalRestartReadsSameRecordAndRelation':label=='normal-restart','metadataReprepared':False,'publicAccepted':False}
 (stage/'verified-attachment-transaction.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');return proof
