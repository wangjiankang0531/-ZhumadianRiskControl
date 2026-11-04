"""Extend the actual normal-role R45 browser probe with security-home asset checks."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;H=V/'home_full_r905';R=Path('D:/Project/Zhumadian');A=R/'Application'
D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();J=lambda p:json.loads(p.read_bytes())
source=A/'tools/verify_r45_original_backend_browser_r850.mjs';s=source.read_text('utf8')
assert not(H/'verify_home_transfer_browser_r906.mjs').exists()
assert s.count("const O='D:/Project/Zhumadian/work/bootstrap-browser-r850'")==1
s=s.replace("const O='D:/Project/Zhumadian/work/bootstrap-browser-r850'","const O='D:/Project/Zhumadian/work/home-browser-r906'")
a='function observe(v){';assert s.count(a)==1
s=s.replace(a,"const homeResourceRequests=[];let homeAssetObservation=false;\n"+a+"\n if(homeAssetObservation&&v.method==='Network.requestWillBeSent'){const u=new URL(v.params.request.url);if(u.origin===w.base&&u.pathname.includes('/assets/'))homeResourceRequests.push(u.pathname);}\n")
insertion=r'''
 // The original emergency login, lists, native detail/refresh and logout above
 // remain unchanged. This second login uses the original security application.
 stage='normal-security-original-login';token='';current=null;homeAssetObservation=true;
 await send('Page.navigate',{url:w.base+'/zhumadian/home'},session);
 await until(()=>evaluate('location.pathname==="/zhumadian/login"&&document.querySelectorAll(".login-body input").length===3'));
 await evaluate(`(()=>{const values=${JSON.stringify([w.account,w.password,'0000'])};document.querySelectorAll('.login-body input').forEach((e,i)=>{e.value=values[i];e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));});const b=Array.from(document.querySelectorAll('.login-body button')).find(e=>e.textContent.trim()==='登录');if(!b)throw Error('NORMAL_SECURITY_LOGIN_BUTTON_REQUIRED');b.click()})()`);
 await until(()=>token&&current);cases.push({case:'original-security-normal-nonadmin-login',passed:true});
 async function homeCheck(){
  await until(()=>evaluate('location.pathname==="/zhumadian/home"&&document.querySelectorAll(".card-container .card-item").length===3'));
  await evaluate('document.fonts.ready.then(()=>true)');
  await until(()=>evaluate('[...document.fonts].some(f=>f.family==="YouSheBiaoTiHei"&&f.status==="loaded")'));
  const state=await evaluate('(()=>{const b=document.querySelector(".background-pattern"),t=document.querySelector("header .title");return{title:t?.textContent?.trim(),font:t?getComputedStyle(t).fontFamily:null,background:b?getComputedStyle(b).backgroundImage:null,overlay:!!document.querySelector("link[data-xnby-home-transfer]"),cards:document.querySelectorAll(".card-container .card-item").length}})()');
  if(state.title!=='驻马店重大风险防控'||!state.font?.includes('YouSheBiaoTiHei')||!state.background?.includes('home-background-415f7103fab4437c.webp')||!state.overlay||state.cards!==3)throw Error('ORIGINAL_HOME_WITH_NEW_LOSSLESS_ASSETS_REQUIRED');
 }
 stage='original-security-home-render';await homeCheck();
 cases.push({case:'original-security-home-cards-title-and-new-background-render',passed:true});
 stage='original-security-home-refresh';await send('Page.navigate',{url:w.base+'/zhumadian/home'},session);await homeCheck();
 await until(()=>homeResourceRequests.some(p=>p.endsWith('YouSheBiaoTiHei-7af84bf1c97ae44e.woff2')));
 if(homeResourceRequests.some(p=>p.endsWith('/YouSheBiaoTiHei-fahbdFno.ttf')||p.endsWith('/background-BHYqFd8n.png')))throw Error('UNUSED_OLD_LARGE_HOME_RESOURCE_REQUESTED');
 cases.push({case:'original-security-home-refresh-uses-woff2-webp-without-old-large-assets',passed:true});
 await Promise.all([...reads]);if(problem)throw Error(problem);if(exceptions.length)throw Error('ORIGINAL_SECURITY_COMPILED_UI_EXCEPTION');
 stage='original-security-header-logout';
 if(!await evaluate('!!document.querySelector("header .user img")'))throw Error('ORIGINAL_SECURITY_LOGOUT_CONTROL_REQUIRED');
 await evaluate('document.querySelector("header .user img").click()');
 await until(()=>evaluate('!!document.querySelector(".el-message-box__btns .el-button--primary")'));
 await evaluate('document.querySelector(".el-message-box__btns .el-button--primary").click()');
 await until(()=>evaluate('location.pathname==="/zhumadian/login"&&document.querySelectorAll(".login-body input").length===3'));
 cases.push({case:'original-security-header-logout-preserves-original-business-login',passed:true});
 await Promise.all([...reads]);if(problem)throw Error(problem);
'''
marker=' proof={passed:true,mode:w.mode,cases,requests,actualCompiledApplicationAndOriginalSDK:true,APIsMocked:false,'
assert s.count(marker)==1;s=s.replace(marker,insertion+'\n'+marker)
s=s.replace('credentialOrTokenPersistedInProof:false,loginVisibleMs,','credentialOrTokenPersistedInProof:false,homeResourceRequests:[...new Set(homeResourceRequests)],normalSecurityHomeOriginalSDKAccepted:true,cacheAndTimingAcceptedByThisInterceptedProbe:false,loginVisibleMs,')
out=H/'verify_home_transfer_browser_r906.mjs';out.write_text(s,encoding='utf8')
assert subprocess.run(['node','--check',str(out)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
files=[*H.glob('*.py'),out]
for p in files:
 if p.suffix=='.py':ast.parse(p.read_bytes(),filename=p.name)
pins={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'originalBrowserSourceSHA256':sha(source),
 'files':{str(p):sha(p) for p in files},'normalRoleLoginAndOriginalSDKStillPending':True,'readOnlyOriginalAPIGuardRetained':True,
 'expectedAdditionalSecurityUICases':4,'cacheBehaviorNotClaimedBecauseRequestInterceptionRemainsEnabled':True}
(H/'home-transfer-source-pins-r906.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'helperSources':len(files),'normalOriginalSDKStillPending':True,'servicesStarted':False}))
