"""Verify the last actual callback chain and R45 task setting without DB/service access."""
from pathlib import Path
import hashlib, importlib.util, io, json, os, subprocess, sys, time, unittest
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent; R=Path('D:/Project/Zhumadian'); A=R/'Application'; G=R/'_g/Application'; T=A/'tools'
O=V/'feedback-preconditions-r878'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    assert not O.exists()
    sys.path.insert(0,str(V));import owned_callback_predecessor_r877 as chain
    previous=R/'work/original-manager-full-lifecycle-r609/task-ui-r806/normal-restart'
    journal=previous/'callback-normal-restart-journal.private.properties'
    expectedJournal='6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98'
    assert sha(journal)==expectedJournal
    oldRoot=R/'Document/Deployment/supervision_factory_candidate_r694_20261104'
    oldPlan=oldRoot/'full-source-and-restore-plan.private.json'
    assert sha(oldPlan)=='6531efddd8ddfbcd5870b825ea87eb3d415f60fd42ea38c88df2da953b717fa4'
    old=json.loads(oldPlan.read_bytes());oldRelease=oldRoot/'runtime-manifests/release-manifest.json'
    assert sha(oldRelease)==old['runtimeCandidateReleaseSHA256']
    verified=chain.verify_predecessor((previous/'callback-normal-restart-plan.private.json').read_bytes(),journal.read_bytes(),
      (previous/'callback-r777-result.json').read_bytes(),expected_journal_sha256=expectedJournal,
      expected_release_sha256=old['runtimeCandidateReleaseSHA256'],expected_application=str(G),
      expected_stage_root=str(previous),expected_data_directory=str(G/'UserData/OriginalServer/database/data'))
    newRoot=R/'Document/Deployment/r45_owned_backend_r848_20261104'
    newPlan=newRoot/'full-source-and-restore-plan.private.json'
    assert sha(newPlan)=='204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09'
    new=json.loads(newPlan.read_bytes());candidate=newRoot/'candidate'
    config=(G/'private/server-configuration.json').read_bytes()
    assert {'bytes':len(config),'sha256':hashlib.sha256(config).hexdigest()}==new['configBefore']==old['configBefore']
    sys.path.insert(0,str(T));import owned_task_configuration_r637 as task
    before={task.CONFIG:config,task.PAYLOAD:(candidate/task.PAYLOAD).read_bytes(),task.RELEASE:(candidate/task.RELEASE).read_bytes()}
    after=task.task_candidate(before)
    # Inspect values only in memory; credentials/config never enter the proof.
    oldConfig=json.loads(config);newConfig=json.loads(after[task.CONFIG])
    assert oldConfig['configuration']['business']['flow.event-task-handle']=='OWN_FORM_CODE'
    assert newConfig['configuration']['business']['flow.event-task-handle']=='tj_eventTask'
    newConfig['configuration']['business']['flow.event-task-handle']='OWN_FORM_CODE';assert newConfig==oldConfig
    assert {'bytes':len(after[task.CONFIG]),'sha256':hashlib.sha256(after[task.CONFIG]).hexdigest()}==old['runtimeConfigurationAfterPin']
    oldPayload=json.loads((oldRoot/'runtime-manifests/payload-manifest.json').read_bytes())['files']
    newPayload=json.loads(after[task.PAYLOAD])['files']
    critical=['payload/business/application.jar','payload/business/portable_runtime.json','payload/business/process-boundary.jar',
      'payload/business/scheduling-isolation.jar','payload/platform/original-platform.jar','payload/platform/process-boundary.jar',
      'payload/platform/boot-loader.jar','payload/business/lib/mysql-connector-j-8.0.33.jar']
    assert all(oldPayload[n]==newPayload[n]for n in critical)
    config=None;oldConfig=None;newConfig=None
    runtimePins={n:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}for n,raw in after.items()};before.clear();after.clear()
    assert runtimePins[task.RELEASE]['sha256']!=old['runtimeCandidateReleaseSHA256']
    budget=load('feedback_pre_budget_r878',T/'bounded_build_job_r671.py')
    mem=budget.memory_snapshot();assert min(mem['availablePhysicalBytes'],mem['availableCommitBytes'])>=2*1024**3
    jobsPath=G/'tools/original_server_windows_job.py';assert sha(jobsPath)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
    jobs=load('feedback_pre_jobs_r878',jobsPath)
    O.mkdir();classes=O/'classes';classes.mkdir()
    source=O/'CallbackRowsGoldenR878.java'
    source.write_text('''import java.util.*;
public final class CallbackRowsGoldenR878 {
 public static void main(String[]args)throws Exception {
  List<OwnedOriginalCallbacksR648.Row> rows=new ArrayList<>();
  for(int n:new int[]{1,2}) {List<String> v=new ArrayList<>(Collections.nCopies(17,null));
   v.set(0,"a546"+String.format("%028x",n));v.set(1,"OWN_MANAGER_CALLBACK_"+v.get(0));
   v.set(2,"合成回调"+n);v.set(3,"3");v.set(4,"3");v.set(5,"{\\"url\\":\\"http://127.0.0.1:50123/synthetic\\"}");v.set(8,"1");
   rows.add(new OwnedOriginalCallbacksR648.Row(v));}
  System.out.println(OwnedOriginalCallbackProvisioningR659.rowsSHA256(rows));
 }
}''',encoding='utf8')
    terminals=[]
    def execute(name,args):
      log=O/(name+'.log')
      with log.open('xb')as out:
        p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,512*1024**2)
        try:
          while p.poll()is None:
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:print('SAME_GOLDEN_CHILD_HANDLE_LIVE_NO_RESTART',flush=True)
          while job.active_processes():time.sleep(.1)
          metrics=cap.metrics()
        finally:
          # Do not close a live Job or force termination on observation failure.
          if p.poll()is not None and job.active_processes()==0:job.close()
        terminals.append({'stage':name,'exitCode':p.returncode,'actualJobDescendantsZero':True,'budget':metrics,'forceTerminationUsed':False})
      assert p.returncode==0,'PRODUCTION_ROW_DIGEST_PARITY_PROCESS_FAILED'
    jdk=G/'runtime/jdk17/bin'
    sources=[T/'OwnedOriginalCallbacksR648.java',V/'task_ui_r806/OwnedCallbackProvisioningJournalR658.java',T/'OwnedOriginalCallbackProvisioningR659.java',source]
    execute('compile',[str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),*map(str,sources)])
    execute('production-digest',[str(jdk/'java.exe'),'-Xmx128m','-cp',str(classes),'CallbackRowsGoldenR878'])
    import test_callback_predecessor_r877 as test
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test))
    assert result.wasSuccessful() and result.testsRun==9
    expected=chain.rows_sha256(test.rows())
    assert (O/'production-digest.log').read_text('ascii').strip()==expected
    assert sha(journal)==expectedJournal and sha(newPlan)=='204cf93719a835cbba7743b4f34193f94195b1cb681202863660fa06b3503c09'
    proof={'schema':'xnby.owned-feedback-preconditions.v1','passed':True,'predecessor':verified,'syntheticMetadataTestsPassed':9,
      'productionJavaRowDigestParityPassed':True,'actualProductionSources':{str(p):sha(p)for p in sources},
      'oldRuntimeReleaseSHA256':old['runtimeCandidateReleaseSHA256'],'r45CodeCandidateReleaseSHA256':new['candidateReleaseSHA256'],
      'plannedR45TaskRuntimePins':runtimePins,'onlySyntheticTaskCodeSettingWouldChange':True,
      'plannedTaskConfigMatchesPriorAcceptedOriginalModelConfig':True,'unchangedOriginalDependencies':{n:newPayload[n] for n in critical},
      'terminals':terminals,'serviceStartPerformed':False,'databaseAccessPerformed':False,'callbackSQLPerformed':False,
      'taskCreateFeedbackApprovePerformed':False,'crossReleaseExecutionJournalAndRuntimeStillRequired':True,
      'credentialsOrRawConfigPersisted':False,'nativeEXEBuiltOrRun':False,'publicOrDesktopTouched':False,'fullCloneReady':False}
    (O/'verification.json').write_bytes(enc(proof));(O/'metadata-tests.log').write_text(log.getvalue(),encoding='utf8')
    print(json.dumps({k:v for k,v in proof.items() if k not in ['actualProductionSources','unchangedOriginalDependencies','terminals','predecessor','plannedR45TaskRuntimePins']},ensure_ascii=False))
if __name__=='__main__':main()
