from copy import deepcopy
from dataclasses import replace
import unittest
from services.auth import Principal
from services.common import ApiError
from services.gas_domain import source_event,new_event,transition,visible_event,CLASSIFICATIONS,CONCLUSIONS

AT='2026-10-19T10:00:00+08:00'
SOURCE={'schema':'xnby.gas.source.v1','sourceSystem':'QA-MONITOR','sourceEventId':'ANOMALY-1','sourceRevision':1,'spatialId':'PUBLIC-POINT','area':'合成公共道路','gasCode':'QA-CH4','unit':'%LEL','observedAt':AT,'concentration':'12.5000','deviceState':'online','alarmState':'alarm','trend':[{'at':'2026-10-19T09:59:00+08:00','value':'11.25'},{'at':AT,'value':'12.5000'}]}
LOCATION={'crs':'EPSG:4326','longitude':114.0,'latitude':33.0,'accuracyMeters':10,'capturedAt':AT,'method':'manual'}
ALL=frozenset({'gas:read','gas:ingest','gas:verify','gas:cooperate','gas:handoff'})
class GasDomainTests(unittest.TestCase):
 def setUp(self):
  self.operator=Principal('QA-OP','QA',ALL,frozenset({'A','B'}),True,True,'qa-v1');self.allowed=frozenset({'PUBLIC-POINT'});self.state=new_event(SOURCE,self.operator,self.allowed,'a'*32,AT)
 def move(self,action,body,principal=None,state=None,**options):
  current=state or self.state;return transition(current,action,{'revision':current['revision'],**body},principal or self.operator,self.allowed,AT,**options)
 def verify(self,principal=None,check_materials=None,**extra):
  return self.move('verify',{'conclusion':'continue','note':'合成现场核实\n不认定责任主体','verifiedAt':AT,'location':LOCATION,'materialRefs':[],**extra},principal=principal,check_materials=check_materials)
 def code(self,wanted,fn):
  with self.assertRaises(ApiError) as e:fn()
  self.assertEqual(e.exception.code,wanted)
 def test_source_keeps_decimal_units_raw_time_and_input_unchanged(self):
  old=deepcopy(SOURCE);source=source_event(SOURCE);self.assertEqual(source['document'],old);self.assertEqual(source['observedAtUTC'],'2026-10-19T02:00:00+00:00');self.assertEqual(source['document']['concentration'],'12.5000');self.assertEqual(SOURCE,old);self.assertEqual(self.state['classification'],'needs-verification');self.assertEqual(self.state['status'],'attention')
 def test_invalid_source_nonfinite_unknown_unit_timezone_and_order(self):
  for patch in [{'concentration':float('nan')},{'concentration':'NaN'},{'concentration':True},{'unit':'LEL-without-unit-definition'},{'observedAt':'2026-10-19T10:00:00'},{'observedAt':'2026-02-30T10:00:00Z'},{'enterpriseId':'A'},{'deviceState':'online','concentration':None},{'trend':list(reversed(SOURCE['trend']))},{'trend':SOURCE['trend']*65}]:
   with self.subTest(patch=patch),self.assertRaises((ValueError,TypeError)):source_event({**SOURCE,**patch})
 def test_device_offline_can_have_missing_concentration_without_fake_zero(self):
  result=source_event({**SOURCE,'deviceState':'offline','concentration':None,'alarmState':'unknown','trend':[]});self.assertIsNone(result['document']['concentration'])
 def test_every_required_classification_and_conclusion_is_distinct(self):
  for value in CLASSIFICATIONS:self.assertEqual(self.move('classify',{'classification':value,'note':'合成分类'})[0]['classification'],value)
  for value in CONCLUSIONS:self.assertEqual(self.verify(conclusion=value)[0]['verification']['conclusion'],value)
 def test_verification_location_is_explicit_no_silent_crs_conversion(self):
  for patch in [{'crs':'GCJ-02'},{'longitude':181},{'latitude':True},{'accuracyMeters':float('inf')},{'method':'auto-guessed'},{'capturedAt':'2026-10-19 10:00'}]:
   with self.subTest(patch=patch),self.assertRaises((ValueError,TypeError)):self.verify(location={**LOCATION,**patch})
 def test_material_refs_require_authorized_binding_callback(self):
  self.code('MATERIAL_BINDING_REQUIRED',lambda:self.verify(materialRefs=['b'*32]))
  calls=[];new,event=self.verify(materialRefs=['b'*32],check_materials=lambda *args:calls.append(args));self.assertEqual(calls[0][1],self.state['id']);self.assertEqual(new['verification']['materialRefs'],['b'*32]);self.assertEqual(event['kind'],'verify');self.assertIsNone(self.state['verification'])
 def test_public_spatial_permission_and_tenant_are_not_inferred_from_enterprise(self):
  for principal in [replace(self.operator,public_spatial=False),replace(self.operator,tenant='OTHER')]:self.code('NOT_FOUND',lambda:visible_event(self.state,principal,self.allowed))
  self.code('NOT_FOUND',lambda:visible_event(self.state,self.operator,frozenset()))
  self.code('FORBIDDEN',lambda:self.verify(principal=replace(self.operator,permissions=frozenset({'gas:read'}))))
 def test_cooperation_is_enterprise_scoped_and_projection_hides_other_enterprises(self):
  feedback=replace(self.operator,subject='QA-A',permissions=frozenset({'gas:read','gas:cooperate'}),enterprises=frozenset({'A'}),all_enterprises=False)
  body={'enterpriseId':'A','state':'explained','activities':['loading'],'statement':'合成企业说明','measures':'合成配合措施'}
  new,_=self.move('cooperate',body,feedback);self.assertEqual(visible_event(new,feedback,self.allowed)['cooperation']['A']['actor'],'QA-A');self.code('NOT_FOUND',lambda:self.move('cooperate',{**body,'enterpriseId':'B'},feedback))
  other=replace(feedback,subject='QA-B',enterprises=frozenset({'B'}));self.assertEqual(visible_event(new,other,self.allowed)['cooperation'],{})
 def test_rejected_material_binding_and_unknown_fields_do_not_change_snapshot(self):
  before=deepcopy(self.state)
  def refuse(*args):raise ApiError(404,'NOT_FOUND')
  self.code('NOT_FOUND',lambda:self.verify(materialRefs=['b'*32],check_materials=refuse));self.assertEqual(self.state,before)
  with self.assertRaises(ValueError):self.verify(fakeApproval='source is not authorization')
  with self.assertRaises(ValueError):transition(self.state,'verify',[],self.operator,self.allowed,AT)
 def test_unit_change_remains_explicit_source_revision_without_comparison(self):
  source={**SOURCE,'sourceRevision':2,'unit':'ppm','concentration':'1250.000','trend':[]};new,event=self.move('source-update',{'source':source});self.assertEqual(new['source']['document']['unit'],'ppm');self.assertEqual(new['source']['document']['concentration'],'1250.000');self.assertEqual(new['classification'],'needs-verification');self.assertEqual(self.state['source']['document']['unit'],'%LEL')
 def test_revision_and_history_bounds_do_not_mutate_input(self):
  before=deepcopy(self.state);self.code('REVISION_CONFLICT',lambda:self.move('classify',{'revision':99,'classification':'persistent','note':'合成'}));self.assertEqual(self.state,before)
  self.code('EVENT_HISTORY_LIMIT',lambda:self.move('classify',{'classification':'persistent','note':'合成'},state={**self.state,'revision':10000}))
 def test_source_revision_preserves_identity_and_invalidates_verification(self):
  verified,_=self.verify();source={**SOURCE,'sourceRevision':2,'concentration':'13.0000'};updated,event=self.move('source-update',{'source':source},state=verified);self.assertIsNone(updated['verification']);self.assertEqual(updated['status'],'attention');self.assertEqual(verified['source']['document']['sourceRevision'],1);self.assertEqual(event['data']['source']['concentration'],'13.0000')
  self.code('SOURCE_IDENTITY_CONFLICT',lambda:self.move('source-update',{'source':{**source,'spatialId':'OTHER'}}));self.code('SOURCE_REVISION_CONFLICT',lambda:self.move('source-update',{'source':SOURCE}))
 def test_handoff_is_pending_until_correlated_result_no_fake_dispatch(self):
  self.code('VERIFICATION_REQUIRED',lambda:self.move('handoff-request',{'requestId':'c'*32,'reason':'合成转办'}));verified,_=self.verify();pending,event=self.move('handoff-request',{'requestId':'c'*32,'reason':'合成持续异常'},state=verified);self.assertEqual(pending['handoff']['state'],'pending-delivery');self.assertIsNone(pending['handoff']['result']);self.assertEqual(pending['handoff']['package']['eventRevision'],verified['revision']);self.code('HANDOFF_RESULT_REQUIRED',lambda:self.move('archive',{'note':'不能当已完成'},state=pending))
  result={'requestId':'c'*32,'externalSystem':'QA-EMERGENCY','externalId':'QA-E1','state':'accepted','note':'合成接收'};accepted,_=self.move('handoff-result',result,state=pending);self.code('HANDOFF_IDENTITY_CONFLICT',lambda:self.move('handoff-result',{**result,'state':'completed','externalId':'OTHER'},state=accepted));completed,_=self.move('handoff-result',{**result,'state':'completed'},state=accepted);self.assertEqual(completed['handoff']['state'],'completed');self.code('HANDOFF_TERMINAL_OR_DUPLICATE',lambda:self.move('handoff-result',result,state=completed))
  projected=visible_event(completed,replace(self.operator,permissions=frozenset({'gas:read'})),self.allowed);self.assertNotIn('package',projected['handoff'])
 def test_unresolved_verification_cannot_be_archived_as_resolved(self):
  verified,_=self.verify(conclusion='continue');self.code('FOLLOWUP_REQUIRED',lambda:self.move('archive',{'note':'仍需关注不能假归档'},state=verified))
  pending,_=self.move('handoff-request',{'requestId':'c'*32,'reason':'合成升级'},state=verified);completed,_=self.move('handoff-result',{'requestId':'c'*32,'externalSystem':'QA-EMERGENCY','externalId':'QA-E1','state':'completed','note':'合成处置完成'},state=pending);archived,_=self.move('archive',{'note':'引用同源版本处置结果'},state=completed);self.assertEqual(archived['status'],'archived')
  updated,_=self.move('source-update',{'source':{**SOURCE,'sourceRevision':2}},state=completed);renewed,_=self.move('verify',{'conclusion':'continue','note':'新版本仍需关注','verifiedAt':AT,'location':LOCATION,'materialRefs':[]},state=updated);self.code('FOLLOWUP_REQUIRED',lambda:self.move('archive',{'note':'旧版本完成不能覆盖新异常'},state=renewed))
 def test_new_anomaly_can_handoff_again_after_previous_result_and_old_callback_is_refused(self):
  verified,_=self.verify(conclusion='emergency');pending,_=self.move('handoff-request',{'requestId':'c'*32,'reason':'第一次合成转办'},state=verified);result={'requestId':'c'*32,'externalSystem':'QA-EMERGENCY','externalId':'QA-E1','state':'completed','note':'第一轮完成'};completed,_=self.move('handoff-result',result,state=pending)
  updated,_=self.move('source-update',{'source':{**SOURCE,'sourceRevision':2}},state=completed);renewed,_=self.move('verify',{'conclusion':'emergency','note':'新测量仍需应急关注','verifiedAt':AT,'location':LOCATION,'materialRefs':[]},state=updated)
  self.code('HANDOFF_ALREADY_EXISTS',lambda:self.move('handoff-request',{'requestId':'c'*32,'reason':'不能重用旧请求ID'},state=renewed));second,event=self.move('handoff-request',{'requestId':'d'*32,'reason':'第二轮合成转办'},state=renewed);self.assertEqual(second['handoff']['state'],'pending-delivery');self.assertEqual(second['handoff']['package']['source']['document']['sourceRevision'],2);self.assertEqual(completed['handoff']['state'],'completed');self.code('HANDOFF_IDENTITY_CONFLICT',lambda:self.move('handoff-result',result,state=second))
 def test_enterprise_cooperation_has_finite_capacity_and_can_update_existing(self):
  body={'enterpriseId':'A','state':'following','activities':[],'statement':'合成说明','measures':'合成措施'};full={**self.state,'cooperation':{'E'+str(i):{} for i in range(64)}};self.code('COOPERATION_CAPACITY',lambda:self.move('cooperate',body,state=full));self.assertEqual(len(full['cooperation']),64)
  full['cooperation']['A']=full['cooperation'].pop('E0');new,_=self.move('cooperate',body,state=full);self.assertEqual(len(new['cooperation']),64);self.assertEqual(new['cooperation']['A']['state'],'following')
 def test_archive_reopen_and_new_source_do_not_erase_history_contract(self):
  self.code('VERIFICATION_REQUIRED',lambda:self.move('archive',{'note':'不能跳过现场核实'}));verified,_=self.verify(conclusion='no-obvious-anomaly');archived,_=self.move('archive',{'note':'合成归档说明'},state=verified);self.code('EVENT_ARCHIVED',lambda:self.move('classify',{'classification':'persistent','note':'合成'},state=archived));opened,event=self.move('reopen',{'note':'合成再次核实'},state=archived);self.assertIsNone(opened['verification']);self.assertEqual(event['data']['note'],'合成再次核实');self.assertIsNotNone(archived['verification']);updated,_=self.move('source-update',{'source':{**SOURCE,'sourceRevision':2}},state=archived);self.assertEqual(updated['status'],'attention');self.assertIsNone(updated['archive'])

if __name__=='__main__':unittest.main()
