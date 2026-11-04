"""Continue the same unsubmitted task using a fresh verified callback stage."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;S=V/'feedback_r880';D=V/'feedback_r887';R=Path('D:/Project/Zhumadian');W=R/'work/original-manager-full-lifecycle-r609/feedback-r880'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):
 assert s.count(a)==1,a[:100]
 return s.replace(a,b)
def main():
 assert not D.exists() and not(W/'normal-restart').exists()
 pins=json.loads((S/'feedback-r880-source-pins.json').read_bytes())['files'];assert all(sha(Path(n))==pin for n,pin in pins.items())
 old=json.loads((R/'work/fb880/verified-feedback-chain-r880.json').read_bytes());ui=json.loads((W/'ui-create-r880/result.json').read_bytes())
 assert not old['passed'] and old['codeRestored'] and old['taskConfigurationRestoredBeforeCode'] and old['originalCurrentPointerRestored']
 assert ui['taskSaveRequests']==ui['researchRequests']==0 and not(W/'ui-create-r880/task-save-issued.json').exists()
 assert sha(W/'first-start/callback-normal-restart-journal.private.properties')=='86ffd49c9e381af5e00cc664bf971179b21a4bf72a3a39103b093aee8e17bf87'
 recovery=json.loads((R/'work/ep885/verified-recovery-r886.json').read_bytes());assert recovery['passed']and recovery['codeRestored']and recovery['originalCurrentPointerRestored']and recovery['allOriginalPIDsAndOwnedReferencesAbsent']
 diagnostic=json.loads((R/'work/event-picker-browser-r885/result.json').read_bytes());assert diagnostic['diagnosticCompleted']and diagnostic['queryDiagnostics'][0]['query']['exactOwnedEventPresent']
 for mode in ['feedback-submit','feedback-readonly','pending-approve','completed-readonly']:assert not(W/('ui-'+mode+'-r880')).exists()
 D.mkdir()
 own=[]
 for p in S.rglob('*'):
  if p.is_file() and p.name!='feedback-r880-source-pins.json' and str(p) in pins:
   relative=p.relative_to(S);q=D/relative;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());own.append(q)
 q=D/'OwnOriginalManagerDirectoryR609.java';s=q.read_text('utf8');s=one(s,'feedback-r880/runtime','feedback-r880/runtime-resume-r887');q.write_text(s,encoding='utf8')
 q=D/'OwnManagerBusinessReadbackR783.java';s=q.read_text('utf8').replace('snapshot-r880-','snapshot-r887-');q.write_text(s,encoding='utf8')
 q=D/'create_task_browser_r880.mjs';s=q.read_text('utf8').replace('ui-create-r880','ui-create-r887')
 s=one(s,"{confirmedFilterMatched:u.searchParams.get('researchStatus')==='1'}", "{confirmedFilterMatched:u.searchParams.get('researchStatus')==='1',expectedNameFilterMatched:u.searchParams.get('eventName')===w.eventName}")
 a=" const before=eventPageCount;await fill('事件名称',w.eventName,true);await clickButton('搜索',true);await until(()=>eventPageCount>before&&eventRows.some(row=>row.id===w.eventId));"
 b=""" await until(()=>requests.some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.confirmedFilterMatched&&r.httpStatus===200&&r.businessCode===0));
 const beforeRequests=requests.length;await fill('事件名称',w.eventName,true);await clickButton('搜索',true);
 await until(()=>requests.slice(beforeRequests).some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.confirmedFilterMatched&&r.expectedNameFilterMatched&&r.exactOwnedEventPresent)&&eventRows.some(row=>row.id===w.eventId));
 await until(()=>evaluate(`Array.from(document.querySelectorAll('.el-dialog .el-table__body tbody tr')).filter(e=>e.textContent.includes(${JSON.stringify(w.eventNumber)})&&e.textContent.includes(${JSON.stringify(w.eventName)})).length===1`));"""
 s=one(s,a,b);q.write_text(s,encoding='utf8')
 q=D/'feedback_probe_r880.py';s=q.read_text('utf8').replace("P=W/'runtime'","P=W/'runtime-resume-r887'").replace('feedback-r880-source-pins.json','feedback-resume-r887-source-pins.json')
 s=s.replace("classes=W/'classes-r880'","classes=W/'classes-r887'").replace('snapshot-r880-','snapshot-r887-')
 s=one(s,"folder=W/'ui-create-r880'","folder=W/'ui-create-r887'")
 s=one(s,"callbackStage=W/'first-start'","callbackStage=W/'normal-restart'")
 s=one(s,"cb=callbacks.run_callback_setup('first-start',","cb=callbacks.run_callback_setup('normal-restart',")
 q.write_text(s,encoding='utf8')
 q=D/'run_feedback_full_r880.py';s=q.read_text('utf8')
 s=s.replace("P=W/'runtime';Z=R/'work/fb880'","P=W/'runtime-resume-r887';Z=R/'work/fb887'")
 s=s.replace('feedback-r880-source-pins.json','feedback-resume-r887-source-pins.json').replace('REQUIRED=6*1024**3','REQUIRED=7*1024**3').replace('CONTROLLER_BUDGET=3*1024**3','CONTROLLER_BUDGET=4*1024**3')
 s=s.replace('six GiB physical','seven GiB physical').replace('three-GiB controller Job','four-GiB controller Job')
 s=one(s,"assert not W.exists()and not P.exists()and not Z.exists(),'EXACT_UNISSUED_FEEDBACK_SCOPE_REQUIRED'", "assert W.is_dir()and not P.exists()and not Z.exists()and not(W/'normal-restart').exists(),'EXACT_UNISSUED_FEEDBACK_RESUME_SCOPE_REQUIRED'")
 a=s.index("prior=J(R/'work/task-status-full-r875/");b=s.index('memory=available()',a)
 s=s[:a]+'''prior=J(R/'work/ep885/verified-recovery-r886.json')
assert prior['passed']and prior['codeRestored']and prior['originalCurrentPointerRestored']and prior['allOriginalPIDsAndOwnedReferencesAbsent']
oldUI=J(W/'ui-create-r880/result.json');assert oldUI['taskSaveRequests']==oldUI['researchRequests']==0 and not(W/'ui-create-r880/task-save-issued.json').exists()
assert sha(W/'first-start/callback-normal-restart-journal.private.properties')=='86ffd49c9e381af5e00cc664bf971179b21a4bf72a3a39103b093aee8e17bf87'
'''+s[b:]
 s=one(s,"W.mkdir();(W/'own-normal-manager-test.marker').write_bytes(b'own-original-manager-full-lifecycle-r609\\n');(W/'flight.private.properties').write_bytes((D/'flight.private.properties').read_bytes())", "assert(W/'own-normal-manager-test.marker').read_bytes()==b'own-original-manager-full-lifecycle-r609\\n'and(W/'flight.private.properties').read_bytes()==(D/'flight.private.properties').read_bytes()")
 s=s.replace('feedback-not-started-r880.json','feedback-not-started-r887.json').replace('verified-feedback-chain-r880.json','verified-feedback-chain-r887.json').replace('feedback-full-result-r880.json','feedback-full-result-r887.json')
 q.unlink();q=D/'run_feedback_resume_r887.py';q.write_text(s,encoding='utf8')
 for p in D.glob('*.py'):ast.parse(p.read_bytes(),filename=p.name)
 for p in D.glob('*.mjs'):assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True).returncode==0
 files=[p for p in D.rglob('*')if p.is_file()];external=[Path(n)for n in pins if not Path(n).is_relative_to(S)]
 (D/'feedback-resume-r887-source-pins.json').write_text(json.dumps({'files':{str(p):sha(p)for p in [*files,*external,Path(__file__)]},'sameUnsubmittedTaskNameAndEvent':True,'priorStageNotRepeated':True,'controllerBudgetBytes':4*1024**3,'minimumAvailableBytes':7*1024**3},indent=2)+'\n',encoding='utf8')
 print(json.dumps({'prepared':True,'sameUnusedFlightPreserved':True,'normalRestartCallbackStageFresh':True,'sameR45RuntimeManifest':True,'controllerBudgetGiB':4,'physicalAndCommitMinimumGiB':7,'servicesStarted':False}))
if __name__=='__main__':main()
