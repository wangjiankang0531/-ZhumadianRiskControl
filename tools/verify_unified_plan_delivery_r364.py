from pathlib import Path
from unittest.mock import patch
import ast,copy,gzip,hashlib,importlib.util,io,json,os,shutil,sys,warnings,zipfile
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_unified_plan_r39_20261103';S=D/'delivery/deploy_unified_plan_r39.py'
O=R/'work/v39';assert not O.exists();assert shutil.disk_usage(V).free>512*1024**2
temporary_path_budget=json.loads((D/'delivery-manifest.json').read_bytes())['maximumExtractionPathCharacters']+len(str(O/'Application'))-len(str(Path('C:/inetpub/wwwroot/Zhumadian/Application')))
assert temporary_path_budget<250,'TEST_FIXTURE_PATH_BUDGET_REQUIRED_BEFORE_ALLOCATION'
O.mkdir()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
manifest=J(D/'delivery-manifest.json');refined=J(D/'final-transport-input-r363.json')
assert sha(D/'delivery-manifest.json')==refined['manifestSHA256']and(D/'delivery/delivery-manifest.json').read_bytes()==(D/'delivery-manifest.json').read_bytes()
assert set(p.name for p in(D/'delivery').iterdir())==set(manifest['files'])|{'delivery-manifest.json'}
for n,pin in manifest['files'].items():assert(D/'delivery'/n).stat().st_size==pin['bytes']and sha(D/'delivery'/n)==pin['sha256']
assert(D/'delivery/r39_update_runtime.py').read_bytes()==(R/'Application/tools/original_public_test_update_r39_plan_runtime_r337.py').read_bytes()
for p in(D/'delivery').glob('*.py'):ast.parse(p.read_bytes())
ns={'__file__':str(S),'__name__':'fixed_r39_transport_tests'};exec(compile(S.read_bytes(),str(S),'exec'),ns)
public_app=ns['APP'];bases=ns['BASES'];archive=D/'delivery'/ns['ARCHIVE_NAME'];assert sha(archive)==ns['ARCHIVE_SHA']
validations=[];plans={};expanded=[]
for old,base in bases.items():
    with zipfile.ZipFile(archive)as z:
        plan=ns['validate_archive'](z,base);assert set(plan['acceptedOldReleases'])=={old};plans[base['label']]=plan
    stage=O/('extract-'+base['label']);ns['extract_selected_archive'](archive,stage,base)
    assert sha(stage/'update-manifest.json')==base['manifestSHA256']and not(stage/'variants').exists()
    assert(stage/'web.config').read_bytes()==(D/'delivery/web.config').read_bytes()
    for n,pin in plan['files'].items():assert(stage/'payload'/n).stat().st_size==pin['bytes']and sha(stage/'payload'/n)==pin['SHA256']
    expanded.append(stage)
    validations.append({'case':base['label']+'-closed-190-member-archive-and-187-extracted-payload-pins','passed':True})
    try:ns['extract_selected_archive'](archive,stage,base)
    except ValueError as e:assert str(e)=='NEW_OWN_STAGE_REQUIRED'
    else:raise AssertionError('EXISTING_STAGE_ACCEPTED')
    validations.append({'case':base['label']+'-existing-stage-refused','passed':True})
with zipfile.ZipFile(archive)as z:members={i.filename:z.read(i.filename)for i in z.infolist()}
selected=next(iter(bases.values()));some_payload=next(n for n in members if n.startswith('payload/frontend/'))
def negative_archive(label,change):
    target=O/(label+'.zip');rows=[(n,b,None)for n,b in members.items()];rows=change(rows)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED)as z:
            for n,b,mode in rows:
                if mode:
                    info=zipfile.ZipInfo(n);info.external_attr=mode<<16;z.writestr(info,b)
                else:z.writestr(n,b)
    try:
        with zipfile.ZipFile(target)as z:ns['validate_archive'](z,selected)
    except (ValueError,KeyError,zipfile.BadZipFile):validations.append({'case':label,'passed':True})
    else:raise AssertionError('BAD_ARCHIVE_ACCEPTED:'+label)
    target.unlink()
