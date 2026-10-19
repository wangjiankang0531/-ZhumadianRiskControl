import copy,json,unittest
from unittest.mock import patch
from services.tests import test_gas_api as fixture
from services.data import fingerprint

class GasNearbyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.GasApiTests.setUpClass()
 def setUp(self):
  self.f=fixture.GasApiTests();self.f.setUp();self.event=self.f.create();self.route='/'+self.event['id']+'/nearby?revision=1&radius=20'
  layer=self.f.p.layers['layers'][0]
  layer['features'][0].update(type='region',positions=[[0,0,0],[20,0,0],[20,40,0],[0,40,0]])
  layer['features'][1]['positions']=[[10,21,0]]
  for ident,kind,points in [('road','line',[[-10000,25,0],[10000,25,0]]),('camera','point',[[10,30,0]]),('far','point',[[10,50,0]]),('unlisted','point',[[10,20.1,0]])]:layer['features'].append({'id':ident,'name':'TEST '+ident,'type':kind,'positions':points,'style':{},'label':{}})
  self.f.p.write('layers.json',self.f.p.layers);self.f.p.config['data']['publicSpatialIds']=['public','road','camera','far'];self.f.p.write('config.json',self.f.p.config)
  from services.api import Service
  self.f.p.server.service=Service(self.f.p.root/'config.json');self.f.service=self.f.p.server.service
 def tearDown(self):self.f.tearDown()
 def test_single_snapshot_distance_ownership_and_same_source_business_details(self):
  with patch.object(self.f.service.store,'snapshot',wraps=self.f.service.store.snapshot) as reader:
   code,data,_=self.f.call(self.route);self.assertEqual(code,200,data);self.assertEqual(reader.call_count,1)
  self.assertEqual([(r['id'],r['distanceMeters']) for r in data['items']],[('a',0),('road',5),('camera',10)]);self.assertEqual(data['total'],3);self.assertEqual(data['distanceMetric'],'horizontal-minimum-metres');self.assertEqual(data['items'][0]['businessRecord']['attributes'][0]['value'],'SECRET-A');self.assertNotIn('SECRET-B',json.dumps(data));self.assertNotIn('unlisted',json.dumps(data));self.assertNotIn('PRIVATE ICON',json.dumps(data));self.assertNotIn('style',data['items'][0])
 def test_scope_applies_before_counts_pagination_and_metadata(self):
  code,data,_=self.f.call(self.route,token=self.f.p.token('QA-A',scope='gas:read spatial:read'));self.assertEqual(code,200,data);self.assertEqual(data['total'],3);self.assertNotIn('businessRecord',str(data));self.assertNotIn('SECRET-A',json.dumps(data));self.assertFalse(data['businessDetailsAuthorized'])
  self.f.p.policy['principals'][0]['enterprises']=[];self.f.p.write('policy.json',self.f.p.policy);code,data,_=self.f.call(self.route);self.assertEqual(code,200,data);self.assertEqual(data['total'],2);self.assertEqual(sum(data['counts'].values()),2);self.assertNotIn('SECRET-A',json.dumps(data));self.assertNotIn('enterpriseId',json.dumps(data))
 def test_pagination_requires_pin_and_data_change_is_not_mixed(self):
  code,first,_=self.f.call(self.route+'&limit=1');self.assertEqual(code,200,first);version=first['datasetVersion'];self.assertEqual(self.f.call(self.route+'&offset=1&limit=1')[0],400)
  code,second,_=self.f.call(self.route+'&offset=1&limit=1&datasetVersion='+version);self.assertEqual(code,200,second);self.assertEqual(second['items'][0]['id'],'road');self.f.p.layers['layers'][0]['features'][-2]['positions'][0][0]+=1;self.f.p.write('layers.json',self.f.p.layers);self.assertEqual(self.f.call(self.route+'&offset=1&limit=1&datasetVersion='+version)[0],409)
 def test_category_filters_after_scoping_and_counts_retain_nearby_scope(self):
  # Known categories come from the authoritative spatial catalog, or existing business reference.
  code,data,_=self.f.call(self.route+'&category=enterprise');self.assertEqual(code,200,data);self.assertEqual([r['id'] for r in data['items']],['a']);self.assertEqual(sum(data['counts'].values()),3);self.assertEqual(self.f.call(self.route+'&category=unknown')[0],400)
 def test_range_and_parameter_limits_and_current_event_permission(self):
  for extra in ['radius=0','radius=5001','radius=01','radius=1.5','radius=NaN']:
   self.assertEqual(self.f.call(self.route.replace('radius=20',extra))[0],400,extra)
  for suffix in ['&limit=51','&radius=2','&datasetVersion=bad','&objectId=a']:self.assertEqual(self.f.call(self.route+suffix)[0],400,suffix)
  self.assertEqual(self.f.call(self.route,token=self.f.p.token('QA-A',scope='gas:read'))[0],403);self.assertEqual(self.f.verify(self.event)[0],200);self.assertEqual(self.f.call(self.route)[0],409)
 def test_scene_target_is_reauthorized_and_recomputed_with_requested_radius(self):
  route='/'+self.event['id']+'/spatial?revision=1&objectId='
  code,data,_=self.f.call(route+'road&radius=20');self.assertEqual(code,200,data);self.assertEqual(data['target']['type'],'line');self.assertEqual(data['point']['id'],'public');self.assertEqual(self.f.call(route+'b&radius=20')[0],404);self.assertEqual(self.f.call(route+'unlisted&radius=20')[0],404);self.assertEqual(self.f.call(route+'far&radius=20')[0],404);self.assertEqual(self.f.call(route+'road')[0],400);self.assertEqual(self.f.call('/'+self.event['id']+'/spatial?revision=1&radius=20')[0],400)
 def test_missing_spatial_permission_refused_before_any_source_read(self):
  with patch.object(self.f.service.store,'snapshot',side_effect=AssertionError('Source must not be read')) as reader:
   code,data,_=self.f.call(self.route,token=self.f.p.token('QA-A',scope='gas:read'));self.assertEqual(code,403,data);self.assertEqual(reader.call_count,0)
 def test_second_enterprise_gets_its_own_nearest_object_not_other_company_details(self):
  self.f.p.policy['principals'][1]['publicSpatial']=True;self.f.p.write('policy.json',self.f.p.policy);code,data,_=self.f.call(self.route,subject='QA-B');self.assertEqual(code,200,data);self.assertEqual([(r['id'],r['distanceMeters']) for r in data['items']],[('b',1),('road',5),('camera',10)]);self.assertIn('SECRET-B',json.dumps(data));self.assertNotIn('SECRET-A',json.dumps(data));self.assertNotIn('a',[r['id'] for r in data['items']])
 def test_missing_business_snapshot_preserves_geometry_without_fabricated_metadata(self):
  self.f.service.store.paths.pop('business');code,data,_=self.f.call(self.route);self.assertEqual(code,200,data);self.assertEqual(data['total'],3);self.assertFalse(any('businessRecord' in r for r in data['items']))
 def test_optional_demo_context_keeps_existing_events_and_authoritative_catalog(self):
  from tools.serve_gas_portal_qa import configure_gas_fixture
  from services.database_transfer import validate_database
  from services.auth import Principal,PERMISSIONS
  p=fixture.fixture.ApiTests();p.setUp()
  try:
   points=configure_gas_fixture(p,p.root/'nearby.sqlite',nearby_demo=True);snapshot=p.service.store.snapshot();actor=Principal('QA-A','QA',frozenset(PERMISSIONS),frozenset({'A'}),False,True,'synthetic')
   self.assertEqual(len(snapshot['objects']),18);self.assertIn('qa-near-video',p.service.store.public);self.assertNotIn('qa-near-unlisted',p.service.store.public)
   with p.service.gas.transaction() as db:validate_database(db);self.assertEqual(db.execute('SELECT count(*) FROM gas_alerts').fetchone()[0],6)
  finally:p.tearDown()
if __name__=='__main__':unittest.main()
