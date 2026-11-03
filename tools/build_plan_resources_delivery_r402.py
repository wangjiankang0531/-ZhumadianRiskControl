from pathlib import Path
import ast,copy,hashlib,json,re,zipfile
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;T=R/'Application/tools'
C=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103';O=R/'work/r40-plan-resource-cancel-r385'
D=R/'Document/Deployment/public_test_plan_resources_r40_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
assert J(C/'verified-stage-r399.json')['actualNormalRoleCases']==29 and J(C/'release-verification/completed-r401.json')['passed']
source=T/'original_public_test_update_r40_resource_cancel_r385.py'
assert sha(source)=='2df899f1b3471b05c5f2312e77055a45290e8053a4ae19f7889c6d18dfb393e2'
assert not D.exists();D.mkdir();delivery=D/'delivery';delivery.mkdir()
bundles={n:O/n/'bundle'for n in ['r36','r37']};plans={n:J(p/'update-manifest.json')for n,p in bundles.items()}
p36,p37=plans.values();assert p36['files']==p37['files']and p36['removedFrontendFiles']==p37['removedFrontendFiles']
assert len(p36['files'])==187 and len(p36['removedFrontendFiles'])==177 and p36['newReleaseSHA256']==p37['newReleaseSHA256']
deny=(R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery/web.config').read_bytes()
archive=delivery/'Zhumadian_Plan_Resources_20261103_R40.zip'
def zip_put(z,name,raw):
 item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,raw,compresslevel=9)
with zipfile.ZipFile(archive,'x')as z:
 zip_put(z,'web.config',deny)
 for label,root in bundles.items():zip_put(z,'variants/'+label+'/update-manifest.json',(root/'update-manifest.json').read_bytes())
 for name,pin in p36['files'].items():
  raw=(bundles['r36']/'payload'/name).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['SHA256']
  assert raw==(bundles['r37']/'payload'/name).read_bytes();zip_put(z,'payload/'+name,raw)
