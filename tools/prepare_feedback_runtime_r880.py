"""Prepare a fixed R45 owned feedback lifecycle; never touch G or start services."""
from pathlib import Path
import ast, hashlib, json, secrets, subprocess, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent; R=Path('D:/Project/Zhumadian'); A=R/'Application'; G=R/'_g/Application'; T=A/'tools'
D=V/'feedback_r880'; W=R/'work/original-manager-full-lifecycle-r609/feedback-r880'
OLD='e957cf851cb253d4ac020ef04711ebd6e9f066bfc1471002b10d53c88de71db2'
NEW='eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93'
JOURNAL='6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def one(s,a,b):
    assert s.count(a)==1,a[:120]
    return s.replace(a,b)
def main():
    assert not D.exists() and not W.exists()
    pre=json.loads((R/'Document/Deployment/feedback_original_preconditions_r879_20261104/verification.json').read_bytes())
    assert pre['passed'] and pre['predecessor']['journalSHA256']==JOURNAL
    source=R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json'
    assert sha(source)=='204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09'
    base=json.loads(source.read_bytes());candidate=source.parent/'candidate'
    sys.path.insert(0,str(T));import owned_task_configuration_r637 as task
    after=task.task_candidate({task.CONFIG:(G/task.CONFIG).read_bytes(),task.PAYLOAD:(candidate/task.PAYLOAD).read_bytes(),task.RELEASE:(candidate/task.RELEASE).read_bytes()})
    assert {n:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}for n,raw in after.items()}==pre['plannedR45TaskRuntimePins']
    assert hashlib.sha256(after[task.RELEASE]).hexdigest()==NEW
    D.mkdir(); (D/'runtime-manifests').mkdir()
    for n in [task.PAYLOAD,task.RELEASE]:(D/'runtime-manifests'/n).write_bytes(after[n])
    plan=dict(base);plan.update(schema='xnby.feedback-original.owned-full-candidate.plan.v1',
      codeCandidateReleaseSHA256=base['candidateReleaseSHA256'],runtimeCandidateReleaseSHA256=NEW,
      runtimeConfigurationAfterPin=pre['plannedR45TaskRuntimePins'][task.CONFIG],sixComponentLifecycleMinimumAvailableBytes=6*1024**3)
    (D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
    oldFlight=dict(line.split('=',1)for line in (R/'work/original-manager-full-lifecycle-r609/task-ui-r806/flight.private.properties').read_text('ascii').splitlines()if line and not line.startswith('#'))
    nonce=secrets.token_hex(16)
    flight={'nonce':nonce,'taskName':'OWN_MANAGER_'+nonce,'formTable':oldFlight['formTable'],'approval':'OWN_MANAGER_APPROVAL_'+nonce}
    (D/'flight.private.properties').write_text(''.join(k+'='+v+'\n'for k,v in flight.items()),encoding='ascii')
    def save(name,s):
      p=D/name;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_text(s,encoding='utf8')
      if p.suffix=='.py':ast.parse(s,filename=name)
      elif p.suffix=='.mjs':assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True).returncode==0
    # Retain the original SQL core, runtime identity and persistent intent state
    # machine. Extend only this explicit prior-release -> fixed-R45 stage.
    s=(V/'task_ui_r806/OwnedCallbackProvisioningJournalR658.java').read_text('utf8')
    begin=s.index('    void previous()throws IOException{');end=s.index('    public byte[] prepare()',begin)
    s=s[:begin]+'''    static String digest(Path p)throws IOException {
        try {return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
        catch(java.security.NoSuchAlgorithmException e){throw new IOException(e);}
    }
    void previous()throws IOException{
        need(binding.stage().equals("normal-restart"),"ONLY_EXPLICIT_MANAGER_REBIND_STAGE_REQUIRED");
        Path root=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609");
        Path first=root.resolve("feedback-r880/first-start"),second=root.resolve("feedback-r880/normal-restart");
        need(path.getParent().equals(first)||path.getParent().equals(second),"EXACT_OWN_FEEDBACK_CALLBACK_CHAIN_REQUIRED");
        boolean transition=path.getParent().equals(first);
        Path previous=(transition?root.resolve("task-ui-r806/normal-restart"):first).resolve("callback-normal-restart-journal.private.properties");plain(previous);
        if(transition)need(digest(previous).equals("'''+JOURNAL+'''"),"PINNED_OLD_CALLBACK_JOURNAL_REQUIRED");
        Properties p=parse(Files.readAllBytes(previous));
        Set<String> keys=new HashSet<>(base.stringPropertyNames());keys.add("phase");need(p.stringPropertyNames().equals(keys),"EXACT_PREVIOUS_CALLBACK_JOURNAL_KEYS_REQUIRED");
        need(p.getProperty("phase").equals("readback-verified"),"VERIFIED_PREVIOUS_CALLBACK_STAGE_REQUIRED");
        for(String k:List.of("schema","attemptId","databaseUUID","dataDirectory"))need(base.getProperty(k).equals(p.getProperty(k)),"PREVIOUS_CALLBACK_STAGE_IDENTITY_DRIFT");
        need(base.getProperty("releaseSHA256").equals("'''+NEW+'''")&&p.getProperty("releaseSHA256").equals(transition?"'''+OLD+'''":"'''+NEW+'''"),"EXACT_FIXED_CALLBACK_RELEASE_TRANSITION_REQUIRED");
        Path previousPlan=previous.resolveSibling("callback-normal-restart-plan.private.json");plain(previousPlan);
        need(p.getProperty("planSHA256").equals(digest(previousPlan)),"PREVIOUS_CALLBACK_PLAN_BINDING_REQUIRED");
        need(p.getProperty("stage").equals("normal-restart")&&p.getProperty("journalPath").equals(previous.toString())&&binding.beforeRowsSHA256().equals(p.getProperty("afterRowsSHA256")),"EXACT_PREVIOUS_CALLBACK_ROWS_REQUIRED");
    }
'''+s[end:]
    save('OwnedCallbackProvisioningJournalR658.java',s)
    s=(V/'task_ui_r806/OwnOriginalCallbackRuntimeR770.java').read_text('utf8')
    s=one(s,'return ROOT.resolve("task-ui-r806").resolve(s);','return ROOT.resolve("feedback-r880").resolve(s);')
    save('OwnOriginalCallbackRuntimeR770.java',s)
    s=(V/'task_ui_r810/OwnOriginalManagerDirectoryR609.java').read_text('utf8').replace('task-ui-r806/resume-r810','feedback-r880/runtime')
    save('OwnOriginalManagerDirectoryR609.java',s)
    s=(V/'task_ui_r810/OwnManagerBusinessReadbackR783.java').read_text('utf8').replace('task-ui-r806','feedback-r880').replace('snapshot-r810-','snapshot-r880-').replace('original-field-baseline-r806','original-field-baseline-r880')
    s=one(s,'"restarted","pending-resume"','"restarted","pending-resume","feedback"')
    s=one(s,'Set.of("submitted","wrong","pending-resume").contains(a[4])','Set.of("submitted","wrong","pending-resume","feedback").contains(a[4])')
    s=one(s,'need("2".equals(businessStatus)&&!ended&&active==1,','need((a[4].equals("feedback")?"1":"2").equals(businessStatus)&&!ended&&active==1,')
    anchor='    boolean ended;try(PreparedStatement p=c.prepareStatement("SELECT END_TIME_ FROM act_hi_procinst WHERE ID_=?"))'
    check='''    if(Set.of("feedback","approved","restarted").contains(a[4])){
     try(PreparedStatement p=c.prepareStatement("SELECT "+col(c,"tj_endanger","event_task","feedbackinfo")+","+col(c,"tj_endanger","event_task","evaluationsum")+","+col(c,"tj_endanger","event_task","disposetime")+" FROM tj_endanger.event_task WHERE "+taskId+"=?")){
      p.setQueryTimeout(10);p.setString(1,id);try(ResultSet r=p.executeQuery()){
       need(r.next()&&("OWN_FEEDBACK_"+input.getProperty("nonce")).equals(r.getString(1))&&("OWN_EVALUATION_"+input.getProperty("nonce")).equals(r.getString(2))&&r.getTimestamp(3)!=null&&r.getTimestamp(3).toLocalDateTime().equals(java.time.LocalDateTime.of(2026,11,4,17,30))&&!r.next(),"EXACT_ORIGINAL_FEEDBACK_EVALUATION_AND_TIME_REQUIRED");
      }
     }result.setProperty("originalFeedbackEvaluationTimeMatched","true");
    }
'''
    s=one(s,anchor,check+anchor);save('OwnManagerBusinessReadbackR783.java',s)
    # The callback planner still holds the exact live controller observation and
    # requires the previous row set from the original builder before execution.
    s=(V/'task_ui_callback_plan_r806.py').read_text('utf8')
    s=s.replace("ATTEMPT/'task-ui-r806'/stage","ATTEMPT/'feedback-r880'/stage")
    s=one(s,"previousRoot=ATTEMPT/'normal-ui-r803/normal-restart' if stage=='first-start'else ATTEMPT/'task-ui-r806/first-start'", "previousRoot=ATTEMPT/'task-ui-r806/normal-restart' if stage=='first-start'else ATTEMPT/'feedback-r880/first-start'")
    s=one(s,"previous['releaseSHA256']==release_sha256", "previous['releaseSHA256']==('"+OLD+"'if stage=='first-start'else'"+NEW+"')and release_sha256=='"+NEW+"'")
    anchor="previous=J(plain(previousPlan));receipt=J(plain(previousResult))"
    s=one(s,anchor,anchor+"\n    if stage=='first-start':need(sha(previousJournal)=='"+JOURNAL+"','PINNED_PREDECESSOR_JOURNAL_REQUIRED')")
    save('callback_plan_r880.py',s)
    s=(V/'run_task_ui_callbacks_r806.py').read_text('utf8')
    s=s.replace("V/'task_ui_callback_plan_r806.py'","V/'callback_plan_r880.py'")
    s=s.replace("V/'task_ui_r806/OwnedCallbackProvisioningJournalR658.java'","V/'OwnedCallbackProvisioningJournalR658.java'").replace("V/'task_ui_r806/OwnOriginalCallbackRuntimeR770.java'","V/'OwnOriginalCallbackRuntimeR770.java'")
    save('run_callbacks_r880.py',s)
    s=(V/'create_task_normal_browser_r810.mjs').read_text('utf8').replace('task-ui-r806','feedback-r880').replace('ui-create-r810','ui-create-r880')
    save('create_task_browser_r880.mjs',s)
    s=(V/'normal_manager_browser_r806.mjs').read_text('utf8').replace('task-ui-r806','feedback-r880').replace('original-field-baseline-r806','original-field-baseline-r880').replace('-r806','-r880')
    save('normal_manager_browser_r880.mjs',s)
    # The parent transaction ordering and lifecycle functions remain the already
    # exercised R810 implementation; the code package/health is exact R45.
    s=(V/'run_research_task_ui_full_r810.py').read_text('utf8')
    s=s.replace("D=R/'Document/Deployment/supervision_factory_candidate_r694_20261104'", "D=V/'feedback_r880'")
    s=s.replace("W=O/'task-ui-r806';P=W/'resume-r810';Z=R/'work/task-ui-full-r810'", "W=O/'feedback-r880';P=W/'runtime';Z=R/'work/fb880'")
    s=s.replace('6531efddd8ddfbcd5870b825ea87eb3d415f60fd42ea38c88df2da953b717fa4',sha(D/'full-source-and-restore-plan.private.json'))
    s=s.replace('xnby.integrated-online.owned-full-candidate.plan.v1','xnby.feedback-original.owned-full-candidate.plan.v1')
    s=s.replace('task-ui-r810-source-pins.json','feedback-r880-source-pins.json')
    s=one(s,"assert W.is_dir()and not P.exists()and not Z.exists(),'EXACT_UNISSUED_TASK_UI_RESUME_REQUIRED'", "assert not W.exists()and not P.exists()and not Z.exists(),'EXACT_UNISSUED_FEEDBACK_SCOPE_REQUIRED'")
    a=s.index("prior=J(R/'work/task-ui-full-r809/");b=s.index('memory=available()',a)
    s=s[:a]+'''prior=J(R/'work/task-status-full-r875/verified-task-status-sequence-r875.json')
assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert len(prior['terminals'])==1 and all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
'''+s[b:]
    s=s.replace('original-manager-business-not-started-r806.json','feedback-not-started-r880.json')
    s=s.replace("T/'factory_integrated_full_health_r696.py'","V/'feedback_health_r880.py'")
    s=s.replace("V/'run_research_task_ui_business_r810.py'","V/'feedback_probe_r880.py'")
    anchor="fixture_nonce=next(line.split('=',1)[1]for line in(W/'flight.private.properties').read_text('ascii').splitlines()if line.startswith('nonce='))"
    s=one(s,anchor,"W.mkdir();(W/'own-normal-manager-test.marker').write_bytes(b'own-original-manager-full-lifecycle-r609\\n');(W/'flight.private.properties').write_bytes((D/'flight.private.properties').read_bytes())\n"+anchor)
    s=s.replace("managerJournal=W/'manager-directory.private.properties'","managerJournal=P/'manager-directory.private.properties'")
    s=s.replace('verified-original-manager-business-r810.json','verified-feedback-chain-r880.json').replace('original-manager-business-r781-result.json','feedback-full-result-r880.json')
    save('run_feedback_full_r880.py',s)
    health='''from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent;D=V
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
 plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes())
 assert plan['runtimeCandidateReleaseSHA256']=='@NEW@'
 p=V.parent/'original_public_test_update_r45_bootstrap_r847.py'
 assert sha(p)=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
 s=importlib.util.spec_from_file_location('feedback_original_runtime_r880',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return plan,m,None
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G
 plan,runtime,_=profile();assert sha(G/'release-manifest.json')==plan['runtimeCandidateReleaseSHA256']
 p=G/'private/server-configuration.json';assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['runtimeConfigurationAfterPin']
 runtime.health(G,row,True,gateway_port=gateway_port)
 return {'originalR45ReleaseHealthRetained':True,'onlyOwnedTaskFlowCodeConfigured':True,'publicAccepted':False}
'''.replace('@NEW@',NEW)
    save('feedback_health_r880.py',health)
    (D/'preparation.json').write_bytes(enc({'prepared':True,'runtimeReleaseSHA256':NEW,'oldReleaseSHA256':OLD,'predecessorJournalSHA256':JOURNAL,'servicesStarted':False,'GChanged':False,'businessMutationsPerformed':False}))
    print('R880_RUNTIME_SOURCES_PREPARED_NO_G_CHANGE')
if __name__=='__main__':main()
