import fs from'node:fs/promises';
const D='D:/Project/Zhumadian/Document/Deployment/public_test_personal_workflow_r35_20261103',profile=D+'/public-ui-r202/chrome-profile';
const started=JSON.parse(await fs.readFile(D+'/public-ui-r203/browser-started.json','utf8'));
if(!started.ownedIsolatedProfile||!Number.isInteger(started.pid))throw Error('OWN_BROWSER_START_PROOF_REQUIRED');
const data=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split('\n');
if(!/^\d{4,5}$/.test(data[0])||!/^\/devtools\/browser\/[0-9a-f-]{36}$/.test(data[1]))throw Error('EXACT_OWN_BROWSER_ENDPOINT_REQUIRED');
const ws=new WebSocket('ws://127.0.0.1:'+data[0]+data[1]);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',()=>reject(Error('OWN_BROWSER_ENDPOINT_UNAVAILABLE')),{once:true});});
ws.send(JSON.stringify({id:1,method:'Browser.close'}));await new Promise(resolve=>ws.addEventListener('close',resolve,{once:true}));
console.log(JSON.stringify({normalBrowserCloseRequested:true,ownedBrowserPID:started.pid,forceTerminationUsed:false}));
