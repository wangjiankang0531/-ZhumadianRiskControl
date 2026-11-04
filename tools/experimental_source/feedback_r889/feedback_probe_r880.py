"""Actual compiled task-create, manager-approve and same-data reopened UI."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';T=R/'Application/tools';V=Path(__file__).resolve().parent
O=R/'work/original-manager-full-lifecycle-r609';W=O/'feedback-r880';P=W/'runtime-resume-r889';CHILDREN=[]
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
callbacks=load('task_ui_callbacks_r806',V/'run_callbacks_r880.py')
def children_exited():return callbacks.children_exited()and all(x['process'].poll()is not None and x['job']is not None and x['job'].active_processes()==0 for x in CHILDREN)
def props(p):return dict(line.split('=',1)for line in p.read_text('ascii').splitlines()if line and not line.startswith('#'))
def run_probe(row,label,gateway_port,nonce,controller_process):
 assert label in ['first-start','normal-restart']and W.is_dir()and J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
 for name,pin in J(V/'feedback-existing-r889-source-pins.json')['files'].items():assert sha(Path(name))==pin
 health=load('task_ui_health_r806',V/'feedback_health_r880.py');plan,runtime,_=health.profile()
 assert runtime.owned_ready(G,plan['runtimeCandidateReleaseSHA256'],gateway_port=gateway_port)==row and controller_process.pid==row['controllerPID']and controller_process.poll()is None and children_exited()
 code=load('task_ui_atomic_r806',T/'owned_candidate_code_transaction_r543.py');save=lambda p,v:code.atomic(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 stage=P/label;stage.mkdir();saveMarker=stage/'own-normal-manager-test.marker';saveMarker.write_bytes(b'own-original-manager-full-lifecycle-r609\n')
 packet=R/'work/original-manager-http-definitions-r615/native-definitions.private.json';assert sha(packet)=='539b57deffd8710dc633cd401f81898440d82ff5e7b7f8f1cbfe86cc55595660'
 d=J(packet)['definitions'][0];assert d['code']=='tj_eventTask'
 flight=props(W/'flight.private.properties');assert flight['nonce']==nonce and flight['taskName']=='OWN_MANAGER_'+nonce and flight['approval']=='OWN_MANAGER_APPROVAL_'+nonce
 seedRoot=R/'work/event_delivery_consistency_20261030/full-business-main-r114';seed=J(seedRoot/'normal-login-seed-result.json');identity=J(seedRoot/'own-normal-login.private.json')
 assert seed['ownCaptchaPolicyEnabled']is False and seed['administratorAccounts']==0 and seed['realAccountsImported']is False and identity['credentialsSynthetic']is True
 jobsPath=G/'tools/original_server_windows_job.py';assert sha(jobsPath)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
 jobs=load('task_ui_jobs_r806',jobsPath);budget=load('task_ui_budget_r806',T/'bounded_build_job_r671.py')
 connector=G/'payload/business/lib/mysql-connector-j-8.0.33.jar';pin=J(G/'payload-manifest.json')['files'][connector.relative_to(G).as_posix()]
 assert connector.stat().st_size==pin['bytes']and sha(connector)==pin['sha256']
 jdk=G/'runtime/jdk17/bin';classes=W/'classes-r889';terminals=[];managerMayNeedRestore=False;cb=None
 env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','NODE_EXTRA_CA_CERTS','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
 def execute(name,command,wire=None):
  with(stage/(name+'.private.log')).open('xb')as out:
   process=subprocess.Popen(command,cwd=W,env=env,stdin=subprocess.PIPE if wire is not None else subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   child={'process':process,'job':None};CHILDREN.append(child);error=None
   try:
    child['job']=jobs.OwnedWindowsJob(process);child['budget']=budget.BoundedBuildJob(child['job'],1024**3)
    process.communicate(input=wire)
   except BaseException as e:
    error=e
    if process.stdin is not None and not process.stdin.closed:process.stdin.close()
    while process.poll()is None:
     try:process.wait(timeout=15)
     except subprocess.TimeoutExpired:print('SAME_OWN_TASK_UI_CHILD_HANDLE_LIVE_NO_RESTART',flush=True)
   assert child['job']is not None
   while child['job'].active_processes():time.sleep(.1)
   metrics=child['budget'].metrics();child['job'].close()
  terminals.append(dict(phase=name,exitCode=process.returncode,actualJobDescendantsZero=True,budget=metrics,forceTerminationUsed=False));save(stage/'probe-terminals-r806.json',terminals)
  if error is not None:raise error
  assert process.returncode==0,'ACTUAL_TASK_UI_CHILD_FAILED:'+name
 def secret():
  value=J(G/'private/server-configuration.json')['seedRootPassword'];assert len(value)==32 and all(c in'0123456789abcdef'for c in value);return value
 def java(name,kind,args):execute(name,[str(jdk/'java.exe'),'-Xmx128m','-cp',str(classes)+os.pathsep+str(connector),kind,*args],(secret()+'\n').encode('ascii'))
 def snapshot(mode):
  assert runtime.owned_ready(G,plan['runtimeCandidateReleaseSHA256'],gateway_port=gateway_port)==row
  target=W/('snapshot-r889-'+mode+'.properties')
  java('snapshot-'+mode,'OwnManagerBusinessReadbackR783',[str(row['databasePort']),row['databaseUUID'],str(G/'UserData/OriginalServer/database/data'),str(target),mode])
  result=props(target);assert result['actualDatabaseIdentityMatched']=='true'and result['persistentWritesIssued']=='false';return result
 def directory(mode):java('directory-'+mode,'OwnOriginalManagerDirectoryR609',[mode,str(row['databasePort']),row['databaseUUID'],str(G/'UserData/OriginalServer/database/data'),str(P/'manager-directory.private.properties')])
 def browser(mode,link=None):
  account='own_reviewer_b'if mode=='pending-approve'else'own_operator_a'
  wire={'base':'http://127.0.0.1:'+str(gateway_port),'account':account,'password':secret(),'expectedUserId':identity['accounts'][account]['id'],
   'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True}
  if mode=='create':
   script=V/'create_task_browser_r880.mjs';folder=W/'ui-create-r887'
   wire.update(researchRequired=researchRequired,eventId='a5320000000000000000000000000006',eventNumber='OWN-NORMAL-WORKFLOW-EVENT',eventName='Own workflow event',taskName=flight['taskName'],taskContent='Own task UI dispatch '+nonce)
  elif mode in ['feedback-submit','feedback-readonly']:
   assert link is not None;script=V/'feedback_browser_r880.mjs';folder=W/('ui-'+mode+'-r889')
   wire.update(mode=mode,eventId='a5320000000000000000000000000006',taskName=flight['taskName'],feedback='OWN_FEEDBACK_'+nonce,evaluation='OWN_EVALUATION_'+nonce,
    opinion=flight['approval'],versionId=d['versionId'],**{k:link[k]for k in ['taskId','instanceId','operatorId','engineTaskId']})
  else:
   assert link is not None;script=V/'normal_manager_browser_r880.mjs';folder=W/('ui-'+mode+'-r889')
   wire.update(mode=mode,opinion=flight['approval'],approveLabel=d['expectedGraph']['childNode']['properties'].get('auditBtnText','通过'),versionId=d['versionId'],**{k:link[k]for k in ['taskId','instanceId','operatorId','engineTaskId']})
  try:execute('browser-'+mode,[r'D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(script)],(json.dumps(wire)+'\n').encode())
  finally:wire.clear()
  result=J(folder/'result.json');assert result['passed']and not result['APIsMocked']and J(folder/'browser-terminal.json')['normalBrowserClosed'];return result
 try:
  if label=='first-start':
   assert not classes.exists();classes.mkdir()
   execute('compile',[str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(V/'OwnManagerBusinessReadbackR783.java'),str(V/'OwnOriginalManagerDirectoryR609.java')])
   submitted=snapshot('pending-resume')
   previous=props(W/'snapshot-r887-submitted.properties')
   assert all(submitted[k]==previous[k]for k in ['taskId','instanceId','operatorId','engineTaskId']),'EXACT_ALREADY_CREATED_TASK_REQUIRED'
   refreshed=W/'snapshot-r889-submitted.properties';assert not refreshed.exists();refreshed.write_bytes((W/'snapshot-r889-pending-resume.properties').read_bytes())
   callbackStage=W/'after-submit-r889';callbackStage.mkdir();(callbackStage/'own-normal-manager-test.marker').write_bytes(b'own-original-manager-full-lifecycle-r609\n')
   cb=callbacks.run_callback_setup('after-submit-r889',J(O/'callback-first-start-plan.private.json')['attemptId'],plan['runtimeCandidateReleaseSHA256'],gateway_port=gateway_port,controller_process=controller_process)
   assert cb['passed']and callbacks.children_exited()
   feedback=browser('feedback-submit',submitted);assert feedback['feedbackUpdateRequests']==1 and feedback['feedbackSaveConfirmed']
   checked=snapshot('feedback');assert checked['originalFeedbackEvaluationTimeMatched']=='true'and checked['activeEngineTasks']=='1'and checked['originalProcessEnded']=='false'
   ui=browser('pending-approve',submitted);assert ui['approvalRequests']==1
   final=snapshot('approved')
  else:
   assert classes.is_dir()and J(P/'first-start/business-result-r880.json')['passed']
   submitted=props(W/'snapshot-r889-submitted.properties');ui=browser('completed-readonly',submitted);assert ui['approvalRequests']==0
   feedback=browser('feedback-readonly',submitted);assert feedback['feedbackUpdateRequests']==0
   final=snapshot('restarted')
  assert final['taskId']==submitted['taskId']and final['instanceId']==submitted['instanceId']and final['taskStatus']=='1'
  assert final['originalReadOnlyFormValuePreserved']=='true'and final['originalManagerOpinionPersisted']=='true'and final['originalFeedbackEvaluationTimeMatched']=='true'
  result=dict(passed=True,stage=label,actualTaskCreationUI=False,previouslyCreatedTaskIdentityVerified=True,actualOriginalManagerApprovalUI=label=='first-start',
   actualCompletedInitiatorCardAndRestart=label=='normal-restart',sameTaskAndInstanceMatched=True,originalFormValueOpinionAndCallbackStateMatched=True,
   originalFeedbackEvaluationAndTimePersisted=True,taskAndApprovalMutationsRetried=False,APIsMocked=False,callbackRebinding=cb if cb is not None else{'performed':False},publicOrDesktopTouched=False,fullCloneReady=False)
  save(stage/'business-result-r880.json',result);return result
 finally:
  assert children_exited(),'ACTUAL_UI_CHILD_EXIT_REQUIRED_BEFORE_RELATION_RESTORE'
  if managerMayNeedRestore:
   assert runtime.owned_ready(G,plan['runtimeCandidateReleaseSHA256'],gateway_port=gateway_port)==row
   directory('restore');assert props(P/'manager-directory.private.properties')['phase']=='restored'
   save(stage/'manager-restored.json',dict(passed=True,restoredWhileSameDatabaseLive=True))
