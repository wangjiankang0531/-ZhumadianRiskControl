"""Real client settings/auditor orchestration. Terminal means worker joined, not requested."""
from dataclasses import dataclass,field
import copy,re,secrets,threading
from resource_grants import require,WRITE
from resource_reports import checked_report
TERMINAL={'passed','failed','cancelled'}
NUMERIC={'expectedFiles','completedFiles','verifiedFiles','readBytes','expectedBytes','catalogsValidated','stabilityFiles'}
def progress_fields(value):
    require(isinstance(value,dict),'RESOURCE_PROGRESS_INVALID');result={}
    for key in NUMERIC:
        if key in value:
            require(type(value[key])is int and 0<=value[key]<=9007199254740991,'RESOURCE_PROGRESS_INVALID');result[key]=value[key]
    if 'phase'in value:
        require(isinstance(value['phase'],str)and len(value['phase'])<=80,'RESOURCE_PROGRESS_INVALID');result['phase']=value['phase']
    return result
def safe_code(error):
    value=str(error);return value if re.fullmatch(r'[A-Z_]{1,80}',value)else'RESOURCE_OPERATION_FAILED'
@dataclass(repr=False)
class Audit:
    id:str
    owner:tuple
    token:str
    root:str
    state:str='preflight'
    progress:dict=field(default_factory=dict)
    report_id:str|None=None
    result:dict|None=None
    outcome:tuple|None=None
    cancel:threading.Event=field(default_factory=threading.Event)
    thread:threading.Thread|None=None
    started:bool=False
@dataclass(repr=False)
class GISOperation:
    id:str
    owner:tuple
    token:str
    action:str
    state:str='preflight'
    phase:str='checking-programme'
    accepted:bool=False
    cancel:threading.Event=field(default_factory=threading.Event)
    thread:threading.Thread|None=None
    started:bool=False
    result:dict|None=None
    outcome:tuple|None=None