negative_archive('duplicate-member',lambda rows:rows+[rows[0]])
negative_archive('extra-member',lambda rows:rows+[('foreign.txt',b'own foreign',None)])
negative_archive('missing-second-variant',lambda rows:[r for r in rows if r[0]!='variants/r37/update-manifest.json'])
negative_archive('wrong-variant-manifest',lambda rows:[(n,b+b' 'if n=='variants/r36/update-manifest.json'else b,m)for n,b,m in rows])
negative_archive('wrong-payload-bytes',lambda rows:[(n,b+b'own corrupt'if n==some_payload else b,m)for n,b,m in rows])
negative_archive('parent-path-member',lambda rows:rows+[('../foreign.txt',b'own',None)])
negative_archive('windows-drive-member',lambda rows:rows+[('C:/foreign.txt',b'own',None)])
negative_archive('backslash-member',lambda rows:rows+[('payload\\foreign.txt',b'own',None)])
negative_archive('trailing-space-member',lambda rows:rows+[('payload/foreign.txt ',b'own',None)])
negative_archive('symlink-member',lambda rows:[(n,b,0o120777 if n=='web.config'else m)for n,b,m in rows])
static_checks=[]
for path,expected in list(ns['STATIC_EXPECTED'].items()):
    original=copy.deepcopy(ns['STATIC_EXPECTED']);body=b'OWN_R39_STATIC_VALIDATOR_BODY'*100
    ns['STATIC_EXPECTED'][path]={'decodedBytes':len(body),'decodedSHA256':hashlib.sha256(body).hexdigest()}
    headers={'cache-control':'public, max-age=31536000, immutable','content-encoding':'gzip','vary':'Accept-Encoding'};packed=gzip.compress(body)
    assert ns['validate_static_response'](path,'gzip',200,headers,packed)['decodedContentMatched'];static_checks.append({'case':path+'-gzip-synthetic-validator','passed':True})
    for label,code,hs,bs,encoding in [('status',503,headers,packed,'gzip'),('vary',200,{k:v for k,v in headers.items()if k!='vary'},packed,'gzip'),('cache',200,{**headers,'cache-control':'no-store'},packed,'gzip'),('content',200,headers,gzip.compress(b'own wrong'),'gzip'),('zero-gzip',200,headers,packed,'identity')]:
        try:ns['validate_static_response'](path,encoding,code,hs,bs)
        except (ValueError,OSError):static_checks.append({'case':label,'passed':True})
        else:raise AssertionError('WRONG_STATIC_ACCEPTED')
    identity={k:v for k,v in headers.items()if k!='content-encoding'};assert ns['validate_static_response'](path,'identity',200,identity,body)['decodedContentMatched'];static_checks.append({'case':'explicit-zero-identity','passed':True});ns['STATIC_EXPECTED']=original
