"""Original normal-user event/research/task/feedback/close APIs on the published business chain and the original native platform."""
import uuid,urllib.parse
import verify_emergency_business_http_20261030 as c
from original_normal_workflow_http_cases_20261031 import run as task_workflow

def run(root,request,headers,platform_port,business_port,snapshot):
 cases=[];actor=headers['own_operator_a'];name='Own event chain '+uuid.uuid4().hex[:12]
 status,identity=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode=cqweh-endanger',authorization=actor);info=(identity.get('data')or{}).get('userInfo')or{};shape={key:len(value)for key,value in info.items()if isinstance(value,str)and ('organize'in key.lower()or'department'in key.lower()or'company'in key.lower())and key.lower().endswith('id')};c.dump(root/'own-actor-organization-id-shape.json',{'nativeHTTP':status,'nativeCode':identity.get('code'),'syntheticActorOnly':True,'organizationIdentifierLengthsOnly':shape,'original32ColumnContractUsedInThisControlCase':True,'prior36IdentifierFailureStillOpen':True})

 def call(label,method,path,body=None):
  status,value=request(business_port,method,path,authorization=actor,json_body=body)
  cases.append({'case':label,'httpStatus':status,'businessCode':value.get('code'),'message':str(value.get('msg',value.get('message','')))[:160]});c.dump(root/'original-emergency-business-chain-cases.json',{'cases':cases,'onlySyntheticUsersAndData':True,'credentialsOrTokensRecorded':False})
  assert status==200 and value.get('code')==0,'ORIGINAL_EMERGENCY_API_FAILED:'+label
  return value.get('data')
 event={'eventName':name,'eventContent':'Own original event API chain','eventType':'OWN','eventLevel':'1','eventLocation':'Own isolated test location','reportTime':'2026-10-31 14:10:30'}
 assert call('normal-event-report','POST','/serv/eventInfo/save',event) is True,'ORIGINAL_EVENT_REPORT_NOT_SAVED'
 page=call('reported-event-query','GET','/serv/eventInfo/getPage?current=1&size=5&eventName='+urllib.parse.quote(name));records=page.get('records',[]);matches=[r for r in records if r.get('eventName')==name];assert len(matches)==1,'ONE_OWN_API_CREATED_EVENT_REQUIRED';record=matches[0];event_id=record['id'];number=record['eventNumber'];assert record.get('researchStatus')=='0' and not record.get('flowId'),'ORIGINAL_EVENT_REPORT_IS_NOT_AUTOMATIC_WORKFLOW'
 assert call('normal-event-research','POST','/serv/eventInfo/updateById',{'id':event_id,'eventLevel':'1','researchStatus':'1','researchResult':'Own original judgment'}) is True,'ORIGINAL_EVENT_RESEARCH_NOT_SAVED'
 selected=call('original-task-event-selector','GET','/serv/eventInfo/getPage?current=1&size=5&researchStatus=1&eventName='+urllib.parse.quote(name));assert any(r.get('id')==event_id and r.get('researchStatus')=='1' for r in selected.get('records',[])),'ORIGINAL_RESEARCHED_EVENT_NOT_SELECTABLE'
 snapshot('final');researched=c.read(root/'workflow-snapshot-final.json');c.dump(root/'workflow-snapshot-event-researched.json',researched);assert not researched['act_ru_task'],'EVENT_REPORT_MUST_NOT_CREATE_SYNTHETIC_WORKFLOW'
 linked=[]
 def linked_request(port,method,path,*args,**kwargs):
  if port==business_port and method=='POST' and path=='/serv/eventTask/save':
   body=dict(kwargs['json_body']);body.update(infoId=event_id,eventNumber=number,eventName=name,executorDept='Own isolated organization',executor='Own intended executor',acceptanceDept='Own acceptance organization');kwargs=dict(kwargs,json_body=body);linked.append(True)
  return request(port,method,path,*args,**kwargs)
 task_workflow(root,linked_request,headers,platform_port,business_port,snapshot);assert linked==[True],'ONE_REAL_EVENT_LINKED_TASK_DISPATCH_REQUIRED';approved=c.read(root/'workflow-snapshot-approved.json');c.dump(root/'workflow-snapshot-original-approval.json',approved);assert len(approved['event_task'])==1;task=approved['event_task'][0];assert task['infoid']==event_id and task['taskstatus']=='1','REAL_API_EVENT_AND_APPROVED_TASK_LINK_REQUIRED';task_id=task['id'];flow_id=task['flowid']
 # This probes the original update API on a completed task; it does not claim the hidden UI disposal button was tested.
 feedback={'id':task_id,'taskStatus':'1','disposeTime':'2026-10-31 14:50:30','feedbackInfo':'Own persisted feedback','evaluationSum':'Own persisted evaluation'}
 assert call('completed-task-feedback-update-api','POST','/serv/eventTask/updateById',feedback) is True,'ORIGINAL_FEEDBACK_API_NOT_SAVED'
 detail=call('completed-task-feedback-readback','GET','/serv/eventTask/getById?id='+urllib.parse.quote(task_id));assert detail.get('feedbackInfo')==feedback['feedbackInfo'] and detail.get('evaluationSum')==feedback['evaluationSum'] and detail.get('disposeTime')==feedback['disposeTime'] and detail.get('taskStatus')=='1' and detail.get('flowId')==flow_id,'FEEDBACK_TIME_EVALUATION_OR_FLOW_LINK_NOT_PERSISTED'
 assert call('normal-event-close','GET','/serv/eventInfo/closeRecord?id='+urllib.parse.quote(event_id)) is True,'ORIGINAL_EVENT_CLOSE_NOT_SAVED'
 closed=call('closed-event-readback','GET','/serv/eventInfo/getById?id='+urllib.parse.quote(event_id));assert closed.get('researchStatus')=='4' and closed.get('researchResult')=='Own original judgment','ORIGINAL_CLOSED_RESEARCH_STATE_REQUIRED';snapshot('approved');c.dump(root/'workflow-snapshot-module-closed.json',c.read(root/'workflow-snapshot-approved.json'))
 c.dump(root/'original-emergency-business-chain-result.json',{'schema':'xnby.original-emergency-business-chain.http.v1','cases':cases,'actualPublishedBusinessAndR22SessionBoundary':True,'normalEventCreatedThroughOriginalAPI':True,'researchState0To1AndSourceSelectorMatched':True,'apiCreatedEventLinkedToRealOriginalTaskWorkflow':True,'taskSubmitWrongAssigneeRefusalAssignedApprovalAndAutomatic2To1Passed':True,'completedTaskFeedbackFieldsAndDatePersistedByOriginalAPI':True,'eventClosedThroughOriginalAPIResearchState4':True,'eventReportDidNotCreateAnInventedApprovalFlow':True,'feedbackDisposalButtonOrPreapprovalUIFlowAccepted':False,'realNangangDesignerTemplateImported':False,'notificationExternalDeliveryOrBrowserAccepted':False,'syntheticDesignerDefinitionOnly':True,'formalRuntimeOrPublicChanged':False,'fullCloneReady':False})
