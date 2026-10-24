import base64,datetime,hashlib,json,os,pathlib,secrets,socket,sqlite3,struct,subprocess,time,uuid,zipfile,http.client
import argparse
p=argparse.ArgumentParser(description='Run unchanged original bigscreen HTTP/WebSocket protocol on an owned reference-data copy.');p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--native-preparation',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args();W=args.workspace.resolve(strict=True);A=W.parents[1];assert A.name=='Application';P=pathlib.Path(__file__).parent/'java';old=args.native_preparation.resolve(strict=True);assert old.is_relative_to(W);meta=json.loads((old/'preparation.json').read_bytes());archive=pathlib.Path(meta['sourceArchive']);reference=pathlib.Path(meta['referenceDatabase']);root=args.output.resolve();assert root.is_relative_to(W) and not root.exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();assert meta['sourceArchiveSHA256']=='97c2f1662a3a4494f01da4c2e83d7fa960e6832bda870e90424ffbaddf667cca' and meta['referenceDatabaseSHA256']=='f35972a2fb79e41d076b0031ee77546664cc335ab0ce8ad83ff199e2c241cb8a';assert sha(archive)==meta['sourceArchiveSHA256'] and sha(reference)==meta['referenceDatabaseSHA256'];proof=json.loads((old/'receipt.json').read_bytes());assert proof['passedChecks']==13 and proof['ownExitCode']==0 and proof['referenceAndCopyDatabaseUnchanged'];assert sha(meta['helperJar'])=='799d1289e3122b0e73ef4b6a3c9639bc5c59d820c7670800c673a1b7acd5a508';root.mkdir()
for name in ('native','data','tmp','home','classes','logs'):(root/name).mkdir()
(root/'native/sqlitejdbc.dll').write_bytes((old/'native/sqlitejdbc.dll').read_bytes());(root/'data/working.db').write_bytes(reference.read_bytes());assert sha(root/'data/working.db')==meta['referenceDatabaseSHA256']
jdk=pathlib.Path(meta['javaHome']);deps=pathlib.Path(meta['dependencyRoot']);assert deps.resolve().is_relative_to(W);env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};env['TMP']=env['TEMP']=str(root/'tmp')
sources=[P/n for n in ('OriginalBigscreenProcessBoundary.java','OriginalBigscreenLaunch.java','OriginalBigscreenObservation.java')]+[P/'CandidateLifecycleObservation.java'];cp=os.pathsep.join(map(str,[meta['helperJar'],archive,*sorted(deps.glob('*.jar'))]))
compile=subprocess.run([str(jdk/'bin/javac.exe'),'-proc:none','-source','1.8','-target','1.8','-encoding','UTF-8','-cp',cp,'-d',str(root/'classes'),*map(str,sources)],cwd=root,env=env,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW);(root/'compile.private.log').write_bytes(compile.stdout+compile.stderr);assert compile.returncode==0,'OWN_BIGSCREEN_COMPILE_FAILED'
with zipfile.ZipFile(root/'own-launcher.jar','w',zipfile.ZIP_DEFLATED) as launcher,zipfile.ZipFile(root/'own-observation.jar','w',zipfile.ZIP_DEFLATED) as observer:
 for file in (root/'classes').rglob('*.class'):
  rel=file.relative_to(root/'classes').as_posix();target=launcher if file.name.startswith(('OriginalBigscreenLaunch','OriginalBigscreenProcessBoundary')) else observer;target.write(file,rel)
