"""Resolve an event to its current, authorized public DLG point in one file snapshot."""
import re
from .common import ApiError

def resolve(service,principal,snapshot,points,event_id,revision):
    principal.require('spatial:read')
    if not isinstance(revision,str) or not re.fullmatch(r'[1-9][0-9]{0,4}',revision) or int(revision)>10000:
        raise ApiError(400,'INVALID_QUERY')
    event=service.gas.detail(principal,points,event_id)
    if event['revision']!=int(revision):raise ApiError(409,'REVISION_CONFLICT')
    identity=event['source']['document']['spatialId']
    feature=next((f for f,owner,*_ in snapshot['objects'] if owner is None and f['type']=='point' and f['id']==identity and f['id'] in points),None)
    if feature is None:raise ApiError(404,'NOT_FOUND')
    return {'eventId':event_id,'eventRevision':event['revision'],'point':{k:feature[k] for k in ('id','name','type','positions')},'coordinates':snapshot['coordinates'],'datasetVersion':snapshot['version'],'layerFingerprint':snapshot['fingerprint']}