assert len(static_checks)==28
fixture=O/'Application';fixture.mkdir();(fixture/'tools').mkdir();(fixture/'private').mkdir()
fake={'schema':'zhumadian.original.server.configuration.v1','syntheticPreflightFixtureOnly':True,'servicesMustNotBeStartedFromThisFixture':True,'containsRealCredentials':False,'configuration':{'platform':{'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_preflight','spring.datasource.dynamic.primary':'jnpf','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'},'business':{'spring.datasource.dynamic.datasource.master.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.datasource.tow.url':'jdbc:mysql://127.0.0.1:9/own_preflight','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0'}}}
roots={'r36':R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle/payload','r37':R/'work/r39-plan-runtime-unified-r1/original-r37-contract/payload'}
updater_rel='tools/original_public_test_update.py'
def set_base(old,base):
    put(fixture/'release-manifest.json',(roots[base['label']]/'release-manifest.json').read_bytes());put(fixture/updater_rel,(roots[base['label']]/updater_rel).read_bytes())
    assert sha(fixture/'release-manifest.json')==old
    put(fixture/'private/server-configuration.json',enc(fake))
ns['APP']=fixture
selection=[];guards=[]
for old,base in bases.items():
    set_base(old,base);assert ns['select_installed_base'](fixture)==(old,base);selection.append({'case':base['label']+'-exact-base-and-updater','passed':True})
    foreign=next(v for v in bases.values()if v!=base);put(fixture/updater_rel,(roots[foreign['label']]/updater_rel).read_bytes())
    try:ns['select_installed_base'](fixture)
    except ValueError as e:assert str(e)=='EXACT_SELECTED_BASE_UPDATER_REQUIRED'
    else:raise AssertionError('WRONG_BASE_UPDATER_ACCEPTED')
    selection.append({'case':base['label']+'-cross-variant-updater-refused','passed':True})
    report={'updateId':base['updateId'],'oldReleaseSHA256':old,'newReleaseSHA256':ns['NEW'],'attempt':str(fixture/'UserData/OriginalPublicUpdates'/('a'*32))}
    assert ns['recovery_guard'](report)==base;guards.append({'case':base['label']+'-exact-own-recovery','passed':True})
    for key,value in [('updateId',foreign['updateId']),('oldReleaseSHA256','0'*64),('newReleaseSHA256','0'*64),('attempt',str(fixture/'outside'/('a'*32))),('attempt',str(fixture/'UserData/OriginalPublicUpdates/not-an-attempt'))]:
        bad={**report,key:value}
        try:ns['recovery_guard'](bad)
        except ValueError:guards.append({'case':base['label']+'-foreign-'+key,'passed':True})
        else:raise AssertionError('FOREIGN_RECOVERY_ACCEPTED')
put(fixture/'release-manifest.json',b'own unknown version')
try:ns['select_installed_base'](fixture)
except ValueError as e:assert str(e)=='ONLY_EXACT_R36_OR_R37_BASE'
else:raise AssertionError('UNKNOWN_BASE_ACCEPTED')
selection.append({'case':'unknown-release-refused','passed':True})
transport_root=O/'transport-fixture';transport_root.mkdir()
for file in(D/'delivery').iterdir():os.link(file,transport_root/file.name)
ns['__file__']=str(transport_root/S.name)
real_validate=ns['validate_archive']
def local_validate(z,base):
    # Keep production manifest target checks exact while adapting only the main fixture root.
    ns['APP']=public_app
    try:return real_validate(z,base)
    finally:ns['APP']=fixture
ns['validate_archive']=local_validate
real_spec=importlib.util.spec_from_file_location;events=[];current={};postcheck='success'
class Loader:
    def __init__(self,base):self.base=base
    def create_module(self,spec):return self.base.create_module(spec)
    def exec_module(self,module):
        self.base.exec_module(module);actual_budget=module.candidate_runtime_pool_preflight
        def load(app,bundle,pin):
            assert app==fixture and pin==current['base']['manifestSHA256'];events.append('load_bundle_explicit_fixture_spy');return plans[current['base']['label']],current['old'],{}
        def budget(app,bundle,plan):
            events.append('actual_budget_enter');r=actual_budget(app,bundle,plan);assert r['originalMapperPreflight']['passed'];events.append('actual_budget_pass');return r
        def owned(app,pin):events.append('owned_ready_explicit_spy');return{}
        def health(app,row):events.append('health_explicit_spy')
        def apply(app,bundle,pin):
            assert pin==current['base']['manifestSHA256'];events.append('apply_update_explicit_spy')
            put(app/'release-manifest.json',(R/'work/r39-plan-runtime-unified-r1/shared/payload/release-manifest.json').read_bytes());put(app/updater_rel,(D/'delivery/r39_update_runtime.py').read_bytes())
            current['applied']={'updateId':current['base']['updateId'],'oldReleaseSHA256':current['old'],'newReleaseSHA256':ns['NEW'],'attempt':str(app/'UserData/OriginalPublicUpdates'/('b'*32)),'ready':True}
            put(app/'UserData/OriginalPublicUpdates/latest.json',enc(current['applied']))
        def rollback(app):events.append('rollback_latest_explicit_spy');set_base(current['old'],current['base'])
        def forbidden(*a,**kw):events.append('FORBIDDEN_REAL_SERVICE');raise AssertionError('WRAPPER_TEST_STARTED_SERVICE')
        module.load_bundle=load;module.candidate_runtime_pool_preflight=budget;module.owned_ready=owned;module.health=health;module.apply_update=apply;module.rollback_latest=rollback
        module.normal_stop=forbidden;module.launch=forbidden;module.backup_code=forbidden;module.recover_pending=forbidden
def factory(name,path,*args,**kw):
    assert Path(path)==transport_root/'r39_update_runtime.py';s=real_spec(name,path,*args,**kw);s.loader=Loader(s.loader);return s
def static_spy(m,root,checked):
    events.append('static_postcheck_explicit_spy')
    if postcheck=='drift':
        foreign=next((o,b)for o,b in bases.items()if o!=current['old']);changed={**current['applied'],'oldReleaseSHA256':foreign[0],'updateId':foreign[1]['updateId']};put(fixture/'UserData/OriginalPublicUpdates/latest.json',enc(changed))
    if postcheck!='success':raise ValueError('OWN_INJECTED_POSTCHECK_FAILURE')
ns['verify_static_gateway_and_iis']=static_spy
orders=[]
for old,base in bases.items():
    current.update(old=old,base=base)
    for bad in [True,False]:
        set_base(old,base);cfg=copy.deepcopy(fake)
        if bad:cfg['configuration']['platform'].pop('spring.datasource.host')
        put(fixture/'private/server-configuration.json',enc(cfg));events.clear()
        try:
            with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S),'--check-only']):ns['main']()
        except ValueError as e:assert bad and str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'and events==['load_bundle_explicit_fixture_spy','actual_budget_enter']
        else:assert not bad and events==['load_bundle_explicit_fixture_spy','actual_budget_enter','actual_budget_pass','owned_ready_explicit_spy','health_explicit_spy']
        if not bad:
            summary=J(transport_root/'r39-scoped-result.json');assert summary['phase']=='preflight-passed'and summary['selectedBase']==base['label']and summary['mysqlMaxConnections']==24 and summary['datasourceCount']==3
            assert not summary['credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded']
        orders.append({'variant':base['label'],'invalidLayout':bad,'events':list(events),'actualFixedArchiveValidatedAndExtracted':True,'actualCandidateBudgetAndMapperGateUsed':True,'realServiceCalls':0})
    for postcheck in ['success','failure','drift']:
        set_base(old,base);events.clear()
        try:
            with patch.object(importlib.util,'spec_from_file_location',factory),patch.object(sys,'argv',[str(S)]):ns['main']()
        except ValueError as e:
            assert postcheck!='success'
            if postcheck=='failure':assert str(e)=='OWN_INJECTED_POSTCHECK_FAILURE'and events[-1]=='rollback_latest_explicit_spy'and sha(fixture/'release-manifest.json')==old
            else:assert str(e)=='POSTCHECK_UPDATE_RECORD_DRIFT_REFUSE_ROLLBACK'and 'rollback_latest_explicit_spy'not in events
        else:assert postcheck=='success'and 'rollback_latest_explicit_spy'not in events
        assert 'FORBIDDEN_REAL_SERVICE'not in events
        summary=J(transport_root/'r39-scoped-result.json');assert summary['phase']=={'success':'deploy-complete','failure':'postcheck-failed-rolled-back','drift':'deploy-started'}[postcheck]
        assert summary['serverLocalGatewayAndIISTLSStaticPassed']==(postcheck=='success')and not summary['externalHTTPSAndLoggedInTimingAccepted']
        orders.append({'variant':base['label'],'postcheck':postcheck,'events':list(events),'actualFixedArchiveValidatedAndExtracted':True,'lifecycleAndTLSAreExplicitSpies':True})
        set_base(old,base)
