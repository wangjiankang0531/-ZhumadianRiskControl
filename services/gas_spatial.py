"""Resolve an event to its current, authorized public DLG point in one file snapshot."""
import re
from .common import ApiError
from .data import CATEGORIES,key
from .spatial_distance import horizontal_distance

def resolve(service,principal,snapshot,points,event_id,revision,object_id=None,radius=None):
    principal.require('spatial:read')
    if not isinstance(revision,str) or not re.fullmatch(r'[1-9][0-9]{0,4}',revision) or int(revision)>10000:
        raise ApiError(400,'INVALID_QUERY')
    event=service.gas.detail(principal,points,event_id)
    if event['revision']!=int(revision):raise ApiError(409,'REVISION_CONFLICT')
    identity=event['source']['document']['spatialId']
    feature=next((f for f,owner,*_ in snapshot['objects'] if owner is None and f['type']=='point' and f['id']==identity and f['id'] in points),None)
    if feature is None:raise ApiError(404,'NOT_FOUND')
    result={'eventId':event_id,'eventRevision':event['revision'],'point':{k:feature[k] for k in ('id','name','type','positions')},'coordinates':snapshot['coordinates'],'datasetVersion':snapshot['version'],'layerFingerprint':snapshot['fingerprint']}
    if object_id is not None:
        radius=bounded_radius(radius)
        target=next((f for f in service.store.spatial(principal,{'limit':10000},snapshot=snapshot)['items'] if f['id']==object_id),None)
        if target is None or horizontal_distance(feature['positions'][0],target)>radius:raise ApiError(404,'NOT_FOUND')
        result['target']={k:target[k] for k in ('id','name','type','positions')};result['radiusMeters']=radius
    elif radius is not None:raise ApiError(400,'INVALID_QUERY')
    return result


def bounded_radius(value):
    if not isinstance(value,str) or not re.fullmatch(r'[1-9][0-9]{0,3}',value) or int(value)>5000:raise ApiError(400,'INVALID_QUERY')
    return int(value)


def nearby(service,principal,snapshot,points,event_id,query):
    radius=bounded_radius(query.get('radius'));offset=query.get('offset',0);limit=query.get('limit',10)
    if limit>50:raise ApiError(400,'INVALID_QUERY')
    expected=query.get('datasetVersion')
    if expected is not None and not re.fullmatch('[a-f0-9]{64}',expected) or offset and expected is None:raise ApiError(400,'INVALID_QUERY')
    category=query.get('category')
    if category is not None and category not in CATEGORIES and category!='unregistered':raise ApiError(400,'INVALID_QUERY')
    origin=resolve(service,principal,snapshot,points,event_id,query.get('revision'))
    if expected is not None and expected!=snapshot['version']:raise ApiError(409,'DATA_CHANGED')
    projected=service.store.spatial(principal,{'limit':10000},snapshot=snapshot)['items'];position=origin['point']['positions'][0]
    records={}
    if 'business:read' in principal.permissions and snapshot['business'] is not None:
        records={key(r):r for r in service.store.business(principal,{'limit':10000},snapshot=snapshot)['items']}
    matches=[];counts={}
    for feature in projected:
        if feature['id']==origin['point']['id']:continue
        distance=horizontal_distance(position,feature)
        if distance>radius:continue
        counts[feature['category']]=counts.get(feature['category'],0)+1
        if category is not None and feature['category']!=category:continue
        item={k:feature[k] for k in ('id','name','type','positions','category','themes','access')};item['distanceMeters']=round(distance,3)
        if 'enterpriseId' in feature:item['enterpriseId']=feature['enterpriseId']
        if feature.get('business') and key(feature['business']) in records:item['businessRecord']=records[key(feature['business'])]
        matches.append((distance,feature['id'],item))
    matches.sort(key=lambda row:(row[0],row[1]))
    return {**origin,'items':[r[2] for r in matches[offset:offset+limit]],'total':len(matches),'offset':offset,'limit':limit,'radiusMeters':radius,'distanceMetric':'horizontal-minimum-metres','counts':counts,'category':category,'businessDetailsAuthorized':'business:read' in principal.permissions}
