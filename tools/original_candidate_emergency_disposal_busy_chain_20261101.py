"""Both original business orderings; manual save only through the real published-base client."""
from pathlib import Path
import json,subprocess
import verify_emergency_business_http_20261030 as c
from original_published_manual_disposal_http_20261101 import run as manual
from original_candidate_emergency_disposal_busy_host_20261101 import host
from original_published_disposal_session_handoff_20261101 import handoff

def run(root,request,headers,platform_port,business_port,snapshot,password):
 seen=[]
 with host(root,business_port,platform_port,'task-dispose')as base:
  def browser(phase,body):
   own=c.read(root/'own-normal-login.private.json');assert own['credentialsSynthetic']
   with handoff(root,request,headers,platform_port,business_port,'task-'+phase,'own_operator_a')as(descriptor,record):
    wire={'base':base,'phase':phase,'account':'own_operator_a','password':password,'expectedWirePassword':own['wirePassword'],'expectedUserId':own['accounts']['own_operator_a']['id'],'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True,'syntheticSessionHandoff':descriptor,'taskName':'Own manual first task',**body};raw=json.dumps(wire).encode('utf-8')
    with open(root/('published-disposal-browser-'+phase+'.stdout.log'),'wb')as out,open(root/('published-disposal-browser-'+phase+'.stderr.log'),'wb')as err:
     process=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(c.T/'verify_candidate_emergency_disposal_busy_browser_20261101.mjs'),root.as_posix()],stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/('published-disposal-browser-'+phase+'-started.json'),{'pid':process.pid});process.communicate(raw)
    wire.clear();del raw;assert process.returncode==0,'PUBLISHED_EMERGENCY_DISPOSAL_BROWSER_FAILED';assert record['accepted']and record['wrongNonceRejected']==1 and record['replayRejected']==1
    path=root/('compiled-task-browser-'+phase);assert c.read(path/'browser-terminal.json')['normalBrowserClosed'];result=c.read(path/'result.json');login=next(x for x in result['http']if x['path'].endswith('/oauth/Login'));assert login['parameterPlacement']=='query'and login['noFormBody']and login['formCipherMatchesNormalHTTP']and login['formAccountMatched']
   own.clear();return result
  def through_browser(port,method,path,*args,**kwargs):
   body=kwargs.get('json_body')or{}
   if port==business_port and method=='POST'and path=='/serv/eventTask/updateById'and body.get('feedbackInfo')=='Own feedback before approval':
    assert not seen;seen.append(dict(body));result=browser('dispose',body);saved=[x for x in result['http']if x['path'].endswith('/eventTask/updateById')and x.get('httpStatus')==200 and x.get('businessCode')==0 and x.get('saved')];assert len(saved)==1 and result['updateAttempts']==2 and result['failedBeforeServer']==1;return saved[0]['httpStatus'],{'code':saved[0]['businessCode'],'data':saved[0]['saved']}
   return request(port,method,path,*args,**kwargs)
  manual(root,through_browser,headers,platform_port,business_port,snapshot);assert len(seen)==1;browser('reopen',seen[0])
 c.dump(root/'published-emergency-disposal-browser-result.json',{'base204WithDeclaredLoginAndDisposalGuard':True,'old206FrontendOrR10TaskLayersUsed':False,'bothApprovalFirstAndManualFirstOriginalFlowsPassed':True,'manualSavePerformedOnlyThroughRealCompiledClient':True,'requiredFieldsAndDoubleClickSingleWritePassed':True,'failedRequestKeepsValuesAndRestoresSubmitWithError':True,'pendingSubmitLoadingAndDisabledObserved':True,'originalAutomaticCallbackAfterManualDisposalHTTPObserved':True,'feedbackDateEvaluationAndFlowLinkRetainedAfterNativeApproval':True,'normalBrowserAndGatewayClosed':True,'realNangangDefinitionOrRoleConfigurationImported':False,'formalOrPublicInstalled':False,'fullCloneReady':False})
