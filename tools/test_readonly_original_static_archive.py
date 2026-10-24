import hashlib,http.client,http.server,io,pathlib,tarfile,tempfile,threading,unittest
from readonly_original_static_archive import ArchiveServer,load_archive,request_name


class OriginalStaticArchive(unittest.TestCase):
    def archive(self,folder,entries):
        path=pathlib.Path(folder)/'input.tar.gz'
        with tarfile.open(path,'w:gz') as archive:
            for name,data,kind in entries:
                item=tarfile.TarInfo(name);item.type=kind;item.size=len(data) if kind==tarfile.REGTYPE else 0
                if kind==tarfile.SYMTYPE:item.linkname='../outside'
                archive.addfile(item,io.BytesIO(data) if kind==tarfile.REGTYPE else None)
        return path,hashlib.sha256(path.read_bytes()).hexdigest()
    def test_archive_sha_limits_and_duplicate_or_link_members(self):
        index=('dist_new/index.html',b'<h1>Original fixture</h1>',tarfile.REGTYPE)
        with tempfile.TemporaryDirectory() as folder:
            path,pin=self.archive(folder,[index])
            self.assertEqual(load_archive(path,pin)[0]['index.html'],index[1])
            with self.assertRaisesRegex(ValueError,'SHA'):load_archive(path,'0'*64)
            with self.assertRaisesRegex(ValueError,'Expanded'):load_archive(path,pin,max_expanded=1)
            for bad in [[index,index],[index,('dist_new/link',b'',tarfile.SYMTYPE)],
                        [index,('dist_new/../outside',b'x',tarfile.REGTYPE)]]:
                path,pin=self.archive(folder,bad)
                with self.assertRaises(ValueError):load_archive(path,pin)
            self.assertEqual([p.name for p in pathlib.Path(folder).iterdir()],['input.tar.gz'])
    def test_request_paths_cannot_escape_archive(self):
        self.assertEqual(request_name('/static/app.js?v=1'),'static/app.js')
        for value in ['/../secret','/%2e%2e/secret','//other/path','/static\\app.js','/%00','https://other/static/app.js']:
            with self.subTest(value=value),self.assertRaises(ValueError):request_name(value)

    def test_original_inspection_proxy_forwards_only_two_read_routes(self):
        observed=[]
        payload=b'{"code":200,"data":{"redirect":false}}'
        class OriginalRouteFixture(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                observed.append(self.path);self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        upstream=http.server.ThreadingHTTPServer(('127.0.0.1',0),OriginalRouteFixture);upstream_thread=threading.Thread(target=upstream.serve_forever);upstream_thread.start()
        server=ArchiveServer({'index.html':b'fixture'},upstream.server_port);worker=threading.Thread(target=server.serve_forever);worker.start()
        def get(path,method='GET'):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            try:
                connection.request(method,path);response=connection.getresponse();return response.status,response.read()
            finally:connection.close()
        try:
            self.assertEqual(get('/api/oauth/getLoginConfig'),(200,payload))
            self.assertEqual(get('/api/oauth/CurrentUser?systemCode=home'),(200,payload))
            self.assertEqual(get('/api/oauth/OtherOperation')[0],503)
            self.assertEqual(get('/api/oauth/Login','POST')[0],503)
            self.assertEqual(observed,['/api/oauth/getLoginConfig','/api/oauth/CurrentUser?systemCode=home'])
            self.assertEqual(len(server.original_reads),2)
        finally:
            server.shutdown();server.server_close();worker.join(timeout=3)
            upstream.shutdown();upstream.server_close();upstream_thread.join(timeout=3)
    def test_real_http_original_bytes_spa_and_unavailable_business_api(self):
        files={'index.html':b'<h1>Original fixture</h1>','static/app.js':b'console.log("original");'}
        server=ArchiveServer(files);thread=threading.Thread(target=server.serve_forever);thread.start()
        def request(path,method='GET',body=None):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            try:
                connection.request(method,path,body);response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
            finally:connection.close()
        try:
            status,headers,data=request('/static/app.js?v=1');self.assertEqual((status,data),(200,files['static/app.js']))
            self.assertTrue(headers['Content-Type'].startswith('application/javascript'))
            self.assertEqual(request('/login')[2],files['index.html'])
            self.assertEqual(request('/assets/missing.js')[0],404)
            self.assertEqual(request('/api/oauth/CurrentUser')[0],503)
            self.assertEqual(request('/api/oauth/Login','POST',b'fixture-only')[0],503)
            self.assertEqual(request('/%2e%2e/outside')[0],400)
            self.assertEqual(request('/static/app.js','HEAD')[2],b'')
        finally:server.shutdown();server.server_close();thread.join(timeout=3)
        self.assertFalse(thread.is_alive())


if __name__=='__main__':unittest.main()
