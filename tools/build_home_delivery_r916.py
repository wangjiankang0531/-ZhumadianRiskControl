"""Freeze the R46 sparse home asset transport; no server or application is started."""
from pathlib import Path
import ast,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;A=R/'Application'
B=R/'work/home-sparse-r914/bundle';C=R/'Document/Deployment/home_sparse_update_r914_20261104'
D=R/'Document/Deployment/public_test_home_transfer_r46_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')

def main():
 assert not D.exists()
 accepted=J(C/'verified-files-r915.json');assert accepted['passed']and len(accepted['negativeCases'])==14
 original=J(R/'Document/Deployment/home_transfer_full_verified_r913_20261104/verified-original-sdk-home-r913.json');assert original['passed']
 p=J(B/'update-manifest.json');assert len(p['files'])==7 and not p['removedFrontendFiles']
 old=next(iter(p['acceptedOldReleases']));assert old=='3b1251784fba66726f8ab4060138a2de78add753d7d06d731d5afa2f3a517bbd'
 source=V/'original_public_test_update_home_r46_r914.py';assert sha(source)==J(C/'prepared-sparse-r914.json')['runtimeSHA256']
 base={old:{'label':'r45','updateId':p['updateId'],'manifestSHA256':sha(B/'update-manifest.json'),'oldUpdaterSHA256':p['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']}}
 parent=A/'tools/deploy_original_bootstrap_r45.py';deny=(R/'Document/Deployment/public_test_original_bootstrap_r45_20261104/delivery/web.config').read_bytes()
 assert hashlib.sha256(deny).hexdigest()=='22013fec240c04fc2a73a6274220772c3cbcf5b00fb71df75557e0e75baedd20'
 delivery=D/'delivery';delivery.mkdir(parents=True)
 archive=delivery/'Zhumadian_Home_Transfer_20261104_R46.zip'
 def put(z,n,b):
  i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
 with zipfile.ZipFile(archive,'x')as z:
  put(z,'web.config',deny);put(z,'variants/r45/update-manifest.json',(B/'update-manifest.json').read_bytes())
  for n,pin in p['files'].items():
   b=(B/'payload'/n).read_bytes();assert len(b)==pin['bytes']and hashlib.sha256(b).hexdigest()==pin['SHA256'];put(z,'payload/'+n,b)
 with zipfile.ZipFile(archive)as z:assert len(z.infolist())==9
 text=parent.read_text('utf8');tree=ast.parse(text);assign={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
 static=ast.literal_eval(assign['STATIC_EXPECTED'].value)
 for n,pin in p['files'].items():
  if n.startswith('frontend/security_pc/assets/'):
   ext=Path(n).suffix;static['/zhumadian/branding-20261025/'+n.removeprefix('frontend/security_pc/') ]={'decodedBytes':pin['bytes'],'decodedSHA256':pin['SHA256'],'encoding':'identity','mime':{'.css':'text/css','.webp':'image/webp','.woff2':'font/woff2'}[ext]}
 assert len(static)==8
 for n,val in {'ARCHIVE_SHA':sha(archive),'ARCHIVE_NAME':archive.name,'NEW':p['newReleaseSHA256'],'UPDATER_SHA':sha(source),'BASES':base,'STATIC_EXPECTED':static}.items():
  oldtext=ast.get_source_segment(text,assign[n]);assert text.count(oldtext)==1;text=text.replace(oldtext,n+'='+repr(val))
 # Normalize only the wrapper's own version labels; keep the R37 static contract symbol.
 text=text.replace('R45','R46').replace('r45','r46').replace('ONLY_EXACT_R36_OR_R37_BASE','ONLY_EXACT_R45_BASE')
 text=text.replace('EXACT_CHANGE_SET_SIZE', 'EXACT_SEVEN_WRITE_ZERO_REMOVAL_SET')
 needle="len(selected['files'])==196 and len(selected['removedFrontendFiles'])==181";assert text.count(needle)==1;text=text.replace(needle,"len(selected['files'])==7 and len(selected['removedFrontendFiles'])==0")
 needle="    expected=STATIC_EXPECTED[path]\n";assert text.count(needle)==1
 text=text.replace(needle,needle+"    if 'mime' in expected:need(headers.get('content-type','').split(';',1)[0].strip().lower()==expected['mime'],'STATIC_EXPECTED_MIME')\n")
 needle="            code,headers,body=fetch(channel,path,'gzip');r=validate_static_response(path,'gzip',code,headers,body);r.update(channel=channel,resource=path);rows.append(r)";assert text.count(needle)==1
 text=text.replace(needle,"            encoding=STATIC_EXPECTED[path].get('encoding','gzip')\n            code,headers,body=fetch(channel,path,encoding);r=validate_static_response(path,encoding,code,headers,body);r.update(channel=channel,resource=path);rows.append(r)")
 needle="    result={'passed':True,'checks':rows";assert text.count(needle)==1
 marker="            if path=='/zhumadian/home':need(b'data-xnby-home-transfer=\"r894\"' in body and b'/zhumadian/branding-20261025/assets/css/xnby-home-transfer-162b8ebe4004d78f.css' in body,'EXACT_HOME_TRANSFER_STYLE_REQUIRED')\n"
 text=text.replace(needle,marker+needle)
 # Labels inside BASES must describe the old R45 release, never the new revision.
 nowassign={n.targets[0].id:n for n in ast.parse(text).body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
 oldtext=ast.get_source_segment(text,nowassign['BASES']);text=text.replace(oldtext,'BASES='+repr(base))
 normalized=parent.read_text('utf8').replace('R45','R46').replace('r45','r46')
 funcs=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(t).body if isinstance(n,ast.FunctionDef)}
 f0,f1=funcs(normalized),funcs(text);assert f0.keys()==f1.keys()
 changed=[n for n in f0 if f0[n]!=f1[n]];assert set(changed)=={'validate_static_response','verify_static_gateway_and_iis','validate_archive','select_installed_base'}
 wrapper=delivery/'deploy_home_transfer_r46.py';wrapper.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
 (delivery/'r46_update_runtime.py').write_bytes(source.read_bytes());(delivery/'web.config').write_bytes(deny)
 for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
  (delivery/(label+'_Home_Transfer_R46.cmd')).write_bytes(('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_home_transfer_r46.py" '+flag+'\r\n').encode('ascii'))
 prefix='C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/payload/'
 maxpath=max(len(prefix+n)for n in p['files']);assert maxpath<240
 manifest={'revision':'R46-lossless-home-background-and-complete-font','targetFTP':'/Zhumadian/Zhumadian_Home_Transfer_20261104_R46/',
  'targetApplication':p['targetApplication'],'files':{f.name:{'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted(delivery.iterdir())},
  'acceptedExactBases':base,'newReleaseSHA256':p['newReleaseSHA256'],'newPayloadManifestSHA256':p['newPayloadManifestSHA256'],'newUpdaterSHA256':sha(source),
  'writes':7,'removedFiles':0,'writePaths':list(p['files']),'oldAndNewOriginalReadinessReports':11,
  'runtimeChangedExistingFunctions':['load_bundle'],'runtimeAddedContractFunction':'r46_home_bundle_contract','runtimeUnchangedFunctionBodies':80,
  'wrapperChangedFunctionsAfterVersionLabelNormalization':changed,'originalStopStartHealthRecoveryAuthMapperPoolBodiesRetained':True,
  'normalOriginalSDKUIAssertionsIncludingRepeatedStages':18,'actualGatewayChecksFromFullApp':10,'staticDOMRenderAllPixelsEqualAtThreeResolutions':True,
  'sourceAssetsBackgroundPixelsICCEXIFAndAll7194FontGlyphsRetained':True,'sourceImagesAndFontRetainedForOtherReferences':True,
  'normalAndFourthWriteRecoveryPassed':True,'negativeFileCases':14,'archiveMembers':9,'maximumExtractionPathCharacters':maxpath,
  'serverGatewayAndIISTLSChecksExpected':22,'transportVerificationStillPending':True,
  'remaining':['actual server baseline and three-dimensional route rediscovery','public HTTPS asset identity and MIME/cache','normal-login cold/warm public experience','favicon 404 and module/API latency','all actual Nangang business templates'],
  'limitedResultReadbackFile':'r46-scoped-result.json','publicDeployed':False,'newPublicGitIncluded':False,'fullCloneReady':False}
 (D/'delivery-manifest.json').write_bytes(enc(manifest));(delivery/'delivery-manifest.json').write_bytes(enc(manifest))
 report={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(f.stat().st_size for f in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),
  'archiveSHA256':sha(archive),'wrapperSHA256':sha(wrapper),'builderSHA256':sha(Path(__file__)),'archiveMembers':9,'maximumExtractionPathCharacters':maxpath,'transportVerificationPending':True,'uploadedOrDeployed':False}
 (D/'preparation-result-r916.json').write_bytes(enc(report));print(json.dumps(report))
if __name__=='__main__':main()
