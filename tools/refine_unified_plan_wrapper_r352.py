from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/public_test_unified_plan_r39_20261103'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
wrapper=D/'delivery/deploy_unified_plan_r39.py';builder=V/'build_unified_plan_delivery_r351.py'
assert sha(wrapper)=='c8d40281ffa060b224b0e07650c1de1f7cc1ab3b30858128a22ef1281b10298a'
assert not(D/'wrapper-refinement-r352.json').exists()
old="""    m.apply_update(APP,stage,base['manifestSHA256'])
    try:verify_static_gateway_and_iis(m,root,checked)
    except BaseException:
        latest=m.read(regular(APP/'UserData/OriginalPublicUpdates/latest.json'));recovery_guard(latest)
        need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_POSTCHECK_ROLLBACK')
        m.rollback_latest(APP)
        raise"""
new="""    m.apply_update(APP,stage,base['manifestSHA256'])
    latest_path=regular(APP/'UserData/OriginalPublicUpdates/latest.json')
    applied_record_raw=latest_path.read_bytes();applied_record=json.loads(applied_record_raw)
    recovery_guard(applied_record)
    need(applied_record.get('ready')is True and applied_record['updateId']==base['updateId']and applied_record['oldReleaseSHA256']==old,'EXACT_THIS_APPLY_RECORD_REQUIRED')
    applied_record_sha=hashlib.sha256(applied_record_raw).hexdigest()
    try:verify_static_gateway_and_iis(m,root,checked)
    except BaseException:
        need(sha(latest_path)==applied_record_sha,'POSTCHECK_UPDATE_RECORD_DRIFT_REFUSE_ROLLBACK')
        latest=m.read(latest_path);recovery_guard(latest)
        need(latest['updateId']==base['updateId']and latest['oldReleaseSHA256']==old,'ONLY_THIS_SELECTED_BASE_POSTCHECK_ROLLBACK')
        need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_POSTCHECK_ROLLBACK')
        m.rollback_latest(APP)
        raise"""
before_wrapper=wrapper.read_bytes();before_builder=builder.read_bytes()
text=wrapper.read_text(encoding='utf-8');build=builder.read_text(encoding='utf-8')
assert text.count(old)==build.count(old)==1
text=text.replace(old,new,1);build=build.replace(old,new,1);ast.parse(text);ast.parse(build)
(D/'unpublished-wrapper-draft-r351.py').write_bytes(before_wrapper);(D/'unpublished-builder-draft-r351.py').write_bytes(before_builder)
(D/'unpublished-transport-manifest-r351.json').write_bytes((D/'delivery-manifest.json').read_bytes())
wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode());builder.write_text(build,encoding='utf-8')
manifest=json.loads((D/'delivery-manifest.json').read_bytes());manifest['files'][wrapper.name]={'bytes':wrapper.stat().st_size,'sha256':sha(wrapper)}
manifest['postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord']=True
(D/'delivery-manifest.json').write_bytes(enc(manifest));(D/'delivery/delivery-manifest.json').write_bytes(enc(manifest))
proof={'refinedBeforeAnyApprovalOrUpload':True,'reason':'Postcheck rollback must use this selected variant and unchanged record captured immediately after this apply, not any other otherwise valid R39 variant record.',
 'priorUnpublishedWrapperSHA256':hashlib.sha256(before_wrapper).hexdigest(),'finalWrapperSHA256':sha(wrapper),'finalBuilderSHA256':sha(builder),
 'manifestSHA256':sha(D/'delivery-manifest.json'),'transportFiles':len(list((D/'delivery').iterdir())),'transportBytes':sum(p.stat().st_size for p in(D/'delivery').iterdir()),
 'candidateRuntimeAndArchiveUnchanged':True,'testsStillPending':True,'publicUploadedOrDeployed':False}
(D/'wrapper-refinement-r352.json').write_bytes(enc(proof));print(json.dumps(proof))
