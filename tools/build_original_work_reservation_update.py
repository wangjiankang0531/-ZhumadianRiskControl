"""Prepare an exact local service-class update. Never install, stop or launch."""
from pathlib import Path
import argparse, copy, datetime, hashlib, json

BASE_RELEASE='3f1ee528b0e2107da4aead4359786fdaf2d87cc7b43214d0822eca9a46c344cd'
UPDATER_SHA='0a5307d620876a17afcaf7418f1d10dfdf66062d24794db16e6f52a8a646754a'
CLASS='payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
REVISION='original-end-time-sync-v1'
OVERLAY='payload/callback-overlay/20261026-password-identity/manifest.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encode(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def need(ok,code):
    if not ok:raise ValueError(code)

def adapt_updater(raw):
    need(digest(raw)==UPDATER_SHA,'PINNED_INSTALLED_UPDATER_REQUIRED')
    text=raw.decode('utf-8');newline='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n')
    anchor="            'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class',\n"
    need(text.count(anchor)==1,'EXACT_OLD_CLASS_WHITELIST_REQUIRED')
    text=text.replace(anchor,anchor+"            '"+CLASS+"',\n",1)
    anchor='    # Verify the composed installation before downtime, including retained dependencies.\n'
    need(text.count(anchor)==1,'EXACT_PRECHECK_BOUNDARY_REQUIRED')
    guard=("    reservation_class = '"+CLASS+"'\n"
        "    if reservation_class in plan['files']:\n"
        "        require(release.get('reservationEndTimeCandidate') == '"+REVISION+"',\n"
        "                'EXPLICIT_RESERVATION_END_TIME_CANDIDATE_REQUIRED')\n"
        "        row = plan['files'][reservation_class]\n"
        "        require(payload['files'].get(reservation_class) == {'bytes': row['bytes'], 'sha256': row['SHA256']},\n"
        "                'RESERVATION_END_TIME_CLASS_PAYLOAD_PIN_REQUIRED')\n")
    return text.replace(anchor,guard+anchor,1).replace('\n',newline).encode('utf-8')

def build(application,evidence,output):
    app=Path(application).resolve(strict=True);ev=Path(evidence).resolve(strict=True);out=Path(output).absolute()
    need(app==Path('D:/Zqa20261025/Application') and not out.exists() and not out.is_relative_to(app),'EXACT_LOCAL_APP_AND_FRESH_SEPARATE_OUTPUT_REQUIRED')
    need(sha(app/'release-manifest.json')==BASE_RELEASE,'EXACT_INSTALLED_LOCAL_RELEASE_REQUIRED')
    report=read(ev/'result.json');plan=read(ev/'prepared.private.json')
    need(report['originalCases']==8 and report['candidateCases']==16 and report['executedCandidateBytesVerified'] and report['exactSingleAssignmentSourceDifferenceVerified'] and not report['runtimeInstalledOrRestarted'],'PASSING_EXECUTED_METHOD_EVIDENCE_REQUIRED')
    for p,pin in plan['sourcePins'].items():need(sha(p)==pin,'EXECUTED_VERIFIER_SOURCE_DRIFT')
    cls=ev/'candidate-classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
    need(sha(cls)==report['candidateClassSHA256'] and cls.stat().st_size<65536,'EXACT_EXECUTED_CLASS_REQUIRED')
    old=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json')
    need(sha(app/'payload-manifest.json')==old['payloadManifestSHA256'] and old['releaseId']==payload['releaseId'],'PINNED_PAYLOAD_BASE_REQUIRED')
    need(CLASS not in payload['files'] and not (app/CLASS).exists(),'NEW_SERVICE_OVERRIDE_REQUIRED')
    need(sha(app/OVERLAY)==old['missingAuthOverlayManifestSHA256'],'UNCHANGED_CALLBACK_OVERLAY_REQUIRED')
    generated={CLASS:cls.read_bytes(),'tools/original_public_test_update.py':adapt_updater((app/'tools/original_public_test_update.py').read_bytes())}
    new_payload=copy.deepcopy(payload);new_payload['files'][CLASS]={'bytes':len(generated[CLASS]),'sha256':digest(generated[CLASS])}
    generated['payload-manifest.json']=encode(new_payload)
    new=copy.deepcopy(old);new.update(payloadManifestSHA256=digest(generated['payload-manifest.json']),reservationEndTimeCandidate=REVISION,publicAccepted=False)
    new['controllerFiles']['tools/original_public_test_update.py']=digest(generated['tools/original_public_test_update.py'])
    generated['release-manifest.json']=encode(new)
    generated['Start_Callback_Candidate.cmd']=('@echo off\r\nsetlocal\r\n"%~dp0runtime\\python\\python.exe" -I -B "%~dp0tools\\serve_original_server_release.py" --application "%~dp0." --release-manifest-sha256 '+digest(generated['release-manifest.json'])+' --gateway-port 18891 --callback-overlay "%~dp0'+OVERLAY.replace('/','\\')+'" --callback-overlay-sha256 '+old['missingAuthOverlayManifestSHA256']+'\r\npause\r\n').encode('ascii')
    need(len(generated)==5 and sum(map(len,generated.values()))<4*1024*1024,'EXACT_SMALL_FIVE_FILE_UPDATE_REQUIRED')
    update={'schema':'zhumadian.public-test-update.v1','updateId':'20261028-reservation-end-time-local','targetApplication':app.as_posix(),'gatewayPort':18891,'releaseId':old['releaseId'],'acceptedOldReleases':{BASE_RELEASE:{'controllerFiles':old['controllerFiles'],'payloadManifestSHA256':old['payloadManifestSHA256']}},'basePayloadManifestSHA256':old['payloadManifestSHA256'],'newPayloadManifestSHA256':new['payloadManifestSHA256'],'newReleaseSHA256':digest(generated['release-manifest.json']),'oldPayloadFiles':{},'legacyEntrySHA256':{'Start_Callback_Candidate.cmd':[sha(app/'Start_Callback_Candidate.cmd')]},'removedFrontendFiles':{},'callbackOverlay':OVERLAY,'callbackOverlaySHA256':old['missingAuthOverlayManifestSHA256'],'iisProxySHA256':old['controllerFiles'].get('deploy/iis_original/App_Code/XnbyReferenceProxy.cs'),'databaseUploadsCredentialsGISOrDependenciesIncluded':False,'files':{name:{'bytes':len(raw),'SHA256':digest(raw)} for name,raw in generated.items()}}
    out.mkdir(parents=True)
    for name,raw in generated.items():p=out/'payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (out/'update-manifest.json').write_bytes(encode(update))
    receipt={'at':datetime.datetime.now().astimezone().isoformat(),'files':5,'payloadBytes':sum(map(len,generated.values())),'manifestSHA256':sha(out/'update-manifest.json'),'oldReleaseSHA256':BASE_RELEASE,'newReleaseSHA256':update['newReleaseSHA256'],'executedClassSHA256':sha(cls),'installed':False,'publicDeployed':False,'databaseOrUserDataIncluded':False,'sameVersionRebuildRequiredIfBaseChanges':True}
    (out/'build-receipt.json').write_bytes(encode(receipt));return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('application','evidence','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.application,a.evidence,a.output)))
