"""Strict server validation of D129 model instances; no landscape mutations."""
import copy,math,re
SCHEMA='xnby.scene-model-state.v1'
JS_TRIM='\u0009\u000b\u000c\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000\ufeff\u000a\u000d\u2028\u2029'
INSTANCE_KEYS={'id','assetId','name','assetSHA256','anchor','scale','rotationDegrees','visible'}
LIGHT_KEYS={'intensity','azimuth','textures','shadows','targetModelId'}
ID=re.compile(r'[-a-z0-9]{1,80}\Z');HASH=re.compile(r'[0-9a-f]{64}\Z')
def number(value):return type(value)is int or type(value)is float and math.isfinite(value)
def catalog_versions(rows):
 if not isinstance(rows,list)or len(rows)>64:raise ValueError('INVALID_SCENE_CATALOG')
 out={}
 for row in rows:
  if not isinstance(row,dict)or not isinstance(row.get('id'),str)or not ID.fullmatch(row['id'])or row['id']in out or not isinstance(row.get('sha256'),str)or not HASH.fullmatch(row['sha256']):raise ValueError('INVALID_SCENE_CATALOG')
  out[row['id']]=row['sha256']
 return out

def validate_state(value,catalog=None):
 if not isinstance(value,dict)or set(value)!={'schema','scene','models','lighting'}or value['schema']!=SCHEMA or value['scene']!='zhumadian':raise ValueError('INVALID_SCENE_MODEL_STATE')
 models=value['models'];light=value['lighting']
 if not isinstance(models,list)or len(models)>1024 or not isinstance(light,dict)or set(light)!=LIGHT_KEYS:raise ValueError('INVALID_SCENE_MODEL_STATE')
 if not number(light['intensity'])or not 0<=light['intensity']<=4 or not number(light['azimuth'])or not 0<=light['azimuth']<=360 or type(light['textures'])is not bool or type(light['shadows'])is not bool:raise ValueError('INVALID_SCENE_LIGHTING')
 ids=set()
 for model in models:
  if not isinstance(model,dict)or set(model)!=INSTANCE_KEYS:raise ValueError('INVALID_SCENE_INSTANCE')
  for key in ['id','assetId']:
   if not isinstance(model[key],str)or not ID.fullmatch(model[key]):raise ValueError('INVALID_SCENE_INSTANCE_ID')
  if model['id']in ids:raise ValueError('DUPLICATE_SCENE_INSTANCE_ID')
  ids.add(model['id']);name=model['name']
  if not isinstance(name,str)or name!=name.strip(JS_TRIM)or not 1<=len(name.encode('utf-16-le'))//2<=120 or re.search(r'[\x00-\x1f\x7f]',name):raise ValueError('INVALID_SCENE_INSTANCE_NAME')
  if not isinstance(model['assetSHA256'],str)or not HASH.fullmatch(model['assetSHA256']):raise ValueError('INVALID_SCENE_ASSET')
  if catalog is not None and catalog.get(model['assetId'])!=model['assetSHA256']:raise ValueError('SCENE_ASSET_VERSION_UNAVAILABLE')
  anchor=model['anchor']
  if not isinstance(anchor,list)or len(anchor)!=3 or any(not number(v)or abs(v)>100000 for v in anchor)or not number(model['scale'])or not 0<model['scale']<=100 or not number(model['rotationDegrees'])or abs(model['rotationDegrees'])>360000 or type(model['visible'])is not bool:raise ValueError('INVALID_SCENE_PLACEMENT')
 if not(models==[]and light['targetModelId']is None)and(not isinstance(light['targetModelId'],str)or light['targetModelId']not in ids):raise ValueError('INVALID_SCENE_LIGHT_TARGET')
 return copy.deepcopy(value)

def empty_state():return{'schema':SCHEMA,'scene':'zhumadian','models':[],'lighting':{'intensity':1.8,'azimuth':135,'textures':True,'shadows':True,'targetModelId':None}}
