"""Lossless complete scenes in a separate fixed library, reusing original project ACL/CAS."""
import hashlib,math,re
from pathlib import Path
from types import SimpleNamespace
from services.common import loads
from services.data import validate_layers
from services.project_files import ProjectFileRepository,project_filename,regular
from tools.landscape_layer_validation import validate_editor_layers
ROUTE='/v2/project/scenes'
SCHEMAS=('xnby.scene-project.v1','xnby.scene-project.v2')
SETTINGS=frozenset({'sceneProjectsRoot','sceneModelCatalog','sceneModelCatalogSHA256'})
JS_TRIM='\u0009\u000b\u000c\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000\ufeff\u000a\u000d\u2028\u2029'
ID=re.compile('[-a-z0-9]{1,80}')
SHA=re.compile('[a-f0-9]{64}')
def exact(value,keys):return isinstance(value,dict)and set(value)==set(keys)
def finite(v):return type(v)in(int,float)and math.isfinite(v)
def utf16_length(v):
 try:return len(v.encode('utf-16-le'))//2
 except(UnicodeError,AttributeError):raise ValueError('INVALID_SCENE_TEXT')from None
def scene_filename(value):
 project_filename(value)
 if not value.endswith('.scene.json')or not value[:-11].strip()or utf16_length(value)>100:raise ValueError('INVALID_SCENE_FILE_NAME')
 return value
def checked_catalog(value):
 if not isinstance(value,dict)or value.get('schema')!='xnby.scene-model-library.v1'or not isinstance(value.get('models'),list)or len(value['models'])>64:raise ValueError('INVALID_SCENE_MODEL_CATALOG')
 result={}
 for row in value['models']:
  if not isinstance(row,dict)or not isinstance(row.get('id'),str)or not ID.fullmatch(row['id'])or row['id']in result or not isinstance(row.get('sha256'),str)or not SHA.fullmatch(row['sha256']):raise ValueError('INVALID_SCENE_MODEL_CATALOG')
  result[row['id']]=row['sha256']
 return result
def validate_scene_project(value,catalog):
 if not exact(value,['schema','scene','landscape','models','lighting'])or value['schema']not in SCHEMAS or value['scene']!='zhumadian':raise ValueError('INVALID_COMPLETE_SCENE')
 validate_editor_layers(value['landscape']);validate_layers(value['landscape'])
 modern=value['schema']==SCHEMAS[1];models=value['models'];light=value['lighting']
 if not isinstance(models,list)or len(models)>(1024 if modern else 64)or not exact(light,['intensity','azimuth','textures','shadows','targetModelId']):raise ValueError('INVALID_SCENE_MODELS')
 if not finite(light['intensity'])or not 0<=light['intensity']<=4 or not finite(light['azimuth'])or not 0<=light['azimuth']<=360 or type(light['textures'])is not bool or type(light['shadows'])is not bool:raise ValueError('INVALID_SCENE_LIGHTING')
 seen=set()
 for m in models:
  fields=['id','assetSHA256','anchor','scale','rotationDegrees','visible']+(['assetId','name']if modern else [])
  if not exact(m,fields)or not isinstance(m['id'],str)or not ID.fullmatch(m['id'])or m['id']in seen or not isinstance(m['assetSHA256'],str)or not SHA.fullmatch(m['assetSHA256']):raise ValueError('INVALID_SCENE_INSTANCE')
  asset=m['assetId']if modern else m['id']
  if not isinstance(asset,str)or not ID.fullmatch(asset)or catalog.get(asset)!=m['assetSHA256']:raise ValueError('SCENE_MODEL_VERSION_UNAVAILABLE')
  if modern:
   name=m['name']
   if not isinstance(name,str)or name!=name.strip(JS_TRIM)or not 1<=utf16_length(name)<=120 or re.search('[\x00-\x1f\x7f]',name):raise ValueError('INVALID_SCENE_INSTANCE_NAME')
  if not isinstance(m['anchor'],list)or len(m['anchor'])!=3 or not all(finite(v)and abs(v)<=100000 for v in m['anchor'])or not finite(m['scale'])or not 0<m['scale']<=100 or not finite(m['rotationDegrees'])or abs(m['rotationDegrees'])>360000 or type(m['visible'])is not bool:raise ValueError('INVALID_SCENE_PLACEMENT')
  seen.add(m['id'])
 if not(modern and not models and light['targetModelId']is None)and(not isinstance(light['targetModelId'],str)or light['targetModelId']not in seen):raise ValueError('INVALID_SCENE_LIGHT_TARGET')
 return value
class SceneProjectRepository(ProjectFileRepository):
 def __init__(self,root,catalog,maximum_files=512):
  pinned=checked_catalog(catalog)
  super().__init__(root,maximum_files,validate_document=lambda doc:validate_scene_project(doc,pinned),filename_validator=scene_filename)
def serve_scene_projects(handler,write=False):
 from services.project_files_api import serve_project_files
 class Request:
  path='/v2/project/files'+handler.path[len(ROUTE):]
  server=SimpleNamespace(access=handler.server.access,project_files=getattr(handler.server,'scene_projects',None),project_origin=getattr(handler.server,'project_origin','https://www.joinlinksmart.com'))
  def __getattr__(self,name):return getattr(handler,name)
 return serve_project_files(Request(),write)
def validate_scene_settings(config):
 present=SETTINGS&set(config)
 if not present:return
 if present!=SETTINGS:raise ValueError('COMPLETE_SCENE_LIBRARY_SETTINGS_REQUIRED')
 for n in ['sceneProjectsRoot','sceneModelCatalog']:
  if not isinstance(config[n],str)or not Path(config[n]).is_absolute():raise ValueError('EXPLICIT_SCENE_LIBRARY_PATH_REQUIRED')
  regular(config[n],directory=n=='sceneProjectsRoot')
 if not isinstance(config['sceneModelCatalogSHA256'],str)or not SHA.fullmatch(config['sceneModelCatalogSHA256']):raise ValueError('PINNED_SCENE_MODEL_CATALOG_REQUIRED')
def configured_scene_repository(config,state_root,run_root):
 validate_scene_settings(config)
 if not SETTINGS&set(config):return None
 root=regular(config['sceneProjectsRoot'],True);catalog_path=regular(config['sceneModelCatalog'])
 others=[Path(state_root),Path(run_root),catalog_path]
 if config.get('projectFilesRoot'):others.append(Path(config['projectFilesRoot']))
 for other in others:
  if root==other or root.is_relative_to(other)or other.is_relative_to(root):raise ValueError('SCENE_LIBRARY_MUST_BE_SEPARATE')
 with catalog_path.open('rb')as f:raw=f.read(262145)
 if len(raw)>262144 or hashlib.sha256(raw).hexdigest()!=config['sceneModelCatalogSHA256']:raise ValueError('SCENE_MODEL_CATALOG_CHANGED')
 return SceneProjectRepository(root,loads(raw))
