"""Real authenticated evidence HTTP/SQLite tests, using synthetic PDF bytes only."""
import base64,concurrent.futures,hashlib,http.client,json,sqlite3,unittest,uuid
from pathlib import Path
from contextlib import closing
from services.tests import test_focus_api as fixture
from services.focus import FocusStore
from services.focus_materials import MATERIAL_LIMIT,MATERIAL_JSON_LIMIT,checked_material
from services.database_transfer import export_database,restore_database,mysql_script,validate_database,upgrade_copy,canonical,LEGACY_TABLES
from services.database import SCHEMA_SQLITE_V2,SCHEMA_VERSION

PDF=b'%PDF-1.4\nSynthetic evidence only\n%%EOF\n'

class MaterialTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.FocusTests.setUpClass()
 def setUp(self):self.f=fixture.FocusTests();self.f.setUp();self.issue=self.f.create()
 def tearDown(self):self.f.tearDown()
 def payload(self,raw=PDF,**changes):return dict(revision=self.issue['revision'],name='模拟复查材料.pdf',mediaType='application/pdf',base64=base64.b64encode(raw).decode(),description='合成佐证材料\n仅作验收',**changes)
 def upload(self,payload=None,subject='QA-A',key=None):return self.f.call('/'+self.issue['id']+'/materials','POST',payload or self.payload(),subject,key)
 def download(self,identity,subject='QA-A',method='GET',suffix=''):
  token=self.f.p.token(subject,scope='spatial:read business:read focus:read focus:track focus:feedback')
  c=http.client.HTTPConnection('127.0.0.1',self.f.p.server.server_port,timeout=15)
  try:
   c.request(method,'/api/v1/focus_issues/'+self.issue['id']+'/materials/'+identity+suffix,headers={'Authorization':'Bearer '+token});r=c.getresponse();return r.status,r.read(),dict(r.getheaders())
  finally:c.close()
 def test_immutable_roundtrip_restart_metadata_headers_and_history(self):
  raw=b'%PDF-1.7\n'+b'Q'*(1048576+9)+b'\n%%EOF';status,data,_=self.upload(self.payload(raw));self.assertEqual(status,200,data);material=data['material'];self.assertEqual(material['revision'],2);self.assertNotIn('base64',material)
  self.f.p.service.focus=FocusStore(self.f.p.root/'focus.sqlite')
  status,listing,_=self.f.call('/'+self.issue['id']+'/materials');self.assertEqual(status,200);self.assertEqual(listing['total'],1);self.assertEqual(listing['items'],[material]);self.assertEqual(listing['revision'],2)
  code,body,h=self.download(material['id']);self.assertEqual(code,200);self.assertEqual(body,raw);self.assertEqual(h['X-XNBY-Material-SHA256'],hashlib.sha256(raw).hexdigest());self.assertEqual(h['X-Content-Type-Options'],'nosniff');self.assertEqual(h['Cache-Control'],'no-store');self.assertIn('attachment;',h['Content-Disposition']);self.assertIn("filename*=UTF-8''",h['Content-Disposition']);self.assertEqual(len(h['X-XNBY-Authorization-Version']),64)
  code,body,h=self.download(material['id'],method='HEAD');self.assertEqual((code,body),(200,b''));self.assertEqual(int(h['Content-Length']),len(raw))
  status,events,_=self.f.call('/'+self.issue['id']+'/events');self.assertEqual(events['items'][-1]['kind'],'material');self.assertEqual(events['items'][-1]['data']['material'],material);self.assertNotIn('base64',events['items'][-1]['data'])
 def test_scope_revocation_readonly_and_feedback_permissions(self):
  self.assertEqual(self.upload(subject='QA-READER')[0],403)
  code,data,_=self.upload(subject='QA-FEEDBACK');self.assertEqual(code,200,data);identity=data['material']['id']
  self.assertEqual(self.download(identity,'QA-READER')[0],200);self.assertEqual(self.download(identity,'QA-B')[0],404);self.assertEqual(self.f.call('/'+self.issue['id']+'/materials',subject='QA-B')[0],404)
  for principal in self.f.p.policy['principals']:
   if principal['subject']=='QA-A':principal['enterprises']=[]
  self.f.p.write('policy.json',self.f.p.policy);self.assertEqual(self.download(identity)[0],404)
 def test_idempotency_and_revision_conflict_do_not_duplicate_material_bytes(self):
  key=uuid.uuid4().hex;payload=self.payload();status,data,_=self.upload(payload,key=key);self.assertEqual(status,200)
  status,replay,_=self.upload(payload,key=key);self.assertEqual(status,200);self.assertTrue(replay['replayed']);self.assertEqual(replay['material']['id'],data['material']['id'])
  changed={**payload,'description':'不同内容'};self.assertEqual(self.upload(changed,key=key)[0],409);self.assertEqual(self.upload(payload)[0],409)
  with self.f.p.service.focus.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM issue_materials').fetchone()[0],1);self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],2)
 def test_bad_paths_types_signatures_lengths_and_queries_are_rejected(self):
  for change in [{'name':'../x.pdf'},{'name':'x.exe'},{'name':'x.pdf\r\nInjected:yes'},{'mediaType':'text/html'},{'base64':'not base64'},{'base64':base64.b64encode(b'not a PDF').decode()},{'extra':True},{'description':''}]:
   self.assertEqual(self.upload({**self.payload(),**change})[0],400,change)
  with self.assertRaises(ValueError):checked_material('x.pdf','application/pdf',b'x'*(MATERIAL_LIMIT+1))
  self.assertEqual(self.f.call('/'+self.issue['id']+'/materials?unknown=1')[0],400)
  with self.f.p.service.focus.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM issue_materials').fetchone()[0],0)
 def test_new_material_invalidates_positive_review_and_archived_issue_cannot_change(self):
  code,data,_=self.f.action(self.issue,'review',{'result':'rectified','note':'合成复查'});self.assertEqual(code,200);self.issue=data['issue']
  code,data,_=self.upload();self.assertEqual(code,200);self.issue=data['issue'];self.assertIsNone(self.issue['latestReview']);self.assertEqual(self.f.action(self.issue,'archive',{'note':'必须重新复查'})[0],409)
  code,data,_=self.f.action(self.issue,'review',{'result':'rectified','note':'重新复查'});self.issue=data['issue'];code,data,_=self.f.action(self.issue,'archive',{'note':'合成归档'});self.issue=data['issue'];self.assertEqual(self.upload()[0],409)
 def test_failed_insert_rolls_back_material_issue_event_and_idempotency_together(self):
  store=self.f.p.service.focus
  with store.transaction(write=True) as db:db.execute("CREATE TRIGGER fail_material BEFORE INSERT ON issue_materials BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
  self.assertEqual(self.upload()[0],503)
  with store.transaction() as db:
   self.assertEqual(db.execute('SELECT count(*) FROM issue_materials').fetchone()[0],0);self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0],1);self.assertEqual(db.execute('SELECT count(*) FROM requests').fetchone()[0],1)
  self.assertEqual(self.f.call('/'+self.issue['id'])[1]['issue']['revision'],1)
 def test_concurrent_same_revision_has_one_material_and_busy_slots_refuse_before_body(self):
  payload=self.payload()
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(lambda _:self.upload(payload)[0],range(2)))
  self.assertEqual(sorted(codes),[200,409]);slots=self.f.p.service.focus.material_slots;slots.acquire();slots.acquire()
  try:self.assertEqual(self.upload()[0],429)
  finally:slots.release();slots.release()
 def test_corrupt_payload_refused_on_download_and_backup(self):
  code,data,_=self.upload();self.assertEqual(code,200);identity=data['material']['id']
  with self.f.p.service.focus.transaction(write=True) as db:db.execute('UPDATE issue_materials SET payload=? WHERE id=?',(b'X'*len(PDF),identity))
  self.assertEqual(self.download(identity)[0],503)
  with self.assertRaises(ValueError):export_database(self.f.p.root/'focus.sqlite',self.f.p.root/'bad-export')
 def test_lossless_backup_restore_and_mysql_target_include_material_bytes(self):
  code,data,_=self.upload();self.assertEqual(code,200);path=self.f.p.root/'focus.sqlite';archive=self.f.p.root/'materials-export';manifest=export_database(path,archive);self.assertEqual(manifest['tables']['issue_materials']['rows'],1)
  restored=self.f.p.root/'restored.sqlite';restore_database(archive,restored)
  with closing(sqlite3.connect(restored)) as db:validate_database(db);self.assertEqual(db.execute('SELECT payload FROM issue_materials').fetchone()[0],PDF)
  script=self.f.p.root/'mysql.sql';mysql_script(archive,script);sql=script.read_text('utf-8');self.assertIn('INSERT INTO `issue_materials`',sql);self.assertIn('0x'+PDF.hex(),sql)
 def test_v2_source_readonly_upgrade_copy_and_legacy_archive_restore(self):
  source=self.f.p.root/'focus.sqlite'
  with closing(sqlite3.connect(source)) as db:db.execute('DROP TABLE issue_materials');db.execute('PRAGMA user_version=2');db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
  before=hashlib.sha256(source.read_bytes()).hexdigest();target=self.f.p.root/'upgraded.sqlite';upgrade_copy(source,target);self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
  with closing(sqlite3.connect(target)) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3);self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],1);self.assertEqual(db.execute('SELECT count(*) FROM issue_materials').fetchone()[0],0)
  archive=self.f.p.root/'v2-archive';manifest=export_database(target,archive);(archive/'issue_materials.jsonl').unlink();del manifest['tables']['issue_materials'];manifest['databaseVersion']=2;manifest['schemaDefinitionSHA256']=hashlib.sha256(SCHEMA_SQLITE_V2.encode()).hexdigest();(archive/'manifest.json').write_bytes(canonical(manifest))
  restored=self.f.p.root/'v2-restored.sqlite';restore_database(archive,restored)
  with closing(sqlite3.connect(restored)) as db:validate_database(db);self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
  with self.assertRaises(ValueError):upgrade_copy(source,target)

class MaterialGatewayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.FocusTests.setUpClass()
 def setUp(self):
  MaterialTests.setUp(self)
  import threading
  from tools.authenticated_portal_server import PortalServer
  self.gateway=PortalServer(('127.0.0.1',0),self.f.p.server.server_port,{'oauth':{'tokenEndpoint':'https://qa.identity.invalid/token'}})
  self.thread=threading.Thread(target=self.gateway.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.gateway.shutdown();self.gateway.server_close();self.thread.join();MaterialTests.tearDown(self)
 def request(self,path,body=None,subject='QA-A',origin=None):
  token=self.f.p.token(subject,scope='spatial:read business:read focus:read focus:track focus:feedback');headers={'Authorization':'Bearer '+token}
  if body is not None:headers.update({'Content-Type':'application/json','Origin':origin or self.gateway.app_origin,'Idempotency-Key':uuid.uuid4().hex})
  c=http.client.HTTPConnection('127.0.0.1',self.gateway.server_port,timeout=15)
  try:
   c.request('POST' if body is not None else 'GET',path,json.dumps(body).encode() if body is not None else None,headers);r=c.getresponse();return r.status,r.read(),dict(r.getheaders())
  finally:c.close()
 def test_gateway_material_origin_large_body_and_binary_headers(self):
  route='/api/v1/focus_issues/'+self.issue['id']+'/materials';payload=MaterialTests.payload(self,b'%PDF-1.7\n'+b'G'*65536+b'\n%%EOF')
  self.assertEqual(self.request(route,payload,origin='https://outside.invalid')[0],403)
  code,raw,_=self.request(route,payload);self.assertEqual(code,200,raw[:200]);data=json.loads(raw);identity=data['material']['id']
  code,raw,headers=self.request(route+'/'+identity);self.assertEqual(code,200);self.assertEqual(hashlib.sha256(raw).hexdigest(),data['material']['sha256']);self.assertEqual(headers['X-XNBY-Authorization-Version'],data['authorizationVersion']);self.assertIn('attachment;',headers['Content-Disposition'])
  self.assertEqual(self.request('/api/v1/focus_issues/'+self.issue['id']+'/review',{'revision':2,'note':'x'*40000,'result':'rectified'})[0],413)
 def test_gateway_cannot_expand_enterprise_scope_and_bounds_material_work(self):
  route='/api/v1/focus_issues/'+self.issue['id']+'/materials'
  self.assertEqual(self.request(route,MaterialTests.payload(self),subject='QA-B')[0],404)
  slots=self.gateway.material_slots;slots.acquire();slots.acquire()
  try:self.assertEqual(self.request(route)[0],429)
  finally:slots.release();slots.release()

if __name__=='__main__':unittest.main()
