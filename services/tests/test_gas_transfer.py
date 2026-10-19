"""Gas archive replay, malicious/corrupt contents and exact legacy upgrade compatibility."""
import base64,hashlib,json,sqlite3,unittest,uuid
from contextlib import closing
from dataclasses import replace
from services.tests import test_gas_repository as fixture
from services.database import SCHEMA_SQLITE_V2,SCHEMA_SQLITE_V3,SCHEMA_VERSION
from services.database_transfer import export_database,restore_database,mysql_script,upgrade_copy,validate_database,canonical,GAS_TABLES,LEGACY_TABLES_V3,TABLES
from services.focus import FocusStore
from services.focus_demo import seed

class GasTransferTests(unittest.TestCase):
 def setUp(self):self.f=fixture.GasRepositoryTests();self.f.setUp()
 def tearDown(self):self.f.tearDown()
 def build(self):
  f=self.f;f.upload(f.a,'enterprise','A');public=f.upload()['material'];f.verify([public['id']]);f.pending();first=f.store.claim(f.op,f.points,f.request_id,lease_seconds=5);f.now+=fixture.timedelta(seconds=6);second=f.store.claim(f.op,f.points,f.request_id);f.store.finish_delivery(f.op,f.points,f.request_id,second['leaseToken'],sent=False,error_code='QA_TIMEOUT');f.now+=fixture.timedelta(minutes=1);third=f.store.claim(f.op,f.points,f.request_id);f.store.finish_delivery(f.op,f.points,f.request_id,third['leaseToken'],sent=True)
  result={'requestId':f.request_id,'externalSystem':'QA-EMERGENCY','externalId':'QA-EXTERNAL','state':'completed','note':'合成处置完成'};f.move('handoff-result',result,f.result);f.move('archive',{'note':'同版本合成归档'});return public
 def test_full_six_table_roundtrip_bytes_and_mysql_script(self):
  self.build();root=self.f.path.parent;archive=root/'export';manifest=export_database(self.f.path,archive);self.assertEqual(len(manifest['tables']),14);restored=root/'restored.sqlite';restore_database(archive,restored)
  with closing(sqlite3.connect(self.f.path)) as a,closing(sqlite3.connect(restored)) as b:
   validate_database(a);validate_database(b)
   for table in TABLES:
    one=[tuple(r) for r in a.execute('SELECT * FROM '+table+' ORDER BY 1,2,3')];two=[tuple(r) for r in b.execute('SELECT * FROM '+table+' ORDER BY 1,2,3')];self.assertEqual(one,two,table)
  sql=root/'mysql.sql';mysql_script(archive,sql);content=sql.read_text('utf8');self.assertIn('INSERT INTO `gas_outbox`',content);self.assertIn('INSERT INTO `gas_delivery_attempts`',content);self.assertIn('0x'+fixture.PDF.hex(),content)
 def test_current_snapshot_history_material_and_outbox_corruption_are_refused(self):
  self.build();root=self.f.path.parent
  cases=[("UPDATE gas_alerts SET payload=json_set(payload,'$.classification','persistent')",()),("UPDATE gas_history SET state_sha256=? WHERE revision=1",('0'*64,)),("UPDATE gas_materials SET payload=?",(b'X'*len(fixture.PDF),)),("UPDATE gas_outbox SET package_sha256=?",('0'*64,)),("DELETE FROM gas_requests WHERE rowid=(SELECT min(rowid) FROM gas_requests)",()),("DELETE FROM gas_delivery_attempts WHERE attempt=1",()),("UPDATE gas_outbox SET target_system='FORGED-TARGET'",())]
  for n,(sql,args) in enumerate(cases):
   path=root/('bad-'+str(n)+'.sqlite')
   with closing(sqlite3.connect(self.f.path)) as source,closing(sqlite3.connect(path)) as target:source.backup(target);target.execute(sql,args);target.commit()
   with self.subTest(case=n),self.assertRaises((ValueError,KeyError)):export_database(path,root/('bad-export-'+str(n)))
 def test_transport_cannot_forge_business_acceptance(self):
  request=self.f.pending();self.f.store.claim(self.f.op,self.f.points,request)
  with self.f.store.transaction(write=True) as db:db.execute("UPDATE gas_outbox SET delivery_state='accepted',lease_sha256=NULL,lease_until=NULL")
  with self.assertRaises(ValueError):export_database(self.f.path,self.f.path.parent/'forged')
 def test_recomputed_archive_hash_does_not_bypass_domain_replay(self):
  self.build();root=self.f.path.parent;archive=root/'export';manifest=export_database(self.f.path,archive);path=archive/'gas_alerts.jsonl';rows=[json.loads(line) for line in path.read_text('utf8').splitlines()];names=manifest['tables']['gas_alerts']['columns'];index=names.index('payload');snapshot=json.loads(rows[0][index]);snapshot['verification']['conclusion']='false-alarm';rows[0][index]=json.dumps(snapshot,ensure_ascii=False);raw=b''.join(canonical(row)+b'\n' for row in rows);path.write_bytes(raw);manifest['tables']['gas_alerts'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());(archive/'manifest.json').write_bytes(canonical(manifest))
  with self.assertRaises(ValueError):restore_database(archive,root/'must-not-publish.sqlite')
  self.assertFalse((root/'must-not-publish.sqlite').exists())
 def test_pending_inflight_and_failed_operational_snapshots_all_validate(self):
  request=self.f.pending()
  for i in range(10):
   with self.f.store.transaction() as db:validate_database(db)
   claimed=self.f.store.claim(self.f.op,self.f.points,request,lease_seconds=5)
   with self.f.store.transaction() as db:validate_database(db)
   if i==9:
    self.f.now+=fixture.timedelta(seconds=6);exhausted=self.f.store.claim(self.f.op,self.f.points,request);self.assertEqual(exhausted['deliveryState'],'failed');self.assertNotIn('leaseToken',exhausted)
   else:self.f.store.finish_delivery(self.f.op,self.f.points,request,claimed['leaseToken'],sent=False,error_code='QA_TIMEOUT');self.f.now+=fixture.timedelta(hours=2)
  with self.f.store.transaction() as db:validate_database(db)
 def test_v3_exact_fingerprint_readonly_upgrade_copy_and_old_archive(self):
  root=self.f.path.parent;path=root/'legacy-v3.sqlite';focus=FocusStore(path);seed(focus)
  actor=replace(self.f.op,permissions=frozenset({'focus:read','focus:track'}))
  with focus.transaction() as db:row=db.execute("SELECT id,revision FROM issues WHERE tenant='QA' AND source_id='A-001'").fetchone();issue_id,revision=row
  focus.add_material(actor,issue_id,{'revision':revision,'name':'legacy.pdf','mediaType':'application/pdf','base64':base64.b64encode(fixture.PDF).decode(),'description':'合成旧版材料'},uuid.uuid4().hex)
  with closing(sqlite3.connect(path)) as db:
   for table in reversed(GAS_TABLES):db.execute('DROP TABLE '+table)
   db.execute('PRAGMA user_version=3');db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
  self.assertEqual(hashlib.sha256(SCHEMA_SQLITE_V3.encode()).hexdigest(),'4a7e36d2183b897a2b264b68c9ac8890b8e2f087ab91e66bf0488ab88bb2cd8d')
  before=hashlib.sha256(path.read_bytes()).hexdigest();upgraded=root/'upgraded.sqlite';upgrade_copy(path,upgraded);self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
  archive=root/'v3archive';manifest=export_database(upgraded,archive)
  for table in GAS_TABLES:(archive/(table+'.jsonl')).unlink();del manifest['tables'][table]
  manifest['databaseVersion']=3;manifest['schemaDefinitionSHA256']=hashlib.sha256(SCHEMA_SQLITE_V3.encode()).hexdigest();(archive/'manifest.json').write_bytes(canonical(manifest));restored=root/'v3-restored.sqlite';restore_database(archive,restored)
  with closing(sqlite3.connect(restored)) as db:
   validate_database(db);self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],SCHEMA_VERSION);self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],10);self.assertEqual(db.execute('SELECT payload FROM issue_materials').fetchone()[0],fixture.PDF)
   for table in GAS_TABLES:self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

if __name__=='__main__':unittest.main()
