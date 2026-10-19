"""Gas anomaly domain rules; adapters/repository must supply live authorization.

No ingestion route, dispatcher or monitoring system is installed by this module.
Source classifications are observations, never an inferred enterprise liability.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib, json, math, re
from .common import ApiError, fields, integer, text, strings

SOURCE_SCHEMA='xnby.gas.source.v1'
CLASSIFICATIONS={'short-fluctuation','persistent','suspected-device','needs-verification','emergency-concern'}
CONCLUSIONS={'false-alarm','short-anomaly','device-fault','no-obvious-anomaly','possibly-enterprise','continue','emergency'}
COOPERATION={'explained','supplement-required','following','measures-taken','focus-suggested'}
ACTIVITIES={'production','storage','pipeline','emission','loading','maintenance','special-work','unknown'}
UNITS={'ppm','mg/m3','%LEL','%vol'}
ID=re.compile(r'^[a-f0-9]{32}$')


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))


def timestamp(value):
    text(value,64)
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})',value):
        raise ValueError('offset timestamp required')
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.utcoffset() is None:raise ValueError('timestamp timezone required')
    return parsed.astimezone(timezone.utc)


def note(value,limit=4000):
    if not isinstance(value,str) or not value.strip() or len(value.encode('utf8'))>limit or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',value):raise ValueError('invalid note')
    return value


def concentration(value):
    # Keep original decimal text and unit; never compare ppm with %LEL or invent a threshold.
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{1,12}(?:\.[0-9]{1,8})?',value) or not Decimal(value).is_finite():raise ValueError('decimal concentration text required')
    return value


def source_event(value):
    required={'schema','sourceSystem','sourceEventId','sourceRevision','spatialId','area','gasCode','unit','observedAt','concentration','deviceState','alarmState','trend'}
    fields(value,required,required)
    if value['schema']!=SOURCE_SCHEMA:raise ValueError('unsupported source schema')
    for key in ('sourceSystem','sourceEventId','spatialId','gasCode'):text(value[key],128,True)
    text(value['area'],256);integer(value['sourceRevision'],1,2**31-1)
    observed=timestamp(value['observedAt'])
    if value['unit'] not in UNITS or value['deviceState'] not in {'online','offline','fault','unknown'} or value['alarmState'] not in {'normal','alarm','unknown'}:raise ValueError('unknown source code')
    if value['concentration'] is None:
        if value['deviceState']=='online':raise ValueError('online observation needs value')
    else:concentration(value['concentration'])
    if not isinstance(value['trend'],list) or len(value['trend'])>128:raise ValueError('trend too large')
    previous=None
    for sample in value['trend']:
        fields(sample,{'at','value'},{'at','value'});at=timestamp(sample['at']);concentration(sample['value'])
        if at>observed or previous is not None and at<=previous:raise ValueError('unordered or future trend')
        previous=at
    return {'document':deepcopy(value),'observedAtUTC':observed.isoformat(),'sha256':hashlib.sha256(canonical(value).encode('utf8')).hexdigest()}


def location(value):
    required={'crs','longitude','latitude','accuracyMeters','capturedAt','method'}
    fields(value,required,required)
    if value['crs']!='EPSG:4326' or value['method'] not in {'manual','device'}:raise ValueError('explicit WGS84 capture method required')
    for key,lo,hi in [('longitude',-180,180),('latitude',-90,90),('accuracyMeters',0,50000)]:
        number=value[key]
        if type(number) not in (int,float) or not math.isfinite(number) or not lo<=number<=hi:raise ValueError('invalid location')
    timestamp(value['capturedAt'])
    return deepcopy(value)


def access(state,principal,public_ids):
    principal.require('gas:read')
    if state['tenant']!=principal.tenant or not principal.public_spatial or state['source']['document']['spatialId'] not in public_ids:raise ApiError(404,'NOT_FOUND')


def new_event(payload,principal,public_ids,identity,at):
    principal.require('gas:read');principal.require('gas:ingest')
    if not ID.fullmatch(identity):raise ValueError('invalid event identity')
    source=source_event(payload);stamp=timestamp(at).isoformat()
    state={'schema':'xnby.gas.event.v1','id':identity,'tenant':principal.tenant,'revision':1,'createdAt':stamp,'updatedAt':stamp,'source':source,'classification':'needs-verification','classificationNote':None,'status':'attention','verification':None,'cooperation':{},'handoff':None,'archive':None}
    access(state,principal,public_ids)
    return state


def visible_event(state,principal,public_ids):
    access(state,principal,public_ids);view=deepcopy(state)
    if 'gas:verify' not in principal.permissions:
        view['cooperation']={k:v for k,v in view['cooperation'].items() if principal.enterprise(k)}
        if view['handoff'] is not None:view['handoff']={k:v for k,v in view['handoff'].items() if k!='package'}
    return view


def transition(state,action,payload,principal,public_ids,at,check_materials=None):
    access(state,principal,public_ids)
    permissions={'source-update':'gas:ingest','classify':'gas:verify','verify':'gas:verify','cooperate':'gas:cooperate','handoff-request':'gas:handoff','handoff-result':'gas:ingest','archive':'gas:verify','reopen':'gas:verify'}
    if action not in permissions:raise ApiError(404,'NOT_FOUND')
    principal.require(permissions[action])
    if not isinstance(payload,dict):raise ValueError('command object required')
    integer(payload.get('revision'),1,2**31-1)
    if payload['revision']!=state['revision']:raise ApiError(409,'REVISION_CONFLICT')
    if state['revision']>=10000:raise ApiError(409,'EVENT_HISTORY_LIMIT')
    if state['status']=='archived' and action not in {'reopen','source-update','handoff-result'}:raise ApiError(409,'EVENT_ARCHIVED')
    next_state=deepcopy(state);stamp=timestamp(at).isoformat()
    if action=='source-update':
        fields(payload,{'revision','source'},{'revision','source'});updated=source_event(payload['source']);old=state['source']['document'];new=updated['document']
        if any(old[k]!=new[k] for k in ('sourceSystem','sourceEventId','spatialId','gasCode')):raise ApiError(409,'SOURCE_IDENTITY_CONFLICT')
        if new['sourceRevision']<=old['sourceRevision']:raise ApiError(409,'SOURCE_REVISION_CONFLICT')
        next_state.update(source=updated,verification=None,archive=None,status='attention',classification='needs-verification',classificationNote=None)
    elif action=='classify':
        fields(payload,{'revision','classification','note'},{'revision','classification','note'})
        if payload['classification'] not in CLASSIFICATIONS:raise ValueError('unknown classification')
        next_state.update(classification=payload['classification'],classificationNote={'note':note(payload['note']),'actor':principal.subject,'at':stamp})
    elif action=='verify':
        required={'revision','conclusion','note','verifiedAt','location','materialRefs'};fields(payload,required,required)
        if payload['conclusion'] not in CONCLUSIONS:raise ValueError('unknown verification conclusion')
        timestamp(payload['verifiedAt']);where=location(payload['location']);refs=strings(payload['materialRefs'],64,32)
        if any(not ID.fullmatch(k) for k in refs):raise ValueError('invalid material reference')
        if refs:
            if check_materials is None:raise ApiError(503,'MATERIAL_BINDING_REQUIRED')
            check_materials(principal,state['id'],tuple(sorted(refs)))
        next_state.update(verification={'conclusion':payload['conclusion'],'note':note(payload['note']),'verifiedAt':payload['verifiedAt'],'location':where,'materialRefs':list(payload['materialRefs']),'sourceRevision':state['source']['document']['sourceRevision'],'actor':principal.subject,'at':stamp},status='verified',archive=None)
    elif action=='cooperate':
        required={'revision','enterpriseId','state','activities','statement','measures'};fields(payload,required,required)
        owner=text(payload['enterpriseId'],256,True)
        if not principal.enterprise(owner):raise ApiError(404,'NOT_FOUND')
        if owner not in state['cooperation'] and len(state['cooperation'])>=64:raise ApiError(409,'COOPERATION_CAPACITY')
        if payload['state'] not in COOPERATION or not strings(payload['activities'],len(ACTIVITIES))<=ACTIVITIES:raise ValueError('invalid cooperation code')
        next_state['cooperation'][owner]={'state':payload['state'],'activities':list(payload['activities']),'statement':note(payload['statement']),'measures':note(payload['measures']),'actor':principal.subject,'at':stamp}
    elif action=='handoff-request':
        principal.require('gas:verify');fields(payload,{'revision','requestId','reason'},{'revision','requestId','reason'})
        if not ID.fullmatch(payload['requestId']):raise ValueError('invalid handoff identity')
        if state['handoff'] is not None:raise ApiError(409,'HANDOFF_ALREADY_EXISTS')
        if state['verification'] is None:raise ApiError(409,'VERIFICATION_REQUIRED')
        package={'schema':'xnby.gas.handoff.v1','eventId':state['id'],'eventRevision':state['revision'],'source':deepcopy(state['source']),'verification':deepcopy(state['verification']),'cooperation':deepcopy(state['cooperation']),'reason':note(payload['reason'])}
        next_state['handoff']={'id':payload['requestId'],'state':'pending-delivery','actor':principal.subject,'at':stamp,'package':package,'packageSHA256':hashlib.sha256(canonical(package).encode('utf8')).hexdigest(),'result':None}
    elif action=='handoff-result':
        required={'revision','requestId','externalSystem','externalId','state','note'};fields(payload,required,required)
        handoff=next_state['handoff']
        if handoff is None or payload['requestId']!=handoff['id']:raise ApiError(409,'HANDOFF_IDENTITY_CONFLICT')
        if payload['state'] not in {'accepted','rejected','completed'}:raise ValueError('invalid handoff result')
        if handoff['state'] in {'rejected','completed'} or handoff['state']=='accepted' and payload['state']=='accepted':raise ApiError(409,'HANDOFF_TERMINAL_OR_DUPLICATE')
        text(payload['externalSystem'],128,True);text(payload['externalId'],256,True)
        previous=handoff['result']
        if previous and any(previous[k]!=payload[k] for k in ('externalSystem','externalId')):raise ApiError(409,'HANDOFF_IDENTITY_CONFLICT')
        handoff.update(state=payload['state'],result={k:payload[k] for k in ('externalSystem','externalId','state')}|{'note':note(payload['note']),'actor':principal.subject,'at':stamp})
    elif action=='archive':
        fields(payload,{'revision','note'},{'revision','note'})
        if state['verification'] is None:raise ApiError(409,'VERIFICATION_REQUIRED')
        if state['handoff'] and state['handoff']['state'] in {'pending-delivery','accepted'}:raise ApiError(409,'HANDOFF_RESULT_REQUIRED')
        resolved={'false-alarm','short-anomaly','device-fault','no-obvious-anomaly'}
        completed=bool(state['handoff'] and state['handoff']['state']=='completed' and state['handoff']['package']['source']['document']['sourceRevision']==state['source']['document']['sourceRevision'])
        if state['verification']['conclusion'] not in resolved and not completed:raise ApiError(409,'FOLLOWUP_REQUIRED')
        next_state.update(status='archived',archive={'note':note(payload['note']),'actor':principal.subject,'at':stamp})
    else:
        fields(payload,{'revision','note'},{'revision','note'});note(payload['note'])
        if state['status']!='archived':raise ApiError(409,'NOT_ARCHIVED')
        next_state.update(status='attention',verification=None,archive=None)
    next_state.update(revision=state['revision']+1,updatedAt=stamp)
    event={'revision':next_state['revision'],'kind':action,'actor':principal.subject,'policyVersion':principal.policy_version,'at':stamp,'data':deepcopy(payload)}
    return next_state,event
