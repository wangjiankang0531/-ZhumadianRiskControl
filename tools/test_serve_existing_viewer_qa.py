import contextlib,copy,http.server,io,json,os,pathlib,subprocess,sys,tempfile,threading,unittest
import serve_existing_viewer_qa as qa

def status(source):return {'schema':'zhumadian.source.runtime.status.v1','identity':qa.IDENTITY,'pid':source['servicePID'],'worker':{'pid':source['readerPID'],'starts':1,'alive':True,'handshakeComplete':True,'failed':False},'readOnly':True,'conversionEnabled':False,'protectedWrites':0}

class ExistingRuntimeBindingTests(unittest.TestCase):
 def test_previous_explicit_default_is_preserved(self):
  self.assertEqual(qa.runtime_source(),{'base':'http://127.0.0.1:8768','port':8768,'servicePID':45700,'readerPID':57944})
 def test_current_owned_runtime_can_be_selected(self):
  source=qa.runtime_source(8767,6448,24964);self.assertEqual(source['base'],'http://127.0.0.1:8767');self.assertIs(qa.verify_protected_runtime(status(source),source).__class__,dict)
 def test_partial_identity_is_never_inferred(self):
  for values in [(8767,None,None),(None,6448,None),(None,None,24964),(8767,6448,None),(8767,None,24964),(None,6448,24964)]:
   with self.subTest(values=values),self.assertRaises(ValueError):qa.runtime_source(*values)
 def test_non_loopback_construction_and_invalid_process_ids_are_rejected(self):
  for values in [(80,1,2),(65536,1,2),(True,1,2),(8767,0,2),(8767,1,-2),(8767,1,1),(8767,1,2**32),(8767,'6448',24964)]:
   with self.subTest(values=values),self.assertRaises(ValueError):qa.runtime_source(*values)
 def test_every_required_identity_and_health_field_fails_closed(self):
  source=qa.runtime_source(8767,6448,24964)
  changes=[('schema','other'),('identity','0'*64),('pid',6449),('pid',True),('worker.pid',24965),('worker.starts',2),('worker.starts',True),('worker.alive',False),('worker.handshakeComplete',False),('worker.failed',True),('readOnly',False),('conversionEnabled',True),('protectedWrites',1),('protectedWrites',False)]
  for field,value in changes:
   bad=status(source);part=bad
   for name in field.split('.')[:-1]:part=part[name]
   part[field.split('.')[-1]]=value
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):qa.verify_protected_runtime(bad,source)
  for value in [None,{},dict(status(source),worker=None)]:
   with self.assertRaises(ValueError):qa.verify_protected_runtime(value,source)
 def test_real_check_cli_reads_only_status_and_creates_no_qa_instance(self):
  requests=[];holder={}
  class Handler(http.server.BaseHTTPRequestHandler):
   def do_GET(self):
    requests.append(self.path);raw=json.dumps(status(holder['source'])).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
   def log_message(self,*args):pass
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with tempfile.TemporaryDirectory()as root:
    p=pathlib.Path(root);static=p/'static';static.mkdir();output=p/'output'
    for name in ('index.html','viewer.js','source-gain-worker.js'):(static/name).write_text('fixture')
    source=qa.runtime_source(server.server_port,os.getpid(),1 if os.getpid()!=1 else 2);holder['source']=source
    command=[sys.executable,'-B',str(pathlib.Path(qa.__file__).resolve()),'--static',str(static),'--output',str(output),'--case','baseline_near','--source-port',str(source['port']),'--expected-service-pid',str(source['servicePID']),'--expected-reader-pid',str(source['readerPID']),'--check']
    result=subprocess.run(command,capture_output=True,text=True,timeout=10)
    self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['nativeStarts'],0);self.assertEqual(requests,['/api/runtime/status']);self.assertFalse(output.exists())
  finally:server.shutdown();server.server_close();thread.join(timeout=3)

if __name__=='__main__':unittest.main()
