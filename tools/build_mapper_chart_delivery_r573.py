from pathlib import Path
import ast, hashlib, json, zipfile
R, V = Path('D:/Project/Zhumadian'), Path(__file__).resolve().parent
C = R/'Document/Deployment/mapper_chart_candidate_r44_20261104'
D = R/'Document/Deployment/public_test_mapper_chart_r44_20261104'
J = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
digest = lambda b: hashlib.sha256(b).hexdigest()
enc = lambda x: (json.dumps(x, ensure_ascii=False, indent=2)+'\n').encode()
assert J(C/'verified-full-bundle-files-r572.json')['passed']
source = V/'original_public_test_update_r44_mapper_chart_r570.py'
assert sha(source) == J(C/'prepared-runtime-r570.json')['runtimeSHA256']
assert not D.exists()
bundles = {n:R/('work/mapper-chart-bundles-r571/'+n+'/bundle') for n in ['r36','r37']}
plans = {n:J(p/'update-manifest.json') for n,p in bundles.items()}
p36, p37 = plans.values()
assert p36['files'] == p37['files'] and p36['removedFrontendFiles'] == p37['removedFrontendFiles']
assert len(p36['files']) == 190 and len(p36['removedFrontendFiles']) == 178
assert p36['newReleaseSHA256'] == p37['newReleaseSHA256']
parent = R/'Document/Deployment/public_test_mapper_equivalence_r42_20261104/delivery/deploy_mapper_equivalence_r42.py'
D.mkdir()
delivery = D/'delivery'
delivery.mkdir()
deny = (parent.parent/'web.config').read_bytes()
archive = delivery/'Zhumadian_Mapper_Chart_20261104_R44.zip'
def zip_put(z, name, raw):
    item = zipfile.ZipInfo(name, (1980,1,1,0,0,0))
    item.compress_type = zipfile.ZIP_DEFLATED
    item.external_attr = 0o100644 << 16
    z.writestr(item, raw, compresslevel=9)
with zipfile.ZipFile(archive, 'x') as z:
    zip_put(z, 'web.config', deny)
    for label, root in bundles.items(): zip_put(z, 'variants/'+label+'/update-manifest.json', (root/'update-manifest.json').read_bytes())
    for name, pin in p36['files'].items():
        raw = (bundles['r36']/'payload'/name).read_bytes()
        assert len(raw) == pin['bytes'] and digest(raw) == pin['SHA256']
        assert raw == (bundles['r37']/'payload'/name).read_bytes()
        zip_put(z, 'payload/'+name, raw)
