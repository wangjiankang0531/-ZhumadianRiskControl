"""Compose pinned frontend and two tested service overrides for local B/S QA.

Read-only against installed code/data; emits a bounded independent update only.
No stop/start, installation, IIS change, database copy or public deployment.
"""
from pathlib import Path
import argparse,copy,datetime,hashlib,json

BASE_RELEASE='3f1ee528b0e2107da4aead4359786fdaf2d87cc7b43214d0822eca9a46c344cd'
UPDATER_SHA='0a5307d620876a17afcaf7418f1d10dfdf66062d24794db16e6f52a8a646754a'
RESERVATION='payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
THIRD='payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class'
OBSERVER='payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class'
REVISION='original-end-time-atomic-v2';THIRD_REVISION='original-credentials-atomic-v2';OBSERVER_REVISION='work-services-existing-singletons-v1'
PREFIX='frontend/security_pc/'
OVERRIDES={RESERVATION:('reservationEndTimeCandidate',REVISION,'RESERVATION_END_TIME'),THIRD:('thirdPartyCredentialsCandidate',THIRD_REVISION,'THIRD_PARTY_CREDENTIALS'),OBSERVER:('workTransactionObservationCandidate',OBSERVER_REVISION,'WORK_TRANSACTION_OBSERVER')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def need(ok,message):
    if not ok:raise ValueError(message)

def adapt_updater(raw):
    need(digest(raw)==UPDATER_SHA,'PINNED_INSTALLED_UPDATER_REQUIRED')
    newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8').replace('\r\n','\n')
    anchor="            'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class',\n"
    need(text.count(anchor)==1,'EXACT_PRIOR_POINT_CLASS_WHITELIST_REQUIRED')
    text=text.replace(anchor,anchor+''.join("            '"+name+"',\n" for name in (RESERVATION,THIRD)),1)
    guard=''
    for i,(name,(field,revision,code)) in enumerate(OVERRIDES.items()):
        var='atomic_class_'+str(i)
        guard+=("    "+var+" = '"+name+"'\n"
                "    if "+var+" in plan['files']:\n"
                "        require(release.get('"+field+"') == '"+revision+"',\n"
                "                'EXPLICIT_"+code+"_CANDIDATE_REQUIRED')\n"
                "        row = plan['files']["+var+"]\n"
                "        require(payload['files'].get("+var+") == {'bytes': row['bytes'], 'sha256': row['SHA256']},\n"
                "                '"+code+"_CLASS_PAYLOAD_PIN_REQUIRED')\n")
    anchor='    # Verify the composed installation before downtime, including retained dependencies.\n'
    need(text.count(anchor)==1,'EXACT_RETAINED_PAYLOAD_VERIFICATION_BOUNDARY_REQUIRED')
    return text.replace(anchor,guard+anchor,1).replace('\n',newline).encode('utf-8')

def build(application,frontend,observer,output):
    app=Path(application).resolve(strict=True);front=Path(frontend).resolve(strict=True);observe=Path(observer).resolve(strict=True);out=Path(output).absolute();r=Path('D:/Project/Zhumadian')
    need(app==Path('D:/Zqa20261025/Application') and not out.exists() and not out.is_relative_to(app),'EXACT_APP_AND_FRESH_DISJOINT_OUTPUT_REQUIRED')
    need(sha(app/'release-manifest.json')==BASE_RELEASE,'EXACT_CURRENT_BASE_REQUIRED')
    import sys
    sys.path.insert(0,str(r/'Application/tools'))
    from run_original_inventory_ownership_probe import state
    current=state();need(current['controllerPID']==35292 and Path(current['run']).name=='j41','EXACT_CURRENT_OWN_RUNTIME_REQUIRED')
    old=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json');need(sha(app/'payload-manifest.json')==old['payloadManifestSHA256'],'PAYLOAD_BASE_PIN_REQUIRED')
    frontend_receipt=read(front/'receipt.json');front_phase=read(front.parent/'result.json');observer_report=read(observe/'result.json');third_report=read(r/'Document/Deployment/third_party_credentials_20261028/v2-result.private.json')
    need(frontend_receipt['kind']=='security_pc' and frontend_receipt['exitCode']==0 and frontend_receipt['sourceFilesUnchanged'] and frontend_receipt['originalReferenceUnchanged'] and frontend_receipt['thirdPartyCredentialsCompatibility']['sourceFileRestored'] and front_phase['componentControlCases']==16 and front_phase['adapterChecks']==9,'EXECUTED_ORIGINAL_FRONTEND_REQUIRED')
    for key in ('businessResultCompatibility','inspectionPointNameCompatibility','approvalRetryCompatibility','workflowRequestCompatibility'):need(bool(frontend_receipt[key]),'PRIOR_ADAPTER_MUST_REMAIN')
    for record in (read(front.parent/'prepared.private.json'),read(observe/'prepared.private.json')):
        for p,pin in record['sourcePins'].items():need(sha(p)==pin,'EXECUTED_BUILD_OR_OBSERVER_SOURCE_CHANGED')
    need(observer_report['originalContexts']==2 and observer_report['additionalContexts']==4 and observer_report['actualCandidateClassBytesVerified'],'EXECUTED_METADATA_OBSERVER_REQUIRED')
    need(third_report['memory']['candidateCases']==18 and third_report['SQL']['candidateSQLCases']==22 and third_report['SQL']['candidateAnnotationDrivenSaveAndEditRollbackVerified'],'EXECUTED_THIRD_PARTY_ATOMIC_EVIDENCE_REQUIRED')
    for name,pin in third_report['sourceFiles'].items():need(sha(r/'Application'/name)==pin['SHA256'],'TESTED_THIRD_PARTY_CANONICAL_SOURCE_CHANGED')
    reservation=r/'work/work_reservation_end_time_update_20261028_v2';need(sha(reservation/'update-manifest.json')=='338b1f52125cf720e808e69612da2763bed5971283129640ab885e610b842adb','EXACT_RESERVATION_V2_BUNDLE_REQUIRED')
    pins={RESERVATION:'4f569208da945cc8c7042f539c11c24dc19f382e507758c93dac63ae69961af2',THIRD:'1bac35eef2c07fc8cfb44af14260730bb24b0b3bed09f89f097b8b302850f67b',OBSERVER:observer_report['observerClassSHA256']}
    sources={RESERVATION:reservation/'payload'/RESERVATION,THIRD:r/'work/third_party_credentials_candidate_20261028/candidate-classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class',OBSERVER:observe/'classes/xnby/replica/OriginalTransactionObservation.class'}
    generated={};before={};active={};unchanged=0
    for row in frontend_receipt['files']:
        name=PREFIX+row['path'];p=front/'dist'/row['path'];need(not p.is_symlink() and p.resolve(strict=True).is_relative_to(front/'dist') and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'EXACT_BUILT_FRONTEND_FILE_REQUIRED');active[name]={'bytes':row['bytes'],'sha256':row['sha256']}
        if name in payload['files']:
            need(sha(app/name)==payload['files'][name]['sha256'],'CURRENT_FRONTEND_SOURCE_DRIFT')
            if row['sha256']==payload['files'][name]['sha256']:unchanged+=1;continue
            before[name]=payload['files'][name]
        else:need(not (app/name).exists(),'UNTRACKED_FRONTEND_TARGET_PRESENT')
        generated[name]=p.read_bytes()
    need(len(active)==frontend_receipt['fileCount'] and sum(p['bytes'] for p in active.values())==frontend_receipt['bytes'],'FULL_FRONTEND_RECEIPT_REQUIRED')
    for name,p in sources.items():
        need(sha(p)==pins[name],'EXACT_EXECUTED_CLASS_BYTES_REQUIRED');generated[name]=p.read_bytes()
        if name in payload['files']:need(sha(app/name)==payload['files'][name]['sha256'],'PRIOR_OBSERVER_CHANGED');before[name]=payload['files'][name]
        else:need(not (app/name).exists(),'NEW_SERVICE_CLASS_ALREADY_PRESENT')
    generated['tools/original_public_test_update.py']=adapt_updater((app/'tools/original_public_test_update.py').read_bytes())
    new_payload=copy.deepcopy(payload)
    for name in list(new_payload['files']):
        if name.startswith(PREFIX):del new_payload['files'][name]
    new_payload['files'].update(active)
    for name in sources:new_payload['files'][name]={'bytes':len(generated[name]),'sha256':pins[name]}
    new_payload['frontendUpdate']={'scope':['security_pc'],'previousPayloadManifestSHA256':old['payloadManifestSHA256'],'buildReceiptSHA256':sha(front/'receipt.json'),'inspectionPointNameCompatibility':frontend_receipt['inspectionPointNameCompatibility'],'thirdPartyCredentialsCompatibility':frontend_receipt['thirdPartyCredentialsCompatibility'],'publicDeployed':False}
    generated['payload-manifest.json']=encode(new_payload);release=copy.deepcopy(old)
    release.update(payloadManifestSHA256=digest(generated['payload-manifest.json']),frontendRevision='original-third-party-certificate-name-20261028',publicAccepted=False)
    for _,(key,value,_) in OVERRIDES.items():release[key]=value
    release['controllerFiles']['tools/original_public_test_update.py']=digest(generated['tools/original_public_test_update.py']);generated['release-manifest.json']=encode(release)
    starter=(app/'Start_Callback_Candidate.cmd').read_bytes();need(starter.count(BASE_RELEASE.encode())==1,'EXACT_CALLBACK_LAUNCHER_PIN_REQUIRED');generated['Start_Callback_Candidate.cmd']=starter.replace(BASE_RELEASE.encode(),digest(generated['release-manifest.json']).encode(),1)
    need(len(generated)<=1000 and sum(map(len,generated.values()))<=32*1024*1024,'SMALL_COMPOSED_UPDATE_REQUIRED')
    plan={'schema':'zhumadian.public-test-update.v1','updateId':'20261028-bs-atomic-local','targetApplication':app.as_posix(),'gatewayPort':18891,'releaseId':old['releaseId'],'acceptedOldReleases':{BASE_RELEASE:{'controllerFiles':old['controllerFiles'],'payloadManifestSHA256':old['payloadManifestSHA256']}},'basePayloadManifestSHA256':old['payloadManifestSHA256'],'newPayloadManifestSHA256':release['payloadManifestSHA256'],'newReleaseSHA256':digest(generated['release-manifest.json']),'oldPayloadFiles':before,'legacyEntrySHA256':{'Start_Callback_Candidate.cmd':[sha(app/'Start_Callback_Candidate.cmd')]},'removedFrontendFiles':{},'callbackOverlay':'payload/callback-overlay/20261026-password-identity/manifest.json','callbackOverlaySHA256':old['missingAuthOverlayManifestSHA256'],'iisProxySHA256':old['controllerFiles'].get('deploy/iis_original/App_Code/XnbyReferenceProxy.cs'),'databaseUploadsCredentialsGISOrDependenciesIncluded':False,'files':{name:{'bytes':len(raw),'SHA256':digest(raw)} for name,raw in generated.items()}}
    out.mkdir(parents=True)
    for name,raw in generated.items():p=out/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (out/'update-manifest.json').write_bytes(encode(plan))
    report={'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':sha(out/'update-manifest.json'),'newReleaseSHA256':plan['newReleaseSHA256'],'oldReleaseSHA256':BASE_RELEASE,'files':len(generated),'payloadBytes':sum(map(len,generated.values())),'activeFrontendFiles':len(active),'unchangedFrontendFiles':unchanged,'classSHA256':pins,'runtimeInstalled':False,'publicDeployed':False,'fullCloneReady':False}
    (out/'build-result.json').write_bytes(encode(report));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('application','frontend','observer','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.application,a.frontend,a.observer,a.output)))
