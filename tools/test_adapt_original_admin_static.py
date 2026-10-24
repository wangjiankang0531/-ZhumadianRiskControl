import http.client,json,pathlib,shutil,subprocess,threading,unittest
from readonly_original_static_archive import ArchiveServer

ROOT=pathlib.Path(__file__).parent
NODE=shutil.which('node')
PARSER=pathlib.Path('D:/Project/Zhumadian/Application/work/tianjin_native_20261023/security_pc/node_modules/@babel/parser/lib/index.js')


class OriginalAdminPrefix(unittest.TestCase):
    @unittest.skipUnless(NODE and PARSER.is_file(),'Existing Node and original locked parser required')
    def test_ast_deployment_preserves_routes_and_subapplication_ids(self):
        fixture='''function getJnpfAppId(){const p=window.location.pathname;return window.location.pathname.startsWith("/JNPF_APP_")?p.split("/")[1]:""}
let VITE_PUBLIC_PATH="/";const appId=getJnpfAppId();appId&&(VITE_PUBLIC_PATH="/"+appId);
const assetsURL=function(path){return "/"+path};
const icon="/static/icon.svg?v=1#glyph", untouched="/module/unrelated";
const theme="light", dynamic=`/static/${"icon"}.svg`, themed="/assets/style."+theme+".css";
'''
        files=[{'path':'static/js/index-26528473.js','text':fixture},{'path':'_app.config.js','text':'window.CONFIG={VITE_GLOB_API_URL:"",VITE_GLOB_APP_TITLE:"Original title"};'},
               {'path':'index.html','text':'<script src="/static/js/index-26528473.js"></script><link href="/static/icon.svg?v=1#glyph">'},
               {'path':'style.css','text':'a{background:url("/static/icon.svg?v=1#glyph")}.unrelated{background:url(/unknown/image.png)}'}]
        request={'base':'/zhumadian/admin','files':files,'assetPaths':['static/js/index-26528473.js','_app.config.js','index.html','static/icon.svg','style.css','assets/style.light.css']}
        adapted=subprocess.run([NODE,str(ROOT/'adapt_original_admin_static.mjs'),str(PARSER)],input=json.dumps(request).encode(),capture_output=True,timeout=15)
        self.assertEqual(adapted.returncode,0,adapted.stderr.decode());result=json.loads(adapted.stdout);texts={x['path']:x['text'] for x in result['files']}
        self.assertIn('/unknown/image.png',texts['style.css']);self.assertIn('untouched="/module/unrelated"',texts['static/js/index-26528473.js'])
        for path,expected_app,expected_base in [('/zhumadian/admin/login','','/zhumadian/admin/'),('/zhumadian/admin/JNPF_APP_fixture/login','JNPF_APP_fixture','/zhumadian/admin/JNPF_APP_fixture')]:
            # Execute only the authored fixture, never supplied original JavaScript.
            code='const window={location:{pathname:'+json.dumps(path)+'}};'+texts['static/js/index-26528473.js']+'\nconsole.log(JSON.stringify({app:getJnpfAppId(),base:VITE_PUBLIC_PATH,asset:assetsURL("static/icon.svg"),icon,untouched,dynamic,themed}));'
            executed=subprocess.run([NODE,'--input-type=module','-e',code],capture_output=True,timeout=10)
            self.assertEqual(executed.returncode,0,executed.stderr.decode());value=json.loads(executed.stdout)
            self.assertEqual((value['app'],value['base']),(expected_app,expected_base))
            self.assertEqual(value['asset'],'/zhumadian/admin/static/icon.svg');self.assertEqual(value['icon'],'/zhumadian/admin/static/icon.svg?v=1#glyph')
            self.assertEqual(value['dynamic'],'/zhumadian/admin/static/icon.svg');self.assertEqual(value['themed'],'/zhumadian/admin/assets/style.light.css')
        request['files'][0]['text']=fixture.replace('const assetsURL=','const changedHelper=')
        rejected=subprocess.run([NODE,str(ROOT/'adapt_original_admin_static.mjs'),str(PARSER)],input=json.dumps(request).encode(),capture_output=True,timeout=15)
        self.assertNotEqual(rejected.returncode,0)

    def test_real_http_subpath_mount_is_bounded_and_preserves_redirect_query(self):
        server=ArchiveServer({'index.html':b'original','static/icon.svg':b'<svg/>','favicon.ico':b'fixture-icon'},mount_prefix='/zhumadian/admin')
        thread=threading.Thread(target=server.serve_forever);thread.start()
        def request(path):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            try:
                connection.request('GET',path);response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
            finally:connection.close()
        try:
            self.assertEqual(request('/zhumadian/admin?kept=1')[1]['Location'],'/zhumadian/admin/?kept=1')
            self.assertEqual(request('/zhumadian/admin/login')[2],b'original')
            self.assertEqual(request('/zhumadian/admin/static/icon.svg')[2],b'<svg/>')
            self.assertEqual(request('/favicon.ico')[1]['Location'],'/zhumadian/admin/favicon.ico')
            self.assertEqual(request('/zhumadian/admin/favicon.ico')[2],b'fixture-icon')
            self.assertEqual(request('/zhumadian/admin/api/oauth/getLoginConfig')[0],503)
            for path in ['/static/icon.svg','/login','/zhumadian/admin-other/login','/zhumadian/admin/../outside']:
                self.assertIn(request(path)[0],[400,404])
        finally:server.shutdown();server.server_close();thread.join(timeout=3)


if __name__=='__main__':unittest.main()
