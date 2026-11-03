from pathlib import Path
import ast,json
V=Path(__file__).parent;D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_personal_workflow_r35_20261103')
outer=json.loads((D/'public-ui-r202-outer-terminal.json').read_bytes());result=json.loads((D/'public-ui-r202/result.json').read_bytes());assert outer['actualDescendantsZeroBeforeClose']and result['normalChromeExitCode']==0
s=(V/'verify_public_personal_workflow_r202.mjs').read_text(encoding='utf-8').replace('public-ui-r202','public-ui-r203')
s=s.replace("PROFILE=O+'/chrome-profile'","PROFILE=D+'/public-ui-r202/chrome-profile'")
old="await send('Page.reload',{ignoreCache:true},session);await until(()=>evaluate('(document.body?.textContent||\"\").includes(\"审批记录\")&&!!document.querySelector(\".left-content .form-content\")'));"
new="const oldLoader=(await send('Page.getFrameTree',{},session)).frameTree.frame.loaderId;await send('Page.reload',{ignoreCache:true},session);await until(async()=>(await send('Page.getFrameTree',{},session)).frameTree.frame.loaderId!==oldLoader);await until(()=>evaluate('document.readyState===\"complete\"&&(document.body?.textContent||\"\").includes(\"审批记录\")&&!!document.querySelector(\".left-content .form-content\")'));"
assert s.count(old)==1;s=s.replace(old,new)
p=V/'verify_public_personal_workflow_r203.mjs';assert not p.exists();p.write_text(s,encoding='utf-8')
s=(V/'run_public_personal_workflow_r202.py').read_text(encoding='utf-8').replace('r202','r203');ast.parse(s);p=V/'run_public_personal_workflow_r203.py';assert not p.exists();p.write_text(s,encoding='utf-8')
print('WAIT_ACTUAL_CHANGED_DOCUMENT_LOADER_BEFORE_DETAIL_RELOAD_ASSERTIONS_REUSE_ONLY_TERMINAL_OWN_PROFILE')
