from pathlib import Path
import ast,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;T=R/'Application/tools'
C=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103';O=R/'work/r39-plan-runtime-unified-r1'
D=R/'Document/Deployment/public_test_unified_plan_r39_20261103';J=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
proof=J(C/'verified-lifecycle-stage-r350.json');assert proof['bothExactBaselinesPassed']and proof['r37CandidateNormalRoleActualCompiledUI21CasesPassed']
source=T/'original_public_test_update_r39_plan_runtime_r337.py';assert sha(source)==proof['candidateUpdaterSHA256']
assert not D.exists();D.mkdir();delivery=D/'delivery';delivery.mkdir()
bundles={label:O/label/'bundle'for label in ['r36','r37']};plans={label:J(root/'update-manifest.json')for label,root in bundles.items()}
p36,p37=plans.values();assert p36['files']==p37['files']and p36['removedFrontendFiles']==p37['removedFrontendFiles']
assert len(p36['files'])==187 and len(p36['removedFrontendFiles'])==177 and p36['newReleaseSHA256']==p37['newReleaseSHA256']
deny=(R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2/delivery/web.config').read_bytes()
archive=delivery/'Zhumadian_Unified_Plan_Runtime_20261103_R39.zip'
def zip_put(z,name,raw):
    item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,raw,compresslevel=9)
with zipfile.ZipFile(archive,'x')as z:
    zip_put(z,'web.config',deny)
    for label,root in bundles.items():zip_put(z,'variants/'+label+'/update-manifest.json',(root/'update-manifest.json').read_bytes())
    for name,pin in p36['files'].items():
        raw=(O/'shared/payload'/name).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256'];zip_put(z,'payload/'+name,raw)
old_updaters={'r36':'67545498b3f823e03394ecebdbf9aed12a64c719cca16b7a56a13abb66b49eca','r37':'52daac9f348be6622592920240794a1ba701d46683fa6b7c3e0cb34da47fcf62'}
bases={}
for label,plan in plans.items():
    assert len(plan['acceptedOldReleases'])==1
    old=next(iter(plan['acceptedOldReleases']));assert plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']==old_updaters[label]
    bases[old]={'label':label,'updateId':plan['updateId'],'manifestSHA256':sha(bundles[label]/'update-manifest.json'),'oldUpdaterSHA256':old_updaters[label]}
parent=R/'Document/Deployment/public_test_unified_mappers_r38_20261103_r2/delivery/deploy_unified_mappers_r38.py'
text=parent.read_text(encoding='utf-8');tree=ast.parse(text)
helpers=['need','sha','regular','validate_static_response','verify_static_gateway_and_iis','verify_candidate_mapper_configuration']
functions={n.name:ast.get_source_segment(text,n)for n in tree.body if isinstance(n,ast.FunctionDef)}
static=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='STATIC_EXPECTED')
header="from pathlib import Path,PurePosixPath\nimport hashlib,importlib.util,json,os,re,sys,uuid,zipfile\n"
constants={'APP':"Path('C:/inetpub/wwwroot/Zhumadian/Application')",'ARCHIVE_SHA':repr(sha(archive)),'ARCHIVE_NAME':repr(archive.name),
 'NEW':repr(p36['newReleaseSHA256']),'UPDATER_SHA':repr(sha(source)),'BASES':repr(bases),'STATIC_EXPECTED':repr(static)}
