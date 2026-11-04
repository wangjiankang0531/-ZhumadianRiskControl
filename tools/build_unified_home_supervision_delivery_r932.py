"""Freeze one R47 delivery after exact original-app and file-recovery acceptance."""
from pathlib import Path
import ast,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
B=R/'work/unified-home-supervision-r928/bundle';C=R/'Document/Deployment/unified_home_supervision_r928_20261104'
D=R/'Document/Deployment/public_test_home_supervision_r47_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def main():
 assert not D.exists()
 files=J(C/'verified-files-r929.json');assert files['passed']and files['normalReplacementAndRestorePassed']and files['fourthWriteFailureAndRestorePassed']
 full=J(R/'work/sv931/verified-exact-supervision-r931.json');assert full['passed']and full['codeRestored']and full['privateConfigurationUnchanged']and full['originalCurrentPointerRestored']
 assert full['health'][0]['exactR47UpdaterAndCoreUsed']and all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in full['terminals'])
 browser=J(R/'work/exact-supervision-browser-r931/result.json');assert browser['passed']and browser['approvalRequests']==0 and not browser['APIsMocked']
 plan=J(B/'update-manifest.json');inner=J(B/'base-r46/update-manifest.json');prepared=J(C/'prepared-r928.json')
 assert len(plan['files'])==11 and not plan['removedFrontendFiles']and len(inner['files'])==7 and not inner['removedFrontendFiles']
 old=next(iter(plan['acceptedOldReleases']));base={old:{'label':'r45','updateId':plan['updateId'],'manifestSHA256':sha(B/'update-manifest.json'),'oldUpdaterSHA256':plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']}}
 parent=R/'Document/Deployment/public_test_home_transfer_r46_20261104/delivery/deploy_home_transfer_r46.py';deny=(parent.parent/'web.config').read_bytes()
 delivery=D/'delivery';delivery.mkdir(parents=True);archive=delivery/'Zhumadian_Home_Supervision_20261104_R47.zip'
 def put(z,n,b):
  i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
 with zipfile.ZipFile(archive,'x')as z:
  put(z,'web.config',deny);put(z,'variants/r45/update-manifest.json',(B/'update-manifest.json').read_bytes());put(z,'base-r46/update-manifest.json',(B/'base-r46/update-manifest.json').read_bytes())
  for prefix,p in [('payload/',plan),('base-r46/payload/',inner)]:
   for n,pin in p['files'].items():
    raw=(B/prefix/n).read_bytes();assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'];put(z,prefix+n,raw)
 with zipfile.ZipFile(archive)as z:assert len(z.infolist())==21
 text=parent.read_text('utf8');assign={n.targets[0].id:n for n in ast.parse(text).body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
 runtime=V/'original_public_test_home_supervision_r47_r928.py';core=V/'original_public_test_base_r46.py'
 for n,val in {'ARCHIVE_SHA':sha(archive),'ARCHIVE_NAME':archive.name,'NEW':plan['newReleaseSHA256'],'UPDATER_SHA':sha(runtime),'BASES':base}.items():
  oldtext=ast.get_source_segment(text,assign[n]);assert text.count(oldtext)==1;text=text.replace(oldtext,n+'='+repr(val))
 text=text.replace('R46','R47').replace('r46','r47')
 assign={n.targets[0].id:n for n in ast.parse(text).body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
 oldtext=ast.get_source_segment(text,assign['BASES']);text=text.replace(oldtext,'BASES='+repr(base))
 marker='\ndef need(ok,message):';assert text.count(marker)==1
 text=text.replace(marker,"\nCORE_SHA="+repr(sha(core))+"\nINNER_MANIFEST_SHA="+repr(sha(B/'base-r46/update-manifest.json'))+marker)
 text=text.replace("len(selected['files'])==7 and len(selected['removedFrontendFiles'])==0","len(selected['files'])==11 and len(selected['removedFrontendFiles'])==0")
 text=text.replace('EXACT_SEVEN_WRITE_ZERO_REMOVAL_SET','EXACT_ELEVEN_WRITE_ZERO_REMOVAL_SET')
 oldline="    need(set(names)=={'web.config'}|{'variants/'+v['label']+'/update-manifest.json'for v in BASES.values()}|{'payload/'+v for v in selected['files']},'EXACT_CLOSED_MEMBERS')"
 newlines="""    need(selected.get('supervisionBaseR46')=={'relativeRoot':'base-r46','manifestSHA256':INNER_MANIFEST_SHA,'coreSHA256':CORE_SHA},'EXACT_FROZEN_HOME_BASE_REFERENCE')
    raw=z.read('base-r46/update-manifest.json');need(hashlib.sha256(raw).hexdigest()==INNER_MANIFEST_SHA,'EXACT_FROZEN_HOME_MANIFEST');inner=json.loads(raw)
    need(len(inner['files'])==7 and not inner['removedFrontendFiles'] and inner['targetApplication']==APP.as_posix()and inner['gatewayPort']==18892 and inner['acceptedOldReleases']==selected['acceptedOldReleases'],'EXACT_FROZEN_HOME_SCOPE')
    need(set(names)=={'web.config','base-r46/update-manifest.json'}|{'variants/'+v['label']+'/update-manifest.json'for v in BASES.values()}|{'payload/'+v for v in selected['files']}|{'base-r46/payload/'+v for v in inner['files']},'EXACT_CLOSED_MEMBERS')
    for name,pin in inner['files'].items():
        raw=z.read('base-r46/payload/'+name);need(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'],'EXACT_FROZEN_INNER_PAYLOAD:'+name)"""
 assert text.count(oldline)==1;text=text.replace(oldline,newlines)
 needle="        for origin,destination in [('web.config','web.config'),('variants/'+base['label']+'/update-manifest.json','update-manifest.json')]+[('payload/'+n,'payload/'+n)for n in plan['files']]:"
 replacement="        inner=json.loads(z.read('base-r46/update-manifest.json'))\n        for origin,destination in [('web.config','web.config'),('variants/'+base['label']+'/update-manifest.json','update-manifest.json'),('base-r46/update-manifest.json','base-r46/update-manifest.json')]+[('payload/'+n,'payload/'+n)for n in plan['files']]+[('base-r46/payload/'+n,'base-r46/payload/'+n)for n in inner['files']]:"
 assert text.count(needle)==1;text=text.replace(needle,replacement)
 needle="    installed=regular(APP/'tools/original_public_test_update.py')";assert text.count(needle)==1
 text=text.replace(needle,"    need(sha(regular(root/'original_public_test_base_r46.py'))==CORE_SHA,'EXACT_FROZEN_R46_CORE_REQUIRED')\n"+needle)
 needle='    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)';assert text.count(needle)==1;text=text.replace(needle,needle+';m=m.runtime()')
 ast.parse(text);wrapper=delivery/'deploy_home_supervision_r47.py';wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
 (delivery/'r47_update_runtime.py').write_bytes(runtime.read_bytes());(delivery/'original_public_test_base_r46.py').write_bytes(core.read_bytes());(delivery/'web.config').write_bytes(deny)
 for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
  (delivery/(label+'_Home_Supervision_R47.cmd')).write_bytes(('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_home_supervision_r47.py" '+flag+'\r\n').encode('ascii'))
 prefix='C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/'
 maximum=max(len(prefix+n)for n in ['payload/'+n for n in plan['files']]+['base-r46/payload/'+n for n in inner['files']]);assert maximum<240
 manifest={'revision':'R47-home-transfer-and-factory-supervision','targetFTP':'/Zhumadian/Zhumadian_Home_Supervision_20261104_R47/','targetApplication':plan['targetApplication'],
  'files':{f.name:{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted(delivery.iterdir())},'acceptedExactBases':base,
  'newReleaseSHA256':plan['newReleaseSHA256'],'newPayloadManifestSHA256':plan['newPayloadManifestSHA256'],'newUpdaterSHA256':sha(runtime),'frozenCoreSHA256':sha(core),
  'writePaths':list(plan['files']),'writes':11,'removedFiles':0,'archiveMembers':21,'maximumExtractionPathCharacters':maximum,
  'oldOriginalReadinessReports':11,'newReadinessReportsIncludingSupervision':12,'exactProductionUpdaterAndCoreFullLifecyclePassed':True,
  'normalOriginalSDKUIAssertionsIncludingRepeats':len(browser['cases']),'existingTwoPDFsExactlyReopened':True,'newBusinessWritesOrApprovalsInFinalProbe':0,
  'normalAndFourthWriteFileRecoveryPassed':True,'fileNegativeCases':len(files['negativeCases']),'transportVerificationStillPending':True,
  'originalJarAuthDataPrivateConfigurationUploadsIISAndOtherSitesRetained':True,'staticHomeAssetsPixelsICCAndCompleteGlyphsRetained':True,
  'originalLedgerSupervisionButtonUIStillPending':True,'publicHTTPSIISRealRoleAndNewGenerationStillPending':True,
  'limitedResultReadbackFile':'r47-scoped-result.json','publicDeployed':False,'newPublicGitIncluded':False,'fullCloneReady':False}
 (D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
 report={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(f.stat().st_size for f in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),
  'archiveSHA256':sha(archive),'wrapperSHA256':sha(wrapper),'archiveMembers':21,'maximumExtractionPathCharacters':maximum,'transportVerificationPending':True,'publicChanged':False}
 (D/'preparation-r932.json').write_bytes(enc(report));print(json.dumps(report))
if __name__=='__main__':main()