assert len(orders)==10
helper_root=O/'limited-result-helper';helper_root.mkdir();base=next(iter(bases.values()));old=next(iter(bases))
ns['write_scoped_result'](helper_root,'preflight-passed',base,old)
summary_file=helper_root/'r39-scoped-result.json';good=summary_file.read_bytes()
for label,bad in [('foreign-schema',enc({'schema':'foreign','newReleaseSHA256':ns['NEW']})),('foreign-release',enc({'schema':'xnby.r39.scoped-deployment-result.v1','newReleaseSHA256':'0'*64})),('oversized',b'X'*(64*1024+1))]:
    summary_file.write_bytes(bad)
    try:ns['write_scoped_result'](helper_root,'deploy-complete',base,old)
    except ValueError:pass
    else:raise AssertionError('FOREIGN_SUMMARY_OVERWRITTEN:'+label)
    assert summary_file.read_bytes()==bad
summary_file.write_bytes(good)
ns['write_scoped_result'](helper_root,'deploy-started',base,old)
assert J(summary_file)['phase']=='deploy-started'and summary_file.stat().st_size<4096

# A clean rerun of the current builder must reproduce the final eight transport files.
builder=V/'build_unified_plan_delivery_r351.py';build=builder.read_text(encoding='utf-8')
anchor="(D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))"
assert build.count(anchor)==1
if "manifest['postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord']=True"not in build:
    build=build.replace(anchor,"manifest['postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord']=True\n"+anchor,1);ast.parse(build);builder.write_text(build,encoding='utf-8')
