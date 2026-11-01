"""Owned controller-side Windows listener witness. No HTTP, token, account or cache access.

Not installed in the current supervisor. A caller must supply its own Popen child,
fixed release image/class pins, and the matching freshly created business run.
"""
from pathlib import Path
import ctypes,hashlib,os,re,socket,struct,threading,time,uuid

SCHEMA='xnby.task-token-owner-authority.v1'
PROBE='xnby.task-token-owner-probe.v1'
REPLY='xnby.task-token-owner-reply.v1'
READY='task-token-identity-ready.properties'
CLASS_PINS={
 'readerClassSHA256':'afa910c8ba00e6e94a1ddf3936e4a9d8a660556e5aa0951d0106f394c19cbdcf',
 'bridgeClassSHA256':'8fd92b21eaeebd8e649f1d366df1dd2022874a109493711fa2f389f8a553f443',
 'originalDefaultLogicClassSHA256':'c1d00813cab32aa76447043ac0854f2d795763228b26e8a83148e6e11719970d',
 'originalDaoClassSHA256':'8fdbc48d000d4daf7c75fd0f9129e56a49c003e2e8243d4d6b002a53d5f8eeed'}

def need(value,code):
 if not value:raise RuntimeError(code)

def canonical(path):
 p=Path(path).absolute();need(p.resolve(strict=True)==p,'CANONICAL_AUTHORITY_PATH_REQUIRED')
 for q in [p,*p.parents]:need(not(q.lstat().st_file_attributes&0x400),'NO_AUTHORITY_REPARSE_POINT')
 return p

def small_file(path):
 p=canonical(path);stat=p.stat();need(p.is_file() and stat.st_size<=4096 and stat.st_nlink==1,'SMALL_SINGLE_LINK_METADATA_REQUIRED')
 with p.open('rb') as f:raw=f.read(4097)
 need(len(raw)<=4096,'BOUNDED_METADATA_BYTES');return raw

def properties(raw):
 result={}
 for line in raw.decode('ascii').splitlines():
  if not line or line.startswith(('#','!')):continue
  need('=' in line and '\\' not in line,'CANONICAL_METADATA_PROPERTIES_REQUIRED');key,value=line.split('=',1)
  need(key not in result,'UNIQUE_METADATA_KEYS_REQUIRED');result[key]=value
 return result

def owner(root):
 values=properties(small_file(root/'server-owner.properties'))
 need(set(values)=={'schema','ownerId'} and values['schema']=='zhumadian.original.server.owner.v1','EXACT_RUN_OWNER_REQUIRED')
 value=values['ownerId'];need(str(uuid.UUID(value))==value,'CANONICAL_OWNER_UUID_REQUIRED');return hashlib.sha256(value.encode()).hexdigest()

def image_sha(path):
 raw=small_image(path);return hashlib.sha256(raw).hexdigest()

def small_image(path):
 p=canonical(path);need(p.is_file() and p.stat().st_size<=1024*1024,'BOUNDED_PROCESS_IMAGE_REQUIRED')
 with p.open('rb') as f:raw=f.read(1024*1024+1)
 need(len(raw)<=1024*1024,'BOUNDED_PROCESS_IMAGE_BYTES');return raw

def process_identity(handle):
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 query=kernel.QueryFullProcessImageNameW;query.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)];query.restype=ctypes.c_int
 size=ctypes.c_ulong(32768);text=ctypes.create_unicode_buffer(size.value);need(query(ctypes.c_void_p(int(handle)),0,text,ctypes.byref(size)),'OWN_PROCESS_IMAGE_REQUIRED')
 times=kernel.GetProcessTimes;times.argtypes=[ctypes.c_void_p,*([ctypes.POINTER(ctypes.c_ulonglong)]*4)];times.restype=ctypes.c_int
 created,exited,kernel_time,user_time=[ctypes.c_ulonglong() for _ in range(4)]
 need(times(ctypes.c_void_p(int(handle)),ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel_time),ctypes.byref(user_time)),'OWN_PROCESS_START_REQUIRED')
 return canonical(text.value),(created.value//10000)-11644473600000

def listener_owner(port):
 # The Windows API returns the listener table in memory. Retain only this owned port.
 api=ctypes.WinDLL('iphlpapi',use_last_error=True).GetExtendedTcpTable
 api.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong),ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong];api.restype=ctypes.c_ulong
 size=ctypes.c_ulong();need(api(None,ctypes.byref(size),False,2,3,0)==122 and size.value<=16*1024*1024,'BOUNDED_WINDOWS_LISTENER_TABLE')
 buf=ctypes.create_string_buffer(size.value);need(api(buf,ctypes.byref(size),False,2,3,0)==0,'WINDOWS_LISTENER_QUERY_FAILED');raw=buf.raw;count=struct.unpack_from('<I',raw)[0];need(4+count*24<=len(raw),'VALID_WINDOWS_LISTENER_TABLE');matches=[]
 for offset in range(count):
  state,addr,local_port,_,_,pid=struct.unpack_from('<6I',raw,4+24*offset)
  if state==2 and socket.ntohs(local_port&65535)==port:matches.append((socket.inet_ntoa(struct.pack('<I',addr)),pid))
 return matches

