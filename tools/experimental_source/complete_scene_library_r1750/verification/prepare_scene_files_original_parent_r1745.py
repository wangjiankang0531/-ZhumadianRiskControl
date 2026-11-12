"""Rebase qualified original eight-component parent onto full compiled fine frontend."""
from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';B=R/'work/fine-original-parent-r1585';S=R/'work/scene-fine-auth-stage-r1743';W=R/'work/fine-browser-parent-r1745';D=R/'Document/Deployment/fine_browser_original_r1745_20261107';V=Path(__file__).parent
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 p=W/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as f:f.write(b)
 return p
assert not W.exists()and not D.exists();last=J(R/'work/su1593/verified-result.json');assert last['passed']and last['originalCodeRestored']and last['originalPointerRestored']and last['allActualJobsZeroBeforeClose']
static=R/'Document/Deployment/scene_fine_auth_stage_r1743_20261107';assert J(static/'actual-static-gateway-r1744.json')['passed']and J(static/'actual-static-outer-r1744.json')['actualJobZero']
assert J(R/'Document/Deployment/scene_model_visibility_build_r1736_20261107/qualified-build-r1736.json')['passed']
assert J(V/'hazard-management-full-r1672-outer-terminal.json')['actualJobDescendantsZero']and J(V/'hazard-management-full-r1673-outer-terminal.json')['actualJobDescendantsZero']
assert J(R/'work/hazard-management-full-r1672/actual-compiled-source-files.json')==J(R/'work/hazard-management-full-r1673/actual-compiled-source-files.json')
plan=J(B/'prepared-plan.private.json');assert all(pin(G/n)==r['before']for n,r in plan['mutations'].items())and J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
W.mkdir();D.mkdir();sources={n:Path(r['source'])for n,r in plan['mutations'].items()if r['after']is not None};release=J(B/'payload/release-manifest.json');pm=J(B/'payload/payload-manifest.json')
for n in list(sources):
 if n.startswith(('frontend/security_pc/','frontend/scene/')):del sources[n]
for n in list(pm['files']):
 if n.startswith(('frontend/security_pc/','frontend/scene/')):del pm['files'][n]
for p in (S/'payload').rglob('*'):
 if p.is_file():n=p.relative_to(S/'payload').as_posix();sources[n]=p;pm['files'][n]=pin(p)
assert sum(n.startswith('frontend/security_pc/')for n in sources)==845 and sum(n.startswith('frontend/scene/')for n in sources)==19
release['sceneStatic']=J(S/'scene-descriptor.json');release['spatialSyncIntegrationRevision']='R1745-complete-D125-fine-auth-scene-and-original-early-host-local-only'
settings=J(B/'spatial-settings.private.json');assert settings['sceneReadOnlyAssets']==J(S/'scene-readonly-assets.private.json');settings['sceneProjectsRoot']=str(R/'work/scene-files-original-r1745/cloud-scenes');settings['sceneModelCatalog']=str(G/'frontend/scene/model-library/catalog.json');settings['sceneModelCatalogSHA256']=sha(S/'payload/frontend/scene/model-library/catalog.json');assert 'a531000000000000000000000001d4c2'in settings['access']['writers'];private=put('spatial-settings.private.json',enc(settings))
release['spatialSync']['settingsSHA256']=sha(private)
# Replace only qualified optional support, not the original parent/Job/six-child code.
support=R/'work/scene-file-frontend-r1735/support'
old_fine=release['fineSource'];old_portal=old_fine['portalConfigurationPath'];assert old_portal.startswith(old_fine['codeRoot']+'/public/')
sources.pop(old_portal);pm['files'].pop(old_portal);release['controllerFiles'].pop(old_portal)
for name in ['original_spatial_sync_release_support.py','original_fine_source_runtime.py','original_fine_gateway.py','original_scene_source_configuration.py','original_scene_asset_policy.py']:
 n='tools/'+name;p=support/name;sources[n]=p;pm['files'][n]=pin(p);release['controllerFiles'][n]=sha(p)
