"""Actual normal-user form/template/dispatch/approval requests against both original application mains."""
import json,uuid,time
import verify_emergency_business_http_20261030 as c

def run(root,request,headers,platform_port,business_port,snapshot):
 definition=c.read(root/'own-workflow-definition.json');cases=[];a=headers['own_operator_a'];b=headers['own_reviewer_b']
 def call(name,port,method,path,actor,body=None,extra=None):
  status,value=request(port,method,path,authorization=actor,json_body=body,extra_headers=extra);cases.append({'case':name,'httpStatus':status,'businessCode':value.get('code'),'message':str(value.get('msg',value.get('message','')))[:200]});c.dump(root/'normal-workflow-http-cases.json',{'cases':cases,'originalAPIUsed':True,'credentialsOrTokensRecorded':False});return status,value
 def native(name,method,path,actor,body=None):
  status,value=call(name,platform_port,method,path,actor,body);assert status==200 and value.get('code')==200,'ORIGINAL_WORKFLOW_API_FAILED:'+name;return value.get('data')
 native('create-form','POST','/api/flowForm/Form',a,definition['formBody']);native('release-form','POST','/api/flowForm/Form/Release/'+definition['formId']+'?isRelease=1',a)
 native('create-template','POST','/api/workflow/Engine/flowTemplate',a,definition['templateBody']);native('release-template','POST','/api/workflow/Engine/flowTemplate/Release/'+definition['templateId'],a)
 forms=native('original-form-to-flow','GET','/api/flowForm/Form/getFlowIdByEnCode?enCode=OWN_FORM_CODE',a);assert any(row.get('flowId')==definition['templateId'] for row in forms),'ORIGINAL_FORM_FLOW_RELATION_MISSING'
 versions=native('original-version-selection','GET','/api/workflow/Engine/flowTemplate/FlowJsonList/'+definition['templateId'],a);assert any(row.get('id')==definition['versionId'] for row in versions),'ORIGINAL_MAIN_VERSION_MISSING';snapshot('prepared')
 for label,wire,agent in [('canonical-prefix','Bearer '+a.split(' ',1)[1] if ' ' in a else 'Bearer '+a,None),('java-agent-original-prefix',a,'Java-http-client/17.0.12')]:
  extra={'User-Agent':agent} if agent else None;call('diagnostic-native-'+label,platform_port,'GET','/api/flowForm/Form/getFlowIdByEnCode?enCode=OWN_FORM_CODE',wire,extra=extra)
 rid=uuid.uuid4().hex;task={'infoId':definition['eventId'],'eventNumber':'OWN-NORMAL-WORKFLOW-EVENT','eventName':'Own workflow event','taskName':'Own normal-user task','taskContent':'Own original workflow dispatch','dispatchTime':'2026-10-31 14:20:30'}
 status,value=call('authenticated-task-submit',business_port,'POST','/serv/eventTask/save',a,task,{'X-Task-Request-Id':rid});assert status==200 and value.get('code')==0 and value.get('data') is True,'AUTHENTICATED_TASK_SUBMIT_NOT_SAVED';snapshot('submitted');state=c.read(root/'workflow-snapshot-submitted.json');assert len(state['event_task'])==len(state['act_hi_procinst'])==len(state['act_ru_task'])==1,'ONE_REAL_PENDING_FLOW_REQUIRED';operators=state['flow_task_operator'];reviewer='a531'+format(101,'028x');operator=next(row for row in operators if row.get('fhandleid')==reviewer and row.get('ftasknodeid'));node=operator['ftasknodeid'];document=state['act_ru_task'][0]['procinstid'];assert state['event_task'][0]['flowid']==document and state['event_task'][0]['taskstatus']=='2','BUSINESS_NATIVE_INSTANCE_AND_PENDING_STATE_REQUIRED'
 audit={'id':document,'flowId':definition['versionId'],'formId':definition['formId'],'formData':{'approval_note':'Own real approval'},'handleOpinion':'Own real approval'}
 status,value=call('non-assignee-audit-rejected',platform_port,'POST','/api/workflow/Engine/FlowBefore/Audit/'+node,a,audit);assert value.get('code')!=200,'NON_ASSIGNEE_MUST_NOT_APPROVE';snapshot('wrong');wrong=c.read(root/'workflow-snapshot-wrong.json');assert wrong['act_ru_task']==state['act_ru_task'] and wrong['event_task']==state['event_task'],'NON_ASSIGNEE_MUST_NOT_ADVANCE_OR_CALLBACK'
 native('assigned-reviewer-audit','POST','/api/workflow/Engine/FlowBefore/Audit/'+node,b,audit);
 for attempt in range(1,9):
  label='approved-'+str(attempt);snapshot(label);approved=c.read(root/('workflow-snapshot-'+label+'.json'))
  if approved['event_task'][0].get('taskstatus')=='1':break
  time.sleep(.15)
 c.dump(root/'workflow-snapshot-approved.json',approved);assert not approved['act_ru_task'],'ORIGINAL_PROCESS_MUST_FINISH';assert approved['act_hi_procinst'][0].get('endtime'),'ORIGINAL_PROCESS_HISTORY_MUST_BE_ENDED';assert approved['event_task'][0].get('taskstatus')=='1','REAL_ORIGINAL_CALLBACK_MUST_UPDATE_BUSINESS';assert len(approved['own_approval_form'])==1 and approved['own_approval_form'][0].get('approvalnote')=='Own real approval','ORIGINAL_FORM_DATA_MUST_PERSIST'
 c.dump(root/'normal-workflow-http-result.json',{'schema':'xnby.original-normal-workflow.http.v1','cases':cases,'originalNormalUsersAndBothApplicationMains':True,'originalFormTemplateCreationReleaseAndSelection':True,'realTaskDispatchAndAssignedReviewerApproval':True,'nonAssigneeRejectedWithoutAdvancement':True,'originalFormDataPersisted':True,'originalCallbackUpdatedBusiness':True,'syntheticDesignerDefinitionOnly':True,'realNangangDesignerTemplateImported':False,'notificationOrBrowserAccepted':False,'formalInstalledOrPublicChanged':False,'fullCloneReady':False})
