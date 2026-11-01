"""Verify/install six owned callback overlay files into a fresh owned platform run."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,shutil,uuid
FILES=frozenset(('own-platform-observation.jar','persistent-launcher-classes/xnby/platform/OriginalPersistentPlatformLaunch.class','persistent-launcher-classes/xnby/platform/OriginalPlatformCallbackScope.class','callback-route-pins.json','business-classes/xnby/replica/OriginalBusinessLaunch.class','business-classes/xnby/replica/OriginalBusinessListenBoundary.class'))
BASELINES=frozenset(('payload/platform/run-template/own-platform-observation.jar','payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalPlatformStorageScope.class','payload/platform/process-boundary.jar','payload/platform/boot-loader.jar','payload/business/process-boundary.jar','payload/business/run-template/classes/xnby/replica/OriginalBusinessLaunch.class'))
def require(ok,code):
 if not ok:raise ValueError(code)
def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def regular(path,root):
 path,root=Path(path).absolute(),Path(root).absolute();require(path.is_relative_to(root),'CALLBACK_OVERLAY_PATH_OUTSIDE_OWNER')
 for part in [root,*[root/p for p in reversed(path.relative_to(root).parents) if str(p)!='.'],path]:
  require(not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'CALLBACK_OVERLAY_REPARSE_REJECTED')
 require(path.is_file(),'CALLBACK_OVERLAY_REGULAR_FILE_REQUIRED');return path

def load_callback_overlay(application,manifest_path,manifest_sha256):
 app=Path(application).absolute();manifest_path=Path(manifest_path).absolute()
 require(app.name=='Application' and app.resolve(strict=True)==app,'CALLBACK_OVERLAY_APPLICATION_ROOT_REQUIRED')
 require(isinstance(manifest_sha256,str) and re.fullmatch('[0-9a-f]{64}',manifest_sha256),'CALLBACK_OVERLAY_MANIFEST_PIN_REQUIRED')
 require(manifest_path.is_relative_to(app/'payload/callback-overlay') and manifest_path.name=='manifest.json','OWN_CALLBACK_OVERLAY_LOCATION_REQUIRED')
 regular(manifest_path,app);require(manifest_path.stat().st_size<=256*1024 and digest(manifest_path)==manifest_sha256,'CALLBACK_OVERLAY_MANIFEST_MISMATCH')
 def pairs(items):
  result={}
  for key,value in items:require(key not in result,'DUPLICATE_CALLBACK_OVERLAY_KEY');result[key]=value
  return result
 manifest=json.loads(manifest_path.read_bytes(),object_pairs_hook=pairs)
 require(manifest.get('schema')=='xnby.original-callback-overlay.v2' and set(manifest.get('files',{}))==FILES and set(manifest.get('baselines',{}))==BASELINES,'EXACT_CALLBACK_OVERLAY_SCOPE_REQUIRED')
 for relative,sha in manifest['baselines'].items():require(digest(regular(app/relative,app))==sha,'CALLBACK_OVERLAY_BASELINE_CHANGED')
 files={};total=0
 for relative,pin in manifest['files'].items():
  name=PurePosixPath(relative);require(str(name)==relative and not name.is_absolute() and '..' not in name.parts and '\\' not in relative,'CALLBACK_OVERLAY_RELATIVE_FILE_REQUIRED')
  path=regular(manifest_path.parent/relative,app);total+=path.stat().st_size
  require(type(pin['bytes']) is int and path.stat().st_size==pin['bytes'] and path.stat().st_size<=1024*1024 and digest(path)==pin['SHA256'],'CALLBACK_OVERLAY_MEMBER_CHANGED');files[relative]=path
 require(total<=2*1024*1024,'CALLBACK_OVERLAY_TOTAL_BOUND')
 raw=files['callback-route-pins.json'].read_bytes();require(len(raw)<=65536,'CALLBACK_ROUTE_PIN_SIZE_BOUND');pins=json.loads(raw,object_pairs_hook=pairs);require(isinstance(pins,dict) and len(pins)==7,'EXACT_SEVEN_CALLBACK_PINS_REQUIRED')
 for ident,pin in pins.items():
  require(re.fullmatch('[0-9a-f]{64}',ident) and isinstance(pin,dict),'CALLBACK_ROUTE_PIN_SHAPE')
  require(all(isinstance(pin.get(key),str) and re.fullmatch('[0-9a-f]{64}',pin[key]) for key in ('hostSHA256','pathSHA256','configSHA256')) and type(pin.get('port')) is int and 1024<=pin['port']<=65535,'CALLBACK_ROUTE_PIN_SHAPE')
 return {'files':files,'filePins':manifest['files'],'pins':pins,'manifestSHA256':manifest_sha256,'application':app}

def install_callback_overlay(overlay,platform,business):
 platform=Path(platform).absolute();app=overlay['application'];regular(platform/'server-owner.properties',app)
 require(platform.parent==app/'UserData/TianjinOriginalPlatform/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}',platform.name),'FRESH_OWN_PLATFORM_RUN_REQUIRED')
 owner=dict(line.split('=',1) for line in (platform/'server-owner.properties').read_text(encoding='ascii').splitlines() if '=' in line)
 require(set(owner)=={'schema','ownerId'} and owner['schema']=='zhumadian.original.server.owner.v1' and str(uuid.UUID(owner['ownerId']))==owner['ownerId'],'CALLBACK_RUN_OWNER_REQUIRED')
 require(not any((platform/name).exists() for name in ('server-ready.txt','own-stop-requested.txt','callback-routes-ready.properties','original-platform-main-requested.txt','own-platform-ready.txt','server-http-port.txt')),'CALLBACK_EXISTING_RUN_REJECTED')
 business=Path(business).absolute();regular(business/'server-owner.properties',app)
 require(business.name=='b' and business.parent.name==platform.name and business.parent.parent==app/'UserData/OriginalServer/runs','MATCHING_OWN_BUSINESS_RUN_REQUIRED')
 business_owner=dict(line.split('=',1) for line in (business/'server-owner.properties').read_text(encoding='ascii').splitlines() if '=' in line)
 require(business_owner==owner,'CALLBACK_COMPONENT_OWNER_MISMATCH')
 require(not any((business/name).exists() for name in ('server-ready.txt','own-stop-requested.txt','own-main-invocation-requested.txt','server-http-port.txt')),'CALLBACK_EXISTING_BUSINESS_RUN_REJECTED')
 for relative in FILES-{'callback-route-pins.json'}:
  source=regular(overlay['files'][relative],app);pin=overlay['filePins'][relative];require(source.stat().st_size==pin['bytes'] and digest(source)==pin['SHA256'],'CALLBACK_OVERLAY_CHANGED_AFTER_LOAD')
  target=business/'classes'/relative.split('/',1)[1] if relative.startswith('business-classes/') else platform/relative
  for parent in (target,*target.parents):
   if parent==app:break
   require(not parent.is_symlink() and (not parent.exists() or not getattr(parent.lstat(),'st_file_attributes',0)&0x400),'CALLBACK_RUN_REDIRECTION_REJECTED')
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,target);require(digest(target)==pin['SHA256'],'CALLBACK_OWN_RUN_COPY_MISMATCH')