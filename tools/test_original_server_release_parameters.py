from pathlib import Path
import copy,unittest
from original_server_release_parameters import materialize,properties_ascii

class Parameters(unittest.TestCase):
    def setUp(self):
        self.spec={'configuration':{'platform':{'context.initializer.classes':'xnby.replica.ServerLifecycleObservation','config.file-storage.minio[0].end-point':'http://127.0.0.1:3001','config.file-storage.minio[0].domain':'http://127.0.0.1:3001/sys-file/','spring.datasource.prepare-url':'jdbc:mysql://127.0.0.1:3002/jnpf?serverRSAPublicKeyFile=old','config.SystemFilePath':'${PLATFORM_DATA}/files/system/'},'business':{'context.initializer.classes':'xnby.replica.ServerLifecycleObservation','flow.url':'http://127.0.0.1:3003/api/work','safety.jnpfUrl':'http://127.0.0.1:3003','spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:3002/tj_endanger?serverRSAPublicKeyFile=old','spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:3002/jnpf?useUnicode=true'}},'platformArguments':['-Down.candidate.maximum-seconds=720','-Down.platform.data.owner=old','-cp','${PLATFORM_RUN}/classes','OriginalPlatform','${PLATFORM_RUN}'],'businessArguments':['-Down.internal.platform.base=http://127.0.0.1:3003','-Down.candidate.maximum-seconds=720','-Down.startup.observation=old','-cp','${BUSINESS_RUN}/classes','OriginalBusiness','${BUSINESS_RUN}']}
        self.args=dict(application=Path('D:/q/Application'),platform_run=Path('D:/q/Application/UserData/TianjinOriginalPlatform/runs/j1'),business_run=Path('D:/q/Application/UserData/Server/runs/j1'),platform_data_owner='10000000-0000-0000-0000-000000000001',run_owner='10000000-0000-0000-0000-000000000002',database_uuid='10000000-0000-0000-0000-000000000003',database_port=4001,redis_port=4002,object_port=4003,database_password='synthetic-db',redis_password='synthetic-redis',object_access='synthetic-access',object_secret='synthetic-secret')
    def render(self,side='platform',**kw):return materialize(self.spec,side=side,**dict(self.args,**kw))
    def test_platform_exact_connections(self):
        v=self.render()['configuration'];self.assertEqual(v['spring.datasource.port'],'4001');self.assertEqual(v['spring.redis.port'],'4002');self.assertEqual(v['spring.datasource.password'],'synthetic-db');self.assertEqual(v['config.file-storage.minio[0].domain'],'http://127.0.0.1:4003/sys-file/')
    def test_business_exact_connections(self):
        v=self.render('business',platform_port=4004)['configuration'];self.assertEqual(v['flow.url'],'http://127.0.0.1:4004/api/work');self.assertIn('127.0.0.1:4001/tj_endanger',v['spring.datasource.dynamic.datasource.master.url']);self.assertEqual(v['minio.port'],'4003')
    def test_no_candidate_lease_or_probe(self):
        a=self.render('business',platform_port=4004)['arguments'];self.assertTrue(any(s=='-Down.server.lifecycle=persistent' for s in a));self.assertFalse(any('maximum-seconds' in s or 'startup.observation' in s for s in a))
    def test_credentials_stay_out_of_jvm_arguments(self):
        for side,extra in [('platform',{}),('business',{'platform_port':4004})]:
            text=' '.join(self.render(side,**extra)['arguments']);self.assertNotIn('synthetic-db',text);self.assertNotIn('synthetic-secret',text)
    def test_does_not_mutate_frozen_input(self):
        old=copy.deepcopy(self.spec);self.render();self.assertEqual(self.spec,old)
    def test_duplicate_port_rejected(self):
        with self.assertRaises(ValueError):self.render(redis_port=4001)
    def test_boolean_port_rejected(self):
        with self.assertRaises(ValueError):self.render(database_port=True)
    def test_missing_business_platform_port_rejected(self):
        with self.assertRaises(ValueError):self.render('business')
    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):self.render(business_run=Path('D:/q/Application/UserData/../../outside'))
    def test_wrong_platform_layout_rejected(self):
        with self.assertRaises(ValueError):self.render(platform_run=Path('D:/q/Application/UserData/TianjinOriginalPlatform/runs/extra/j1'))
    def test_malformed_owner_rejected(self):
        with self.assertRaises(ValueError):self.render(run_owner='not-a-uuid')
    def test_java_properties_escapes(self):
        v=properties_ascii({'key':'驻马店😀\nD:\\tmp',' a=b':' x'});self.assertIn(b'\\u9a7b\\u9a6c\\u5e97\\ud83d\\ude00\\nD\\:\\\\tmp',v);self.assertIn(b'\\ a\\=b=\\ x',v)

if __name__=='__main__':unittest.main()
