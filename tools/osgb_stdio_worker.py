"""One owned, bounded stdio reader; no per-node process starts or auto-restart."""
from __future__ import annotations
import atexit
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import queue
import re
import struct
import subprocess
import threading
from osgb_cropped_pages import PinnedCropReader, SourceImageNeedsCrop, unique_pairs
from osgb_memory_pages import canonical, sha, MIB
from osgb_memory_reader import MAX_SOURCE
from readonly_source_memory_store import ordinary


class OwnedWindowsJob:
    def __init__(self, process):
        if os.name != 'nt':
            raise RuntimeError('Owned stdio reader is currently validated on Windows only')
        class Basic(ctypes.Structure):
            _fields_=[('processTime',ctypes.c_longlong),('jobTime',ctypes.c_longlong),('flags',wintypes.DWORD),
                      ('minimumWorkingSet',ctypes.c_size_t),('maximumWorkingSet',ctypes.c_size_t),
                      ('activeProcesses',wintypes.DWORD),('affinity',ctypes.c_size_t),
                      ('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(key,ctypes.c_ulonglong) for key in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Basic),('io',IO),('processMemory',ctypes.c_size_t),('jobMemory',ctypes.c_size_t),
                      ('peakProcessMemory',ctypes.c_size_t),('peakJobMemory',ctypes.c_size_t)]
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];self.api.CreateJobObjectW.restype=wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];self.api.SetInformationJobObject.restype=wintypes.BOOL
        self.api.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p];self.api.QueryInformationJobObject.restype=wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];self.api.AssignProcessToJobObject.restype=wintypes.BOOL
        self.api.CloseHandle.argtypes=[wintypes.HANDLE];self.api.CloseHandle.restype=wintypes.BOOL
        self.handle=self.api.CreateJobObjectW(None,None)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        limits=Extended();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not self.api.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
            error=ctypes.WinError(ctypes.get_last_error());self.close();raise error
        actual=Extended()
        if not self.api.QueryInformationJobObject(self.handle,9,ctypes.byref(actual),ctypes.sizeof(actual),None) or not actual.basic.flags&0x2000:
            self.close();raise RuntimeError("Owned job kill-on-close policy was not applied")
        self.limit_flags=actual.basic.flags
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None


def frame_extent(prefix):
    if len(prefix)!=24 or prefix[:8] not in (b'ZMDWRK01',b'ZMDERR01',b'ZMDOSGB1',b'ZMDGEO01',b'ZMDROI01'):
        raise ValueError('unknown stdio worker frame')
    header,payload=struct.unpack_from('<QQ',prefix,8)
    if not 0<header<=MIB or payload>128*MIB or (prefix[:8] in (b'ZMDWRK01',b'ZMDERR01') and payload!=0):
        raise ValueError('stdio worker frame exceeds bounds')
    return header,payload