repro=O/'reproduced-delivery';needle="D=R/'Document/Deployment/public_test_unified_plan_r39_20261103'";assert build.count(needle)==1
local=build.replace(needle,'D=Path('+repr(str(repro))+')',1)
exec(compile(local,str(builder),'exec'),{'__name__':'reproduce_fixed_transport','__file__':str(builder)})
assert set(p.name for p in(repro/'delivery').iterdir())==set(p.name for p in(D/'delivery').iterdir())
assert all((repro/'delivery'/p.name).read_bytes()==p.read_bytes()for p in(D/'delivery').iterdir())
assert sha(builder)==hashlib.sha256(build.replace('\n',os.linesep).encode()).hexdigest()
assert sha(D/'delivery-manifest.json')==refined['manifestSHA256']
result={'passed':True,'manifestSHA256':sha(D/'delivery-manifest.json'),'all8TransportFileBytesAndPinsExact':True,'all190ArchiveMembersAnd187PayloadPinsExact':True,
 'bothSelectedManifestsRemainSingleExactBase':True,'archiveAndExtractionBoundaryCases':len(validations),'staticResponseValidatorSyntheticCases':len(static_checks),
 'baseSelectionCases':len(selection),'recoveryGuardCases':len(guards),'actualWrapperMainPreflightAndPostcheckScenarios':len(orders),
 'postcheckForeignVariantRecordDriftRefusedWithoutRollback':True,'ownPostcheckFailureExactlyOneScopedRollbackSpy':True,
 'actualCandidateBudgetBeforeAnyServiceUsed':True,'fullLoadBundleIdentityReadinessLifecycleAndIISInWrapperTestsAreExplicitSpies':True,
 'priorSameFinalUpdaterTwoActualSixComponentLifecyclesAnd21UIEvidenceRetained':True,
 'scopedResultPhaseAndThreeForeignOrOversizeRefusalsPassed':True,'cleanTransportBuilderReproducedAll8FilesByteForByte':True,'finalBuilderSHA256':sha(builder),'finalWrapperSHA256':sha(S),
 'realServicesDatabasePublicOrDesktopTouched':False,'publicDeployed':False,'fullCloneReady':False}
for name,value in [('verified-fixed-transport-r364.json',result),('archive-cases-r353.json',validations),('selection-and-recovery-cases-r353.json',{'selection':selection,'recovery':guards}),('wrapper-order-cases-r353.json',orders),('response-cases-r353.json',static_checks)]:put(D/name,enc(value))
put(O/'terminal.json',enc({'passed':True,'noProcessStarted':True,'exactTemporaryRoot':str(O),'safeToRemoveAfterVerification':True,'logicalBudgetBytes':128*1024**2}))
print(json.dumps(result))