(root/'own-logback.xml').write_text('<configuration><appender name="OWN" class="ch.qos.logback.core.ConsoleAppender"><encoder><pattern>%level %logger - %msg%n</pattern></encoder></appender><root level="WARN"><appender-ref ref="OWN"/></root></configuration>',encoding='ascii')
arguments=[str(jdk/'bin/java.exe'),'-Xmx256m','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-Duser.home='+str(root/'home'),'-Dorg.sqlite.lib.path='+str(root/'native'),'-Dorg.sqlite.lib.name=sqlitejdbc.dll','-Dorg.sqlite.tmpdir='+str(root/'tmp'),'-Dserver.address=127.0.0.1','-Dserver.port=0','-Dserver.ssl.enabled=false','-Dsqlite.file='+str(root/'data/working.db'),'-Dhkinfo.app-host=127.0.0.1:9','-Dhkinfo.app-key=own-'+secrets.token_hex(8),'-Dhkinfo.app-secret=own-'+secrets.token_hex(16),'-Dspring.cloud.bootstrap.enabled=false','-Dspring.cloud.nacos.config.enabled=false','-Dspring.cloud.nacos.discovery.enabled=false','-Dspring.jmx.enabled=false','-Dmanagement.server.port=-1','-Dmanagement.endpoints.enabled-by-default=false','-Dspring.devtools.restart.enabled=false','-Dspring.main.banner-mode=off','-Dlogging.config='+(root/'own-logback.xml').as_uri(),'-Dlogback.configurationFile='+str(root/'own-logback.xml'),'-Down.boundary.trace=true','-Down.candidate.root='+str(root),'-Down.candidate.maximum-seconds=300','-Dcontext.initializer.classes=xnby.bigscreen.OriginalBigscreenObservation,xnby.replica.CandidateLifecycleObservation','-cp',os.pathsep.join(map(str,[archive,root/'own-launcher.jar',meta['helperJar']])),'xnby.bigscreen.OriginalBigscreenLaunch',str(archive),str(root)]
receipt={'startedAt':datetime.datetime.now().astimezone().isoformat(),'sourceArchiveSHA256':sha(archive),'referenceDatabaseSHA256':sha(reference),'sourceSHA256':{p.name:sha(p) for p in sources},'originalApplicationStarted':False,'originalSourceOrJarModified':False,'realVideoQueryOrControlAttempted':False,'originalDatabaseOrDLGOpenedWritable':False,'fullCloneReady':False};process=None;clients=[];log=(root/'startup.private.log').open('wb')
def props(path):return dict(l.split('=',1) for l in path.read_text('ascii').splitlines() if l and not l.startswith(('#','!')))
def count():
 c=sqlite3.connect((root/'data/working.db').as_uri()+'?mode=ro',uri=True);n=c.execute('SELECT COUNT(*) FROM SURVEY').fetchone()[0];c.close();return n
class WS:
 def __init__(self,port,path):
  self.sock=socket.create_connection(('127.0.0.1',port),timeout=4);self.sock.settimeout(4);self.buffer=b'';key=base64.b64encode(secrets.token_bytes(16)).decode();self.sock.sendall(('GET '+path+' HTTP/1.1\r\nHost: 127.0.0.1:'+str(port)+'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: '+key+'\r\n\r\n').encode('ascii'))
  while b'\r\n\r\n' not in self.buffer:self.buffer+=self.sock.recv(4096)
  header,self.buffer=self.buffer.split(b'\r\n\r\n',1);assert header.startswith(b'HTTP/1.1 101 '),'ORIGINAL_WS_HANDSHAKE_FAILED';expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest());assert expected.lower() in header.lower(),'WS_ACCEPT_MISMATCH'
 def readn(self,n):
  while len(self.buffer)<n:
   part=self.sock.recv(max(4096,n-len(self.buffer)));assert part,'WS_EARLY_CLOSE';self.buffer+=part
  value,self.buffer=self.buffer[:n],self.buffer[n:];return value
 def receive(self):
  head=self.readn(2);length=head[1]&127
  if length==126:length=struct.unpack('!H',self.readn(2))[0]
  elif length==127:length=struct.unpack('!Q',self.readn(8))[0]
  assert length<=1024**2;mask=self.readn(4) if head[1]&128 else None;payload=self.readn(length)
  if mask:payload=bytes(v^mask[i%4] for i,v in enumerate(payload))
  if head[0]&15==9:self.send(payload,10);return self.receive()
  assert head[0]&15==1,'WS_TEXT_FRAME_REQUIRED';return payload.decode('utf-8')
 def send(self,text,opcode=1):
  payload=text.encode('utf-8') if isinstance(text,str) else text;mask=secrets.token_bytes(4);length=len(payload);header=bytes([128|opcode,128|length]) if length<126 else bytes([128|opcode,128|126])+struct.pack('!H',length);self.sock.sendall(header+mask+bytes(v^mask[i%4] for i,v in enumerate(payload)))
 def until(self,predicate):
  for _ in range(12):
   raw=self.receive()
   try:value=json.loads(raw)
   except ValueError:continue
   if predicate(value):return value
  raise AssertionError('EXPECTED_ORIGINAL_WS_MESSAGE_MISSING')
 def close(self):
  try:self.send(struct.pack('!H',1000),8)
  except OSError:pass
  self.sock.close()