bases = {}
for label, plan in plans.items():
    assert len(plan['acceptedOldReleases']) == 1
    old = next(iter(plan['acceptedOldReleases']))
    bases[old] = {'label':label, 'updateId':plan['updateId'], 'manifestSHA256':sha(bundles[label]/'update-manifest.json'),
        'oldUpdaterSHA256':plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']}
text = parent.read_text('utf-8')
assign = {n.targets[0].id:n for n in ast.parse(text).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
static = ast.literal_eval(assign['STATIC_EXPECTED'].value)
style = J(R/'Document/Deployment/workplace_style_delivery_r564_20261104/prepared-css-delivery-r564.json')
css_url = '/zhumadian/branding-20261025/assets/css/'+style['cssName']
static[css_url] = {'decodedBytes':1915, 'decodedSHA256':style['cssSHA256']}
for name, value in {'ARCHIVE_SHA':sha(archive), 'ARCHIVE_NAME':archive.name, 'NEW':p36['newReleaseSHA256'], 'UPDATER_SHA':sha(source), 'BASES':bases, 'STATIC_EXPECTED':static}.items():
    old = ast.get_source_segment(text, assign[name])
    assert text.count(old) == 1
    text = text.replace(old, name+'='+repr(value), 1)
text = text.replace('R42','R44').replace('r42','r44')
count_before = "len(selected['files'])==188 and len(selected['removedFrontendFiles'])==178"
assert text.count(count_before) == 1
text = text.replace(count_before, "len(selected['files'])==190 and len(selected['removedFrontendFiles'])==178")
html_before = "code,headers,body=fetch(channel,path,'identity');need(code==200 and 'no-store'in headers.get('cache-control',''),'HTML_ENTRY_MUST_NOT_BE_LONG_CACHED');rows.append({'channel':channel,'resource':path,'status':code,'htmlNoStoreVerified':True})"
assert text.count(html_before) == 1
html_after = html_before+"\n            if path=='/zhumadian/home':need("+repr(css_url.encode())+" in body and b'data-xnby-workplace-period=\"20261104-r564\"' in body,'EXACT_WORKPLACE_STYLE_LINK_REQUIRED')"
text = text.replace(html_before, html_after)
functions = lambda s: {n.name:ast.dump(n, include_attributes=False) for n in ast.parse(s).body if isinstance(n, (ast.FunctionDef,ast.ClassDef))}
old_functions = functions(parent.read_text('utf-8').replace('R42','R44').replace('r42','r44'))
new_functions = functions(text)
assert set(old_functions) == set(new_functions)
changed = [n for n in old_functions if old_functions[n] != new_functions[n]]
assert set(changed) == {'validate_archive','verify_static_gateway_and_iis'}
wrapper = delivery/'deploy_mapper_chart_r44.py'
wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode())
(delivery/'r44_update_runtime.py').write_bytes(source.read_bytes())
(delivery/'web.config').write_bytes(deny)
for label, flag in [('Check_Only','--check-only'), ('Deploy',''), ('Recover_This','--recover-this-update')]:
    command = '@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_mapper_chart_r44.py" '+flag+'\r\n'
    (delivery/(label+'_Mapper_Chart_R44.cmd')).write_bytes(command.encode('ascii'))
prefix = 'C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/'
maxpath = max(len(prefix+'payload/'+n) for n in p36['files'])
assert maxpath < 240
manifest = {'revision':'R44-exact-mapper-equivalence-and-scoped-workplace-period-layout',
    'targetFTP':'/Zhumadian/Zhumadian_Mapper_Chart_20261104_R44/', 'targetApplication':'C:/inetpub/wwwroot/Zhumadian/Application',
    'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(delivery.iterdir())},
    'acceptedExactBases':bases, 'eachExtractedBundleAcceptsOneExactBase':True, 'bothVariantsUseOneSharedFinalPayload':True,
    'newReleaseSHA256':p36['newReleaseSHA256'], 'newPayloadManifestSHA256':p36['newPayloadManifestSHA256'], 'newUpdaterSHA256':sha(source),
    'writes':190, 'removedFiles':178, 'oldReadinessReports':11, 'newOriginalReadinessReports':11, 'additionalPlanRuntimeByteCheck':True,
    'styleOnlyDeltaOverR42Bytes':4506, 'newStyleStaticResponseIncludedInGatewayAndIISTLSChecks':True,
    'runtimeChangedFunctionsAgainstR42':['r38_unified_bundle_contract'], 'runtimeUnchangedFunctionsAgainstR42':80,
    'wrapperChangedFunctionsAgainstR42':changed, 'originalStopStartRestoreAuthHealthBodiesRetained':True,
    'R42OriginalMapperResolverProofRetained':True, 'onlyTwoExactMapperPatternsAcceptedNoConfigurationRewrite':True,
    'R44TwoBaseActualCoreFileAndFourthWriteRecoveryPassed':True, 'R44SixComponentLifecycleNotRepeated':True,
    'sameBackendAsPreviouslyVerifiedR41LifecycleButNotFreshR44Acceptance':True,
    'styleComponentScenarios':21, 'styleFilterInteractions':16, 'styleActualNginxTransportChecks':10,
    'originalReportedOverlapNotReproducedInLocalBaseline':True, 'publicLayoutAndIISHTTPSAcceptancePending':True,
    'supervisionPDFModuleAndUnbuiltOnlineFormCandidateIncluded':False,
    'originalJarAuthHistoryDatabasePrivateConfigurationUploadsAndOtherSitesRetained':True,
    'iisProxySourceFromR42IncludedMappingsRetained':True, 'maximumExtractionPathCharacters':maxpath,
    'limitedResultReadbackFile':'r44-scoped-result.json', 'publicDeployed':False, 'newPublicGitIncluded':False, 'fullCloneReady':False}
(D/'delivery-manifest.json').write_bytes(enc(manifest))
(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
result = {'prepared':True, 'transportFiles':len(list(delivery.iterdir())), 'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),
    'manifestSHA256':sha(D/'delivery-manifest.json'), 'archiveSHA256':sha(archive), 'wrapperSHA256':sha(wrapper),
    'builderSHA256':sha(Path(__file__)), 'archiveMembers':193, 'maximumExtractionPathCharacters':maxpath,
    'transportVerificationPending':True, 'uploadedOrDeployed':False}
(D/'preparation-result-r573.json').write_bytes(enc(result))
print(json.dumps(result))
