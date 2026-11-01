"""Exercise the actual normal-authenticated risk unit API using owned synthetic rows only."""
import uuid,urllib.parse
import verify_emergency_business_http_20261030 as c
def run(root,request,headers,platform_port,business_port,snapshot,password):
 # The unchanged nine risk cases are audited here; full task/workflow regression is a separate pending gate.
 assert c.read(root/'risk-unit-seed-result.json')['syntheticRows']==31
 cases=[]
 def call(label,method,path,body=None):
  status,value=request(business_port,method,path,authorization=headers['own_operator_a'],json_body=body)
  cases.append({'case':label,'httpStatus':status,'businessCode':value.get('code')});c.dump(root/'risk-unit-http-cases.json',{'cases':cases,'onlyOwnedSyntheticData':True})
  assert status==200 and value.get('code')==0,'ORIGINAL_RISK_API_FAILED:'+label
  return value.get('data')
 def page(label,current=1,**filters):return call(label,'GET','/serv/riskLevel/getPage?'+urllib.parse.urlencode({'current':current,'size':10,**filters}))
 initial=page('initial-newest-first');c.dump(root/'risk-unit-initial-shape.json',{'total':initial.get('total'),'totalType':type(initial.get('total')).__name__,'firstID':initial.get('records',[{}])[0].get('id'),'recordCount':len(initial.get('records',[]))});assert int(initial['total'])==31 and initial['records'][0]['id']==format(31,'019d'),'RISK_TIED_TIMESTAMP_ID_ORDER_REQUIRED'
 name='Own newest risk '+uuid.uuid4().hex[:10]
 body={'department':'Own risk department A','person':'Own risk person','analysisObject':name,'analysisUnit':'Own newest unit','riskLevel':'1','coordinate':'113.0,32.0'}
 assert call('normal-create','POST','/serv/riskLevel/save',body)is True
 exact=page('created-record-exact-readback',analysisObject=name)
 assert int(exact['total'])==1 and len(exact['records'])==1 and exact['records'][0]['analysisObject']==name,'OWN_CREATED_RECORD_EXACT_MATCH_REQUIRED'
 created=exact['records'][0]
 c.dump(root/'risk-unit-created-record-shape.json',{'exactOwnRecordMatched':True,'idPresent':bool(created.get('id')),'createTime':created.get('createTime'),'createTimeType':type(created.get('createTime')).__name__,'createByPresent':bool(created.get('createBy'))})
 latest=page('new-record-first');new=latest['records'][0]
 c.dump(root/'risk-unit-after-save-shape.json',{'total':latest.get('total'),'firstIsNewRecord':new.get('analysisObject')==name,'firstReturnedRecordCreateTimePresent':new.get('createTime')is not None})
 assert int(latest['total'])==32 and new.get('analysisObject')==name and new.get('createTime'),'RISK_ACTUAL_NEW_RECORD_MUST_BE_FIRST'
 second=page('second-page',current=2);assert len(second['records'])==10 and all(v['id']!=new['id']for v in second['records'])
 # All seeded rows have deterministic timestamps including ties, so ordering is checked across a page boundary.
 joined=latest['records'][1:]+second['records'];expected=[format(i,'019d')for i in range(31,12,-1)]
 assert [v['id']for v in joined]==expected,'RISK_STABLE_ORDER_ACROSS_PAGES_REQUIRED'
 matching=page('department-filter',department='Own risk department A');assert int(matching['total'])==17 and matching['records'][0]['id']==new['id']
 empty=page('object-filter',analysisObject='Own no matching object');assert int(empty['total'])==0
 edited=dict(created,analysisUnit='Own edited newest unit')
 assert call('normal-edit','POST','/serv/riskLevel/updateById',edited)is True
 reopened=call('edit-readback','GET','/serv/riskLevel/getById?'+urllib.parse.urlencode({'id':created['id']}))
 assert reopened.get('analysisUnit')==edited['analysisUnit'] and reopened.get('createTime')==created.get('createTime'),'RISK_EDIT_MUST_PRESERVE_CREATION_TIME'
 c.dump(root/'risk-unit-newest-http-result.json',{'cases':cases,'actualNormalOriginalLoginAndBusinessMain':True,'actualNativeRiskControllerMapperAndFill':True,'candidateOnlyOriginalRiskServiceSortAndNullCreateTimeDefaultChanged':True,'syntheticSeedRows':31,'newRecordFirstAndTimestampPresent':True,'stableTimestampAndIDOrderAcrossPages':True,'editPreservesCreateTime':True,'originalFiltersPreserved':True,'frontendReturnFlowOrRealDataAccepted':False,'formalOrPublicChanged':False,'fullCloneReady':False})
