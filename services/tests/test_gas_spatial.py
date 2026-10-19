import unittest
from unittest.mock import patch
from services.tests import test_gas_api as fixture
from services.data import fingerprint

class GasSpatialTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.GasApiTests.setUpClass()
 def setUp(self):self.f=fixture.GasApiTests();self.f.setUp();self.event=self.f.create();self.route='/'+self.event['id']+'/spatial?revision=1'
 def tearDown(self):self.f.tearDown()
 def test_authorized_point_uses_one_snapshot_and_contains_no_private_details(self):
  original=self.f.service.store.snapshot
  with patch.object(self.f.service.store,'snapshot',wraps=original) as reader:
   code,data,_=self.f.call(self.route);self.assertEqual(code,200,data);self.assertEqual(reader.call_count,1)
  self.assertEqual(data['point'],{'id':'public','name':'TEST public','type':'point','positions':[[10,20,30]]});self.assertEqual(data['coordinates'],self.f.p.layers['coordinates']);self.assertEqual(data['datasetVersion'],original()['version']);self.assertNotIn('PRIVATE',str(data));self.assertNotIn('SECRET',str(data))
 def test_event_revision_is_mandatory_and_stale_navigation_does_not_locate(self):
  for suffix in ['/spatial','/spatial?revision=0','/spatial?revision=01','/spatial?revision=10001','/spatial?revision=1&revision=1','/spatial?revision=1&offset=0']:
   self.assertEqual(self.f.call('/'+self.event['id']+suffix)[0],400,suffix)
  self.assertEqual(self.f.verify(self.event)[0],200);self.assertEqual(self.f.call(self.route)[0],409);self.assertEqual(self.f.call(self.route.replace('revision=1','revision=2'))[0],200)
 def test_spatial_and_gas_permissions_both_required_and_current_policy_applies(self):
  self.assertEqual(self.f.call(self.route,token=self.f.p.token('QA-A',scope='gas:read'))[0],403);self.assertEqual(self.f.call(self.route,token=self.f.p.token('QA-A',scope='spatial:read'))[0],403)
  self.f.p.policy['principals'][0]['publicSpatial']=False;self.f.p.write('policy.json',self.f.p.policy);self.assertEqual(self.f.call(self.route)[0],404)
 def test_point_moved_dataset_identity_changes_and_old_snapshot_not_reused(self):
  first=self.f.call(self.route)[1];self.f.p.layers['layers'][0]['features'][2]['positions']=[[20,30,40]];self.f.p.write('layers.json',self.f.p.layers)
  code,current,_=self.f.call(self.route);self.assertEqual(code,200,current);self.assertNotEqual(first['datasetVersion'],current['datasetVersion']);self.assertEqual(current['point']['positions'],[[20,30,40]])
 def test_missing_private_and_nonpoint_public_objects_never_resolve(self):
  for patcher in ('private','region','missing'):
   layer=self.f.p.layers['layers'][0];point=next((f for f in layer['features'] if f['id']=='public'),None)
   if patcher=='private':point['business']={'objectType':'enterprise','sourceSystem':'QA','businessId':'new-private','enterpriseId':'A'}
   elif patcher=='region':point.pop('business');point['type']='region';point['positions']=[[0,0,0],[10,0,0],[0,10,0]]
   else:layer['features']=[f for f in layer['features'] if f['id']!='public']
   self.f.p.write('layers.json',self.f.p.layers);self.assertEqual(self.f.call(self.route)[0],404,patcher)
 def test_readonly_route_rejects_write_and_head_has_no_body(self):
  self.assertEqual(self.f.call('/'+self.event['id']+'/spatial','POST',{'revision':1})[0],405)
  import http.client
  c=http.client.HTTPConnection('127.0.0.1',self.f.p.server.server_port,timeout=10)
  try:
   c.request('HEAD','/api/v1/gas_alerts'+self.route,headers={'Authorization':'Bearer '+self.f.p.token('QA-A',scope='gas:read spatial:read')});r=c.getresponse();self.assertEqual(r.status,200);self.assertEqual(r.read(),b'');self.assertEqual(r.getheader('Cache-Control'),'no-store')
  finally:c.close()
class GasSpatialGatewayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.GasGatewayTests.setUpClass()
 def test_only_scene_html_allows_verified_local_geometry_blob_connections(self):
  f=fixture.GasGatewayTests();f.setUp()
  try:
   import http.client
   c=http.client.HTTPConnection('127.0.0.1',f.gateway.server_port,timeout=10)
   for route,allows in [('/',True),('/index.html',True),('/gas.html',False),('/application/config.json',False),('/api/v1/gas_alerts',False)]:
    c.request('GET',route);r=c.getresponse();r.read();policy=r.getheader('Content-Security-Policy');connect=next(v.strip() for v in policy.split(';') if v.strip().startswith('connect-src '));self.assertEqual('blob:' in connect,allows,route);self.assertNotIn('unsafe-eval',policy);self.assertNotIn('*',connect)
   c.close()
  finally:f.tearDown()
if __name__=='__main__':unittest.main()
