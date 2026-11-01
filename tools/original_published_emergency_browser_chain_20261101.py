"""Original API flow followed by exact published-frontend readonly task inspection."""
from pathlib import Path
import json,subprocess
import verify_emergency_business_http_20261030 as c
from original_published_emergency_workflow_http_20261101 import run as workflow
from original_published_emergency_portal_host_20261101 import host
from original_published_emergency_session_handoff_20261101 import handoff

def run(root,request,headers,platform_port,business_port,snapshot,password):
 workflow(root,request,headers,platform_port,business_port,snapshot)
 task=c.read(root/'workflow-snapshot-module-closed.json')['event_task'][0];status,detail=request(business_port,'GET','/serv/eventTask/getById?id='+task['id'],authorization=headers['own_operator_a']);assert status==200 and detail['code']==0;body=detail['data'];assert body['taskStatus']=='1'
 own=c.read(root/'own-normal-login.private.json');assert own['credentialsSynthetic']
 with host(root,business_port,platform_port,'task-reopen')as base:
  with handoff(root,request,headers,platform_port,business_port,'task-reopen','own_operator_a')as(descriptor,record):
   wire={'base':base,'phase':'reopen','account':'own_operator_a','password':password,'expectedWirePassword':own['wirePassword'],'expectedUserId':own['accounts']['own_operator_a']['id'],'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True,'syntheticSessionHandoff':descriptor,'id':body['id'],'taskName':body['taskName'],'feedbackInfo':body['feedbackInfo'],'evaluationSum':body['evaluationSum'],'disposeTime':body['disposeTime']};raw=json.dumps(wire).encode('utf-8')
   with open(root/'published-task-browser.stdout.log','wb')as out,open(root/'published-task-browser.stderr.log','wb')as err:
    process=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(c.T/'verify_published_emergency_detail_browser_20261101.mjs'),root.as_posix()],stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/'published-task-browser-started.json',{'pid':process.pid});process.communicate(raw)
   wire.clear();del raw;assert process.returncode==0,'PUBLISHED_EMERGENCY_BROWSER_FAILED';assert record['accepted']and record['wrongNonceRejected']==1 and record['replayRejected']==1
   assert c.read(root/'compiled-task-browser-reopen/browser-terminal.json')['normalBrowserClosed']
 own.clear();c.dump(root/'published-emergency-browser-result.json',{'exact204PublishedEmergencyFilesUsed':True,'old206CandidateNotUsed':True,'originalLoginMenuTaskListReadonlyDetailPassed':True,'persistedFeedbackTimeEvaluationRendered':True,'normalBrowserAndGatewayClosed':True,'browserBusinessUpdates':0,'feedbackButtonOrPreapprovalUIAccepted':False,'formalOrPublicInstalled':False,'fullCloneReady':False})
