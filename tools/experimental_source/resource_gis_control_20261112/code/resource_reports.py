"""Current-user private report copies; opaque ids and authority-bound account/project."""
import datetime,hashlib,heapq,json,re,secrets,threading
from pathlib import Path
from client_control import ordinary,private_directory,atomic_json,load_json
from client_job import StateLock
from resource_grants import require,SHA
ID=re.compile(r'[a-f0-9]{32}')
MAXIMUM=262144
def checked_report(value):
    require(isinstance(value,dict)and value.get('schema')=='xnby.offline-osgb.integrity.v1'and type(value.get('passed'))is bool and type(value.get('cancelled'))is bool and type(value.get('issueCount'))is int and value['issueCount']>=0 and not(value['passed']and value['cancelled']),'RESOURCE_REPORT_INVALID')
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8');require(len(raw)<=MAXIMUM,'RESOURCE_REPORT_TOO_LARGE');return json.loads(raw)
class OwnedReports:
    def __init__(self,folder,*,binding):
        self._binding=tuple(sorted(self.checked_binding(binding).items()));self.folder=ordinary(Path(folder));self.lock=threading.Lock()
    @staticmethod
    def checked_binding(value):
        require(isinstance(value,dict)and set(value)=={'installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity'}and all(isinstance(v,str)and SHA.fullmatch(v)for v in value.values()),'RESOURCE_REPORT_BINDING_INVALID');return dict(value)
    @property
    def binding(self):return dict(self._binding)
    def exported(self,value,metadata):
        binding=self.checked_binding(metadata.get('binding'));value.pop('_clientResourceReport');value['clientResourceBinding']=binding;value['reportMatchesCurrentInstallation']=binding==self.binding;return value
    def _path(self,owner,*,create=False):
        require(isinstance(owner,tuple)and len(owner)==2 and all(isinstance(x,str)and SHA.fullmatch(x)for x in owner),'RESOURCE_REPORT_OWNER_INVALID')
        key=hashlib.sha256((owner[0]+'\0'+owner[1]).encode('ascii')).hexdigest();path=ordinary(self.folder/key)
        if create:
            self.folder.mkdir(parents=True,exist_ok=True);private_directory(self.folder);path.mkdir(exist_ok=True);private_directory(path)
        return path
    def persist(self,owner,value):
        report=checked_report(value);identifier=secrets.token_hex(16);created=datetime.datetime.now(datetime.timezone.utc).isoformat();report['_clientResourceReport']={'id':identifier,'createdAt':created,'actorKey':owner[0],'projectKey':owner[1],'binding':self.binding}
        require(len((json.dumps(report,allow_nan=False,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))<=MAXIMUM,'RESOURCE_REPORT_TOO_LARGE')
        with self.lock:
            directory=self._path(owner,create=True);lock=StateLock(directory)
            try:atomic_json(directory/(identifier+'.json'),report,replace=False)
            finally:lock.close()
        return identifier
    def read(self,owner,identifier):
        require(isinstance(identifier,str)and ID.fullmatch(identifier),'RESOURCE_IDENTIFIER_INVALID');path=ordinary(self._path(owner)/(identifier+'.json'))
        if not path.exists():raise FileNotFoundError('RESOURCE_REPORT_NOT_FOUND')
        value=load_json(path,MAXIMUM);checked_report(value);metadata=value.get('_clientResourceReport')
        require(isinstance(metadata,dict)and metadata.get('id')==identifier and (metadata.get('actorKey'),metadata.get('projectKey'))==owner,'RESOURCE_REPORT_OWNER_MISMATCH');return self.exported(value,metadata)
    def summaries(self,owner):
        folder=self._path(owner)
        if not folder.exists():return[]
        candidates=(entry for entry in folder.iterdir()if ID.fullmatch(entry.stem)and entry.suffix=='.json')
        selected=heapq.nlargest(32,candidates,key=lambda path:ordinary(path,directory=False).stat().st_mtime_ns);rows=[]
        for path in selected:
            value=load_json(path,MAXIMUM);checked_report(value);metadata=value.get('_clientResourceReport');require(isinstance(metadata,dict)and metadata.get('id')==path.stem and (metadata.get('actorKey'),metadata.get('projectKey'))==owner,'RESOURCE_REPORT_OWNER_MISMATCH');require(isinstance(metadata.get('createdAt'),str)and len(metadata['createdAt'])<=80,'RESOURCE_REPORT_INVALID');self.checked_binding(metadata.get('binding'));rows.append({'id':path.stem,'createdAt':metadata['createdAt']})
        return rows
