"""Freeze one transport for two exact original releases after actual backend/UI and file recovery tests."""
from pathlib import Path
import ast,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
C=R/'Document/Deployment/original_backend_bootstrap_r45_20261104'
D=R/'Document/Deployment/public_test_original_bootstrap_r45_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def main():
 assert not D.exists()
 assert J(C/'verified-full-bundle-files-r852.json')['passed']
 lifecycle=J(R/'work/original-backend-full-r850/verified-component-bootstrap-r850.json')
 assert lifecycle['passed']and lifecycle['codeRestored']and lifecycle['privateConfigurationUnchanged']and lifecycle['originalCurrentPointerRestored']
 assert len(lifecycle['health'])==1 and lifecycle['health'][0]['newBackendOrSupervisionModulePresent']is False
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(x==0 for x in t['exitCodes'].values())for t in lifecycle['terminals'])
 ui=J(R/'work/bootstrap-browser-r850/result.json');assert ui['passed']and len(ui['cases'])==13 and ui['approvalRequests']==0 and not ui['APIsMocked']
 gateway=J(R/'work/original-backend-full-r850/normal-restart-static-result.json');assert gateway['passed']and len(gateway['rows'])==10
 source=V/'original_public_test_update_r45_bootstrap_r847.py'
 assert sha(source)==J(C/'prepared-bundles-r847.json')['runtimeSHA256']
 bundles={label:R/f'work/original-backend-bootstrap-r847/{label}/bundle'for label in ['r36','r37']}
 plans={label:J(root/'update-manifest.json')for label,root in bundles.items()};p36,p37=plans.values()
 assert p36['files']==p37['files']and p36['removedFrontendFiles']==p37['removedFrontendFiles']
 assert len(p36['files'])==196 and len(p36['removedFrontendFiles'])==181 and p36['newReleaseSHA256']==p37['newReleaseSHA256']
 prefix='C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/'
 maxpath=max(len(prefix+'payload/'+n)for n in p36['files']);assert maxpath<240
 parent=R/'Document/Deployment/public_test_mapper_chart_r44_20261104/delivery/deploy_mapper_chart_r44.py'
 deny=(parent.parent/'web.config').read_bytes();delivery=D/'delivery';delivery.mkdir(parents=True)
 archive=delivery/'Zhumadian_Original_Bootstrap_20261104_R45.zip'
 def zip_put(z,name,raw):
  item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16
  z.writestr(item,raw,compresslevel=9)
 with zipfile.ZipFile(archive,'x')as z:
  zip_put(z,'web.config',deny)
  for label,root in bundles.items():zip_put(z,'variants/'+label+'/update-manifest.json',(root/'update-manifest.json').read_bytes())
  for name,pin in p36['files'].items():
   raw=(bundles['r36']/'payload'/name).read_bytes()
   assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256']and raw==(bundles['r37']/'payload'/name).read_bytes()
   zip_put(z,'payload/'+name,raw)
 with zipfile.ZipFile(archive)as z:assert len(z.infolist())==199
 bases={}
 for label,plan in plans.items():
  assert len(plan['acceptedOldReleases'])==1
  old=next(iter(plan['acceptedOldReleases']))
  bases[old]={'label':label,'updateId':plan['updateId'],'manifestSHA256':sha(bundles[label]/'update-manifest.json'),
   'oldUpdaterSHA256':plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']}
 text=parent.read_text(encoding='utf8')
 assign={n.targets[0].id:n for n in ast.parse(text).body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
 static=ast.literal_eval(assign['STATIC_EXPECTED'].value)
 for key in list(static):
  if key.startswith('/zhumadian/emergency/'):del static[key]
 for row in gateway['rows']:
  if row['requestedEncoding']=='gzip'and row['path'].startswith('/zhumadian/emergency/')and'/assets/'in row['path']:
   static[row['path']]={'decodedBytes':row['decodedBytes'],'decodedSHA256':row['decodedSHA256']}
 assert len(static)==5
 for name,value in {'ARCHIVE_SHA':sha(archive),'ARCHIVE_NAME':archive.name,'NEW':p36['newReleaseSHA256'],
  'UPDATER_SHA':sha(source),'BASES':bases,'STATIC_EXPECTED':static}.items():
  old=ast.get_source_segment(text,assign[name]);assert text.count(old)==1;text=text.replace(old,name+'='+repr(value))
 text=text.replace('R44','R45').replace('r44','r45')
 count="len(selected['files'])==190 and len(selected['removedFrontendFiles'])==178"
 assert text.count(count)==1;text=text.replace(count,"len(selected['files'])==196 and len(selected['removedFrontendFiles'])==181")
 funcs=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 oldFunctions=funcs(parent.read_text(encoding='utf8').replace('R44','R45').replace('r44','r45'));newFunctions=funcs(text)
 assert set(oldFunctions)==set(newFunctions)
 changed=[n for n in oldFunctions if oldFunctions[n]!=newFunctions[n]];assert changed==['validate_archive']
 wrapper=delivery/'deploy_original_bootstrap_r45.py';wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
 (delivery/'r45_update_runtime.py').write_bytes(source.read_bytes());(delivery/'web.config').write_bytes(deny)
 for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
  command='@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_original_bootstrap_r45.py" '+flag+'\r\n'
  (delivery/(label+'_Original_Bootstrap_R45.cmd')).write_bytes(command.encode('ascii'))
 manifest={'revision':'R45-original-online-forms-canonical-authenticated-bootstrap-and-retained-R44',
  'targetFTP':'/Zhumadian/Zhumadian_Original_Bootstrap_20261104_R45/',
  'targetApplication':'C:/inetpub/wwwroot/Zhumadian/Application',
  'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())},
  'acceptedExactBases':bases,'eachExtractedBundleAcceptsOneExactBase':True,'bothVariantsUseOneSharedFinalPayload':True,
  'newReleaseSHA256':p36['newReleaseSHA256'],'newPayloadManifestSHA256':p36['newPayloadManifestSHA256'],'newUpdaterSHA256':sha(source),
  'writes':196,'removedFiles':181,'oldReadinessReports':11,'newOriginalReadinessReports':11,
  'runtimeChangedFunctionsAgainstR44':['r38_unified_bundle_contract'],'runtimeUnchangedFunctionsAgainstR44':80,
  'wrapperChangedFunctionsAgainstR44':changed,'originalStopStartRestoreAuthHealthBodiesRetained':True,
  'retainedR44MapperStaticPerformanceAndWorkplaceStyles':True,'completeCompiledFrontendFiles':344,
  'normalOriginalBackendLifecyclePassed':True,'normalOriginalBackendActualUICases':13,'actualGatewayStaticRequestsChecked':10,
  'originalBackendWithoutNewSupervisionModuleValidated':True,'actualCoreFileNormalAndFourthWriteRecoveryPassedForBothBases':True,
  'originalJarAuthenticationHistoryPrivateConfigurationDatabaseUploadsAndOtherSitesRetained':True,
  'publicIISHTTPSRealRolesColdWarmAndFullNangangAcceptanceStillPending':True,
  'maximumExtractionPathCharacters':maxpath,'limitedResultReadbackFile':'r45-scoped-result.json',
  'publicDeployed':False,'newPublicGitIncluded':False,'fullCloneReady':False}
 (D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
 report={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),
  'manifestSHA256':sha(D/'delivery-manifest.json'),'archiveSHA256':sha(archive),'wrapperSHA256':sha(wrapper),
  'builderSHA256':sha(Path(__file__)),'archiveMembers':199,'maximumExtractionPathCharacters':maxpath,
  'transportVerificationPending':True,'uploadedOrDeployed':False}
 (D/'preparation-result-r853.json').write_bytes(enc(report));print(json.dumps(report))
if __name__=='__main__':main()
