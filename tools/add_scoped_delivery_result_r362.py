from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/public_test_unified_plan_r39_20261103'
wrapper=D/'delivery/deploy_unified_plan_r39.py';builder=V/'build_unified_plan_delivery_r351.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert sha(wrapper)=='fe9a5a123f564d45427e61663fcf32ac3f0b9726af750cfde1a2d2422e73822f'
assert not(D/'scoped-result-wrapper-r362.json').exists()
helper=r'''
def write_scoped_result(root,phase,base,old,budget=None):
    output=regular(root/'r39-scoped-result.json');schema='xnby.r39.scoped-deployment-result.v1'
    if output.exists():
        need(output.stat().st_size<=64*1024,'BOUNDED_OWN_SCOPED_RESULT_REQUIRED')
        previous=json.loads(output.read_bytes())
        need(previous.get('schema')==schema and previous.get('newReleaseSHA256')==NEW,'FOREIGN_SCOPED_RESULT_REFUSE_OVERWRITE')
    result={'schema':schema,'phase':phase,'selectedBase':base['label'],'updateId':base['updateId'],
        'oldReleaseSHA256':old,'newReleaseSHA256':NEW,'updaterSHA256':UPDATER_SHA,
        'serverLocalGatewayAndIISTLSStaticPassed':phase=='deploy-complete','externalHTTPSAndLoggedInTimingAccepted':False,
        'credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded':False,'fullCloneReady':False}
    if budget is not None:
        result['mysqlMaxConnections']=budget['budget']['mysqlMaxConnections']
        result['datasourceCount']=len(budget['budget']['datasources'])
    raw=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode();need(len(raw)<=4096,'BOUNDED_SCOPED_RESULT')
    temporary=regular(root/('r39-result-'+uuid.uuid4().hex+'.tmp'))
    with temporary.open('xb')as f:f.write(raw)
    os.replace(temporary,output)

'''
def amend(text):
    anchor='def main():\n';assert text.count(anchor)==1;text=text.replace(anchor,helper+anchor,1)
    a="    if mode==['--check-only']:\n        print('R39_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return"
    b="    if mode==['--check-only']:\n        write_scoped_result(root,'preflight-passed',base,old,candidate_pool)\n        print('R39_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return"
    assert text.count(a)==1;text=text.replace(a,b,1)
    a="    print('R39_APPLY_COMPLETED_EXTERNAL_HTTPS_AND_USER_LAYOUT_PENDING',flush=True)"
    b="    write_scoped_result(root,'deploy-complete',base,old,candidate_pool)\n"+a
    assert text.count(a)==1;text=text.replace(a,b,1);ast.parse(text);return text
before=sha(wrapper);text=amend(wrapper.read_text(encoding='utf-8'));build=amend(builder.read_text(encoding='utf-8'))
old_manifest= (D/'delivery-manifest.json').read_bytes();(D/'unpublished-transport-manifest-r352.json').write_bytes(old_manifest)
wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode());builder.write_text(build,encoding='utf-8')
manifest=json.loads(old_manifest);manifest['files'][wrapper.name]={'bytes':wrapper.stat().st_size,'sha256':sha(wrapper)}
manifest['limitedResultReadbackFile']='r39-scoped-result.json';manifest['limitedResultContainsNoCredentialsBusinessRowsOrRuntimeUUID']=True
anchor="manifest['postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord']=True"
build=builder.read_text(encoding='utf-8');assert build.count(anchor)==1
build=build.replace(anchor,anchor+"\nmanifest['limitedResultReadbackFile']='r39-scoped-result.json';manifest['limitedResultContainsNoCredentialsBusinessRowsOrRuntimeUUID']=True",1);ast.parse(build);builder.write_text(build,encoding='utf-8')
(D/'delivery-manifest.json').write_bytes(enc(manifest));(D/'delivery/delivery-manifest.json').write_bytes(enc(manifest))
proof={'preparedBeforeUpload':True,'priorWrapperSHA256':before,'wrapperSHA256':sha(wrapper),'builderSHA256':sha(builder),'manifestSHA256':sha(D/'delivery-manifest.json'),
 'transportFiles':len(list((D/'delivery').iterdir())),'transportBytes':sum(p.stat().st_size for p in(D/'delivery').iterdir()),
 'limitedPreflightAndDeployResultAdded':True,'candidateRuntimeArchiveAndStaticPostcheckOrRollbackSemanticsChanged':False,'finalVerificationPending':True,'publicUploadedOrDeployed':False}
(D/'scoped-result-wrapper-r362.json').write_bytes(enc(proof));print(json.dumps(proof))
