"""Transactional public gas anomaly store. No network dispatch and no implicit source trust."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import base64,hashlib,hmac,json,re,secrets,sqlite3,threading,uuid
from .common import ApiError,fields,integer,text
from .database import SQLiteDatabase
from .gas_domain import access,canonical,new_event,source_event,timestamp,transition,visible_event,ID,note
from .focus_materials import checked_material,validate_stored_material,material_metadata,MATERIAL_LIMIT,ISSUE_MATERIAL_LIMIT,ISSUE_MATERIAL_COUNT

ACTIONS={'source-update':'gas:ingest','classify':'gas:verify','verify':'gas:verify','cooperate':'gas:cooperate','handoff-request':'gas:handoff','handoff-result':'gas:ingest','archive':'gas:verify','reopen':'gas:verify','material':'gas:read'}

def digest(value):return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()
def utc(value):return timestamp(value).astimezone(timezone.utc).isoformat(timespec='microseconds')
def identity(value):
    if not isinstance(value,str) or not ID.fullmatch(value):raise ValueError('invalid identity')
    return value

def metadata(row):return material_metadata(row)|{'scope':row['scope'],'enterpriseId':row['enterprise']}
def material_visible(row,principal):return 'gas:verify' in principal.permissions or row['scope']=='public' or principal.enterprise(row['enterprise'])

class GasRepository(SQLiteDatabase):
    def __init__(self,path,*,source_system=None,source_subjects=(),emergency_system=None,result_subjects=(),clock=None):
        self.source_system=text(source_system,128,True) if source_system is not None else None
        self.emergency_system=text(emergency_system,128,True) if emergency_system is not None else None
        self.source_subjects=frozenset(text(s,256,True) for s in source_subjects)
        self.result_subjects=frozenset(text(s,256,True) for s in result_subjects)
        if self.source_subjects & self.result_subjects:raise ValueError('source and result adapter identities must differ')
        self.clock=clock or (lambda:datetime.now(timezone.utc).isoformat())
        self.material_slots=threading.BoundedSemaphore(2)
        super().__init__(path)

    def _time(self):return utc(self.clock())
    def _row(self,db,principal,event_id,public_ids):
        identity(event_id);principal.require('gas:read')
        row=db.execute('SELECT * FROM gas_alerts WHERE tenant=? AND id=?',(principal.tenant,event_id)).fetchone()
        if row is None:raise ApiError(404,'NOT_FOUND')
        state=json.loads(row['payload']);access(state,principal,public_ids)
        return state

    def _authorize(self,principal,action,payload):
        principal.require('gas:read')
        if action not in ACTIONS:raise ApiError(404,'NOT_FOUND')
        principal.require(ACTIONS[action])
        if not isinstance(payload,dict):raise ValueError('command object required')
        if action=='source-update':self._source_trust(principal,payload.get('source'))
        if action=='handoff-result':
            if not self.emergency_system or not self.result_subjects:raise ApiError(503,'RESULT_ADAPTER_NOT_CONFIGURED')
            if principal.subject not in self.result_subjects:raise ApiError(403,'RESULT_ADAPTER_FORBIDDEN')
            if payload.get('externalSystem')!=self.emergency_system:raise ApiError(409,'RESULT_SYSTEM_CONFLICT')
        if action=='handoff-request':
            principal.require('gas:verify')
            if not self.emergency_system:raise ApiError(503,'EMERGENCY_ADAPTER_NOT_CONFIGURED')
        if action=='cooperate' and not principal.enterprise(payload.get('enterpriseId')):raise ApiError(404,'NOT_FOUND')
        if action=='material':
            material=payload.get('material',{})
            if material.get('scope')=='public':principal.require('gas:verify')
            elif material.get('scope')=='enterprise':
                principal.require('gas:cooperate')
                if not principal.enterprise(material.get('enterpriseId')):raise ApiError(404,'NOT_FOUND')
            else:raise ValueError('invalid material scope')

    def _source_trust(self,principal,source):
        principal.require('gas:ingest')
        if not self.source_system or not self.source_subjects:raise ApiError(503,'SOURCE_ADAPTER_NOT_CONFIGURED')
        if principal.subject not in self.source_subjects:raise ApiError(403,'SOURCE_ADAPTER_FORBIDDEN')
        source_event(source)
        if source['sourceSystem']!=self.source_system:raise ApiError(409,'SOURCE_SYSTEM_CONFLICT')

    def _project(self,db,state,principal,public_ids):
        view=visible_event(state,principal,public_ids)
        if view['verification'] is not None:
            allowed={r['id'] for r in db.execute('SELECT id,scope,enterprise FROM gas_materials WHERE tenant=? AND event_id=?',(principal.tenant,state['id'])) if material_visible(r,principal)}
            view['verification']['materialRefs']=[k for k in view['verification']['materialRefs'] if k in allowed]
        return view

    def _response(self,db,state,principal,public_ids,result,replayed=False):
        response={'event':self._project(db,state,principal,public_ids),'committedRevision':result['revision'],'replayed':replayed}
        if result.get('materialId'):
            row=db.execute('SELECT * FROM gas_materials WHERE tenant=? AND event_id=? AND id=?',(principal.tenant,state['id'],result['materialId'])).fetchone()
            if row is None or not material_visible(row,principal):raise ApiError(404,'NOT_FOUND')
            response['material']=metadata(row)
        return response

    def _previous(self,db,principal,key,command_digest):
        identity(key)
        row=db.execute('SELECT digest,result FROM gas_requests WHERE tenant=? AND actor=? AND key=?',(principal.tenant,principal.subject,key)).fetchone()
        if row is None:return None
        if row['digest']!=command_digest:raise ApiError(409,'IDEMPOTENCY_CONFLICT')
        return json.loads(row['result'])

    def _remember(self,db,principal,key,command_digest,result):
        db.execute('INSERT INTO gas_requests VALUES(?,?,?,?,?,?)',(principal.tenant,principal.subject,key,result['eventId'],command_digest,canonical(result)))

    def _history(self,db,state,principal,kind,data,at):
        db.execute('INSERT INTO gas_history VALUES(?,?,?,?,?,?,?,?,?)',(principal.tenant,state['id'],state['revision'],at,principal.subject,principal.policy_version,kind,canonical(data),digest(state)))

    def ingest(self,principal,public_ids,source,key):
        principal.require('gas:read');self._source_trust(principal,source);identity(key)
        # Authorize the point before looking up any idempotency result.
        candidate=new_event(source,principal,public_ids,uuid.uuid4().hex,self._time())
        command_digest=digest(['source',source])
        with self.transaction(write=True) as db:
            previous=self._previous(db,principal,key,command_digest)
            if previous:
                state=self._row(db,principal,previous['eventId'],public_ids)
                return self._response(db,state,principal,public_ids,previous,True)
            try:
                db.execute('INSERT INTO gas_alerts VALUES(?,?,?,?,?,?,?,?,?)',(principal.tenant,candidate['id'],source['sourceSystem'],source['sourceEventId'],source['spatialId'],source['sourceRevision'],1,candidate['updatedAt'],canonical(candidate)))
            except sqlite3.IntegrityError:raise ApiError(409,'SOURCE_ALREADY_REGISTERED') from None
            self._history(db,candidate,principal,'source',{'source':source},candidate['createdAt'])
            result={'eventId':candidate['id'],'revision':1};self._remember(db,principal,key,command_digest,result)
            return self._response(db,candidate,principal,public_ids,result)

    def detail(self,principal,public_ids,event_id):
        with self.transaction() as db:return self._project(db,self._row(db,principal,event_id,public_ids),principal,public_ids)

    def list(self,principal,public_ids,*,offset=0,limit=50):
        principal.require('gas:read');integer(offset,0,1000000);integer(limit,1,100)
        if not principal.public_spatial or not public_ids:return {'items':[],'total':0,'offset':offset,'limit':limit}
        points=sorted(set(text(k,128,True) for k in public_ids))
        if len(points)>1000:raise ValueError('point scope exceeds limit')
        where='tenant=? AND spatial_id IN ('+','.join('?' for _ in points)+')';args=(principal.tenant,*points)
        with self.transaction() as db:
            total=db.execute('SELECT count(*) FROM gas_alerts WHERE '+where,args).fetchone()[0]
            items=[self._project(db,json.loads(r[0]),principal,public_ids) for r in db.execute('SELECT payload FROM gas_alerts WHERE '+where+' ORDER BY updated DESC,id LIMIT ? OFFSET ?',(*args,limit,offset))]
            return {'items':items,'total':total,'offset':offset,'limit':limit}

    def mutate(self,principal,public_ids,event_id,action,payload,key):
        if action=='material':raise ApiError(400,'MATERIAL_UPLOAD_REQUIRED')
        self._authorize(principal,action,payload);identity(key);identity(event_id)
        with self.transaction(write=True) as db:return self._mutate(db,principal,public_ids,event_id,action,payload,key)

    def _mutate(self,db,principal,public_ids,event_id,action,payload,key,*,command_digest=None,raw=None,at=None):
        self._authorize(principal,action,payload)
        state=self._row(db,principal,event_id,public_ids);command_digest=command_digest or digest([event_id,action,payload])
        previous=self._previous(db,principal,key,command_digest)
        if previous:return self._response(db,self._row(db,principal,previous['eventId'],public_ids),principal,public_ids,previous,True)
        def check_materials(actor,event,refs):
            for material_id in refs:
                row=db.execute('SELECT * FROM gas_materials WHERE tenant=? AND event_id=? AND id=?',(actor.tenant,event,material_id)).fetchone()
                if row is None or row['revision']>state['revision'] or not material_visible(row,actor):raise ApiError(404,'NOT_FOUND')
                validate_stored_material(row)
        updated,event=transition(state,action,payload,principal,public_ids,at or self._time(),check_materials)
        # Compare-and-swap remains explicit, even with SQLite's single writer.
        changed=db.execute('UPDATE gas_alerts SET source_revision=?,revision=?,updated=?,payload=? WHERE tenant=? AND id=? AND revision=?',(updated['source']['document']['sourceRevision'],updated['revision'],updated['updatedAt'],canonical(updated),principal.tenant,event_id,state['revision'])).rowcount
        if changed!=1:raise ApiError(409,'REVISION_CONFLICT')
        self._history(db,updated,principal,action,payload,event['at'])
        result={'eventId':event_id,'revision':updated['revision']}
        if action=='material':
            meta=payload['material'];validate_stored_material({'payload':raw,'bytes':meta['bytes'],'name':meta['name'],'media_type':meta['mediaType'],'sha256':meta['sha256']})
            db.execute('INSERT INTO gas_materials VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(principal.tenant,event_id,meta['id'],meta['revision'],meta['scope'],meta['enterpriseId'],meta['name'],meta['mediaType'],meta['bytes'],meta['sha256'],meta['createdAt'],meta['actor'],meta['description'],raw));result['materialId']=meta['id']
        if action=='handoff-request':
            handoff=updated['handoff']
            if db.execute('SELECT 1 FROM gas_outbox WHERE tenant=? AND id=?',(principal.tenant,handoff['id'])).fetchone():raise ApiError(409,'HANDOFF_IDENTITY_REUSED')
            db.execute('INSERT INTO gas_outbox VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(principal.tenant,handoff['id'],event_id,updated['revision'],self.emergency_system,'pending',0,None,None,utc(event['at']),None,handoff['packageSHA256'],canonical(handoff['package'])))
        if action=='handoff-result':
            changed=db.execute('UPDATE gas_outbox SET delivery_state=?,lease_sha256=NULL,lease_until=NULL,last_error=NULL WHERE tenant=? AND id=? AND event_id=? AND target_system=?',(payload['state'],principal.tenant,payload['requestId'],event_id,self.emergency_system)).rowcount
            if changed!=1:raise ApiError(409,'HANDOFF_IDENTITY_CONFLICT')
            db.execute("UPDATE gas_delivery_attempts SET finished_at=?,outcome='acknowledged' WHERE tenant=? AND request_id=? AND outcome='inflight'",(event['at'],principal.tenant,payload['requestId']))
        self._remember(db,principal,key,command_digest,result)
        return self._response(db,updated,principal,public_ids,result)

    def add_material(self,principal,public_ids,event_id,payload,key):
        fields(payload,{'revision','name','mediaType','base64','description','scope','enterpriseId'},{'revision','name','mediaType','base64','description','scope','enterpriseId'})
        identity(key);integer(payload['revision'],1,10000);note(payload['description'])
        meta={'scope':payload['scope'],'enterpriseId':payload['enterpriseId']}
        self._authorize(principal,'material',{'material':meta})
        if not isinstance(payload['base64'],str) or len(payload['base64'])>((MATERIAL_LIMIT+2)//3)*4:raise ValueError('material exceeds limit')
        if not self.material_slots.acquire(blocking=False):raise ApiError(429,'MATERIAL_BUSY')
        try:
            raw=base64.b64decode(payload['base64'],validate=True);sha=checked_material(payload['name'],payload['mediaType'],raw)
            command_digest=digest([event_id,'upload',payload['revision'],payload['name'],payload['mediaType'],sha,payload['description'],payload['scope'],payload['enterpriseId']])
            with self.transaction(write=True) as db:
                self._row(db,principal,event_id,public_ids)
                previous=self._previous(db,principal,key,command_digest)
                if previous:return self._response(db,self._row(db,principal,previous['eventId'],public_ids),principal,public_ids,previous,True)
                count,size=db.execute('SELECT count(*),coalesce(sum(bytes),0) FROM gas_materials WHERE tenant=? AND event_id=?',(principal.tenant,event_id)).fetchone()
                if count>=ISSUE_MATERIAL_COUNT or size+len(raw)>ISSUE_MATERIAL_LIMIT:raise ApiError(409,'MATERIAL_CAPACITY')
                at=self._time();meta.update(id=uuid.uuid4().hex,revision=payload['revision']+1,name=payload['name'],mediaType=payload['mediaType'],bytes=len(raw),sha256=sha,createdAt=timestamp(at).isoformat(),actor=principal.subject,description=payload['description'])
                # Use one captured instant for metadata and the domain journal.
                return self._mutate(db,principal,public_ids,event_id,'material',{'revision':payload['revision'],'material':meta},key,command_digest=command_digest,raw=raw,at=at)
        finally:self.material_slots.release()

    def materials(self,principal,public_ids,event_id):
        with self.transaction() as db:
            state=self._row(db,principal,event_id,public_ids)
            items=[metadata(r) for r in db.execute('SELECT id,revision,name,media_type,bytes,sha256,created,actor,description,scope,enterprise FROM gas_materials WHERE tenant=? AND event_id=? ORDER BY revision',(principal.tenant,event_id)) if material_visible(r,principal)]
            return {'revision':state['revision'],'items':items,'total':len(items)}

    def material(self,principal,public_ids,event_id,material_id):
        identity(material_id)
        with self.transaction() as db:
            self._row(db,principal,event_id,public_ids)
            row=db.execute('SELECT * FROM gas_materials WHERE tenant=? AND event_id=? AND id=?',(principal.tenant,event_id,material_id)).fetchone()
            if row is None or not material_visible(row,principal):raise ApiError(404,'NOT_FOUND')
            return metadata(row),validate_stored_material(row)

    def history(self,principal,public_ids,event_id):
        with self.transaction() as db:
            self._row(db,principal,event_id,public_ids);items=[]
            for row in db.execute('SELECT * FROM gas_history WHERE tenant=? AND event_id=? ORDER BY revision',(principal.tenant,event_id)):
                data=json.loads(row['payload']);restricted=False
                if 'gas:verify' not in principal.permissions:
                    restricted=row['kind']=='cooperate' and not principal.enterprise(data['enterpriseId']) or row['kind']=='material' and not material_visible({'scope':data['material']['scope'],'enterprise':data['material']['enterpriseId']},principal)
                if restricted:items.append({'revision':row['revision'],'kind':'restricted','at':row['at']})
                else:items.append({'revision':row['revision'],'kind':row['kind'],'at':row['at'],'actor':row['actor'],'policyVersion':row['policy'],'data':data})
            # A verification reference must not reveal private material identifiers through history.
            if 'gas:verify' not in principal.permissions:
                allowed={r['id'] for r in db.execute('SELECT id,scope,enterprise FROM gas_materials WHERE tenant=? AND event_id=?',(principal.tenant,event_id)) if material_visible(r,principal)}
                for item in items:
                    if item['kind']=='verify':item['data']['materialRefs']=[k for k in item['data']['materialRefs'] if k in allowed]
            return items

    def _outbox(self,db,principal,public_ids,request_id):
        identity(request_id);principal.require('gas:read');principal.require('gas:handoff');principal.require('gas:verify')
        row=db.execute('SELECT * FROM gas_outbox WHERE tenant=? AND id=?',(principal.tenant,request_id)).fetchone()
        if row is None:raise ApiError(404,'NOT_FOUND')
        self._row(db,principal,row['event_id'],public_ids)
        if not self.emergency_system or row['target_system']!=self.emergency_system:raise ApiError(503,'EMERGENCY_ADAPTER_NOT_CONFIGURED')
        if digest(json.loads(row['payload']))!=row['package_sha256']:raise ValueError('stored handoff package differs')
        return row

    def claim(self,principal,public_ids,request_id,*,lease_seconds=60):
        integer(lease_seconds,5,300)
        with self.transaction(write=True) as db:
            row=self._outbox(db,principal,public_ids,request_id);at=self._time()
            if row['delivery_state']=='inflight' and row['lease_until']<=at:
                db.execute("UPDATE gas_delivery_attempts SET finished_at=?,outcome='expired' WHERE tenant=? AND request_id=? AND attempt=? AND outcome='inflight'",(at,principal.tenant,request_id,row['attempts']))
            elif row['delivery_state']!='pending' or row['next_attempt_at']>at:raise ApiError(409,'DELIVERY_NOT_DUE')
            if row['attempts']>=10:
                db.execute("UPDATE gas_outbox SET delivery_state='failed',lease_sha256=NULL,lease_until=NULL WHERE tenant=? AND id=?",(principal.tenant,request_id))
                return {'requestId':request_id,'deliveryState':'failed','attempt':row['attempts']}
            token=secrets.token_hex(32);sha=hashlib.sha256(token.encode('ascii')).hexdigest();until=utc((timestamp(at)+timedelta(seconds=lease_seconds)).isoformat());attempt=row['attempts']+1
            db.execute("UPDATE gas_outbox SET delivery_state='inflight',attempts=?,lease_sha256=?,lease_until=? WHERE tenant=? AND id=?",(attempt,sha,until,principal.tenant,request_id))
            db.execute('INSERT INTO gas_delivery_attempts VALUES(?,?,?,?,?,?,?,?,?)',(principal.tenant,request_id,attempt,at,sha,until,None,'inflight',None))
            return {'requestId':request_id,'targetSystem':row['target_system'],'package':json.loads(row['payload']),'packageSHA256':row['package_sha256'],'attempt':attempt,'leaseToken':token,'leaseUntil':until}

    def finish_delivery(self,principal,public_ids,request_id,token,*,sent,error_code=None):
        if type(sent) is not bool or not isinstance(token,str) or not re.fullmatch('[a-f0-9]{64}',token):raise ValueError('invalid delivery result')
        if not sent and (not isinstance(error_code,str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,63}',error_code)):raise ValueError('bounded error code required')
        if sent and error_code is not None:raise ValueError('sent result has no error code')
        with self.transaction(write=True) as db:
            row=self._outbox(db,principal,public_ids,request_id);at=self._time()
            if row['delivery_state']!='inflight' or not row['lease_sha256'] or row['lease_until']<=at or not hmac.compare_digest(row['lease_sha256'],hashlib.sha256(token.encode('ascii')).hexdigest()):raise ApiError(409,'DELIVERY_LEASE_CONFLICT')
            state='awaiting-result' if sent else ('failed' if row['attempts']>=10 else 'pending')
            next_at=utc((timestamp(at)+timedelta(seconds=min(3600,2**row['attempts']*5))).isoformat())
            db.execute('UPDATE gas_outbox SET delivery_state=?,lease_sha256=NULL,lease_until=NULL,next_attempt_at=?,last_error=? WHERE tenant=? AND id=?',(state,next_at,error_code,principal.tenant,request_id))
            db.execute('UPDATE gas_delivery_attempts SET finished_at=?,outcome=?,error_code=? WHERE tenant=? AND request_id=? AND attempt=?',(at,'sent' if sent else 'failed',error_code,principal.tenant,request_id,row['attempts']))
            return {'requestId':request_id,'deliveryState':state,'attempt':row['attempts']}
