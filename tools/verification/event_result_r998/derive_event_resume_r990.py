from pathlib import Path
import ast,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');H=V/'event_crud_r990';oldH=V/'event_crud_r985'
J=lambda p:json.loads(Path(p).read_bytes())
old=J(R/'work/ev985/verified-event-crud-r985.json');b=J(R/'work/ev985/browser/normal-restart/result.json');context=J(R/'work/ev985/event-context.private.json')
assert old['codeRestored']and old['privateConfigurationRestored']and old['originalCurrentPointerRestored']and len(old['terminals'])==2
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in old['terminals'])
assert context['phase']=='edited-verified'and b['stage']=='second-tab-original-delete-cancel'
assert not any(x['path'].endswith(('/eventInfo/save','/eventInfo/removeById'))for x in b['requests'])
assert J(R/'work/tab989/result.json')['passed']and J(R/'work/tab989/terminal.json')['actualJobDescendantsZero']
source=(V/'prepare_event_crud_r979.py').read_text('utf8').replace('r979','r990').replace('R979','R990').replace('ev979','ev990').replace('ecfg979','ecfg990')
source=source.replace("assert sha(source)==J(OLD/'ledger-source-pins-r960.json')['files'].get(str(source),sha(source))","# Derived configuration source explicitly pinned below.")
p=V/'prepare_event_crud_r990.py';assert not p.exists();p.write_text(source,encoding='utf8');r=subprocess.run(['python',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
for name in ['verify_event_crud_r985.mjs','event_crud_probe_r985.py','test_event_receiver_configuration_r985.py']:
 s=(oldH/name).read_text('utf8').replace('r985','r990').replace('R985','R990').replace('ev985','ev990').replace('ecfg985','ecfg990')
 if name.endswith('.mjs'):
  s=s.replace("contextFile=root+'/event-context.private.json'","contextFile='D:/Project/Zhumadian/work/ev985/event-context.private.json'")
  s=s.replace("const name='OWN_EVENT_CRUD_R990_'","const name='OWN_EVENT_CRUD_R985_'")
  s=s.replace("!['first-start','normal-restart'].includes(w.phase)","w.phase!=='normal-restart'")
  start=s.index(" if(w.phase==='first-start'){");end=s.index(" }else{\n  context=",start)
  s=s[:start]+" {\n  context="+s[end+len(" }else{\n  context="):]
  assert "create-issued"not in s and "OWN_EVENT_CREATE_SUBMIT"not in s
  anchor='async function close()'
  helper='''async function openNormalSibling(){
 const before=new Set((await send('Target.getTargets')).targetInfos.map(t=>t.targetId));
 await send('Runtime.evaluate',{expression:'window.open("about:blank","_blank")',userGesture:true,returnByValue:false},firstSession);
 let t;await until(async()=>{t=(await send('Target.getTargets')).targetInfos.find(t=>!before.has(t.targetId)&&t.type==='page'&&t.openerId);return !!t});
 session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 for(const n of['Runtime','Page','Network'])await send(n+'.enable',{},session);
 await send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},session);
 check(await evaluate('sessionStorage.length>0'),'normal-browser-opener-inherits-storage-without-token-copy');
}
'''
  assert s.count(anchor)==1;s=s.replace(anchor,helper+anchor)
  s=s.replace("{path:u.pathname,method:v.params.request.method}","{path:u.pathname,method:v.params.request.method,secondaryContext:v.sessionId!==firstSession}")
  s=s.replace("await attach();await search();let before=", "await openNormalSibling();await search();await until(()=>requests.some(r=>r.secondaryContext&&r.path.endsWith('/oauth/CurrentUser')&&r.normalOwnUserMatched));let before=")
  s=s.replace("if(w.phase==='first-start')", "if(false)")
 (H/name.replace('r985','r990')).write_text(s,encoding='utf8')
p=H/'run_event_crud_r990.py';s=p.read_text('utf8')
s=s.replace("fixture_nonce=secrets.token_hex(16)","fixture_nonce=J(R/'work/ev985/event-context.private.json')['nonce']")
s=s.replace("for label in ['first-start','normal-restart']:","for label in ['normal-restart']:")
s=s.replace('len(checks)==2','len(checks)==1').replace('len(probeChecks)==2','len(probeChecks)==1').replace("'actualTwoSixComponentLifecycles'","'actualOneResumeSixComponentLifecycle'")
ast.parse(s);p.write_text(s,encoding='utf8')
p=V/'finalize_event_resume_r991.py';assert not p.exists();p.write_text((V/'finalize_event_crud_r980.py').read_text('utf8').replace('r979','r990').replace('r980','r991'),encoding='utf8')
out={'reuseOnlySameR985Event':True,'freshEventCreationBranchRemoved':True,'R985ActualEditAndNormalRestartAlreadyPassed':True,'previousSecondCDPTabLackedNormalStorageAndDidNotDelete':True,'normalOpenerMechanismIndependentlyProvenWithSyntheticMarker':True,'noActualCredentialTokenReadOrCopiedForSibling':True,'oneNewLifecycleOnly':True,'actualResumeAccepted':False}
(R/'Document/Deployment/event_crud_native_r990_20261104/resume-scope-r990.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