def atomic_properties(path,values,replace=False):
 need(not path.exists() or replace,'FRESH_AUTHORITY_METADATA_REQUIRED');pending=path.with_name(path.name+'.pending')
 raw=''.join(k+'='+str(v)+'\n' for k,v in values.items()).encode('ascii')
 need(len(raw)<=4096 and not pending.exists(),'BOUNDED_FRESH_AUTHORITY_WRITE')
 with pending.open('xb') as f:f.write(raw);f.flush()
 if replace:os.replace(pending,path)
 else:os.rename(pending,path) # Windows rename refuses an existing destination.

class OwnedTaskIdentityAuthority:
 def __init__(self,platform_process,business_root,platform_image,platform_image_sha256,controller_image,controller_image_sha256,registration_class_sha256):
  self.process=platform_process;self.business=canonical(business_root);p=self.business
  need(p.name=='b' and re.fullmatch(r'j[1-9][0-9]{0,3}',p.parent.name) and p.parents[1].name=='runs' and p.parents[2].name=='OriginalServer' and p.parents[3].name=='UserData' and p.parents[4].name=='Application','OWN_BUSINESS_RUN_REQUIRED')
  self.platform=canonical(p.parents[3]/'TianjinOriginalPlatform/runs'/p.parent.name);self.owner=owner(p);need(owner(self.platform)==self.owner,'PAIRED_RUN_OWNER_REQUIRED');self.registration=registration_class_sha256
  self.platform_image=canonical(platform_image);self.controller_image=canonical(controller_image);self.platform_sha=platform_image_sha256;self.controller_sha=controller_image_sha256
  for value in [self.platform_sha,self.controller_sha,self.registration]:need(re.fullmatch('[0-9a-f]{64}',value),'FIXED_RELEASE_SHA_REQUIRED')
  need(image_sha(self.platform_image)==self.platform_sha and image_sha(self.controller_image)==self.controller_sha,'FIXED_RELEASE_IMAGES_REQUIRED')
  image,self.platform_start=process_identity(platform_process._handle);need(image==self.platform_image and platform_process.poll() is None,'OWN_LIVE_PLATFORM_CHILD_REQUIRED')
  image,self.controller_start=process_identity(-1);need(image==self.controller_image,'OWN_CONTROLLER_IMAGE_REQUIRED');self.ready=small_file(self.platform/READY);self.ready_sha=hashlib.sha256(self.ready).hexdigest();ready=properties(self.ready)
  need(ready.get('schema')=='xnby.original-task-token-bridge.v1' and ready.get('state')=='ACTIVE' and ready.get('platformPID')==str(self.process.pid) and ready.get('ownerSHA256')==self.owner and ready.get('registrationClassSHA256')==self.registration,'OWN_READY_BINDING_REQUIRED')
  need(all(ready.get(k)==v for k,v in CLASS_PINS.items()),'PINNED_ORIGINAL_IDENTITY_CLASSES_REQUIRED');self.port=int(ready['port']);need(1024<=self.port<=65535,'VALID_OWN_BRIDGE_PORT');self.folder=self.business/'task-token-owner-probes';self.folder.mkdir();self.folder=canonical(self.folder);self.nonce=uuid.uuid4().hex;self.stop_event=threading.Event();self.thread=None;self.accepted=0;self.rejected=0;self.error=False;self.stopped=False
  self._live()
  atomic_properties(self.folder/'authority.properties',{'schema':SCHEMA,'ownerSHA256':self.owner,'authorityNonce':self.nonce,'controllerPID':os.getpid(),'controllerStartEpochMillis':self.controller_start,'controllerImageSHA256':self.controller_sha,'platformPID':self.process.pid,'platformStartEpochMillis':self.platform_start,'platformImageSHA256':self.platform_sha,'readySHA256':self.ready_sha,'port':self.port})
 def _live(self):
  need(self.process.poll() is None,'OWN_PLATFORM_EXITED')
  need(owner(self.business)==self.owner and owner(self.platform)==self.owner and small_file(self.platform/READY)==self.ready,'RUN_METADATA_CHANGED')
  for name in ['task-token-identity-closing.properties','task-token-identity-stopped.properties']:need(not(self.platform/name).exists(),'PLATFORM_IDENTITY_CLOSING')
  image,start=process_identity(self.process._handle);need(image==self.platform_image and start==self.platform_start,'PLATFORM_PROCESS_REPLACED')
  need(listener_owner(self.port)==[('127.0.0.1',self.process.pid)],'EXACT_WINDOWS_LISTENER_OWNER_REQUIRED')
  need(self.process.poll() is None,'PLATFORM_EXITED_DURING_WITNESS')
 def start(self):
  need(self.thread is None and not self.stopped,'AUTHORITY_SINGLE_START')
  self.thread=threading.Thread(target=self._loop,name='owned-task-identity-authority',daemon=True);self.thread.start()
 def _loop(self):
  try:
   while not self.stop_event.is_set():
    entries=list(self.folder.iterdir());need(len(entries)<=128,'BOUNDED_AUTHORITY_PROBE_QUEUE')
    for path in entries:
     if not re.fullmatch(r'[0-9a-f]{32}\.request',path.name):continue
     nonce=path.stem;response=self.folder/(nonce+'.response')
     if response.exists():continue
     try:
      age=time.time()-path.stat().st_mtime
      if age>3:path.unlink();continue
      need(age>=-1,'VALID_AUTHORITY_REQUEST_TIME')
      values=properties(small_file(path))
     except FileNotFoundError:continue # A timed-out caller can remove its own request.
     need(values=={'schema':PROBE,'nonce':nonce},'EXACT_METADATA_ONLY_PROBE')
     verdict='OWNER';reply={'schema':REPLY,'nonce':nonce,'authorityNonce':self.nonce}
     try:self._live()
     except (RuntimeError,OSError,ValueError):verdict='REJECTED'
     reply['verdict']=verdict
     if verdict=='OWNER':
      reply.update(ownerSHA256=self.owner,controllerPID=os.getpid(),controllerStartEpochMillis=self.controller_start,controllerImageSHA256=self.controller_sha,platformPID=self.process.pid,platformStartEpochMillis=self.platform_start,platformImageSHA256=self.platform_sha,readySHA256=self.ready_sha,port=self.port);self.accepted+=1
     else:self.rejected+=1
     atomic_properties(response,reply)
    # Only orphan protocol replies/pending writes in this new owned folder are reclaimable.
    for path in entries:
     try:
      if re.fullmatch(r'[0-9a-f]{32}\.response(?:\.pending)?',path.name) and not(self.folder/(path.name[:32]+'.request')).exists() and time.time()-path.stat().st_mtime>5:
       need(path.is_file() and not path.is_symlink(),'OWN_PROTOCOL_FILE_REQUIRED');path.unlink()
     except FileNotFoundError:pass
    self.stop_event.wait(.01)
  except (RuntimeError,OSError,ValueError):self.error=True;self.stop_event.set()
 def stop(self,seconds=2):
  need(0<=seconds<=2,'BOUNDED_AUTHORITY_STOP');self.stop_event.set()
  if self.thread is not None:self.thread.join(seconds)
  drained=self.thread is None or not self.thread.is_alive()
  if not self.stopped:
   atomic_properties(self.folder/'stopped.properties',{'schema':SCHEMA,'authorityNonce':self.nonce,'state':'STOPPED' if drained else 'STOP_INCOMPLETE'});self.stopped=True
  return drained
 def status(self):return {'acceptedFreshWindowsWitnesses':self.accepted,'rejectedWitnesses':self.rejected,'fixedMetadataProtocolError':self.error,'ownedThreadAlive':self.thread is not None and self.thread.is_alive(),'tokenAccountSessionOrBusinessAccessed':False}
