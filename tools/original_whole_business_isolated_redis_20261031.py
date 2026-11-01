"""Fresh, authenticated, loopback-only real Redis owned by one audit fixture."""
from pathlib import Path
import json,os,re,socket,subprocess,time
import verify_emergency_business_http_20261030 as c
from original_task_identity_authority import listener_owner,process_identity

class AuditRedis:
 def __init__(self,root,secret,nonce):
  self.root=Path(root).resolve(strict=True);assert self.root.parent==c.W and re.fullmatch('full-business-main-r[0-9]+',self.root.name);assert len(secret)==32 and re.fullmatch(b'[a-f0-9]{32}',secret);self.secret=secret;self.nonce=nonce;self.process=None;self.job=None;self.log=None;self.port=0;self.ready=False;self.cache=self.root/'cache';self.cache.mkdir();exe=c.Q/'runtime/redis/redis-server.exe';pin=c.read(c.Q/'payload-manifest.json')['files']['runtime/redis/redis-server.exe'];assert c.sha(exe)==pin['sha256']=='79cd623a9999d75e944e8d2509547ddeee67a2c6c7b88d11d1137eb57fec10a0';self.exe=exe
 def command(self,*values,shutdown=False):
  with socket.create_connection(('127.0.0.1',self.port),timeout=3) as sock:
   stream=sock.makefile('rb')
   def exchange(parts):
    raw=[p if isinstance(p,bytes) else str(p).encode('ascii') for p in parts];sock.sendall(b'*'+str(len(raw)).encode()+b'\r\n'+b''.join(b'$'+str(len(v)).encode()+b'\r\n'+v+b'\r\n' for v in raw));line=stream.readline(4097);assert len(line)<4097
    if not line:return None
    if line.startswith(b'+'):return line[1:-2].decode('ascii')
    if line.startswith(b':'):return int(line[1:-2])
    raise RuntimeError('OWN_REDIS_RESPONSE_TYPE_'+line[:1].hex())
   assert exchange(['AUTH',self.secret])=='OK'
   try:return exchange(values)
   except (ConnectionResetError,ConnectionAbortedError):
    if shutdown:return None
    raise
 def start(self):
  with socket.socket() as reserve:reserve.bind(('127.0.0.1',0));self.port=reserve.getsockname()[1]
  assert listener_owner(self.port)==[];config=self.cache/'own-redis.conf';config.write_text('bind 127.0.0.1\nport '+str(self.port)+'\ndatabases 1\ndaemonize no\nsave ""\nappendonly no\nmaxmemory 64mb\ndir "'+self.cache.as_posix()+'"\ndbfilename own-cache.rdb\nloglevel warning\nrequirepass '+self.secret.decode('ascii')+'\n',encoding='ascii');self.log=open(self.cache/'server.log','wb');self.process=subprocess.Popen([str(self.exe),str(config)],cwd=self.cache,env=dict(os.environ,TEMP=str(self.cache),TMP=str(self.cache)),stdin=subprocess.DEVNULL,stdout=self.log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);self.job=c.OwnedWindowsJob(self.process);image,start=process_identity(self.process._handle);assert image==self.exe.resolve();deadline=time.monotonic()+15
  while True:
   assert self.process.poll() is None,'OWN_REDIS_START_FAILED'
   try:
    assert listener_owner(self.port)==[('127.0.0.1',self.process.pid)];assert self.command('PING')=='PONG' and self.command('DBSIZE')==0;break
   except (OSError,AssertionError):assert time.monotonic()<deadline,'OWN_REDIS_READY_TIMEOUT';time.sleep(.05)
  self.ready=True;(self.root/'own-redis.properties').write_text('port='+str(self.port)+'\nnonce='+self.nonce+'\n',encoding='ascii');c.dump(self.root/'own-redis-started.json',{'pid':self.process.pid,'processCreationFiletime':start,'imageSHA256':c.sha(self.exe),'boundOnly127001':True,'syntheticCredentialOnly':True,'emptyFreshCache':True,'port':self.port,'formalCacheConnected':False})
 def close(self):
  if self.process is None:return
  normal=False;keys=None;forced=False
  try:
   if self.process.poll() is None:
    assert listener_owner(self.port)==[('127.0.0.1',self.process.pid)];keys=self.command('DBSIZE');self.command('SHUTDOWN','NOSAVE',shutdown=True);self.process.wait(timeout=12)
    normal=self.process.returncode==0
  finally:
   forced=self.process.poll() is None
   if self.job:self.job.close()
   self.process.wait(timeout=10)
   if self.log:self.log.close()
   assert self.secret not in (self.cache/'server.log').read_bytes(),'SYNTHETIC_CACHE_SECRET_OUTPUT_REFUSED';receipt={'pid':self.process.pid,'exitCode':self.process.returncode,'startupReady':self.ready,'normalAuthenticatedShutdown':normal,'lastOwnKeyCount':keys,'listenerGone':listener_owner(self.port)==[],'forcedJobClosure':forced,'formalCacheConnected':False};c.dump(self.root/'own-redis-stopped.json',receipt);self.secret=b''
  assert receipt['listenerGone'] and (normal or not self.ready),'OWN_REDIS_NORMAL_SHUTDOWN_REQUIRED'
