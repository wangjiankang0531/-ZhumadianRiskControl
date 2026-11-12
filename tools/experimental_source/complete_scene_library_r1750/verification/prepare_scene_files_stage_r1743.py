"""Stage complete current B/S host compiler output and exact D118 scene; no GIS copy."""
from pathlib import Path
from urllib.parse import unquote
import ast,hashlib,importlib.util,json,os,re,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
W=R/'work/scene-fine-auth-stage-r1743';D=R/'Document/Deployment/scene_fine_auth_stage_r1743_20261107'
BUILD=R/'work/hazard-management-full-r1673';BASE=R/'work/unified-attachment-r49-r1361/payload'
def J(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b)
def link(p,s):p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();os.link(s,p);assert pin(p)==pin(s)
assert not W.exists()and not D.exists()
proof=J(BUILD/'full-build-result.json');assert proof['passed']and proof['sharedAndIsolatedSourcesRestored']and proof['loopbackHostDevelopmentBuild']and not proof['productionFrontendCompilerOutput']
assert J(V/'hazard-management-full-r1673-outer-terminal.json')['actualJobDescendantsZero']
assert sha(BASE/'release-manifest.json')=='d2918cf14933b7a903368a0f88e6b2075116081cdbb847ca435b67bd01c8ea88'
compiled=J(BUILD/'candidate-result.json')['fullFrontendFiles'];previous=J(R/'work/hazard-management-full-r1181/candidate-result.json')['fullFrontendFiles'];pm=J(BASE/'payload-manifest.json')
assert len(compiled)==841 and all(pin(BUILD/'build/dist'/n)==row for n,row in compiled.items())
old_security={n.removeprefix('frontend/security_pc/'):r for n,r in pm['files'].items()if n.startswith('frontend/security_pc/')}
extras=set(old_security)-set(previous);assert len(extras)==4
W.mkdir();D.mkdir();root=W/'payload';security=root/'frontend/security_pc'
for n in compiled:
 if n!='index.html':link(security/n,BUILD/'build/dist'/n)
for n in extras:
 source=BASE/'frontend/security_pc'/n
 if not source.exists():source=R/'work/scene-host-integration-r1477/payload/frontend/security_pc'/n
 assert pin(source)==old_security[n];link(security/n,source)
old=(BASE/'frontend/security_pc/index.html').read_bytes();new=(BUILD/'build/dist/index.html').read_bytes()
oe=re.findall(rb'<script type="module" crossorigin src="([^"]+)"',old);ne=re.findall(rb'<script type="module" crossorigin src="([^"]+)"',new);assert len(oe)==len(ne)==1
def normal(b):
 b=re.sub(rb'<link[^>]+data-xnby-(?:workplace-period|home-transfer)=[^>]+>\s*',b'',b)
 return re.sub(rb'\s+',b' ',b.replace(oe[0],b'/OWN_ENTRY').replace(ne[0],b'/OWN_ENTRY')).strip()
assert normal(old)==normal(new),'ONLY_MAIN_ENTRY_AND_RETAINED_OVERLAYS_ALLOWED'
merged=old.replace(oe[0],ne[0]);assert all(merged.count(('data-xnby-'+k+'=').encode())==1 for k in ['home-viewport','workplace-period','home-transfer'])
put(security/'index.html',merged)
refs=0;dynamic=[]
for p in security.rglob('*'):
 if not p.is_file()or p.suffix not in ['.html','.css','.js']:continue
 text=p.read_text('utf8');values=re.findall(r'''["']([^"'\r\n]{1,240}\.(?:js|css|woff2?|ttf|svg|png|webp|jpe?g|gif|ico)(?:\?[^"']*)?)["']''',text)
 if p.suffix=='.css':values+=re.findall(r'''url\(([^)"']+)\)''',text)
 for value in values:
  ref=value.strip().strip('"\'')
  if ref.startswith(('http:','https:','data:','blob:','//','#')):continue
  ref=unquote(ref.split('?',1)[0].split('#',1)[0]);target=None
  if '{'in ref or '}'in ref:dynamic.append({'consumer':p.relative_to(security).as_posix(),'reference':ref});continue
  if ref.startswith('/zhumadian/branding-20261025/'):target=security/ref.removeprefix('/zhumadian/branding-20261025/')
  elif ref.startswith('/zhumadian/')and not ref.startswith('/zhumadian/api/'):target=security/ref.removeprefix('/zhumadian/')
  elif ref.startswith('assets/'):target=security/ref
  elif ref.startswith(('./','../')):target=p.parent/ref
  if target is not None:refs+=1;assert target.resolve().is_relative_to(security)and target.is_file(),(p.name,ref)
