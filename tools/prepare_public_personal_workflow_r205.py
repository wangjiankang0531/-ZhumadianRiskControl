from pathlib import Path
import ast,json
V=Path(__file__).parent;D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_personal_workflow_r35_20261103')
for n in ['r202','r203']:
 assert json.loads((D/('public-ui-'+n+'-outer-terminal.json')).read_bytes())['actualDescendantsZeroBeforeClose']
 assert json.loads((D/('public-ui-'+n+'/result.json')).read_bytes())['normalChromeExitCode']==0
s=(V/'verify_public_personal_workflow_r203.mjs').read_text(encoding='utf-8').replace("O=D+'/public-ui-r203'","O=D+'/public-ui-r205'")
old=" chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe'"
new=" const previousPortFile=await fs.readFile(PROFILE+'/DevToolsActivePort','utf8').catch(()=>null);\n chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe'"
assert s.count(old)==1;s=s.replace(old,new)
old="active=(await fs.readFile(PROFILE+'/DevToolsActivePort','utf8')).trim().split('\\n');return true;"
new="const current=await fs.readFile(PROFILE+'/DevToolsActivePort','utf8');if(current===previousPortFile)return false;active=current.trim().split('\\n');return true;"
assert s.count(old)==1;s=s.replace(old,new)
p=V/'verify_public_personal_workflow_r205.mjs';assert not p.exists();p.write_text(s,encoding='utf-8')
s=(V/'run_public_personal_workflow_r203.py').read_text(encoding='utf-8').replace('r203','r205');ast.parse(s);p=V/'run_public_personal_workflow_r205.py';assert not p.exists();p.write_text(s,encoding='utf-8')
print('NEW_BROWSER_REQUIRES_FRESH_DEVTOOLS_ENDPOINT_NOT_STALE_PROFILE_METADATA')
