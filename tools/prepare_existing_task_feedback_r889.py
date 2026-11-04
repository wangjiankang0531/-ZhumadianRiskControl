"""Resume only the already-created owned task; never reissue task creation."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;S=V/'feedback_r887';D=V/'feedback_r889';R=Path('D:/Project/Zhumadian');W=R/'work/original-manager-full-lifecycle-r609/feedback-r880'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
 assert s.count(a)==1,a[:140]
 return s.replace(a,b)
def main():
 assert not D.exists() and not(W/'after-submit-r889').exists()
 pins=json.loads((S/'feedback-resume-r887-source-pins.json').read_bytes())['files'];assert all(sha(Path(n))==pin for n,pin in pins.items())
 prior=json.loads((R/'work/fb887/verified-feedback-chain-r887.json').read_bytes());created=json.loads((W/'ui-create-r887/result.json').read_bytes());feedback=json.loads((W/'ui-feedback-submit-r880/result.json').read_bytes())
 assert not prior['passed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
 assert created['passed']and created['taskSaveRequests']==1 and created['taskSaveConfirmed']and not created['APIsMocked']
 assert not feedback['passed']and feedback['feedbackUpdateRequests']==feedback['approvalRequests']==0 and not(W/'ui-feedback-submit-r880/feedback-issued.json').exists()
 assert sha(W/'normal-restart/callback-normal-restart-journal.private.properties')=='234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc'
 assert not(W/'original-field-baseline-r880.private.properties').exists()
 D.mkdir()
 for p in S.rglob('*'):
  if p.is_file()and p.name!='feedback-resume-r887-source-pins.json'and str(p)in pins:
   q=D/p.relative_to(S);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 q=D/'OwnedCallbackProvisioningJournalR658.java';s=q.read_text('utf8')
 s=one(s,'Path first=root.resolve("feedback-r880/first-start"),second=root.resolve("feedback-r880/normal-restart");', 'Path first=root.resolve("feedback-r880/first-start"),second=root.resolve("feedback-r880/normal-restart"),third=root.resolve("feedback-r880/after-submit-r889");')
 s=one(s,'path.getParent().equals(first)||path.getParent().equals(second)', 'path.getParent().equals(first)||path.getParent().equals(second)||path.getParent().equals(third)')
 s=one(s,'(transition?root.resolve("task-ui-r806/normal-restart"):first)', '(transition?root.resolve("task-ui-r806/normal-restart"):path.getParent().equals(third)?second:first)')
 a='        if(transition)need(digest(previous).equals("6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98"),"PINNED_OLD_CALLBACK_JOURNAL_REQUIRED");'
 s=one(s,a,a+'\n        if(path.getParent().equals(third))need(digest(previous).equals("234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc"),"PINNED_CREATED_TASK_PREDECESSOR_REQUIRED");')
 q.write_text(s,encoding='utf8')
 q=D/'OwnOriginalCallbackRuntimeR770.java';s=q.read_text('utf8');s=one(s,'Set.of("first-start","normal-restart").contains(s)','Set.of("first-start","normal-restart","after-submit-r889").contains(s)');q.write_text(s,encoding='utf8')
 q=D/'callback_plan_r880.py';s=q.read_text('utf8').replace("['first-start','normal-restart']","['first-start','normal-restart','after-submit-r889']")
 a="previousRoot=ATTEMPT/'task-ui-r806/normal-restart' if stage=='first-start'else ATTEMPT/'feedback-r880/first-start'"
 s=one(s,a,"previousRoot=ATTEMPT/'feedback-r880/normal-restart'if stage=='after-submit-r889'else ATTEMPT/'task-ui-r806/normal-restart'if stage=='first-start'else ATTEMPT/'feedback-r880/first-start'")
 a="    if stage=='first-start':need(sha(previousJournal)=='6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98','PINNED_PREDECESSOR_JOURNAL_REQUIRED')"
 s=one(s,a,a+"\n    if stage=='after-submit-r889':need(sha(previousJournal)=='234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc','PINNED_CREATED_TASK_PREDECESSOR_REQUIRED')")
 q.write_text(s,encoding='utf8')
 q=D/'run_callbacks_r880.py';s=q.read_text('utf8').replace("['first-start','normal-restart']","['first-start','normal-restart','after-submit-r889']");q.write_text(s,encoding='utf8')
 q=D/'OwnManagerBusinessReadbackR783.java';s=q.read_text('utf8').replace('snapshot-r887-','snapshot-r889-');q.write_text(s,encoding='utf8')
 q=D/'feedback_browser_r880.mjs';s=q.read_text('utf8');s=one(s,"const O=root+'/ui-'+w.mode+'-r880';", "const O=root+'/ui-'+w.mode+'-r889';")
 a="const item=Array.from(document.querySelectorAll('.el-form-item')).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\\s:：]/g,'')===${JSON.stringify(label)});const input=item?.querySelector('input,textarea');if(!input||input.disabled||input.readOnly)return false;"
 b="const controls=[...new Set(Array.from(document.querySelectorAll('.el-form-item')).filter(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.replace(/[\\s:：]/g,'')===${JSON.stringify(label)}).flatMap(e=>Array.from(e.querySelectorAll('input,textarea'))))].filter(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly);if(controls.length!==1)return false;const input=controls[0];"
 s=one(s,a,b)
 a='const e=Array.from(document.querySelectorAll(".el-form-item")).find(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="处置时间")?.querySelector("input");'
 b='const controls=[...new Set(Array.from(document.querySelectorAll(".el-form-item")).filter(e=>e.querySelector(".el-form-item__label")?.textContent.trim()==="处置时间").flatMap(e=>Array.from(e.querySelectorAll("input"))))].filter(e=>e.getClientRects().length&&!e.disabled&&!e.readOnly);if(controls.length!==1)throw Error("ONE_EDITABLE_DISPOSAL_TIME_REQUIRED");const e=controls[0];'
 s=one(s,a,b);q.write_text(s,encoding='utf8')
 q=D/'normal_manager_browser_r880.mjs';s=q.read_text('utf8');s=one(s,"const O=root+'/ui-'+w.mode+'-r806';", "const O=root+'/ui-'+w.mode+'-r889';") if "const O=root+'/ui-'+w.mode+'-r806';"in s else one(s,"const O=root+'/ui-'+w.mode+'-r880';", "const O=root+'/ui-'+w.mode+'-r889';");q.write_text(s,encoding='utf8')
 q=D/'feedback_probe_r880.py';s=q.read_text('utf8').replace("P=W/'runtime-resume-r887'","P=W/'runtime-resume-r889'").replace('feedback-resume-r887-source-pins.json','feedback-existing-r889-source-pins.json').replace("classes=W/'classes-r887'","classes=W/'classes-r889'").replace('snapshot-r887-','snapshot-r889-')
 s=s.replace("folder=W/('ui-'+mode+'-r880')","folder=W/('ui-'+mode+'-r889')")
 begin=s.index("   inspected=snapshot('inspect');");end=s.index("   checked=snapshot('feedback');",begin)
 s=s[:begin]+'''   submitted=snapshot('pending-resume')
   previous=props(W/'snapshot-r887-submitted.properties')
   assert all(submitted[k]==previous[k]for k in ['taskId','instanceId','operatorId','engineTaskId']),'EXACT_ALREADY_CREATED_TASK_REQUIRED'
   refreshed=W/'snapshot-r889-submitted.properties';assert not refreshed.exists();refreshed.write_bytes((W/'snapshot-r889-pending-resume.properties').read_bytes())
   callbackStage=W/'after-submit-r889';callbackStage.mkdir();(callbackStage/'own-normal-manager-test.marker').write_bytes(b'own-original-manager-full-lifecycle-r609\\n')
   cb=callbacks.run_callback_setup('after-submit-r889',J(O/'callback-first-start-plan.private.json')['attemptId'],plan['runtimeCandidateReleaseSHA256'],gateway_port=gateway_port,controller_process=controller_process)
   assert cb['passed']and callbacks.children_exited()
   feedback=browser('feedback-submit',submitted);assert feedback['feedbackUpdateRequests']==1 and feedback['feedbackSaveConfirmed']
'''+s[end:]
 s=one(s,"actualTaskCreationUI=label=='first-start'", "actualTaskCreationUI=False,previouslyCreatedTaskIdentityVerified=True")
 q.write_text(s,encoding='utf8')
 old=D/'run_feedback_resume_r887.py';s=old.read_text('utf8')
 s=s.replace("P=W/'runtime-resume-r887';Z=R/'work/fb887'","P=W/'runtime-resume-r889';Z=R/'work/fb889'").replace('feedback-resume-r887-source-pins.json','feedback-existing-r889-source-pins.json')
 s=s.replace("not(W/'normal-restart').exists()","not(W/'after-submit-r889').exists()")
 a=s.index("prior=J(R/'work/ep885/");b=s.index('memory=available()',a)
 s=s[:a]+'''prior=J(R/'work/fb887/verified-feedback-chain-r887.json')
assert not prior['passed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
created=J(W/'ui-create-r887/result.json');assert created['passed']and created['taskSaveRequests']==1 and created['taskSaveConfirmed']
oldFeedback=J(W/'ui-feedback-submit-r880/result.json');assert not oldFeedback['passed']and oldFeedback['feedbackUpdateRequests']==0 and not(W/'ui-feedback-submit-r880/feedback-issued.json').exists()
assert sha(W/'normal-restart/callback-normal-restart-journal.private.properties')=='234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc'
'''+s[b:]
 s=s.replace('verified-feedback-chain-r887.json','verified-feedback-chain-r889.json').replace("prior=J(R/'work/fb887/verified-feedback-chain-r889.json')","prior=J(R/'work/fb887/verified-feedback-chain-r887.json')").replace('feedback-full-result-r887.json','feedback-full-result-r889.json').replace('feedback-not-started-r887.json','feedback-not-started-r889.json')
 old.unlink();(D/'run_existing_task_feedback_r889.py').write_text(s,encoding='utf8')
 for p in D.glob('*.py'):ast.parse(p.read_bytes(),filename=p.name)
 for p in D.glob('*.mjs'):assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True).returncode==0
 own=[p for p in D.rglob('*')if p.is_file()];external=[Path(n)for n in pins if not Path(n).is_relative_to(S)]
 (D/'feedback-existing-r889-source-pins.json').write_text(json.dumps({'files':{str(p):sha(p)for p in [*own,*external,Path(__file__)]},'taskCreationAllowed':False,'originalTaskAndEventPreserved':True,'controllerBudgetBytes':4*1024**3,'minimumAvailableBytes':7*1024**3},indent=2)+'\n',encoding='utf8')
 print('R889_PREPARED_EXISTING_TASK_ONLY_NO_RECREATE')
if __name__=='__main__':main()
