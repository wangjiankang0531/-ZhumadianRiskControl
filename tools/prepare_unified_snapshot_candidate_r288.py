from pathlib import Path
import ast,copy,hashlib,json,os
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
W=R/'work/user_feedback_20261031';OLD=W/'r38-unified-original-mappers-r1/bundle';O=W/'r38-unified-original-mappers-r2'
D=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2';D1=R/'Document/Deployment/public_test_unified_mappers_r38_20261103'
source=T/'original_public_test_update_r38_mapper_preflight_r286.py'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert not O.exists()and not D.exists();assert J(R/'Document/Deployment/original_mapper_install_preflight_r285_20261103/verified-cases-r287.json')['candidateSourceSHA256']==sha(source)
O.mkdir();D.mkdir();bundle=O/'bundle';plan=copy.deepcopy(J(OLD/'update-manifest.json'));release=J(OLD/'payload/release-manifest.json');payload=J(OLD/'payload/payload-manifest.json');updater='tools/original_public_test_update.py'
release['controllerFiles'][updater]=sha(source)
if updater in payload['files']:payload['files'][updater]={'bytes':source.stat().st_size,'sha256':sha(source)}
qraw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(qraw).hexdigest();raw=enc(release)
plan.update(updateId=plan['updateId']+'-r2',newPayloadManifestSHA256=hashlib.sha256(qraw).hexdigest(),newReleaseSHA256=hashlib.sha256(raw).hexdigest())
replacements={updater:source.read_bytes(),'payload-manifest.json':qraw,'release-manifest.json':raw}
for name,pin in plan['files'].items():
    out=bundle/'payload'/name;out.parent.mkdir(parents=True,exist_ok=True)
    if name in replacements:out.write_bytes(replacements[name]);plan['files'][name]={'bytes':out.stat().st_size,'SHA256':sha(out)}
    else:
        src=OLD/'payload'/name;assert src.stat().st_size==pin['bytes']and sha(src)==pin['SHA256'];os.link(src,out)
(bundle/'update-manifest.json').write_bytes(enc(plan))
report={'prepared':True,'previousUnpublishedCandidateSuperseded':True,'updaterSourceSHA256':sha(source),
 'updateManifestSHA256':sha(bundle/'update-manifest.json'),'oldReleaseSHA256':next(iter(plan['acceptedOldReleases'])),
 'newReleaseSHA256':plan['newReleaseSHA256'],'writes':len(plan['files']),'removals':len(plan['removedFrontendFiles']),
 'onlyUpdaterAndReleaseMetadataChangedFromPreviousCandidate':True,
 'sameSnapshotMapperAndPoolPreflightNowInsideInstallTransaction':True,
 'publicR37AndR36Untouched':True,'publicUploadedOrInstalled':False,
 'fullProgramAndFileTransactionsPending':True}
(D/'bundle-preparation-r288.json').write_bytes(enc(report));(O/'preparation.json').write_bytes(enc(report))
withdraw={'withdrawnForNewDeployments':True,'reason':'Mapper snapshot must be validated inside actual installation preflight; wrapper-only validation is insufficient when configuration changes.',
 'replacementCandidateDirectory':str(D),'previousManifestSHA256':sha(D1/'delivery-manifest.json'),
 'previousPackageWasNeverUploadedOrDeployed':True,'existingR37ApprovalAndPayloadUnaffected':True}
(D1/'withdrawn-status-r285.json').write_bytes(enc(withdraw))
for oldname,newname in [('verify_unified_full_program_r275.py','verify_unified_full_program_r288.py'),
                         ('verify_unified_composition_recovery_r276.py','verify_unified_composition_recovery_r288.py')]:
    s=(T/oldname).read_text(encoding='utf-8')
    s=s.replace('r38-unified-original-mappers-r1','r38-unified-original-mappers-r2').replace('public_test_unified_mappers_r38_20261103','public_test_unified_mappers_r38_20261103_r2')
    s=s.replace('r38-unified-full-preflight-r275','r38-unified-full-preflight-r288').replace('original_public_test_update_r38_unified_20261103.py','original_public_test_update_r38_mapper_preflight_r286.py')
    if oldname.startswith('verify_unified_full_program'):
        anchor="capacity=m.candidate_runtime_pool_preflight(app,bundle,loaded);assert capacity['budget']['mysqlMaxConnections']==24 and len(capacity['budget']['datasources'])==3"
        assert s.count(anchor)==1;s=s.replace(anchor,anchor+";assert capacity['originalMapperPreflight']['passed']and capacity['originalMapperPreflight']['defaultWillApply']")
        s=s.replace("'publicDeliveryWrapperNotPreparedYet':True","'publicDeliveryWrapperNotPreparedYet':True,'internalSameSnapshotMapperGatePassed':True")
    ast.parse(s);dst=V/newname;assert not dst.exists();dst.write_text(s,encoding='utf-8')
print(json.dumps(report))