class StdioWorker:
    def __init__(self, executable, source_root):
        self.executable,self.source_root=Path(executable),Path(source_root)
        self.process=self.job=None;self.failed=False;self.closed=False;self.starts=0;self.requests=0
        self.responses=queue.Queue(maxsize=1);self.lock=threading.Lock();self.stderr=bytearray()
        atexit.register(self.close)
    def _read_exact(self,size):
        data=bytearray()
        while len(data)<size:
            part=self.process.stdout.read(min(size-len(data),1024*1024))
            if not part:raise EOFError('owned source reader closed stdout')
            data.extend(part)
        return bytes(data)
    def _receive(self):
        try:
            while True:
                prefix=self._read_exact(24);header,payload=frame_extent(prefix)
                self.responses.put(prefix+self._read_exact(header+payload))
        except Exception as error:
            if not self.closed:
                try:self.responses.put(error,timeout=1)
                except queue.Full:pass
    def _drain_stderr(self):
        while True:
            data=self.process.stderr.read(4096)
            if not data:return
            self.stderr.extend(data[:max(0,8192-len(self.stderr))])
    def _response(self,timeout=45):
        try:value=self.responses.get(timeout=timeout)
        except queue.Empty:
            self._hold();raise TimeoutError('owned source reader exceeded bounded response time')
        if isinstance(value,Exception):self._hold();raise RuntimeError('owned source reader frame failed: '+str(value))
        return value
    def _hold(self):
        self.failed=True
        if self.job:self.job.close();self.job=None
        if self.process and self.process.poll() is None:self.process.kill()
    def _start(self):
        if self.failed or self.closed:raise RuntimeError('owned source reader is held; no automatic restart')
        if self.process is not None:return
        self.starts+=1
        try:
            env={k:os.environ[k] for k in ('SystemRoot','WINDIR','SystemDrive') if k in os.environ}
            env['PATH']=str(self.executable.parent)+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
            self.process=subprocess.Popen([str(self.executable),str(self.source_root),'--stdio-worker-v1',str(self.executable.parent/'osgPlugins-3.6.5')],
                executable=str(self.executable),cwd=self.executable.parent,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                bufsize=0,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
            self.job=OwnedWindowsJob(self.process)
            threading.Thread(target=self._receive,daemon=True,name='source-frame-reader').start()
            threading.Thread(target=self._drain_stderr,daemon=True,name='source-stderr-reader').start()
            raw=self._response();header,payload=frame_extent(raw[:24])
            expected=dict(schema='zhumadian.osgb.worker.v1',readOnly=True,maxHeaderBytes=MIB,maxPayloadBytes=128*MIB,requestLimitBytes=4096)
            value=json.loads(raw[24:24+header],object_pairs_hook=unique_pairs)
            if raw[:8]!=b'ZMDWRK01' or canonical(value)!=canonical(expected):raise ValueError('worker handshake differs')
        except Exception:self._hold();raise
    def request(self,node,mode):
        raw=canonical({'node':node,'mode':mode})+b'\n'
        if len(raw)>4096:raise ValueError('worker request exceeds bounds')
        with self.lock:
            self._start()
            if self.process.poll() is not None:self._hold();raise RuntimeError('owned source reader exited; no automatic restart')
            try:
                pending=memoryview(raw)
                while pending:
                    written=self.process.stdin.write(pending)
                    if not written:raise BrokenPipeError("owned source reader accepted no request bytes")
                    pending=pending[written:]
                self.process.stdin.flush();result=self._response();self.requests+=1
                return result
            except Exception:self._hold();raise
    def audit(self):
        return {'starts':self.starts,'requests':self.requests,'pid':self.process.pid if self.process else None,
                'alive':bool(self.process and self.process.poll() is None),'failed':self.failed,'closed':self.closed,
                'restartEnabled':False,'jobOwned':self.job is not None,'jobLimitFlags':self.job.limit_flags if self.job else None,'stderrBytesRetained':len(self.stderr)}
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            if self.process:
                try:self.process.stdin.close()
                except OSError:pass
                try:self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:self._hold();self.process.wait(timeout=3)
            if self.job:self.job.close();self.job=None


class PinnedPersistentCropReader(PinnedCropReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.worker=StdioWorker(self.executable,self.source_root)
        self.identity=sha(canonical({'runtime':self.identity,'workerProtocol':'zhumadian.osgb.worker.v1',
                                     'hostCode':sha(Path(__file__).read_bytes())}))
    def _invoke(self,node,record,mode=None):
        self.verify_runtime()
        if not re.fullmatch(r'(Tile_[0-9]+)/\1_L[0-9]+_0[0-9u]+\.osgb',node):raise ValueError('invalid original source node')
        source=ordinary(self.source_root/node,self.source_root);stat=source.stat();before=(stat.st_size,stat.st_mtime_ns,sha(source.read_bytes()))
        if not 0<before[0]<=MAX_SOURCE or before[0]!=record['bytes'] or before[2]!=record['sha256']:raise ValueError('source differs from pinned catalog')
        raw=self.worker.request(node,mode)
        stat=source.stat()
        if before!=(stat.st_size,stat.st_mtime_ns,sha(source.read_bytes())):self.worker._hold();raise RuntimeError('source changed while reading')
        if raw[:8]==b'ZMDERR01':
            header,payload=frame_extent(raw[:24]);error=json.loads(raw[24:24+header],object_pairs_hook=unique_pairs)
            if (set(error)!=set(('schema','node','mode','returnCode','reason','message')) or error.get('schema')!='zhumadian.osgb.worker_error.v1' or
                error.get('node')!=node or error.get('mode')!=mode or type(error.get('returnCode')) is not int or error.get('returnCode')!=1 or
                not isinstance(error.get('message'),str) or len(error['message'])>8192):
                self.worker._hold();raise ValueError('invalid owned-reader error response')
            if error.get('reason')=='full_image_budget' and mode is None and error['message']=='embedded image exceeds byte budget':
                raise SourceImageNeedsCrop('original image requires bounded crop delivery')
            if error.get('reason')!='decode_refused':self.worker._hold();raise ValueError('unknown worker refusal')
            raise RuntimeError('read-only source refused: '+error['message'])
        if raw[:8] not in (b'ZMDOSGB1',b'ZMDGEO01',b'ZMDROI01'):
            self.worker._hold();raise ValueError('unexpected owned-reader response type')
        return raw
    def close(self):self.worker.close()
