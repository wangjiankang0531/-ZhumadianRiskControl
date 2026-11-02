"""Prepare a pinned PC-only exam editor update against the current local release.

Preserves every non-PC payload entry/controller; no runtime or data mutation.
"""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,sys
BASE='8b5d5bb1cbd98f00c371ba973328c6f0dbbf6cb8f04a25ab13e0a4a3da874c2a'
UPDATER='aa79302b53024ea4ea1ae1c36a0f20874aa9f5a7546e5e358d7a54e91eec6042'
PREFIX='frontend/security_pc/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def encode(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def need(ok,code):
 if not ok:raise ValueError(code)
def build(app,frontend,output):
 app=Path(app).resolve(strict=True);front=Path(frontend).resolve(strict=True);out=Path(output).absolute()
 need(app==Path('D:/Zqa20261025/Application') and not out.exists() and not out.is_relative_to(app),'EXACT_APP_AND_FRESH_OUTPUT')
 need(sha(app/'release-manifest.json')==BASE and sha(app/'tools/original_public_test_update.py')==UPDATER,'PINNED_CURRENT_BASE_AND_UPDATER')
 old=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json');need(sha(app/'payload-manifest.json')==old['payloadManifestSHA256'],'CURRENT_PAYLOAD_PIN')
 receipt=read(front/'receipt.json');phase=read(front.parent/'result.json')
 need(receipt['kind']=='security_pc' and receipt['exitCode']==0 and receipt['sourceFilesUnchanged'] and receipt['originalReferenceUnchanged'] and receipt['trainingAssessmentCompatibility']['sourceFileRestored'],'EXACT_COMPILED_ORIGINAL_PC_REQUIRED')
 need(phase['adapterChecks']==8 and phase['componentCases']==18 and phase['priorThirdPartyAdapterChecks']==9,'EXECUTED_ORIGINAL_COMPONENT_CHECKS_REQUIRED')
 for name in ['thirdPartyCredentialsCompatibility','inspectionPointNameCompatibility','businessResultCompatibility','requestErrorCompatibility','workflowRequestCompatibility','approvalRetryCompatibility']:need(bool(receipt[name]),'ALL_PRIOR_ADAPTERS_REQUIRED')
 generated={};before={};active={}
 for row in receipt['files']:
  name=PREFIX+row['path'];source=front/'dist'/row['path'];need(source.resolve(strict=True).is_relative_to(front/'dist') and not source.is_symlink() and source.stat().st_size==row['bytes'] and sha(source)==row['sha256'],'COMPILED_ASSET_PIN')
  active[name]={'bytes':row['bytes'],'sha256':row['sha256']}
  if name in payload['files']:
   need(sha(app/name)==payload['files'][name]['sha256'],'INSTALLED_ASSET_DRIFT')
   if row['sha256']==payload['files'][name]['sha256']:continue
   before[name]=payload['files'][name]
  else:need(not (app/name).exists(),'UNTRACKED_NEW_TARGET_PRESENT')
  generated[name]=source.read_bytes()
 need(len(active)==receipt['fileCount'] and sum(x['bytes'] for x in active.values())==receipt['bytes'],'COMPLETE_FRONTEND_TOTALS')
 updated=copy.deepcopy(payload);updated['files']={k:v for k,v in payload['files'].items() if not k.startswith(PREFIX)};updated['files'].update(active)
 need({k:v for k,v in payload['files'].items() if not k.startswith(PREFIX)}=={k:v for k,v in updated['files'].items() if not k.startswith(PREFIX)},'NON_PC_PAYLOAD_UNCHANGED')
 updated['frontendUpdate']={'scope':['security_pc'],'previousPayloadManifestSHA256':old['payloadManifestSHA256'],'buildReceiptSHA256':sha(front/'receipt.json'),'trainingAssessmentCompatibility':receipt['trainingAssessmentCompatibility'],'thirdPartyCredentialsCompatibility':receipt['thirdPartyCredentialsCompatibility'],'publicDeployed':False}
 generated['payload-manifest.json']=encode(updated);release=copy.deepcopy(old);release.update(payloadManifestSHA256=digest(generated['payload-manifest.json']),frontendRevision='original-exam-time-identity-20261028',publicAccepted=False);generated['release-manifest.json']=encode(release)
 need(release['controllerFiles']==old['controllerFiles'],'CONTROLLER_PIN_UNCHANGED')
 cmd=(app/'Start_Callback_Candidate.cmd').read_bytes();need(cmd.count(BASE.encode())==1,'EXACT_CURRENT_STARTER');generated['Start_Callback_Candidate.cmd']=cmd.replace(BASE.encode(),digest(generated['release-manifest.json']).encode(),1)
 need(len(generated)<=1000 and sum(map(len,generated.values()))<=32*1024*1024,'BOUNDED_SPARSE_PC_UPDATE')
 plan={'schema':'zhumadian.public-test-update.v1','updateId':'20261028-exam-time-identity-local','targetApplication':app.as_posix(),'gatewayPort':18891,'releaseId':old['releaseId'],'acceptedOldReleases':{BASE:{'controllerFiles':old['controllerFiles'],'payloadManifestSHA256':old['payloadManifestSHA256']}},'basePayloadManifestSHA256':old['payloadManifestSHA256'],'newPayloadManifestSHA256':release['payloadManifestSHA256'],'newReleaseSHA256':digest(generated['release-manifest.json']),'oldPayloadFiles':before,'legacyEntrySHA256':{'Start_Callback_Candidate.cmd':[sha(app/'Start_Callback_Candidate.cmd')]},'removedFrontendFiles':{},'callbackOverlay':'payload/callback-overlay/20261026-password-identity/manifest.json','callbackOverlaySHA256':old['missingAuthOverlayManifestSHA256'],'iisProxySHA256':old['controllerFiles'].get('deploy/iis_original/App_Code/XnbyReferenceProxy.cs'),'databaseUploadsCredentialsGISOrDependenciesIncluded':False,'files':{name:{'bytes':len(raw),'SHA256':digest(raw)} for name,raw in generated.items()}}
 out.mkdir(parents=True)
 for name,raw in generated.items():p=out/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 (out/'update-manifest.json').write_bytes(encode(plan))
 spec=importlib.util.spec_from_file_location('own_existing_pinned_updater',app/'tools/original_public_test_update.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 loaded,base,changes=module.load_bundle(app,out,sha(out/'update-manifest.json'),expected_target=app,expected_port=18891)
 need(base==BASE and loaded['newReleaseSHA256']==plan['newReleaseSHA256'] and len(changes)==len(generated),'ACTUAL_INSTALLED_UPDATER_PREFLIGHT')
 report={'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':sha(out/'update-manifest.json'),'oldReleaseSHA256':BASE,'newReleaseSHA256':plan['newReleaseSHA256'],'files':len(generated),'payloadBytes':sum(map(len,generated.values())),'all835FrontendAssetsVerified':len(active)==835,'allNonPCPayloadAndControllerPinsUnchanged':True,'existingUpdaterComposedPayloadPreflightPassed':True,'runtimeInstalledOrRestarted':False,'publicDeployed':False,'fullCloneReady':False}
 (out/'build-result.json').write_bytes(encode(report));return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['application','frontend','output']:p.add_argument('--'+key,required=True)
 a=p.parse_args();print(json.dumps(build(a.application,a.frontend,a.output)))