bases={}
for label,plan in plans.items():
 assert len(plan['acceptedOldReleases'])==1;old=next(iter(plan['acceptedOldReleases']))
 bases[old]={'label':label,'updateId':plan['updateId'],'manifestSHA256':sha(bundles[label]/'update-manifest.json'),
  'oldUpdaterSHA256':plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']}
parent=R/'Document/Deployment/public_test_unified_plan_r39_20261103/delivery/deploy_unified_plan_r39.py'
text=parent.read_text(encoding='utf-8');before=ast.parse(text)
assign={n.targets[0].id:n for n in before.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
static=ast.literal_eval(assign['STATIC_EXPECTED'].value);static={n:p for n,p in static.items()if not n.startswith('/zhumadian/emergency/')}
entry=(bundles['r36']/'payload/frontend/emergency_pc/index.html').read_text(encoding='utf-8')
paths=re.findall(r'(?:src|href)="(/zhumadian/emergency/assets/(?:js/wf-index-[^"<>]+\.js|css/index-[^"<>]+\.css))"',entry)
assert len(paths)==2
payload=J(bundles['r36']/'payload/payload-manifest.json')
for path in paths:
 name='frontend/emergency_pc/'+path.split('/zhumadian/emergency/',1)[1];pin=payload['files'][name]
 static[path.replace('/zhumadian/emergency/','/zhumadian/emergency/branding-20261025/',1)]={'decodedBytes':pin['bytes'],'decodedSHA256':pin['sha256']}
assert len(static)==4
replacements={'ARCHIVE_SHA':sha(archive),'ARCHIVE_NAME':archive.name,'NEW':p36['newReleaseSHA256'],
 'UPDATER_SHA':sha(source),'BASES':bases,'STATIC_EXPECTED':static}
for name,value in replacements.items():
 old=ast.get_source_segment(text,assign[name]);assert text.count(old)==1;text=text.replace(old,name+'='+repr(value),1)
text=text.replace('R39','R40').replace('r39','r40')
previous={n.name:ast.dump(n,include_attributes=False)for n in before.body if isinstance(n,ast.FunctionDef)}
current={n.name:ast.dump(n,include_attributes=False).replace('R40','R39').replace('r40','r39')for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
assert previous==current,'ONLY_CONSTANTS_AND_VERSION_LABELS_CHANGED_FROM_FINAL_R39_WRAPPER'
wrapper=delivery/'deploy_plan_resources_r40.py';wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode())
(delivery/'r40_update_runtime.py').write_bytes(source.read_bytes());(delivery/'web.config').write_bytes(deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
 (delivery/(label+'_Plan_Resources_R40.cmd')).write_bytes(('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_plan_resources_r40.py" '+flag+'\r\n').encode('ascii'))
prefix='C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/'
maxpath=max(len(prefix+'payload/'+name)for name in p36['files']);assert maxpath<240
checks={n:J(C/'release-verification'/n/'full-program-preflight.json')for n in ['r36','r37']}
recovery={n:J(C/'release-verification'/n/'composition-and-recovery.json')for n in ['r36','r37']}
manifest={'revision':'R40-plan-resources-cancel-original-mappers-native-plan-and-static-performance',
 'targetFTP':'/Zhumadian/Zhumadian_Plan_Resources_20261103_R40/','targetApplication':'C:/inetpub/wwwroot/Zhumadian/Application',
 'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())},
 'acceptedExactBases':bases,'eachExtractedBundleAcceptsOneExactBase':True,'bothVariantsUseOneSharedFinalPayload':True,
 'newReleaseSHA256':p36['newReleaseSHA256'],'newPayloadManifestSHA256':p36['newPayloadManifestSHA256'],'newUpdaterSHA256':sha(source),
 'writes':187,'removedFiles':177,'oldReadinessReports':11,'newOriginalReadinessReports':11,'additionalPlanRuntimeByteCheck':True,
 'newDeclaredControlFiles':22,'actualThisR40UpdaterApplyAndRollbackBase':'R37','r37ActualSixComponentLifecycleControllers':3,
 'r36ThisR40SixComponentLifecycleNotRepeated':True,'priorR39LifecycleBodiesAllASTRetained':True,
 'finalCandidateNormalRoleBrowserCasesPassed':29,'finalCandidateNormalRoleJavaScriptExceptions':0,
 'fullProgramFilesEachBase':{n:p['fullProgramFilesVerified']for n,p in checks.items()},
 'negativeCompositionCasesEach':{n:p['negativeCompositionCases']for n,p in recovery.items()},
 'fileRecoveryScenariosEach':{n:len(p['normalAndFaultFileRecoveryCases'])for n,p in recovery.items()},
 'dataConfigurationUploadPathsNotInInstallScope':True,'originalJarAuthHistoryAndSecurityFrontendRetainedByComposition':True,
 'iisProxySourceUpdatedButMappingsAndOtherSitesRetained':True,'maximumExtractionPathCharacters':maxpath,
 'postcheckRollbackBoundToSelectedBaseAndExactAppliedRecord':True,'limitedResultReadbackFile':'r40-scoped-result.json',
 'limitedResultContainsNoCredentialsBusinessRowsOrRuntimeUUID':True,'wrapperFunctionsUnchangedApartFromVersionLabels':True,
 'serverIISHTTPSAndPublicLoggedInTimingPending':True,'publicDeployed':False,'newPublicGitIncluded':False,'fullCloneReady':False}
(D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
result={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),
 'manifestSHA256':sha(D/'delivery-manifest.json'),'archiveSHA256':sha(archive),'wrapperSHA256':sha(wrapper),'builderSHA256':sha(Path(__file__)),
 'archiveMembers':190,'maximumExtractionPathCharacters':maxpath,'transportVerificationPending':True,'uploadedOrDeployed':False}
(D/'preparation-result-r402.json').write_bytes(enc(result));print(json.dumps(result))
