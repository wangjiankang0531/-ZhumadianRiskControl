import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
const R='D:/Project/Zhumadian',variant=process.argv[2];if(!['baseline','candidate'].includes(variant))throw Error('EXACT_OWN_COMPONENT_VARIANT');
const W=R+'/work/plan-resource-cancel-r375',O=W+'/'+variant,P=R+'/Application/work/tianjin_native_20261023/emergency_pc',require=createRequire(P+'/package.json');
const esbuild=require('esbuild'),sfc=require('@vue/compiler-sfc'),pause=ms=>new Promise(r=>setTimeout(r,ms));
await fs.mkdir(O,{recursive:true});await fs.writeFile(O+'/run-started.json',JSON.stringify({variant,headlessComponentOnly:true}),{flag:'wx'});
const sourceRoot=variant==='baseline'?R+'/Application/source-review/emergency-plan-exercise-r224/src/views/emergencyPlans/structured/components':W+'/candidate-sources';
const site=O+'/site';await fs.mkdir(site);
for(const kind of ['goodsList','teamsList','expertsList'])await fs.copyFile(sourceRoot+'/'+kind+'.vue',site+'/'+kind+'.vue');
await fs.writeFile(site+'/TableStub.ts',`import{defineComponent,h}from'vue';export default defineComponent({props:['data','columns'],setup(p,{slots}){return()=>h('div',{'data-own-table':'true'},(p.data||[]).map((row,index)=>h('div',{'data-own-row':index},slots.operation?.({row,$index:index}))));}});`);
await fs.writeFile(site+'/ApiStub.ts',`import{ref}from'vue';export const getPage=async()=>{throw Error('RESOURCE_GET_NOT_PART_OF_CANCEL_COMPONENT_TEST')};export const useDict=()=>({goodsTypeData:ref([]),inspectionCategory:ref([])});`);
await fs.writeFile(site+'/entry.ts',`import{createApp,h,ref}from'vue';import ElementPlus from'element-plus';import'element-plus/dist/index.css';import Goods from'./goodsList.vue';import Teams from'./teamsList.vue';import Experts from'./expertsList.vue';
const lists={goods:ref([{id:'OWN_CANCEL_GOODS'}]),teams:ref([{id:'OWN_CANCEL_TEAMS'}]),experts:ref([{id:'OWN_CANCEL_EXPERTS'}])},deletes=[],unhandled=[],errors=[];
window.addEventListener('unhandledrejection',e=>{unhandled.push(String(e.reason));e.preventDefault()});window.addEventListener('error',e=>errors.push(String(e.message)));
const components={goods:Goods,teams:Teams,experts:Experts};const app=createApp({setup(){return()=>h('main',Object.entries(components).map(([kind,c])=>h('section',{'data-own-kind':kind},[h(c,{list:lists[kind].value,onDelete:index=>{deletes.push({kind,index});lists[kind].value.splice(index,1)}})])))}});app.use(ElementPlus);app.mount('#app');window.fixture={deletes,unhandled,errors,counts:()=>Object.fromEntries(Object.entries(lists).map(([k,v])=>[k,v.value.length]))};`);
await esbuild.build({absWorkingDir:P,entryPoints:[site+'/entry.ts'],outdir:site,bundle:true,format:'esm',platform:'browser',minify:false,logLevel:'silent',nodePaths:[P+'/node_modules'],define:{'process.env.NODE_ENV':'"production"','__VUE_OPTIONS_API__':'true','__VUE_PROD_DEVTOOLS__':'false','__VUE_PROD_HYDRATION_MISMATCH_DETAILS__':'false'},plugins:[{
 name:'exact-resource-components',setup(build){
  build.onResolve({filter:/^@\//},args=>({path:args.path.includes('/ProTable/')?site+'/TableStub.ts':site+'/ApiStub.ts'}));
  build.onLoad({filter:/\.vue$/},async args=>{const code=await fs.readFile(args.path,'utf8'),parsed=sfc.parse(code,{filename:args.path});if(parsed.errors.length)throw parsed.errors[0];const compiled=sfc.compileScript(parsed.descriptor,{id:'own-cancel-'+path.basename(args.path),inlineTemplate:true});return{contents:compiled.content,loader:'tsx',resolveDir:path.dirname(args.path)};});
 }}]});
await fs.writeFile(site+'/index.html',`<!doctype html><meta charset=utf-8><link rel=stylesheet href=/entry.css><div id=app></div><script type=module src=/entry.js></script>`);
const requests=[];const server=http.createServer(async(req,res)=>{const name={'/':'index.html','/entry.js':'entry.js','/entry.css':'entry.css'}[req.url];requests.push({path:req.url,allowed:!!name});if(!name){res.writeHead(404);res.end();return;}try{res.setHeader('Content-Type',name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html');res.end(await fs.readFile(site+'/'+name));}catch{res.writeHead(500);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;
let chrome,ws,session,seq=0,stage='launch',failure=null;const pending=new Map(),cases=[];
function send(method,params={},sid){return new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('OWN_CDP_TIMEOUT_'+method))},15000);pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw Error('OWN_COMPONENT_EVALUATE');return r.result.value;}
async function until(fn){const end=Date.now()+20000;for(;;){if(await fn())return;if(Date.now()>end)throw Error('OWN_COMPONENT_TIMEOUT_'+stage);await pause(40);}}
const box=`Array.from(document.querySelectorAll('.el-message-box')).find(e=>e.getClientRects().length)`;
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--disable-gpu','--no-first-run','--disable-sync','--disable-background-networking','--remote-debugging-port=0','--user-data-dir='+O+'/profile','about:blank'],{windowsHide:true,stdio:'ignore'});
 await until(async()=>{try{await fs.access(O+'/profile/DevToolsActivePort');return true}catch{return false}});
 const lines=(await fs.readFile(O+'/profile/DevToolsActivePort','utf8')).trim().split(/\r?\n/);ws=new WebSocket('ws://127.0.0.1:'+lines[0]+lines[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(!p)return;pending.delete(m.id);m.error?p.reject(Error('OWN_CDP_ERROR')):p.resolve(m.result)});
 const target=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;await send('Page.enable',{},session);await send('Runtime.enable',{},session);
 await send('Page.navigate',{url:'http://127.0.0.1:'+port+'/'},session);await until(()=>evaluate('!!window.fixture&&document.querySelectorAll("[data-own-kind] button").length===3'));
 for(const kind of ['goods','teams','experts']){
  for(const action of ['cancel','close','confirm']){
   stage=kind+'-'+action;const before=await evaluate('({rejected:fixture.unhandled.length,deleted:fixture.deletes.length})');
   if(!await evaluate(`(()=>{const r=document.querySelector('[data-own-kind=${kind}]'),b=Array.from(r?.querySelectorAll('button')||[]).find(e=>e.textContent.trim()==='删除');b?.click();return!!b})()`))throw Error('OWN_COMPONENT_DELETE_BUTTON');
   await until(()=>evaluate(`!!(${box})`));
   if(action==='close')await evaluate(`(${box}).querySelector('.el-message-box__headerbtn').click()`);
   else await evaluate(`Array.from((${box}).querySelectorAll('.el-message-box__btns button')).find(e=>e.textContent.trim()===${JSON.stringify(action==='cancel'?'取消':'确定')}).click()`);
   await until(()=>evaluate(`!(${box})`));await pause(120);
   const state=await evaluate('({rejected:fixture.unhandled.length,deleted:fixture.deletes.length,counts:fixture.counts(),errors:fixture.errors})');
   if(state.errors.length)throw Error('OWN_COMPONENT_UNEXPECTED_WINDOW_ERROR');
   if(action==='confirm'){
    if(state.deleted!==before.deleted+1||state.counts[kind]!==0||state.rejected!==before.rejected)throw Error('OWN_COMPONENT_CONFIRM_CONTRACT');
   }else{
    if(state.deleted!==before.deleted||state.counts[kind]!==1)throw Error('OWN_COMPONENT_CANCEL_MUTATED_SELECTION');
    const expected=variant==='baseline'?before.rejected+1:before.rejected;if(state.rejected!==expected)throw Error('OWN_COMPONENT_CANCEL_REJECTION_EXPECTATION');
   }
   cases.push({kind,action,passed:true,unhandledRejectionDelta:state.rejected-before.rejected,selectionCount:state.counts[kind]});
  }
 }
 const state=await evaluate('({rejections:fixture.unhandled,deletes:fixture.deletes,errors:fixture.errors})');
 if(state.rejections.length!==(variant==='baseline'?6:0)||state.deletes.length!==3)throw Error('OWN_COMPONENT_FINAL_COUNTS');
 await fs.writeFile(O+'/result.json',JSON.stringify({passed:true,variant,cases,actualUnhandledRejections:state.rejections.length,actualResourceSFCsAndRealElementPlusConfirmation:true,proTableAndDictionaryApiExplicitStubs:true,noBusinessBackendOrNormalRoleAcceptedByThisTest:true,publicOrFormalOrDesktopTouched:false,requests},null,2));
}catch(e){failure={stage,message:String(e.message),cases};await fs.writeFile(O+'/failure.json',JSON.stringify(failure,null,2));}
finally{
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close();}if(chrome)await new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));
 await new Promise(r=>server.close(r));await fs.writeFile(O+'/terminal.json',JSON.stringify({chromeExitCode:chrome?.exitCode,serverNormallyClosed:true,forceTerminationUsed:false}));
}
if(failure)throw Error(failure.message);console.log(JSON.stringify({variant,passed:true,cases:cases.length,actualUnhandledRejections:variant==='baseline'?6:0}));
