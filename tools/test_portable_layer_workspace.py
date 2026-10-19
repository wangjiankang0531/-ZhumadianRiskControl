"""Real local publication/reopen/restore checks, with synthetic point/line/region data."""
from contextlib import closing
import copy, hashlib, http.client, http.server, json, sqlite3, tempfile, threading, unittest
from pathlib import Path
from portable_layer_workspace import initialize_layer_repository
from services.database import SCHEMA_VERSION, SCHEMA_SQLITE_V3
from services.database_transfer import export_database, restore_database, mysql_script
from services.layers import LayerRepository
from tools.landscape_web_server import Handler


def sample():
    return {"schema":"hongtu.landscape.layers.v1","scene":"zhumadian",
      "coordinates":{"srs":"EPSG:32650","unit":"metre","axes":"east,north,up","origin":[225319.5,3648440.1,30.9]},
      "layers":[{"id":"manual","name":"�˹���ע����","visible":True,"locked":False,"features":[
        {"id":"p","name":"ģ����ҵ��","type":"point","positions":[[4,5,6]],
         "style":{"icon":"warning","sizePx":18,"pattern":"solid","widthPx":2,"color":"#22D3EE","opacity":0.8,"fillColor":"#22D3EE","fillOpacity":0.25},
         "label":{"text":"ģ����ҵ","visible":True,"fontPx":16,"color":"#FFFFFF","opacity":1,"offset":[12,-16]},
         "business":{"sourceSystem":"DEMO","objectType":"enterprise","businessId":"DEMO-E","enterpriseId":"DEMO-E"}},
        {"id":"l","name":"ģ��·��","type":"line","positions":[[4,5,6],[7,8,9]],
         "style":{"icon":"pin","sizePx":18,"pattern":"dash","widthPx":4,"color":"#F59E0B","opacity":0.6,"fillColor":"#F59E0B","fillOpacity":0.25}},
        {"id":"r","name":"ģ���ֻ�����","type":"region","positions":[[4,5,6],[7,8,9],[9,2,6]],
         "style":{"icon":"pin","sizePx":18,"pattern":"solid","widthPx":2,"color":"#00FF00","fillColor":"#34D399","opacity":1,"fillOpacity":0.25}}
      ]}]}


class PortableLayerWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="zmd_portable_layers_");self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"���� �ո��";self.user=self.root/"UserData";self.user.mkdir(parents=True)
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


if __name__=='__main__':unittest.main()