class ResourceManager:
    def __init__(self,*,authority,settings,reports,gis=None):
        require(all(callable(getattr(settings,name,None))for name in ['configuration','save_authorized','audit'])and all(callable(getattr(reports,name,None))for name in ['persist','read','summaries']),'RESOURCE_QUALIFIED_BACKENDS_REQUIRED')
        require(reports.binding=={k:authority.expected[k]for k in ['installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity']},'RESOURCE_REPORT_STORE_BINDING_MISMATCH')
        require(gis is None or all(callable(getattr(gis,name,None))for name in ['status','execute']),'GIS_QUALIFIED_BACKEND_REQUIRED')
        self.gis=gis;self.controls={};self.active_control=None
        self.authority=authority;self.settings=settings;self.reports=reports;self.lock=threading.RLock();self.jobs={};self.active_id=None;self.mutating=False;self.closing=False;self.stop_event=threading.Event();authority.bind_revoke(self._revoked)
        self.watcher=threading.Thread(target=self._watch,name='XNBY-Resource-Lifecycle',daemon=False);self.watcher.start()
    def configuration(self,token):
        principal=self.authority.get(token);value=self.settings.configuration();self.authority.get(token);return{**value,'canConfigure':WRITE in principal.scopes}
    def save(self,token,root):
        self.authority.get(token,write=True);require(isinstance(root,str)and 0<len(root)<=1024 and not any(ord(c)<32 for c in root),'RESOURCE_WORKSPACE_INVALID')
        with self.lock:
            require(not self.closing and not self.mutating and self.active_id is None and self.active_control is None,'RESOURCE_OPERATION_BUSY');self.mutating=True
        try:
            self.settings.save_authorized(root,lambda operation:self.authority.commit(token,operation));return self.configuration(token)
        finally:
            with self.lock:self.mutating=False
    def _snapshot(self,job):
        return{'schema':'xnby.client-resources.audit.v1','id':job.id,'state':job.state,'progress':dict(job.progress),'reportId':job.report_id,'result':copy.deepcopy(job.result)}
    def _owned(self,principal,identifier):
        require(isinstance(identifier,str)and re.fullmatch(r'[a-f0-9]{32}',identifier),'RESOURCE_IDENTIFIER_INVALID');job=self.jobs.get(identifier);require(job is not None and job.owner==principal.owner,'RESOURCE_AUDIT_NOT_FOUND');return job
    def audit(self,token,identifier):
        principal=self.authority.get(token)
        with self.lock:return self._snapshot(self._owned(principal,identifier))
    def start_audit(self,token):
        principal=self.authority.get(token);root=self.settings.configuration()['workspaceRoot'];self.authority.get(token)
        with self.lock:
            require(not self.closing and not self.mutating and self.active_id is None and self.active_control is None,'RESOURCE_OPERATION_BUSY')
            if len(self.jobs)>=128:
                oldest=next((identifier for identifier,value in self.jobs.items()if value.state in TERMINAL),None);require(oldest is not None,'RESOURCE_JOB_LIMIT');self.jobs.pop(oldest)
            job=Audit(secrets.token_hex(16),principal.owner,token,root);self.jobs[job.id]=job;self.active_id=job.id
            job.thread=threading.Thread(target=self._work,args=(job,),name='XNBY-Full-GIS-Audit',daemon=False)
            try:job.thread.start();job.started=True
            except Exception:
                job.state='failed';job.result={'passed':False,'cancelled':False,'issueCount':1,'code':'RESOURCE_WORKER_START_FAILED'};self.active_id=None;raise
            return self._snapshot(job)
    def _progress(self,job,value):
        fields=progress_fields(value)
        with self.lock:
            job.progress.update(fields)
            if job.state=='preflight':job.state='running'
    def _work(self,job):
        try:
            value=self.settings.audit(job.root,progress=lambda value:self._progress(job,value),cancel_event=job.cancel);report=checked_report(value['result']);report_id=self.reports.persist(job.owner,report)
            state='passed'if report['passed']else'cancelled'if report['cancelled']else'failed';result={'passed':report['passed'],'cancelled':report['cancelled'],'issueCount':report['issueCount']};fields=progress_fields(report.get('progress',{}));outcome=(state,report_id,result,fields)
        except Exception as error:outcome=('failed',None,{'passed':False,'cancelled':False,'issueCount':1,'code':safe_code(error)},{})
        with self.lock:job.outcome=outcome
    def _finalize(self,job):
        if not job.started or job.thread.is_alive():return
        job.thread.join()
        with self.lock:
            if job.state in TERMINAL:return
            outcome=job.outcome or('failed',None,{'passed':False,'cancelled':False,'issueCount':1,'code':'RESOURCE_WORKER_OUTCOME_MISSING'},{});job.state,job.report_id,job.result,fields=outcome;job.progress.update(fields)
            if self.active_id==job.id:self.active_id=None
    def cancel_audit(self,token,identifier):
        principal=self.authority.get(token)
        with self.lock:
            job=self._owned(principal,identifier)
            if job.state not in TERMINAL:job.state='cancelling';job.cancel.set()
            return self._snapshot(job)
    def _revoked(self,token):
        with self.lock:
            for job in self.controls.values():
                if job.token==token and not job.accepted:job.cancel.set()
            for job in self.jobs.values():
                if job.token==token and job.state not in TERMINAL:job.state='cancelling';job.cancel.set()
    def gis_status(self,token):
        self.authority.get(token);require(self.gis is not None,'GIS_CONTROL_UNAVAILABLE');value=self.gis.status();self.authority.get(token)
        with self.lock:return{**value,'operationActive':self.active_control is not None}
    def _control_snapshot(self,job):
        return{'schema':'xnby.client-resources.gis-operation.v1','id':job.id,'action':job.action,'state':job.state,'phase':job.phase,'accepted':job.accepted,'result':copy.deepcopy(job.result)}
    def _owned_control(self,principal,identifier):
        require(isinstance(identifier,str)and re.fullmatch('[a-f0-9]{32}',identifier),'RESOURCE_IDENTIFIER_INVALID');job=self.controls.get(identifier);require(job is not None and job.owner==principal.owner,'GIS_OPERATION_NOT_FOUND');return job
    def gis_operation(self,token,identifier):
        principal=self.authority.get(token)
        with self.lock:return self._control_snapshot(self._owned_control(principal,identifier))
    def start_gis_operation(self,token,action):
        principal=self.authority.get(token,write=True);require(action in ('start','stop')and self.gis is not None,'GIS_CONTROL_UNAVAILABLE')
        with self.lock:
            require(not self.closing and not self.mutating and self.active_id is None and self.active_control is None,'RESOURCE_OPERATION_BUSY')
            if len(self.controls)>=64:
                oldest=next((identifier for identifier,value in self.controls.items()if value.state in ('completed','failed','cancelled')),None);require(oldest is not None,'GIS_OPERATION_LIMIT');self.controls.pop(oldest)
            job=GISOperation(secrets.token_hex(16),principal.owner,token,action);self.controls[job.id]=job;self.active_control=job.id
            job.thread=threading.Thread(target=self._work_control,args=(job,),name='XNBY-Registered-GIS-Control',daemon=False)
            try:job.thread.start();job.started=True
            except Exception:
                job.state='failed';job.result={'code':'GIS_CONTROL_WORKER_START_FAILED'};self.active_control=None;raise
            return self._control_snapshot(job)
    def _control_accept(self,job,operation):
        def accept():
            with self.lock:require(not self.closing and not job.cancel.is_set(),'RESOURCE_CONTROL_CANCELLED')
            value=operation();self.authority.get(job.token,write=True)
            with self.lock:
                require(not self.closing and not job.cancel.is_set(),'RESOURCE_CONTROL_CANCELLED');job.accepted=True;job.state='running'
            return value
        return self.authority.commit(job.token,accept)
    def _control_progress(self,job,phase):
        require(isinstance(phase,str)and re.fullmatch('[a-z-]{1,60}',phase),'GIS_CONTROL_PROGRESS_INVALID')
        with self.lock:job.phase=phase
    def _work_control(self,job):
        try:
            result=self.gis.execute(job.action,commit=lambda operation:self._control_accept(job,operation),cancel_event=job.cancel,progress=lambda phase:self._control_progress(job,phase));outcome=('completed',result)
        except Exception as error:
            code=safe_code(error);outcome=('cancelled'if not job.accepted and(code in ('RESOURCE_CONTROL_CANCELLED','RESOURCE_SESSION_REQUIRED'))else'failed',{'code':code})
        with self.lock:job.outcome=outcome
    def _finalize_control(self,job):
        if not job.started or job.thread.is_alive():return
        job.thread.join()
        with self.lock:
            if job.state in ('completed','failed','cancelled'):return
            job.state,job.result=job.outcome or('failed',{'code':'GIS_CONTROL_OUTCOME_MISSING'})
            if self.active_control==job.id:self.active_control=None
    def _watch(self):
        while not self.stop_event.wait(.025):
            with self.lock:jobs=[job for job in self.jobs.values()if job.state not in TERMINAL]
            for job in jobs:
                self.authority.active(job.token);self._finalize(job)
            with self.lock:controls=[job for job in self.controls.values()if job.state not in ('completed','failed','cancelled')]
            for job in controls:
                if not self.authority.active(job.token) and not job.accepted:job.cancel.set()
                self._finalize_control(job)
    def close_session(self,token):
        with self.lock:jobs=[job for job in self.jobs.values()if job.token==token]
        self.authority.revoke(token)
        with self.lock:controls=[job for job in self.controls.values()if job.token==token]
        for control in controls:
            if not control.accepted:control.cancel.set()
            if control.started:control.thread.join();self._finalize_control(control)
        for job in jobs:
            if job.started:job.thread.join();self._finalize(job)
    def list_reports(self,token):
        principal=self.authority.get(token);rows=self.reports.summaries(principal.owner);self.authority.get(token);return{'schema':'xnby.client-resources.reports.v1','reports':rows}
    def report(self,token,identifier):
        principal=self.authority.get(token);value=self.reports.read(principal.owner,identifier);self.authority.get(token);return value
    def close(self):
        with self.lock:self.closing=True;jobs=list(self.jobs.values())
        self.authority.close();self.stop_event.set()
        with self.lock:controls=list(self.controls.values())
        for control in controls:
            if not control.accepted:control.cancel.set()
            if control.started:control.thread.join();self._finalize_control(control)
        for job in jobs:
            if job.state not in TERMINAL:job.cancel.set()
            if job.started:job.thread.join();self._finalize(job)
        self.watcher.join()
