from pathlib import Path
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
for tag,intercept in [('r956',True),('r957',False)]:
 p=V/('test_stable_download_click_'+tag+'.mjs');assert not p.exists() and not(R/'work'/('dl'+tag[1:])).exists()
 s=(V/'test_stable_download_click_r954.mjs').read_text('utf8')
 old="new URL('./stable-download-test-r954/',import.meta.url)";assert s.count(old)==1;s=s.replace(old,"new URL('file:///D:/Project/Zhumadian/work/dl"+tag[1:]+"/')")
 s=s.replace('own-download-r954.bin','own-download-'+tag+'.bin')
 if not intercept:
  old="await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);";assert s.count(old)==1;s=s.replace(old,'/* Self-authored localhost-only mechanism fixture: no Fetch interception. */')
  s=s.replace('actualFetchInterceptionEnabled:true','actualFetchInterceptionEnabled:false')
 p.write_text(s,encoding='utf8')
 s=(V/'run_stable_download_test_r954.py').read_text('utf8').replace('test_stable_download_click_r954.mjs','test_stable_download_click_'+tag+'.mjs')
 s=s.replace("not(V/'stable-download-test-r954').exists()","not(R/'work/dl"+tag[1:]+"').exists()")
 s=s.replace('stable-download-r954.private.log','stable-download-'+tag+'.private.log').replace('stable-download-terminal-r954.json','stable-download-terminal-'+tag+'.json')
 p=V/('run_stable_download_test_'+tag+'.py');assert not p.exists();p.write_text(s,encoding='utf8')
print('PREPARED_TWO_ISOLATED_SHORT_PATH_VARIANTS_NO_SERVICE_OR_BUSINESS_ACCESS')
