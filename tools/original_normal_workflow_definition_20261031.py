"""Prepare only synthetic form/flow input from previously pinned owned original-model artifacts."""
import copy,json
import verify_emergency_business_http_20261030 as c

def prepare(root,business_port):
 source=c.W/'task-business-workflow-bridge-r6';inputs=[source/'original-template-input.json',source/'original-form-storage-assembly.json'];original=c.read(inputs[0]);form=c.read(inputs[1]);assert original['originalConverterUsed'] and not original['realNangangDesignerTemplateImported'] and form['syntheticFormDefinitionAndRows'] and not form['originalFormMethodsReplaced'];ids={name:'a532'+format(value,'028x') for name,value in [('form',1),('template',2),('version',3),('group',4),('interface',5),('event',6)]};tree=copy.deepcopy(original['tree']);tree['properties']['formId']=ids['form'];tree['content']='Own task applicant';tree['childNode']['content']='Own assigned reviewer';tree['childNode']['properties'].update(assigneeType=6,approvers=['a531'+format(101,'028x')+'--user'])
 def rewrite(value):
  if isinstance(value,dict):return {k:rewrite(v) for k,v in value.items()}
  if isinstance(value,list):return [rewrite(v) for v in value]
  if value=='OWN_INTERFACE':return ids['interface']
  return value
 tree=rewrite(tree);version=copy.deepcopy(original['version']);version.update(id=ids['version'],templateId=ids['template'],groupId=ids['group'],processDefinitionId=None,deploymentId=None,secondKey='OWN_NORMAL_WORKFLOW_1',templateName='Own normal workflow',fullName='Own normal version',flowTemplateJson=json.dumps(tree,ensure_ascii=False),formIds=json.dumps([ids['form']]),creatorUserId=None,creatorTime=None,lastModifyUserId=None,lastModifyTime=None)
 body={'id':ids['template'],'enCode':'OWN_NORMAL_WORKFLOW','fullName':'Own normal workflow','type':0,'category':'OWN_CATEGORY','sortCode':1,'flowTemplateJson':json.dumps([version],ensure_ascii=False)}
 formbody={'id':ids['form'],'enCode':'OWN_FORM_CODE','fullName':'Own normal workflow form','flowType':0,'formType':2,'category':'OWN_CATEGORY','dbLinkId':'0','propertyJson':form['formPropertyJson'],'draftJson':form['formPropertyJson'],'tableJson':form['tableJson'],'sortCode':1}
 api={'apiData':{'url':'http://127.0.0.1:'+str(business_port)+'/serv/eventTask/callback','method':1,'bodyType':1,'body':'','header':[],'query':[{'field':'id','source':'1','defaultValue':'id'},{'field':'result','source':'1','defaultValue':'result'}]}}
 c.dump(root/'own-workflow-definition.json',{'formId':ids['form'],'templateId':ids['template'],'versionId':ids['version'],'interfaceId':ids['interface'],'eventId':ids['event'],'formBody':formbody,'templateBody':body,'interfaceConfiguration':api,'syntheticInputOnly':True,'normalRoleDirectoryUsed':True,'notificationsNotYetAccepted':True});c.dump(root/'workflow-definition-input-pins.json',{str(p):c.sha(p) for p in inputs})
