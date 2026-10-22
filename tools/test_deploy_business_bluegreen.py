import hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from tools import deploy_business_bluegreen as deploy

class BluegreenTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=self.root/'old';self.new=self.root/'new'
  for root in (self.old,self.new):(root/'iis/App_Code').mkdir(parents=True)
  self.proxy=self.old/'iis/App_Code/XnbyReferenceProxy.cs';self.proxy.write_bytes(b'old fixed 127.0.0.1:18873')
  (self.new/'iis/App_Code/XnbyReferenceProxy.cs').write_bytes(b'new fixed 127.0.0.1:18874')
  self.config=self.old/'iis/web.config';self.config.write_bytes(b'<configuration><appSettings><add key="XnbyIngressKey" value="private-fixture-only"/></appSettings><system.web><httpRuntime maxRequestLength="128" /></system.web></configuration>')
  self.manifest=self.old/'package_manifest.json';self.manifest.write_text(json.dumps(dict(version='fixture',files=[dict(path='iis/App_Code/XnbyReferenceProxy.cs',bytes=self.proxy.stat().st_size,sha256=deploy.digest(self.proxy.read_bytes()))])),encoding='utf-8')
  self.pin=deploy.digest(self.manifest.read_bytes())
 def tearDown(self):self.temp.cleanup()
 def changes(self):
  with patch.object(deploy,'OLD_MANIFEST_SHA',self.pin):return deploy.ingress_changes(self.old,self.new)
 def test_switch_and_rollback_restore_exact_bytes_and_preserve_private_key(self):
  changes=self.changes();written=deploy.switch(changes,self.root/'backups')
  self.assertIn(b'maxRequestLength="3072"',self.config.read_bytes());self.assertIn(b'private-fixture-only',self.config.read_bytes())
  manifest=json.loads(self.manifest.read_bytes());self.assertEqual(manifest['files'][0]['sha256'],deploy.digest(self.proxy.read_bytes()))
  deploy.rollback(written)
  for path,before,_ in changes:self.assertEqual(path.read_bytes(),before)
 def test_unexpected_old_manifest_or_proxy_is_rejected_before_write(self):
  with self.assertRaises(ValueError):deploy.ingress_changes(self.old,self.new)
  self.proxy.write_bytes(b'changed outside this deployment')
  with self.assertRaises(ValueError):self.changes()
  self.assertIn(b'maxRequestLength="128"',self.config.read_bytes())
 def test_concurrent_ingress_change_rejected_without_overwriting_foreign_file(self):
  changes=self.changes();self.config.write_bytes(b'foreign edit')
  with self.assertRaises(ValueError):deploy.switch(changes,self.root/'backup-race')
  self.assertEqual(self.config.read_bytes(),b'foreign edit');self.assertEqual(self.proxy.read_bytes(),changes[0][1])
 def test_rollback_refuses_to_clobber_later_foreign_change(self):
  changes=self.changes();written=deploy.switch(changes,self.root/'backups');self.manifest.write_bytes(b'foreign post-deploy edit')
  with self.assertRaises(ValueError):deploy.rollback(written)
  self.assertEqual(self.manifest.read_bytes(),b'foreign post-deploy edit')
 def test_online_sqlite_backup_includes_committed_wal_and_preserves_source(self):
  source=self.root/'source.sqlite';target=self.root/'backup.sqlite'
  with closing(sqlite3.connect(source)) as db:
   db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE records(id INTEGER PRIMARY KEY,value BLOB)');db.execute('INSERT INTO records VALUES(1,?)',(b'original bytes',));db.commit()
   before=source.read_bytes();deploy.backup_database(source,target);self.assertEqual(source.read_bytes(),before)
   with closing(sqlite3.connect(target)) as copy:self.assertEqual(copy.execute('SELECT * FROM records').fetchall(),[(1,b'original bytes')])
  with self.assertRaises(ValueError):deploy.backup_database(source,target)
 def test_missing_or_duplicate_http_limit_is_rejected(self):
  self.config.write_bytes(b'<configuration/>')
  with self.assertRaises(ValueError):self.changes()
  self.config.write_bytes(b'<configuration><httpRuntime maxRequestLength="128"/><httpRuntime maxRequestLength="128"/></configuration>')
  with self.assertRaises(ValueError):self.changes()
if __name__=='__main__':unittest.main()
