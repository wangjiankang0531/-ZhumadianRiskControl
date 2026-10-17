import copy, hashlib, http.client, json, sqlite3, tempfile, threading, unittest
from contextlib import closing
from pathlib import Path
from services.tests import test_api as fixture
from services.api import Service
from services.layers import LayerRepository
from services.database import SCHEMA_VERSION
from services.database_transfer import export_database,restore_database,mysql_script,validate_database
from services.common import ApiError

class DatabaseLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.ApiTests.setUpClass()
    def setUp(self):
        self.p=fixture.ApiTests();self.p.setUp();self.path=self.p.root/'business.sqlite';self.repo=LayerRepository(self.path)
        self.raw=b'\xef\xbb\xbf'+json.dumps(self.p.layers,ensure_ascii=False,indent=2).encode('utf-8')
    def tearDown(self):self.p.tearDown()
    def load(self):return self.repo.import_bytes('QA','default',self.raw,0)
    def test_exact_dlg_bytes_and_materialized_geometry_styles_order(self):
        result=self.load();self.assertEqual(result['featureCount'],4);self.assertEqual(self.repo.get('QA')['raw'],self.raw)
        with self.repo.transaction() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],SCHEMA_VERSION)
            rows=db.execute('SELECT feature_id,payload FROM dlg_features ORDER BY sort_index').fetchall()
            self.assertEqual([r[0] for r in rows],['a','b','public','unknown'])
            self.assertEqual(json.loads(rows[0][1]),self.p.layers['layers'][0]['features'][0])
            validate_database(db)
    def test_cas_rejects_stale_writer_and_retains_full_history(self):
        self.load();new=copy.deepcopy(self.p.layers);new['layers'][0]['name']='修改图层颜色与中文名'
        raw=json.dumps(new,ensure_ascii=False).encode();self.repo.import_bytes('QA','default',raw,1)
        with self.assertRaises(ApiError) as error:self.repo.import_bytes('QA','default',self.raw,1)
        self.assertEqual(error.exception.code,'LAYER_REVISION_CONFLICT');self.assertEqual(self.repo.get('QA')['raw'],raw)
        with self.repo.transaction() as db:
            rows=db.execute('SELECT revision,payload FROM dlg_versions ORDER BY revision').fetchall();self.assertEqual(len(rows),2);self.assertEqual(bytes(rows[0][1]),self.raw)
        self.assertFalse(self.repo.import_bytes('QA','default',raw,2)['changed'])
    def test_invalid_snapshot_does_not_change_current_or_history(self):
        self.load();bad=copy.deepcopy(self.p.layers);bad['layers'][0]['visible']='false'
        with self.assertRaises(ValueError):self.repo.import_bytes('QA','default',json.dumps(bad).encode(),1)
        self.assertEqual(self.repo.get('QA')['revision'],1)
        with self.repo.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM dlg_versions').fetchone()[0],1)
    def test_authorized_api_reads_database_after_source_file_is_removed(self):
        self.load();self.p.config['businessDatabase']='business.sqlite';self.p.config['data']['layerDocument']='default';self.p.write('config.json',self.p.config)
        self.p.server.service=Service(self.p.root/'config.json');(self.p.root/'layers.json').unlink()
        status,data,_=self.p.request('/api/v1/spatial_objects');self.assertEqual(status,200,data);self.assertEqual({i['id'] for i in data['items']},{'a','public'})
        other=self.p.request('/api/v1/spatial_objects',self.p.token('QA-B'))[1];self.assertEqual([i['id'] for i in other['items']],['b'])
    def test_lossless_export_restore_and_mysql_script(self):
        self.load();from services.focus import FocusStore
        from services.focus_demo import seed
        seed(FocusStore(self.path));archive=self.p.root/'export';manifest=export_database(self.path,archive)
        self.assertEqual(manifest['tables']['issues']['rows'],10)
        restored=self.p.root/'restored.sqlite';restore_database(archive,restored);self.assertEqual(LayerRepository(restored).get('QA')['raw'],self.raw)
        with closing(sqlite3.connect(restored)) as db:validate_database(db)
        script=self.p.root/'migration.sql';mysql_script(archive,script);sql=script.read_text(encoding='utf-8');self.assertIn('0x'+self.raw.hex(),sql)
        self.assertEqual(sql.count('INSERT INTO `issues`'),10);self.assertTrue(sql.rstrip().endswith('COMMIT;'))
        with self.assertRaises(ValueError):restore_database(archive,restored)
        with self.assertRaises(ValueError):export_database(self.path,archive)
    def test_corrupt_export_rejected_before_target_is_created(self):
        self.load();archive=self.p.root/'export';export_database(self.path,archive)
        with (archive/'dlg_documents.jsonl').open('ab') as f:f.write(b'x')
        target=self.p.root/'never-created.sqlite'
        with self.assertRaises(ValueError):restore_database(archive,target)
        self.assertFalse(target.exists())
    def test_local_database_publication_and_corrupt_editor_save_preserve_snapshot(self):
        from tools.landscape_web_server import Handler
        import http.server
        source=self.p.root/'editor.json';source.write_bytes(self.raw)
        class Local(Handler):
            layers=source;layer_repository=self.repo
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Local);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def get():
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            try:c.request('GET','/layers/default.json');r=c.getresponse();return r.status,r.read(),dict(r.getheaders())
            finally:c.close()
        try:
            status,raw,h=get();self.assertEqual(status,200);self.assertEqual(raw,self.raw);self.assertEqual(h['X-XNBY-Layer-Storage'],'sqlite')
            source.write_bytes(b'{broken');self.assertEqual(get()[0],422);self.assertEqual(self.repo.get('zhumadian')['raw'],self.raw)
        finally:server.shutdown();server.server_close();thread.join()


    def test_generated_database_contract_matches_tracked_migration_schema(self):
        from tools.generate_database_docs import generate
        target=self.p.root/'generated';generate(target)
        tracked=Path(__file__).resolve().parents[2]/'deploy/database'
        for name in ['schema_mysql_v2.sql','schema_manifest.json']:
            self.assertEqual((target/name).read_bytes(),(tracked/name).read_bytes(),name)

if __name__=='__main__':unittest.main()
