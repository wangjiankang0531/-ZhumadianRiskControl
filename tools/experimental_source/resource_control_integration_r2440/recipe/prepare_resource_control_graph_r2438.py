"""Local complete resource candidate. No installed paths, processes or public writes."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
OLD=R/'work/public-same-window-r2330';F=R/'work/hazard-management-full-r2434'
SCENE=R/'work/resource-scene-control-r2435/products';W=R/'work/resource-complete-control-r2438'
NEW=A/'tools/experimental_source/client_resource_ingress_r2397'
PRIVATE=V/'public-offline-entry-private-r2306';PRIVATE_PROPOSAL=PRIVATE/'spatial-sync-settings.client-resources-r2438.private.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def j(p):return json.loads(p.read_bytes())
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(raw)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def row(raw):return{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def main():
 assert not W.exists()and not PRIVATE_PROPOSAL.exists(),'FRESH_LOCAL_PREPARATION_REQUIRED'
 assert j(F/'full-build-result.json')['passed']and j(R/'work/resource-scene-control-r2435/verification.json')['passed']
 portal_terminal=j(V/'hazard-management-full-r2434-outer-terminal.json');assert portal_terminal['exitCode']==0 and portal_terminal['actualJobDescendantsZero']
 scene_terminal=j(V/'d176-scene-r2435-outer-terminal.json');assert scene_terminal['rootExitCode']==0 and scene_terminal['actualJobBeforeClose']==0
 assert sha(OLD/'bundle/payload/release-manifest.json')=='b36491663db37033ae2fc450b0209e864d5ebd7b7b7ed1bba7fda6a7e5545323'
 old_settings=PRIVATE/'spatial-sync-settings.private.json'
 assert sha(old_settings)=='286aef3fa30d953d3037f36dc5dc2fadb3771a5cd229226ee2b117e5d1ff83f3'
 before_settings=j(old_settings);settings=copy.deepcopy(before_settings);assert 'clientResources'not in settings
 gis_manifest=A/'Packages/ClientGISSettingsCandidate_20261107/client-gis-install.json'
 assert sha(gis_manifest)=='26342711ce4091661d71893ce43a1e0431417117ba9f9d522d3ce8ea738cac72'
 gis=j(gis_manifest);pair={k:gis[k]for k in('sourceRuntimeIdentity','sourceIndexIdentity')}
 assert any(all(v.get(k)==h for k,h in pair.items())for v in settings['localGIS']['allowedSources'])
 installations=[]
 for machine,pin in(('250','bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b'),('252','0903a5506ecf6d7677c2dcadd8bf089e3e65db6adc8d956d914d91b700aa5bce')):
  manifest=A/('Packages/ResourceGISControlCandidate_20261112/client-'+machine+'/client-resources-install.json')
  assert sha(manifest)==pin
  for n,v in j(manifest)['files'].items():
   p=manifest.parent/n;assert p.stat().st_size==v['bytes']and sha(p)==v['sha256']
  installations.append({'installationIdentity':pin,**pair})
 settings['clientResources']={'schema':'xnby.client-resources.server-settings.v1','allowedInstallations':installations}
 assert {k:v for k,v in settings.items()if k!='clientResources'}==before_settings
 settings_raw=enc(settings);settings_pin=row(settings_raw)['sha256']
 # This file stays under the already protected R50 private directory, outside transport/source/Git.
 assert PRIVATE.resolve()==PRIVATE and not PRIVATE.is_symlink()and not PRIVATE.is_junction()
 put(PRIVATE_PROPOSAL,settings_raw)
 changed={};c=j(OLD/'runtime/tools/original_offline_scene_contract_r2193.json')
 old_release=j(OLD/'bundle/payload/release-manifest.json');old_payload=j(OLD/'bundle/payload/payload-manifest.json')
 files=c['candidatePayload']['files'];controllers=c['candidateRelease']['controllerFiles']
 def replace(n,raw,controller=False):
  assert not n.startswith(('private/','UserData/','Assets/','runtime/','seed/'))
  changed[n]=raw;files[n]=row(raw)
  if controller:controllers[n]=row(raw)['sha256']
 prefix='frontend/security_pc/';prior_front=j(R/'work/hazard-management-full-r2322/candidate-result.json')['fullFrontendFiles']
 new_front=j(F/'candidate-result.json')['fullFrontendFiles'];assert len(prior_front)==len(new_front)==841
 retained={n:r for n,r in files.items()if n.startswith(prefix)and n.removeprefix(prefix)not in prior_front};assert len(retained)==4
 extra=b'    <link rel="stylesheet" data-xnby-workplace-period="20261104-r564" href="/zhumadian/assets/css/xnby-workplace-period-736f7b07dd2c.css">\n    <link rel="stylesheet" data-xnby-home-transfer="r894" href="/zhumadian/branding-20261025/assets/css/xnby-home-transfer-162b8ebe4004d78f.css">\n'
 old_html=(R/'work/hazard-management-full-r2322/build/dist/index.html').read_bytes()
 assert(OLD/'bundle/payload'/prefix/'index.html').read_bytes()==old_html.replace(b'</head>',extra+b'</head>',1)
 for n in list(files):
  if n.startswith(prefix):del files[n]
 files.update(retained)
 for n,v in new_front.items():
  raw=(F/'build/dist'/n).read_bytes();assert row(raw)==v
  if n=='index.html':assert raw.count(b'</head>')==1;raw=raw.replace(b'</head>',extra+b'</head>',1)
  replace(prefix+n,raw)
 package=NEW/'package';manifest=package/'package-manifest.json';assert sha(manifest)=='6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3'
 package_rows=j(manifest)['inputs'];assert len(package_rows)==44
 code_root=c['candidateRelease']['spatialSync']['codeRoot']
 for n,v in package_rows.items():
  raw=(package/n).read_bytes();assert row(raw)==v;replace(code_root+'/'+n,raw,True)
 replace(code_root+'/package-manifest.json',manifest.read_bytes(),True)
 support=NEW/'original_spatial_sync_release_support.py';assert sha(support)=='dcc83dbb6f23f5c426b978fb99cd09a3e11bf479734452856f5e48c8900c558f'
 replace('tools/original_spatial_sync_release_support.py',support.read_bytes(),True)
 c['candidateRelease']['spatialSync']['packageManifestSHA256']=sha(manifest)
 c['candidateRelease']['spatialSync']['settingsSHA256']=settings_pin
 c['candidateRelease']['spatialSync']['settingsPath']='private/spatial-sync-settings.client-resources-r2438.private.json'
 proxy=NEW/'iis/XnbyReferenceProxy.cs';assert sha(proxy)=='cdfae1908c16f6724ea5d6582fc78c9b0ea68ea7e8cbeac6b782f1811d0a38a5'
 for n in('iis/App_Code/XnbyReferenceProxy.cs','deploy/iis_original/App_Code/XnbyReferenceProxy.cs'):
  replace(n,proxy.read_bytes(),True);c['candidateRelease']['staticInitialLoadPerformance']['files'][n]=row(proxy.read_bytes())
 static_path=c['candidateRelease']['sceneStatic']['manifestPath'];static=j(OLD/'bundle/payload'/static_path)
 source_receipt=j(SCENE/'rebuild-receipt.json')
 for n in('viewer.js','source-gain-worker.js','index.html','source-config.html','scene-help.html'):
  raw=(SCENE/n).read_bytes();assert row(raw)=={k:source_receipt['outputs'][n][k]for k in('bytes','sha256')}
  static['files'][n]=row(raw);replace('frontend/scene/'+n,raw)
 replace(static_path,enc(static));c['candidateRelease']['sceneStatic']['manifestSHA256']=row(enc(static))['sha256']
 runtime=W/'runtime'
 for p in(OLD/'runtime/tools').iterdir():
  if p.is_file()and p.name not in('original_offline_scene_contract_r2193.json','original_offline_scene_profile_r2191.py','original_public_test_update.py'):put(runtime/'tools'/p.name,p.read_bytes())
 helper=(OLD/'runtime/tools/original_offline_scene_profile_r2191.py').read_text('utf8')
 old_revision="REVISION = '20261112-public-scene-same-window-r51'";assert helper.count(old_revision)==1
 helper=helper.replace(old_revision,"REVISION = '20261112-client-resource-control-integration-r2438-local-candidate'",1);ast.parse(helper)
 put(runtime/'tools/original_offline_scene_profile_r2191.py',helper.encode())
 contract=runtime/'tools/original_offline_scene_contract_r2193.json';put(contract,enc(c))
 wrapper=(OLD/'runtime/tools/original_public_test_update.py').read_text('utf8')
 for key,p in [('HELPER_SHA',runtime/'tools/original_offline_scene_profile_r2191.py'),('CONTRACT_SHA',contract)]:
  wrapper,count=re.subn(key+" = '[a-f0-9]{64}'",key+" = '"+sha(p)+"'",wrapper);assert count==1
 ast.parse(wrapper);put(runtime/'tools/original_public_test_update.py',wrapper.encode())
 module=load('resource_complete_graph2438',runtime/'tools/original_public_test_update.py').runtime();profile=module.SCENE_IIS_PROFILE
 plan=profile.expected_plan(Path('C:/inetpub/wwwroot/Zhumadian/Application'),18892);payload=profile.payload();release=profile.release(plan['newPayloadManifestSHA256'])
 permitted={'spatialSync','sceneStatic','staticInitialLoadPerformance','controllerFiles','payloadManifestSHA256','publicTestRevision'}
 assert all(release[k]==old_release[k]for k in old_release if k not in permitted)
 assert not any(n.startswith(('private/','UserData/','Assets/','runtime/','seed/'))for n in plan['files'])
 assert all(n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))for n in plan['removedFrontendFiles'])
 for n,v in plan['files'].items():
  if n=='payload-manifest.json':raw=enc(payload)
  elif n=='release-manifest.json':raw=enc(release)
  elif n in profile.component:raw=(runtime/n).read_bytes()
  elif n in changed:raw=changed[n]
  else:raw=(OLD/'bundle/payload'/n).read_bytes()
  assert row(raw)=={'bytes':v['bytes'],'sha256':v['SHA256']},n;put(W/'bundle/payload'/n,raw)
 put(W/'bundle/update-manifest.json',enc(plan))
 changed_rows={n:v for n,v in payload['files'].items()if old_payload['files'].get(n)!=v}
 expected_prefixes=(prefix,'frontend/scene/',code_root+'/')
 expected_controls=set(profile.component)|{'tools/original_spatial_sync_release_support.py','iis/App_Code/XnbyReferenceProxy.cs','deploy/iis_original/App_Code/XnbyReferenceProxy.cs'}
 assert all(n.startswith(expected_prefixes)or n in expected_controls for n in changed_rows)
 result={'prepared':True,'publicOrClientInstalled':False,'completePayloadFiles':len(payload['files']),'R49QualificationWrites':len(plan['files']),'R49QualificationRemovals':len(plan['removedFrontendFiles']),'actualDeployNeedsFreshPublicBaselineAndNewIncrementalPlan':True,'newReleaseSHA256':sha(W/'bundle/payload/release-manifest.json'),'retainedR51ReleaseSHA256':sha(OLD/'bundle/payload/release-manifest.json'),'publicUnchangedAtR51':True,'newPrivateSettingsSHA256':settings_pin,'newPrivateSettingsBytes':len(settings_raw),'newPrivateSettingsProposalOnlyNotTransmitted':True,'newSidecarPathPreservesActiveR51PrivateFile':True,'originalAccessAndEveryOtherPrivateSettingPreserved':True,'allowedResourceInstallations':2,'newWorkerSources':44,'sourceGISDataIncluded':False,'completeFrontFiles':len(new_front),'retainedFrontFiles':len(retained),'matchingSceneProducts':5,'bothIISProxySourcesAndStaticMetadataMatched':True,'changedRowsAgainstR51':changed_rows,'wholeOriginalApplicationLifecycleAccepted':False,'normalPublicUser250252Accepted':False,'fixedR51TransportChanged':False}
 put(W/'prepared-scope.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='changedRowsAgainstR51'}))
if __name__=='__main__':main()
