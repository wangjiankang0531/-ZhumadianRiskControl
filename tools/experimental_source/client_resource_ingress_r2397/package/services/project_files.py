"""A fixed-directory, lossless DLG JSON library with cross-process compare-and-swap."""
from pathlib import Path
from contextlib import contextmanager
import ctypes,datetime,hashlib,json,os,re,stat,threading,time,unicodedata,uuid
from services.common import ApiError,loads
from services.data import validate_layers
from tools.landscape_layer_validation import validate_editor_layers
MAX_BYTES=16*1048576

def project_filename(value):
    if not isinstance(value,str)or not 1<=len(value)<=100 or value!=value.strip()or unicodedata.normalize('NFC',value)!=value or not value.lower().endswith('.json'):
        raise ValueError('INVALID_PROJECT_FILE_NAME')
    stem=value[:-5]
    device=stem.split('.',1)[0].rstrip(' ').casefold()
    if device in {'con','prn','aux','nul','clock$','conin$','conout$'}or re.fullmatch(r'(com|lpt)[1-9¹²³]',device):raise ValueError('INVALID_PROJECT_FILE_NAME')
    if not stem or stem!=stem.strip()or stem.endswith('.')or re.search(r'[<>:"/\\|?*\x00-\x1f\x7f]',value)or re.match(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)',stem,re.I):
        raise ValueError('INVALID_PROJECT_FILE_NAME')
    return value

def regular(path,directory=False):
    path=Path(path)
    if not path.is_absolute()or '..'in path.parts:raise ValueError('EXPLICIT_PROJECT_DIRECTORY_REQUIRED')
    for item in [*reversed(path.parents),path]:
        try:info=item.lstat()
        except FileNotFoundError:continue
        if stat.S_ISLNK(info.st_mode)or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('PROJECT_PATH_REDIRECTION_REJECTED')
        if item==path and (stat.S_ISDIR(info.st_mode)!=directory or not directory and not stat.S_ISREG(info.st_mode)):raise ValueError('INVALID_PROJECT_PATH_KIND')
    return path

class ProjectFileRepository:
    def __init__(self,root,maximum_files=512,*,validate_document=None,filename_validator=project_filename):
        if type(maximum_files)is not int or not 1<=maximum_files<=4096:raise ValueError('INVALID_PROJECT_FILE_CAPACITY')
        self._filename=filename_validator
        def legacy_validator(document):validate_editor_layers(document);validate_layers(document)
        self._validate=validate_document if validate_document is not None else legacy_validator
        self.root=regular(root,True);self.root.mkdir(parents=True,exist_ok=True);regular(self.root,True)
        st=self.root.stat();self.identity=(st.st_dev,st.st_ino);self.maximum_files=maximum_files;self._thread_lock=threading.Lock()
    def _check_root(self):
        regular(self.root,True);st=self.root.stat()
        if(st.st_dev,st.st_ino)!=self.identity:raise ValueError('PROJECT_DIRECTORY_REPLACED')
    @contextmanager
    def _pin(self):
        self._check_root();handle=None;kernel=None
        if os.name=='nt':
            kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateFileW.restype=ctypes.c_void_p;kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            handle=kernel.CreateFileW(str(self.root),0x81,3,None,3,0x02000000,None)
            if handle in [None,ctypes.c_void_p(-1).value]:raise ctypes.WinError(ctypes.get_last_error())
        try:self._check_root();yield
        finally:
            if handle is not None:kernel.CloseHandle(handle)
    @contextmanager
    def _lease(self):
        with self._thread_lock,self._pin():
            path=regular(self.root/'.project-library.lock');f=path.open('a+b');locked=False
            try:
                if f.seek(0,2)==0:f.write(b'0');f.flush()
                end=time.monotonic()+2
                while True:
                    try:
                        f.seek(0)
                        if os.name=='nt':
                            import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
                        else:
                            import fcntl;fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                        locked=True;break
                    except OSError:
                        if time.monotonic()>=end:raise TimeoutError('PROJECT_LIBRARY_BUSY')
                        time.sleep(.02)
                self._check_root();yield
            finally:
                if locked:
                    f.seek(0)
                    if os.name=='nt':
                        import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
                    else:
                        import fcntl;fcntl.flock(f.fileno(),fcntl.LOCK_UN)
                f.close()
    def _path(self,name):return regular(self.root/self._filename(name))
    def _raw(self,path):
        with path.open('rb')as stream:raw=stream.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('PROJECT_FILE_TOO_LARGE')
        regular(path);return raw
    @staticmethod
    def _metadata(path):
        st=path.stat();return {'name':path.name,'bytes':st.st_size,'modifiedAt':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat()}
    def _names(self):
        names=[]
        for path in self.root.iterdir():
            if not path.name.lower().endswith('.json'):continue
            if path.is_dir():regular(path,True);continue
            self._filename(path.name);regular(path)
            names.append(path.name)
            if len(names)>self.maximum_files:raise ApiError(409,'PROJECT_FILE_CAPACITY_EXCEEDED')
        return sorted(names,key=str.casefold)
    def list(self):
        with self._lease():return {'files':[self._metadata(self._path(n))for n in self._names()],'maximumFileBytes':MAX_BYTES,'maximumFiles':self.maximum_files}
    def get(self,name):
        with self._lease():
            path=self._path(name)
            if not path.exists():raise ApiError(404,'PROJECT_FILE_NOT_FOUND')
            raw=self._raw(path);document=loads(raw);self._validate(document)
            return dict(self._metadata(path),sha256=hashlib.sha256(raw).hexdigest(),document=document)
    def save(self,name,document,expected_sha256):
        self._filename(name)
        if expected_sha256 is not None and(not isinstance(expected_sha256,str)or not re.fullmatch('[a-f0-9]{64}',expected_sha256)):raise ValueError('INVALID_PROJECT_FILE_REVISION')
        self._validate(document)
        raw=(json.dumps(document,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode('utf-8')
        if len(raw)>MAX_BYTES:raise ValueError('PROJECT_FILE_TOO_LARGE')
        digest=hashlib.sha256(raw).hexdigest()
        with self._lease():
            path=self._path(name);existing=path.exists();current=hashlib.sha256(self._raw(path)).hexdigest()if existing else None
            if current!=expected_sha256:raise ApiError(409,'PROJECT_FILE_REVISION_CONFLICT')
            if existing and current==digest:return dict(self._metadata(path),sha256=digest,changed=False)
            if not existing and len(self._names())>=self.maximum_files:raise ApiError(409,'PROJECT_FILE_CAPACITY_EXCEEDED')
            temporary=regular(self.root/('.dlg-'+uuid.uuid4().hex+'.pending'))
            try:
                with temporary.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                deadline=time.monotonic()+.5
                while True:
                    self._check_root();self._path(name)
                    latest=hashlib.sha256(self._raw(path)).hexdigest()if path.exists()else None
                    if latest!=current:raise ApiError(409,'PROJECT_FILE_REVISION_CONFLICT')
                    try:os.replace(temporary,path);break
                    except OSError as error:
                        if getattr(error,'winerror',None)not in [5,32,33]or time.monotonic()>=deadline:raise
                        time.sleep(.02)
                return dict(self._metadata(path),sha256=digest,changed=True)
            finally:
                if temporary.exists():temporary.unlink()