wrapper=header+'\n'.join(k+'='+value for k,value in constants.items())+'\n\n'
wrapper+='\n\n'.join(functions[name].replace('R38_','R39_')for name in helpers)+'\n\n'
wrapper+=r'''
def select_installed_base(app):
    installed=sha(regular(app/'release-manifest.json'))
    need(installed in BASES,'ONLY_EXACT_R36_OR_R37_BASE')
    base=BASES[installed]
    need(sha(regular(app/'tools/original_public_test_update.py'))==base['oldUpdaterSHA256'],'EXACT_SELECTED_BASE_UPDATER_REQUIRED')
    return installed,base

def recovery_guard(report):
    old=report.get('oldReleaseSHA256');need(old in BASES,'ONLY_THIS_OLD_RELEASE')
    base=BASES[old]
    need(report.get('updateId')==base['updateId'],'ONLY_THIS_UPDATE')
    need(report.get('newReleaseSHA256')==NEW,'ONLY_THIS_NEW_RELEASE')
    attempt=regular(Path(report['attempt']).absolute())
    need(attempt.parent==APP/'UserData/OriginalPublicUpdates'and re.fullmatch('[0-9a-f]{32}',attempt.name)is not None,'ONLY_OWN_BACKUP_PARENT_AND_ID')
    return base

def validate_archive(z,base):
    entries=z.infolist();names=[v.filename for v in entries]
    need(len(entries)<=512 and len(names)==len(set(names))and sum(v.file_size for v in entries)<=40*1024**2,'CLOSED_TRANSPORT_BOUNDS')
    need(all(not v.is_dir()and not(v.flag_bits&1)and ((v.external_attr>>16)&0o170000)!=0o120000 for v in entries),'REGULAR_UNENCRYPTED_MEMBERS')
    for info in entries:
        rel=PurePosixPath(info.filename)
        need(str(rel)==info.filename and not rel.is_absolute()and all(p not in ('.','..')and not re.search(r'[\\:\x00-\x1f]',p)and not p.endswith((' ','.'))for p in rel.parts),'EXACT_RELATIVE_MEMBER')
    plans={}
    for old,pin in BASES.items():
        member='variants/'+pin['label']+'/update-manifest.json';raw=z.read(member)
        need(hashlib.sha256(raw).hexdigest()==pin['manifestSHA256'],'FIXED_VARIANT_MANIFEST')
        plan=json.loads(raw)
        need(plan['updateId']==pin['updateId']and plan['newReleaseSHA256']==NEW and set(plan['acceptedOldReleases'])=={old},'FIXED_SINGLE_BASE_UPDATE_IDENTITY')
        need(plan['targetApplication']==APP.as_posix()and plan['gatewayPort']==18892,'EXACT_VARIANT_TARGET')
        plans[pin['label']]=plan
    selected=plans[base['label']]
    need(all(v['files']==selected['files']and v['removedFrontendFiles']==selected['removedFrontendFiles']for v in plans.values()),'SAME_FINAL_PAYLOAD_FOR_BOTH_BASES')
    need(len(selected['files'])==187 and len(selected['removedFrontendFiles'])==177,'EXACT_CHANGE_SET_SIZE')
    need(set(names)=={'web.config'}|{'variants/'+v['label']+'/update-manifest.json'for v in BASES.values()}|{'payload/'+v for v in selected['files']},'EXACT_CLOSED_MEMBERS')
    for name,pin in selected['files'].items():
        raw=z.read('payload/'+name)
        need(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'],'EXACT_ARCHIVED_PAYLOAD_PIN:'+name)
    return selected

def extract_selected_archive(archive,stage,base):
    with zipfile.ZipFile(archive)as z:
        plan=validate_archive(z,base)
        stage=regular(stage);need(not stage.exists(),'NEW_OWN_STAGE_REQUIRED');stage.mkdir(parents=True)
        # Deny HTTP access before creating any executable or manifest in this directory.
        for origin,destination in [('web.config','web.config'),('variants/'+base['label']+'/update-manifest.json','update-manifest.json')]+[('payload/'+n,'payload/'+n)for n in plan['files']]:
            dest=regular(stage.joinpath(*PurePosixPath(destination).parts));dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb')as target,z.open(origin)as stream:
                while True:
                    chunk=stream.read(65536)
                    if not chunk:break
                    target.write(chunk)
    need(sha(stage/'update-manifest.json')==base['manifestSHA256'],'EXACT_SELECTED_STAGE_MANIFEST')
    return plan


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

def main():
    sys.dont_write_bytecode=True
    need(os.name=='nt'and regular(APP).resolve(strict=True)==APP,'EXACT_SERVER')
    mode=sys.argv[1:];need(mode in ([],['--check-only'],['--recover-this-update']),'ONLY_SCOPED_MODES')
    root=regular(Path(__file__).absolute().parent)
    source=regular(root/'r39_update_runtime.py');need(sha(source)==UPDATER_SHA,'EXACT_FIXED_R39_UPDATE_RUNTIME')
    installed=regular(APP/'tools/original_public_test_update.py')
    need(sha(installed) in {UPDATER_SHA,*[v['oldUpdaterSHA256']for v in BASES.values()]},'EXACT_OLD_OR_THIS_UPDATE_UPDATER')
    sys.path.insert(0,str(APP/'tools'))
    spec=importlib.util.spec_from_file_location('fixed_r39_updater',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if mode==['--recover-this-update']:
        pending_path=regular(APP/'UserData/OriginalPublicUpdates/pending.json')
        pending=m.read(pending_path)if pending_path.exists()else{}
        if pending.get('updateId')in {v['updateId']for v in BASES.values()}and pending.get('failureType')and not pending.get('ready'):
            recovery_guard(pending);m.recover_pending(APP)
        else:
            latest=m.read(regular(APP/'UserData/OriginalPublicUpdates/latest.json'));recovery_guard(latest)
            need(sha(APP/'release-manifest.json')==NEW,'THIS_RELEASE_CURRENT_FOR_ROLLBACK');m.rollback_latest(APP)
        return
    old,base=select_installed_base(APP)
    archive=regular(root/ARCHIVE_NAME);need(sha(archive)==ARCHIVE_SHA,'EXACT_FIXED_ARCHIVE')
    stage=regular(APP/'UserData/OriginalPublicUpdates/staging'/uuid.uuid4().hex)
    extract_selected_archive(archive,stage,base)
    checked,old_checked,changes=m.load_bundle(APP,stage,base['manifestSHA256'])
    need(old_checked==old and checked['newReleaseSHA256']==NEW,'EXACT_SELECTED_BASE_RECHECK')
    candidate_pool=m.candidate_runtime_pool_preflight(APP,stage,checked);need(candidate_pool is not None,'EXACT_CANDIDATE_POOL_PREFLIGHT_REQUIRED')
    verify_candidate_mapper_configuration(APP)
    print('R39_SELECTED_'+base['label'].upper()+'_XML_AND_POOL_PREFLIGHT_PASSED_BEFORE_ANY_SHUTDOWN',flush=True)
    row=m.owned_ready(APP,old);m.health(APP,row)
    if mode==['--check-only']:
        write_scoped_result(root,'preflight-passed',base,old,candidate_pool)
        print('R39_PREFLIGHT_PASSED_EXACT_BASE_RUNTIME_AND_CLOSED_FILES_NO_SERVICE_CHANGED',flush=True);return
    write_scoped_result(root,'deploy-started',base,old,candidate_pool)
    m.apply_update(APP,stage,base['manifestSHA256'])
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
        write_scoped_result(root,'postcheck-failed-rolled-back',base,old,candidate_pool)
        raise
    write_scoped_result(root,'deploy-complete',base,old,candidate_pool)
    print('R39_APPLY_COMPLETED_EXTERNAL_HTTPS_AND_USER_LAYOUT_PENDING',flush=True)
if __name__=='__main__':main()
'''
ast.parse(wrapper);(delivery/'deploy_unified_plan_r39.py').write_bytes(wrapper.replace('\r\n','\n').replace('\n','\r\n').encode())
(delivery/'r39_update_runtime.py').write_bytes(source.read_bytes());(delivery/'web.config').write_bytes(deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
    (delivery/(label+'_Unified_Plan_R39.cmd')).write_bytes(('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_unified_plan_r39.py" '+flag+'\r\n').encode('ascii'))
stage_prefix='C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/'
maxpath=max(len(stage_prefix+'payload/'+name)for name in p36['files']);assert maxpath<240
manifest={'revision':'R39-unified-plan-runtime-original-mappers-and-static-performance','targetFTP':'/Zhumadian/Zhumadian_Unified_Plan_Runtime_20261103_R39/',
 'targetApplication':'C:/inetpub/wwwroot/Zhumadian/Application','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())},
 'acceptedExactBases':bases,'eachExtractedBundleAcceptsOneExactBase':True,'bothVariantsUseOneSharedFinalPayload':True,
 'newReleaseSHA256':p36['newReleaseSHA256'],'newPayloadManifestSHA256':p36['newPayloadManifestSHA256'],'newUpdaterSHA256':sha(source),
 'writes':187,'removedFiles':177,'oldReadinessReports':11,'newOriginalReadinessReports':11,'additionalPlanRuntimeByteCheck':True,'newDeclaredControlFiles':22,
 'sameFinalUpdaterActualApplyAndRollbackBothBasesPassed':True,'actualSixComponentControllersAcrossBothBases':6,
 'finalCandidateNormalRoleBrowserCasesPassed':21,'finalCandidateNormalRoleJavaScriptExceptions':0,
 'fullProgramFilesEachBase':15557,'negativeCompositionCasesEach':57,'fileRecoveryScenariosEach':16,
 'originalBusinessJarAuthHistoryDatabasePrivateConfigurationUploadsAndSecurityFrontendRetained':True,
 'iisProxySourceUpdatedButMappingsAndOtherSitesRetained':True,'maximumExtractionPathCharacters':maxpath,
 'serverIISHTTPSAndPublicLoggedInTimingPending':True,'publicDeployed':False,'newPublicGitIncluded':False,'fullCloneReady':False}
manifest['postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord']=True
manifest['limitedResultReadbackFile']='r39-scoped-result.json';manifest['limitedResultContainsNoCredentialsBusinessRowsOrRuntimeUUID']=True
(D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
result={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),
 'archiveSHA256':sha(archive),'wrapperSHA256':sha(delivery/'deploy_unified_plan_r39.py'),'archiveMembers':190,'maximumExtractionPathCharacters':maxpath,
 'selectedWrapperAndRecoveryBoundaryVerificationPending':True,'uploadedOrDeployed':False}
(D/'preparation-result-r351.json').write_bytes(enc(result));print(json.dumps(result))
