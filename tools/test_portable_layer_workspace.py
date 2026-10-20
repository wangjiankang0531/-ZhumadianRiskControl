"""Real local publication/reopen/restore checks, with synthetic point/line/region data."""
from contextlib import closing
import copy, hashlib, http.client, http.server, json, sqlite3, tempfile, threading, unittest
from pathlib import Path
from portable_layer_workspace import initialize_layer_repository, read_editor_publication, publish_layer_bytes
from portable_source_runtime import initialize_user_layers
from services.database import SCHEMA_VERSION, SCHEMA_SQLITE_V3
from services.database_transfer import export_database, restore_database, mysql_script
from services.layers import LayerRepository
from tools.landscape_web_server import Handler


def sample():
    return {"schema":"hongtu.landscape.layers.v1","scene":"zhumadian",
      "coordinates":{"srs":"EPSG:32650","unit":"metre","axes":"east,north,up","origin":[225319.5,3648440.1,30.9]},
      "layers":[{"id":"manual","name":"人工标注测试","visible":True,"locked":False,"features":[
        {"id":"p","name":"模拟企业点","type":"point","positions":[[4,5,6]],
         "style":{"icon":"warning","sizePx":18,"pattern":"solid","widthPx":2,"color":"#22D3EE","opacity":0.8,"fillColor":"#22D3EE","fillOpacity":0.25},
         "label":{"text":"模拟企业","visible":True,"fontPx":16,"color":"#FFFFFF","opacity":1,"offset":[12,-16]},
         "business":{"sourceSystem":"DEMO","objectType":"enterprise","businessId":"DEMO-E","enterpriseId":"DEMO-E"}},
        {"id":"l","name":"模拟路线","type":"line","positions":[[4,5,6],[7,8,9]],
         "style":{"icon":"pin","sizePx":18,"pattern":"dash","widthPx":4,"color":"#F59E0B","opacity":0.6,"fillColor":"#F59E0B","fillOpacity":0.25}},
        {"id":"r","name":"模拟手绘区域","type":"region","positions":[[4,5,6],[7,8,9],[9,2,6]],
         "style":{"icon":"pin","sizePx":18,"pattern":"solid","widthPx":2,"color":"#00FF00","fillColor":"#34D399","opacity":1,"fillOpacity":0.25}}
      ]}]}


class PortableLayerWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="zmd_portable_layers_");self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"中文 空格包";self.user=self.root/"UserData";self.user.mkdir(parents=True)
        self.path=self.user/"BusinessData/layers.sqlite";self.file=self.user/"layers.json"
        self.raw=b'\xef\xbb\xbf'+json.dumps(sample(),ensure_ascii=False,indent=2).encode('utf8');self.file.write_bytes(self.raw)
    def start(self,repository):
        source=self.file
        class Local(Handler):
            layers=source;layer_repository=repository;allow_local_layer_database=True
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Local)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def close():server.shutdown();server.server_close();thread.join()
        self.addCleanup(close)
        def get():
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            try:c.request('GET','/layers/default.json');response=c.getresponse();return response.status,response.read(),dict(response.getheaders())
            finally:c.close()
        return get
    def test_editor_file_http_sqlite_versions_and_reopen_keep_exact_bytes(self):
        repo=initialize_layer_repository(self.root);get=self.start(repo)
        status,body,headers=get();self.assertEqual(status,200);self.assertEqual(body,self.raw)
        self.assertEqual(headers['X-XNBY-Layer-Storage'],'sqlite');self.assertEqual(headers['X-XNBY-Layer-Revision'],'1')
        changed=sample();changed['layers'][0]['features'][1]['style']['widthPx']=9
        raw=json.dumps(changed,ensure_ascii=False,separators=(',',':')).encode('utf8');self.file.write_bytes(raw)
        self.assertEqual(get()[:2],(200,raw));again=initialize_layer_repository(self.root)
        self.assertEqual(again.get('zhumadian')['raw'],raw);self.assertEqual(again.get('zhumadian')['revision'],2)
        with repo.transaction() as db:
            rows=db.execute('SELECT revision,payload FROM dlg_versions ORDER BY revision').fetchall()
            self.assertEqual([(x[0],bytes(x[1])) for x in rows],[(1,self.raw),(2,raw)])
            features=db.execute('SELECT geometry_type,enterprise,payload FROM dlg_features ORDER BY sort_index').fetchall()
            self.assertEqual([x[0] for x in features],['point','line','region']);self.assertEqual(features[0][1],'DEMO-E')
            self.assertEqual([json.loads(x[2]) for x in features],changed['layers'][0]['features'])
        self.assertEqual(get()[2]['X-XNBY-Layer-Revision'],'2')
    def test_partial_editor_save_never_overwrites_valid_published_snapshot(self):
        repo=initialize_layer_repository(self.root);get=self.start(repo);self.assertEqual(get()[0],200)
        self.file.write_bytes(b'{partial editor save')
        self.assertEqual(get()[0],422);self.assertEqual(repo.get('zhumadian')['raw'],self.raw)
        self.assertEqual(repo.get('zhumadian')['revision'],1);self.assertEqual(self.file.read_bytes(),b'{partial editor save')
    def test_workspace_archive_restore_and_mysql_preserve_dlg_blob(self):
        repo=initialize_layer_repository(self.root);repo.import_bytes('zhumadian','default',self.raw,0)
        archive=self.user/'export';export_database(self.path,archive)
        restored=self.user/'restored.sqlite';restore_database(archive,restored)
        self.assertEqual(LayerRepository(restored).get('zhumadian')['raw'],self.raw)
        sql=self.user/'mysql.sql';mysql_script(archive,sql)
        self.assertIn('0x'+self.raw.hex(),sql.read_text('utf8'))
    def test_older_database_is_refused_without_schema_or_file_change(self):
        self.path.parent.mkdir()
        with closing(sqlite3.connect(self.path)) as db:db.executescript(SCHEMA_SQLITE_V3+'PRAGMA user_version=3;')
        before=self.path.read_bytes();mtime=self.path.stat().st_mtime_ns
        with self.assertRaisesRegex(ValueError,'explicit copy migration'):initialize_layer_repository(self.root)
        self.assertEqual(self.path.read_bytes(),before);self.assertEqual(self.path.stat().st_mtime_ns,mtime)
    def test_unknown_current_schema_is_refused_without_automatic_repair(self):
        self.path.parent.mkdir()
        with closing(sqlite3.connect(self.path)) as db:db.executescript('CREATE TABLE unexpected(x);PRAGMA user_version='+str(SCHEMA_VERSION)+';')
        before=self.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'schema differs'):initialize_layer_repository(self.root)
        self.assertEqual(self.path.read_bytes(),before)
    def test_wrong_database_or_sidecar_kind_is_refused(self):
        self.path.parent.mkdir();self.path.mkdir()
        with self.assertRaisesRegex(ValueError,'path kind'):initialize_layer_repository(self.root)


    def snapshot(self, document):
        folder=self.user/'PublishedLayers';folder.mkdir(exist_ok=True)
        raw=json.dumps(document,ensure_ascii=False,indent=2).encode('utf8');sha=hashlib.sha256(raw).hexdigest()
        path=folder/(sha+'.json')
        if not path.exists():path.write_bytes(raw)
        marker={'schema':'zhumadian.layers.publication.v1','sha256':sha,'bytes':len(raw)}
        (folder/'current.json').write_text(json.dumps(marker),'utf8')
        return raw,path,marker
    def test_current_project_switch_uses_snapshot_without_overwriting_default_or_history(self):
        repo=initialize_layer_repository(self.root)
        publish_layer_bytes(repo,read_editor_publication(self.root,self.file))
        first=sample();first['layers'][0]['name']='工程A';raw_a,path_a,meta_a=self.snapshot(first)
        self.assertEqual(publish_layer_bytes(repo,read_editor_publication(self.root,self.file))['revision'],2)
        second=copy.deepcopy(first);second['layers'][0]['features'][1]['style']['widthPx']=9
        raw_b,path_b,meta_b=self.snapshot(second)
        self.assertEqual(publish_layer_bytes(repo,read_editor_publication(self.root,self.file))['revision'],3)
        (self.user/'PublishedLayers/current.json').write_text(json.dumps(meta_a),'utf8')
        self.assertEqual(publish_layer_bytes(repo,read_editor_publication(self.root,self.file))['revision'],4)
        self.assertEqual(repo.get('zhumadian')['raw'],raw_a)
        self.assertEqual((self.file.read_bytes(),path_a.read_bytes(),path_b.read_bytes()),(self.raw,raw_a,raw_b))
        with repo.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM dlg_versions').fetchone()[0],4)
    def test_valid_publication_survives_missing_or_partial_default_workspace(self):
        raw,path,meta=self.snapshot(sample())
        self.file.write_bytes(b'{partial default must be kept')
        self.assertEqual(initialize_user_layers(self.root),self.file)
        self.assertEqual(read_editor_publication(self.root,self.file),raw)
        self.assertEqual(self.file.read_bytes(),b'{partial default must be kept')
        self.file.unlink()
        self.assertEqual(initialize_user_layers(self.root),self.file)
        self.assertFalse(self.file.exists())
        self.assertEqual(read_editor_publication(self.root,self.file),raw)
    def test_bad_marker_and_corrupt_payload_keep_previous_sqlite_snapshot(self):
        repo=initialize_layer_repository(self.root);publish_layer_bytes(repo,self.raw)
        raw,path,meta=self.snapshot(sample());marker=self.user/'PublishedLayers/current.json'
        for bad in ({**meta,'path':'../outside.json'},{**meta,'bytes':True},{**meta,'sha256':'../escape'},
                    {**meta,'schema':'unknown'},{**meta,'bytes':16*1048576+1}):
            marker.write_text(json.dumps(bad),'utf8')
            with self.assertRaises(ValueError):read_editor_publication(self.root,self.file)
            self.assertEqual(repo.get('zhumadian')['raw'],self.raw)
        marker.write_text(json.dumps(meta),'utf8');path.write_bytes(b'corrupt retained payload')
        with self.assertRaisesRegex(ValueError,'identity differs'):read_editor_publication(self.root,self.file)
        self.assertEqual(repo.get('zhumadian')['revision'],1);self.assertEqual(path.read_bytes(),b'corrupt retained payload')
    def test_publication_consumes_the_validated_bytes_without_rereading_changed_file(self):
        repo=initialize_layer_repository(self.root);raw,path,meta=self.snapshot(sample())
        captured=read_editor_publication(self.root,self.file);path.write_bytes(b'changed after validated read')
        stored=publish_layer_bytes(repo,captured)
        self.assertEqual(stored['raw'],raw);self.assertEqual(path.read_bytes(),b'changed after validated read')
    def test_pending_publication_never_selects_partial_project(self):
        folder=self.user/'PublishedLayers';folder.mkdir();(folder/'current_interrupted.pending.json').write_bytes(b'{partial')
        self.assertEqual(read_editor_publication(self.root,self.file),self.raw)
        raw,path,meta=self.snapshot(sample());self.assertEqual(read_editor_publication(self.root,self.file),raw)
        self.assertEqual((folder/'current_interrupted.pending.json').read_bytes(),b'{partial')
    def test_marker_bound_and_duplicate_keys_are_refused(self):
        raw,path,meta=self.snapshot(sample());marker=self.user/'PublishedLayers/current.json'
        marker.write_bytes(b' '*4097)
        with self.assertRaisesRegex(ValueError,'exceeds bound'):read_editor_publication(self.root,self.file)
        marker.write_text('{"schema":"first","schema":"second"}','utf8')
        with self.assertRaisesRegex(ValueError,'duplicate'):read_editor_publication(self.root,self.file)
    def test_marker_or_payload_wrong_kind_is_refused(self):
        folder=self.user/'PublishedLayers';folder.mkdir();marker=folder/'current.json';marker.mkdir()
        with self.assertRaisesRegex(ValueError,'path kind'):read_editor_publication(self.root,self.file)
    def test_republishing_identical_saved_project_is_idempotent(self):
        repo=initialize_layer_repository(self.root);raw,path,meta=self.snapshot(sample())
        first=publish_layer_bytes(repo,read_editor_publication(self.root,self.file))
        second=publish_layer_bytes(repo,read_editor_publication(self.root,self.file))
        self.assertEqual(first['revision'],second['revision']);self.assertEqual(second['raw'],raw)


if __name__=='__main__':unittest.main()
