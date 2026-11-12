"""Explicit independent model-state root/catalog; existing business and scene-file stores unchanged."""
from pathlib import Path
import hashlib,re
from services.common import loads
from services.project_files import regular
from scene_model_sync.repository import SceneModelRepository
from scene_model_sync.validation import catalog_versions
SETTINGS=frozenset({'sceneModelsRoot','sceneModelsCatalog','sceneModelsCatalogSHA256'})
def validate_model_settings(config):
 present=SETTINGS&set(config)
 if not present:return
 if present!=SETTINGS:raise ValueError('COMPLETE_SCENE_MODEL_SETTINGS_REQUIRED')
 for n in ['sceneModelsRoot','sceneModelsCatalog']:
  if not isinstance(config[n],str)or not Path(config[n]).is_absolute():raise ValueError('EXPLICIT_MODEL_STORAGE_PATH_REQUIRED')
  regular(config[n],directory=n=='sceneModelsRoot')
 if not isinstance(config['sceneModelsCatalogSHA256'],str)or not re.fullmatch('[0-9a-f]{64}',config['sceneModelsCatalogSHA256']):raise ValueError('PINNED_MODEL_STORAGE_CATALOG_REQUIRED')
def configured_scene_models(config,state_root,run_root):
 validate_model_settings(config)
 if not SETTINGS&set(config):return None
 root=regular(config['sceneModelsRoot'],True);catalog=regular(config['sceneModelsCatalog'])
 others=[Path(state_root),Path(run_root),catalog]
 for key in ['projectFilesRoot','sceneProjectsRoot']:
  if config.get(key):others.append(Path(config[key]))
 for other in others:
  if root==other or root.is_relative_to(other)or other.is_relative_to(root):raise ValueError('SCENE_MODEL_STORAGE_MUST_BE_SEPARATE')
 with catalog.open('rb')as f:raw=f.read(262145)
 if len(raw)>262144 or hashlib.sha256(raw).hexdigest()!=config['sceneModelsCatalogSHA256']:raise ValueError('MODEL_STORAGE_CATALOG_CHANGED')
 document=loads(raw)
 if not isinstance(document,dict)or document.get('schema')!='xnby.scene-model-library.v1':raise ValueError('MODEL_STORAGE_CATALOG_INVALID')
 rows=document.get('models');catalog_versions(rows)
 root.mkdir(parents=True,exist_ok=True);regular(root,True)
 return SceneModelRepository(root,rows)