def request_json(port,method,path,payload):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
 try:c.request(method,path,body=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Connection':'close'});r=c.getresponse();raw=r.read(65537);assert len(raw)<65537;return r.status,json.loads(raw)
 finally:c.close()
try:
 process=subprocess.Popen(arguments,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);receipt.update(originalApplicationStarted=True,ownPID=process.pid);(root/'attempt_started.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print('ORIGINAL_BIGSCREEN_MAIN_STARTED',flush=True)
 limit=time.monotonic()+90
 while not all((root/n).exists() for n in ('candidate-ready.txt','candidate-http-port.txt','original-main-returned.txt','original-bigscreen-observation.properties')):
  assert process.poll() is None,'ORIGINAL_BIGSCREEN_EXITED_BEFORE_READY';assert time.monotonic()<limit,'ORIGINAL_BIGSCREEN_READY_TIMEOUT';time.sleep(.2)
 observed=props(root/'original-bigscreen-observation.properties');assert observed.get('passed')=='true' and observed['originalSurveyRows']=='4';port=int((root/'candidate-http-port.txt').read_text());base=observed.get('originalServletContextPath','');receipt.update(originalMainReturned=True,originalObservation=observed,ownPort=port,originalContextPath=base);print('ORIGINAL_BIGSCREEN_SQLITE_AND_BEANS_READY',flush=True)
 alpha=WS(port,base+'/collaborate/own_alpha');clients.append(alpha);data=alpha.until(lambda x:x.get('type')=='dataList');assert len(data['data'])==4;receipt['firstClientOriginalRows']=4
 beta=WS(port,base+'/collaborate/own_beta');clients.append(beta);data=beta.until(lambda x:x.get('type')=='dataList');assert len(data['data'])==4;users=alpha.until(lambda x:x.get('type')=='userList' and 'own_beta' in x.get('data',''));assert 'own_alpha' in users['data'];receipt['twoClientPresenceAndReferenceRowsVerified']=True
 item={'id':'own_'+uuid.uuid4().hex,'user':'own_alpha','type':'marker','action':'create','data':'{"ownedProbe":true}'};alpha.send(json.dumps(item));received=beta.until(lambda x:x.get('id')==item['id'] and x.get('action')=='create');assert received==item
 limit=time.monotonic()+5
 while count()!=5:assert process.poll() is None and time.monotonic()<limit;time.sleep(.05)
 receipt['originalCreateBroadcastAndSQLiteCommitVerified']=True
 delete=dict(item,action='delete');alpha.send(json.dumps(delete));assert beta.until(lambda x:x.get('id')==item['id'] and x.get('action')=='delete')==delete
 limit=time.monotonic()+5
 while count()!=4:assert process.poll() is None and time.monotonic()<limit;time.sleep(.05)
 receipt['originalDeleteBroadcastAndSQLiteCommitVerified']=True
 alpha.close();clients.remove(alpha);beta.until(lambda x:x.get('type')=='userList' and x.get('data')=='own_beta');assert count()==4;receipt['firstDisconnectPreservesRowsVerified']=True
 beta.close();clients.remove(beta);limit=time.monotonic()+5
 while count()!=0:assert process.poll() is None and time.monotonic()<limit;time.sleep(.05)
 receipt['lastDisconnectClearsOnlyOwnCopyAsOriginal']=True
 interact=WS(port,base+'/interact');clients.append(interact);assert interact.receive()=='连接成功';payload={'type':'own-protocol-probe','id':uuid.uuid4().hex};status,body=request_json(port,'POST',base+'/wsi/interact',payload);assert status==200 and body.get('success') is True and json.loads(interact.receive())==payload;receipt['originalHTTPToInteractionWebSocketVerified']=True;interact.close();clients.remove(interact)
 status,body=request_json(port,'POST',base+'/hikvideo/query',{});assert status==200 and body.get('success') is False;receipt['originalVideoEmptyInputValidationVerifiedWithoutVendorCall']=True
 receipt['passed']=True;print('ORIGINAL_BIGSCREEN_WEBSOCKET_SQLITE_AND_HTTP_PROTOCOL_PASSED',flush=True)
except Exception as error:
 import traceback
 (root/'failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');receipt.update(passed=False,failureClass=type(error).__name__);print('OWN_BIGSCREEN_PROTOCOL_FAILED_DETAILS_RETAINED',flush=True)
finally:
 for client in clients:
  try:client.close()
  except OSError:pass
 if process is not None and process.poll() is None:
  (root/'own-stop-requested.txt').write_text('stop-own-original-bigscreen-protocol\n',encoding='ascii')
  try:process.wait(timeout=18)
  except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10);receipt['forcedTermination']=True
 log.close();receipt.update(completedAt=datetime.datetime.now().astimezone().isoformat(),ownExitCode=process.returncode if process else None,contextClosed=(root/'candidate-context-closed.txt').exists(),referenceDatabaseUnchanged=sha(reference)==meta['referenceDatabaseSHA256'],sourceArchiveUnchanged=sha(archive)==meta['sourceArchiveSHA256'],originalDatabaseOrDLGOpenedWritable=False,realVideoQueryOrControlAttempted=False,fullCloneReady=False)
 if (root/'boundary-result.properties').exists():receipt['boundaryAfterClose']=props(root/'boundary-result.properties')
 (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:receipt.get(k) for k in ('passed','ownExitCode','contextClosed','forcedTermination','referenceDatabaseUnchanged','sourceArchiveUnchanged','fullCloneReady')}),flush=True)

if not (receipt.get('passed') and receipt.get('ownExitCode')==0 and receipt.get('contextClosed') and not receipt.get('forcedTermination') and receipt.get('referenceDatabaseUnchanged') and receipt.get('sourceArchiveUnchanged')):raise SystemExit(1)