release['fineSource']={k:old_fine[k]for k in ['codeRoot','sourceManifestSHA256','inputsSHA256']}
release['fineSource'].update(schema='xnby.original.fine-source.v2',configurationHelperSHA256=sha(support/'original_scene_source_configuration.py'))
backend=R/'work/scene-file-frontend-r1735/backend';old_code=release['spatialSync']['codeRoot'];new_code='extensions/spatial_sync_scene_files_r1745'
for n in list(sources):
 if n.startswith(old_code+'/'):sources.pop(n);pm['files'].pop(n,None);release['controllerFiles'].pop(n,None)
for p in backend.rglob('*'):
 if p.is_file():
  n=new_code+'/'+p.relative_to(backend).as_posix();sources[n]=p;pm['files'][n]=pin(p);release['controllerFiles'][n]=sha(p)
release['spatialSync']['codeRoot']=new_code;release['spatialSync']['packageManifestSHA256']=sha(backend/'package-manifest.json')
sources['payload-manifest.json']=put('payload/payload-manifest.json',enc(pm));release['payloadManifestSHA256']=sha(sources['payload-manifest.json']);sources['release-manifest.json']=put('payload/release-manifest.json',enc(release))
for n,h in release['controllerFiles'].items():assert sha(sources.get(n,G/n))==h,n
for n,row in pm['files'].items():
 if not n.startswith('seed/mysql/'):assert pin(sources.get(n,G/n))==row,n
mutations={}
for n,p in sources.items():
 before,after=pin(G/n),pin(p)
 if before!=after:mutations[n]={'before':before,'after':after,'source':str(p)}
old=J(G/'payload-manifest.json')
for p in (G/'frontend/security_pc').rglob('*'):
 if p.is_file():
  n=p.relative_to(G).as_posix()
  if n not in sources:assert pin(p)==old['files'][n];mutations[n]={'before':pin(p),'after':None,'source':None}
for n,row in plan['mutations'].items():
 if row['after']is None and pin(G/n)is not None and n not in mutations:mutations[n]=row
plan.update(mutations=mutations,candidateReleaseSHA256=sha(sources['release-manifest.json']),privateSettingsSource=str(private),privateSettingsAfter=pin(private),allOriginalAndExtensionControllerFilesVerified=len(release['controllerFiles']),explicitNewCodePayloadMetadataBindings=sorted(release['controllerFiles']),fineBrowserSourcePrepared=True,productionFrontendCompilerOutput=False,successfulUIWritesAlreadyConfirmed=True,replayPriorSuccessfulSpatialPostAllowed=False)
put('prepared-plan.private.json',enc(plan));resource={'schema':'xnby.fine.browser.original-parent.scope.v1','planSHA256':sha(W/'prepared-plan.private.json'),'priorActualParentTerminalAndRestored':True,'priorSuccessfulUIWritesConfirmed':True,'saveReplayAllowed':False,'priorLayerRevision':2,'browserLimitBytes':6*1024**3,'outerLimitBytes':12*1024**3,'minimumAvailablePhysicalAndCommitBytes':15*1024**3,'expectedComponents':8,'fineProviderNativeAndOriginalRoleHTTPAlreadyPassed':True,'fullProductionAndLocalSourceInputsEqual':True,'fineSourceProtocolContracts':827,'stageCompleteStaticHTTPChecks':len(J(static/'actual-static-gateway-r1744.json')['checks']),'portalConfigScope':'Dedicated scene config generated from active provider and protected by original project read ACL; actual normal login still pending'};put('resource-and-reconciliation.json',enc(resource))
proof={'preparedOnly':True,'candidateReleaseSHA256':plan['candidateReleaseSHA256'],'planSHA256':sha(W/'prepared-plan.private.json'),'resourceSHA256':sha(W/'resource-and-reconciliation.json'),'codePaths':len(mutations),'nonSeedFilesVerified':sum(not n.startswith('seed/mysql/')for n in pm['files']),'controllerFilesVerified':len(release['controllerFiles']),'frontendInputs':3733,'sourceMainInputs':169,'actualBrowserStillPending':True,'allPriorBackendControllerFilesPreserved':True,'successfulWritesReplayAllowed':False,'publicUpdated':False};(D/'prepared-browser-parent-r1745.json').write_bytes(enc(proof));print(json.dumps(proof))
