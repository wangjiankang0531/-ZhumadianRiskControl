"""Offline gas archive consistency replay; this is not proof of historic authorization."""
import hashlib,json,re
from .common import text,fields,integer
from .gas_domain import canonical,new_event,transition,timestamp
from .focus_materials import validate_stored_material
from .gas_repository import metadata,digest,utc,ACTIONS

class ReplayPrincipal:
    permissions=frozenset({'gas:read','gas:ingest','gas:verify','gas:cooperate','gas:handoff'})
    public_spatial=True
    def __init__(self,tenant,actor,policy):
        self.tenant=text(tenant,128,True);self.subject=text(actor,256,True);self.policy_version=text(policy,128,True)
    def require(self,permission):
        if permission not in self.permissions:raise ValueError('invalid replay permission')
    def enterprise(self,enterprise):return bool(enterprise)

def validate_gas(db):
    expected_outbox={};expected_requests={};expected_materials=set()
    for current in db.execute('SELECT * FROM gas_alerts'):
        tenant,event_id=current['tenant'],current['id'];state=None;revision=0
        for row in db.execute('SELECT * FROM gas_history WHERE tenant=? AND event_id=? ORDER BY revision',(tenant,event_id)):
            revision+=1
            if row['revision']!=revision:raise ValueError('incomplete gas history')
            actor=ReplayPrincipal(tenant,row['actor'],row['policy']);data=json.loads(row['payload']);kind=row['kind']
            if revision==1:
                if kind!='source' or set(data)!={'source'}:raise ValueError('gas source history differs')
                points=frozenset({data['source']['spatialId']});state=new_event(data['source'],actor,points,event_id,row['at']);request_digest=digest(['source',data['source']])
            else:
                if kind not in ACTIONS:raise ValueError('unknown gas history kind')
                def check_materials(principal,identity,refs):
                    for material_id in refs:
                        material=db.execute('SELECT * FROM gas_materials WHERE tenant=? AND event_id=? AND id=?',(tenant,identity,material_id)).fetchone()
                        if material is None or material['revision']>=revision:raise ValueError('gas material reference differs')
                        validate_stored_material(material)
                state,event=transition(state,kind,data,actor,points,row['at'],check_materials)
                if event['at']!=row['at']:raise ValueError('gas journal timestamp differs')
                request_digest=digest([event_id,kind,data])
                if kind=='material':
                    meta=data['material'];material=db.execute('SELECT * FROM gas_materials WHERE tenant=? AND event_id=? AND id=?',(tenant,event_id,meta['id'])).fetchone()
                    if material is None or metadata(material)!=meta:raise ValueError('gas material journal differs')
                    validate_stored_material(material);expected_materials.add((tenant,event_id,meta['id']))
                    request_digest=digest([event_id,'upload',data['revision'],meta['name'],meta['mediaType'],meta['sha256'],meta['description'],meta['scope'],meta['enterpriseId']])
                if kind=='handoff-request':
                    handoff=state['handoff'];key=(tenant,handoff['id'])
                    if key in expected_outbox:raise ValueError('gas handoff identity reused')
                    expected_outbox[key]={'event':event_id,'revision':revision,'package':handoff['package'],'sha':handoff['packageSHA256'],'result':None,'resultSystem':None}
                if kind=='handoff-result':expected_outbox[(tenant,data['requestId'])].update(result=data['state'],resultSystem=data['externalSystem'])
            if row['state_sha256']!=digest(state):raise ValueError('gas history snapshot digest differs')
            expected_requests[(tenant,event_id,revision)]=(actor.subject,request_digest,data.get('material',{}).get('id'))
        if state is None or canonical(state)!=canonical(json.loads(current['payload'])):raise ValueError('gas current snapshot differs')
        source=state['source']['document']
        if (state['revision'],source['sourceSystem'],source['sourceEventId'],source['spatialId'],source['sourceRevision'],state['updatedAt'])!=(current['revision'],current['source_system'],current['source_id'],current['spatial_id'],current['source_revision'],current['updated']):raise ValueError('gas current index differs')
    actual_materials=set()
    for row in db.execute('SELECT tenant,event_id,id FROM gas_materials'):actual_materials.add(tuple(row))
    if expected_materials!=actual_materials:raise ValueError('orphan gas material')
    seen_requests=set()
    for row in db.execute('SELECT * FROM gas_requests'):
        if not re.fullmatch('[a-f0-9]{32}',row['key']):raise ValueError('invalid gas idempotency key')
        result=json.loads(row['result']);fields(result,{'eventId','revision','materialId'},{'eventId','revision'});integer(result['revision'],1,10000)
        key=(row['tenant'],row['event_id'],result['revision']);expected=expected_requests.get(key)
        if key in seen_requests or result['eventId']!=row['event_id'] or expected!=(row['actor'],row['digest'],result.get('materialId')):raise ValueError('gas idempotency journal differs')
        seen_requests.add(key)
    if seen_requests!=set(expected_requests):raise ValueError('incomplete gas idempotency journal')
    seen_outbox=set()
    for row in db.execute('SELECT * FROM gas_outbox'):
        key=(row['tenant'],row['id']);expected=expected_outbox.get(key);seen_outbox.add(key)
        if expected is None or (row['event_id'],row['revision'],row['package_sha256'])!=(expected['event'],expected['revision'],expected['sha']) or canonical(json.loads(row['payload']))!=canonical(expected['package']):raise ValueError('gas outbox package differs')
        text(row['target_system'],128,True);integer(row['attempts'],0,10)
        if expected['resultSystem'] is not None and row['target_system']!=expected['resultSystem']:raise ValueError('gas result target differs')
        if row['next_attempt_at']!=utc(row['next_attempt_at']):raise ValueError('noncanonical delivery time')
        state=row['delivery_state']
        if state not in {'pending','inflight','awaiting-result','accepted','rejected','completed','failed'}:raise ValueError('unknown delivery state')
        if (expected['result'] is None and state in {'accepted','rejected','completed'}) or (expected['result'] is not None and state!=expected['result']):raise ValueError('transport cannot invent business result')
        if state=='inflight':
            if not isinstance(row['lease_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',row['lease_sha256']) or row['lease_until']!=utc(row['lease_until']):raise ValueError('gas active lease differs')
        elif row['lease_sha256'] is not None or row['lease_until'] is not None:raise ValueError('gas inactive lease remains')
        if state=='failed' and row['attempts']!=10:raise ValueError('gas retry exhaustion differs')
        attempts=list(db.execute('SELECT * FROM gas_delivery_attempts WHERE tenant=? AND request_id=? ORDER BY attempt',key))
        if len(attempts)!=row['attempts']:raise ValueError('incomplete delivery attempts')
        for number,attempt in enumerate(attempts,1):
            if attempt['attempt']!=number or not re.fullmatch('[a-f0-9]{64}',attempt['lease_sha256']):raise ValueError('invalid delivery attempt')
            start,end=timestamp(attempt['claimed_at']),timestamp(attempt['lease_until'])
            if not 5<=(end-start).total_seconds()<=300:raise ValueError('invalid delivery lease duration')
            outcome=attempt['outcome']
            if outcome not in {'inflight','sent','failed','expired','acknowledged'}:raise ValueError('invalid delivery outcome')
            if outcome=='inflight':
                if number!=len(attempts) or state!='inflight' or attempt['finished_at'] is not None or (attempt['lease_sha256'],attempt['lease_until'])!=(row['lease_sha256'],row['lease_until']):raise ValueError('delivery lease journal differs')
            else:
                finished=timestamp(attempt['finished_at'])
                if finished<start or outcome=='expired' and finished<end or outcome in {'sent','failed'} and finished>=end:raise ValueError('delivery finish time differs')
            error=attempt['error_code']
            if (outcome=='failed' and (not isinstance(error,str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,63}',error))) or (outcome!='failed' and error is not None):raise ValueError('delivery error code differs')
        if state=='inflight' and not attempts:raise ValueError('active delivery without attempt')
        if state=='awaiting-result' and (not attempts or attempts[-1]['outcome']!='sent'):raise ValueError('sent delivery missing journal')
        if state=='pending' and attempts and attempts[-1]['outcome']!='failed':raise ValueError('retry pending without failed attempt')
        if state=='failed' and (not attempts or attempts[-1]['outcome'] not in {'failed','expired'}):raise ValueError('failed delivery missing journal')
    if seen_outbox!=set(expected_outbox):raise ValueError('incomplete gas outbox')