scene=root/'frontend/scene';rebuilt=J(R/'Document/Deployment/scene_model_visibility_build_r1736_20261107/qualified-build-r1736.json');assert rebuilt['passed'];receipt={'sha256':'db20241a05d950655e881b2f784bba553cbab27135e69c4d46695ea391dffa6c','members':rebuilt['fiveOutputs']}
for n,row in receipt['members'].items():
 p=R/'work/scene-file-frontend-r1735/delivery-fine-auth-r1736'/n;assert pin(p)==row;put(scene/n,p.read_bytes())
catalog=A.parent/'Assets/Icons/PointSymbols/System/catalog.json';data=J(catalog);assert len(data['icons'])==10
put(scene/'point-symbols/system/catalog.json',catalog.read_bytes())
for icon in data['icons']:
 p=catalog.parent/icon['file'];assert pin(p)=={k:icon[k]for k in ['bytes','sha256']};put(scene/'point-symbols/system'/icon['file'],p.read_bytes())
put(scene/'THREE-LICENSE.txt',(A/'web/node_modules/three/LICENSE').read_bytes())
model_root=R/'Assets/MODELS/Runtime/TianjinZhongyuan';model_source=model_root/'catalog.json';assert sha(model_source)=='3798b38b77a81e6546b56e88de2c2f86e297e26197dc0f44b3475c568aa6c006'
models=J(model_source);assert len(models['models'])==29
public_models=J(model_source)
for row in public_models['models']:
 assert isinstance(row['sourceFile'],str);row['sourceFile']=row['sourceFile'].replace('\\','/').rsplit('/',1)[-1]
put(scene/'model-library/catalog.json',enc(public_models))

manifest={'schema':'xnby.scene.static-files.v1','files':{p.relative_to(scene).as_posix():pin(p)for p in scene.rglob('*')if p.is_file()}}
put(scene/'scene-static-manifest.json',enc(manifest));descriptor={'schema':'xnby.original.scene-static.v1','manifestPath':'frontend/scene/scene-static-manifest.json','manifestSHA256':sha(scene/'scene-static-manifest.json')}
spec=importlib.util.spec_from_file_location('scene_r1476',V/'original_scene_model_static_routes_r1560.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
assets=J(R/'work/scene-host-integration-r1477/scene-readonly-assets.private.json');assert set(assets)==set(mod.ASSETS)
for row in models['models']:
 p=model_root/row['file'];assets['model-library/'+row['file']]={'path':str(p),'bytes':row['bytes'],'sha256':row['sha256']}

rows=mod.preflight(root,descriptor,assets);assert len(rows)==57
put(W/'scene-descriptor.json',enc(descriptor));put(W/'scene-readonly-assets.private.json',enc(assets));put(W/'scene-locations.private.json',enc(rows))
ast.parse((V/'original_scene_model_static_routes_r1560.py').read_text('utf8'));put(root/'tools/original_scene_static_routes.py',(V/'original_scene_model_static_routes_r1560.py').read_bytes())
result={'passed':True,'onlyPrepared':True,'fullSafetyFiles':len(compiled)+4,'literalFrontendAssetReferencesChecked':refs,'unacceptedDynamicTemplates':dynamic,'currentHomeViewportWorkplaceHomeTransferOverlaysRetained':True,'peerStaticSourceArchiveSHA256':receipt['sha256'],'sceneStaticFiles':len(manifest['files']),'systemPNGFiles':10,'readonlyGISFiles':len(mod.ASSETS),'readonlyModelFiles':len(models['models']),'readonlyGISLogicalBytes':sum(assets[n]['bytes']for n in mod.ASSETS),'readonlyModelLogicalBytes':sum(r['bytes']for r in models['models']),'GISCopied':False,'optionalReadonlyStaticRoutes':len(rows),'thisStageDoesNotRunFineProvider':True,'normalHostBrowserAndOriginalSDKIntegrationPending':True,'productionHostCompilerOutputPending':False,'D125FineAuthStaticPreparedOnly':True,'thisIsLoopbackTestFrontend':True,'normalD125FineAuthHostUIAccepted':False,'originalModelCatalogUnchanged':sha(model_source)=='3798b38b77a81e6546b56e88de2c2f86e297e26197dc0f44b3475c568aa6c006','publicDeployed':False}
put(D/'prepared-scene-fine-auth-stage-r1743.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='unacceptedDynamicTemplates'}))
