import fs from 'node:fs/promises';import path from 'node:path';import http from 'node:http';import{spawn}from'node:child_process';import{createRequire}from'node:module';import{createHash}from'node:crypto';
const R='D:/Project/Zhumadian',src=R+'/Application/work/tianjin_native_20261023/security_pc',root=R+'/work/user_feedback_20261031/workflow-initiator-r61',req=createRequire(src+'/package.json'),sfc=req('@vue/compiler-sfc'),sass=req('sass'),esbuild=req('esbuild');
const run=process.argv[2]||'browser-r1';if(!/^browser-r[1-9]\d*$/.test(run))throw Error('OWN_RUN_NAME_REQUIRED');const out=root+'/'+run;await fs.mkdir(out,{recursive:false});
const sha=b=>createHash('sha256').update(b).digest('hex'),pins=JSON.parse(await fs.readFile(root+'/source-pins.json')),sourcePins={};
for(const[n,p]of Object.entries(pins))if(sha(await fs.readFile(root+'/'+n))!==p)throw Error('SFC_SOURCE_DRIFT');
const doubles={
 user:'const store={info:{userId:"own-user-a"},async fetchUserInfo(){window.__identityFetches=(window.__identityFetches||0)+1;this.info={userId:"own-user-a"}}};window.__identity=store;export function useUserStore(){return store}',
 api:'const invoke=(name,p)=>{window.__calls.push({name,params:JSON.parse(JSON.stringify(p))});return Promise.resolve({list:[{id:"own-row"}],pagination:{currentPage:p.currentPage,pageSize:p.pageSize,total:40}})};export const flowLaunch=p=>invoke("launch",p),flowBefore1=p=>invoke("pending",p),flowBefore2=p=>invoke("completed",p),flowMonitor=p=>invoke("monitor",p);',
 router:'export function useRouter(){return{push:value=>window.__nav.push(value)}}',
 utils:'export function handleProp(prop){const fields=prop.split(".");return fields[fields.length-1]}',
 picker:'import{h,ref}from"vue";export default{setup(p,{emit,expose}){const show=ref(false);expose({acceptParams(){show.value=true}});const choose=data=>{emit("checkData",data);show.value=false};return()=>show.value?h("div",{"data-own-picker":"true",style:{position:"fixed",inset:"200px 30px auto",background:"white",zIndex:99999}},["a","b","empty","cancel"].map(key=>h("button",{"data-pick":key,onClick:()=>key==="cancel"?show.value=false:choose(key==="empty"?[]:[{id:"own-user-"+key,fullName:"Own synthetic "+key.toUpperCase()}])},key))):null}}',
 page:'import{h}from"vue";export default{props:["pageable","handleCurrentChange","handleSizeChange"],setup(p){return()=>h("button",{"data-next":"true",onClick:()=>p.handleCurrentChange(2)},"第2页")}}',
 list:'import{h}from"vue";export default{props:["data","loading","type"],setup(p,{emit}){return()=>h("button",{"data-route":"true","data-row-count":p.data.length,onClick:()=>emit("to",{id:"own-row",flowId:"own-flow"})},"自有合成流程")}}'
};
for(const mode of ['baseline','candidate']){
 const entry=out+'/'+mode+'-entry.js';
 await fs.writeFile(entry,[
  'import{createApp,h,ref,nextTick}from"vue";import ElementPlus from"element-plus";import"element-plus/dist/index.css";',
  'import Workflow from '+JSON.stringify(root+'/'+mode+'-index.vue')+';',
  'window.__calls=[];window.__nav=[];window.__errors=[];window.addEventListener("error",e=>window.__errors.push(e.message));window.addEventListener("unhandledrejection",e=>window.__errors.push(String(e.reason)));',
  'const type=ref("待办事宜");const app=createApp({setup(){return()=>h(Workflow,{key:type.value,type:type.value,to:"/own-detail",flowCategory:"OWN_CATEGORY",listParameters:"id,flowId",fixedParameters:{ownFixed:"retained"}})}});app.config.errorHandler=e=>window.__errors.push(String(e));app.use(ElementPlus);app.mount("#app");window.__type=async value=>{type.value=value;await nextTick()};window.__ready=true;'
 ].join('\n'));
 const plugin={name:'original-workflow-query-components',setup(b){
  b.onResolve({filter:/^@\/api\/workFlow$/},()=>({path:'api',namespace:'fixture'}));
  b.onResolve({filter:/^@\/store\/modules\/user$/},()=>({path:'user',namespace:'fixture'}));
  b.onResolve({filter:/^vue-router$/},a=>a.importer.endsWith('-index.vue')?{path:'router',namespace:'fixture'}:undefined);
  b.onResolve({filter:/^\.\.\/\.\.\/user-select\/index.vue$/},()=>({path:'picker',namespace:'fixture'}));
  b.onResolve({filter:/^\.\/components\/(list|pagination)\.vue$/},a=>({path:a.path.includes('pagination')?'page':'list',namespace:'fixture'}));
  b.onResolve({filter:/^\.\/components\/searchForm\.vue$/},()=>({path:root+'/'+mode+'-searchForm.vue'}));
  b.onResolve({filter:/^@\/utils$/},()=>({path:'utils',namespace:'fixture'}));
  b.onResolve({filter:/^@\//},a=>({path:src+'/src/'+a.path.slice(2)}));
  b.onLoad({filter:/.*/,namespace:'fixture'},a=>({loader:'js',resolveDir:src,contents:doubles[a.path]}));
  b.onLoad({filter:/\.vue$/},async a=>{
   const raw=await fs.readFile(a.path,'utf8');sourcePins[a.path]=sha(raw);const id='data-v-'+sha(a.path).slice(0,8),d=sfc.parse(raw,{filename:a.path}).descriptor,script=sfc.compileScript(d,{id,genDefaultAs:'__sfc__',inlineTemplate:true});
   const css=d.styles.map(x=>sfc.compileStyle({source:x.lang==='scss'?sass.compileString(x.content).css:x.content,id,scoped:x.scoped,filename:a.path}).code).join('\n');
   return{loader:'ts',resolveDir:path.dirname(a.path),contents:script.content+'\n__sfc__.__scopeId='+JSON.stringify(id)+';export default __sfc__;const style=document.createElement("style");style.textContent='+JSON.stringify(css)+';document.head.append(style)'};
  });
 }};
 await esbuild.build({entryPoints:[entry],outfile:out+'/'+mode+'/entry.js',bundle:true,format:'esm',platform:'browser',nodePaths:[src+'/node_modules'],plugins:[plugin],logLevel:'warning',define:{'process.env.NODE_ENV':'"production"','__VUE_OPTIONS_API__':'true','__VUE_PROD_DEVTOOLS__':'false','__VUE_PROD_HYDRATION_MISMATCH_DETAILS__':'false'}});
}
const server=http.createServer(async(q,s)=>{try{
 const u=new URL(q.url,'http://localhost').pathname;if(['/baseline','/candidate'].includes(u)){s.setHeader('Content-Type','text/html;charset=utf-8');s.end('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="'+u+'/entry.css"><style>body{margin:24px}.table-search{padding:18px}</style><div id="app"></div><script type="module" src="'+u+'/entry.js"></script>');return}
 const p=path.resolve(out,'.'+u);if(!p.startsWith(path.resolve(out)+path.sep))throw Error('FILE_SCOPE');s.setHeader('Content-Type',p.endsWith('.css')?'text/css':'text/javascript');s.end(await fs.readFile(p));
 }catch{s.writeHead(404);s.end()}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base='http://127.0.0.1:'+server.address().port,profile=out+'/headless-owned-profile',sleep=ms=>new Promise(r=>setTimeout(r,ms)),pending=new Map(),results=[];
let chrome,ws,session,seq=0,exitPromise,exit,passed=false,failure;
function send(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++seq,t=setTimeout(()=>{pending.delete(id);reject(Error('CDP_TIMEOUT_'+method))},15000);pending.set(id,{resolve:r=>{clearTimeout(t);resolve(r)},reject});ws.send(JSON.stringify({id,method,params,...sessionId?{sessionId}:{}}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails){await fs.writeFile(out+'/evaluation-failure.json',JSON.stringify(r.exceptionDetails));throw Error('OWN_BROWSER_JS_FAILED')}return r.result.value}
async function until(fn,timeout=15000){const end=Date.now()+timeout;while(!await fn()){if(Date.now()>end)throw Error('OWN_WAIT_TIMEOUT');await sleep(40)}}
async function click(expression){await evaluate(expression+'.click()');await sleep(90)}
async function last(){return evaluate('window.__calls[window.__calls.length-1]')}
async function search(expectAPI=true){const n=await evaluate('window.__calls.length');await click('[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==="搜索")');if(expectAPI)await until(()=>evaluate('window.__calls.length>'+n));else await until(()=>evaluate('document.querySelector("[data-row-count]").getAttribute("data-row-count")==="0"'));return expectAPI?last():{noAPI:await evaluate('window.__calls.length==='+n),empty:true}}
async function pick(value){await click('document.querySelector(".el-select")');await until(()=>evaluate('!!document.querySelector("[data-own-picker]")'));await click('document.querySelector("[data-pick='+value+']")')}
function check(ok,label,proof={}){results.push({case:label,passed:!!ok,...proof});if(!ok)throw Error('CANDIDATE_FAILED_'+label)}
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});exitPromise=new Promise(r=>chrome.once('exit',(code,signal)=>r({code,signal})));
 let active;await until(async()=>{try{active=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});
 ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});ws.addEventListener('message',e=>{const x=JSON.parse(e.data),p=pending.get(x.id);if(p){pending.delete(x.id);x.error?p.reject(Error('CDP_ERROR')):p.resolve(x.result)}});
 const t=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;await send('Runtime.enable',{},session);await send('Page.enable',{},session);await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false},session);
 for(const mode of ['baseline','candidate']){
  await send('Page.navigate',{url:base+'/'+mode},session);await until(()=>evaluate('window.__ready&&window.__calls.length>0'));
  for(const type of mode==='baseline'?['待办事宜']:['待办事宜','我已处理','流程监控','我发起的']){
   if(type!=='待办事宜'){await evaluate('window.__type('+JSON.stringify(type)+')');await sleep(160)}
   await evaluate('[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==="更多")?.click()');await sleep(90);
   await click('document.querySelector("[data-next]")');await pick('a');
   const labelShown=await evaluate('document.querySelector(".el-select").textContent.includes("Own synthetic A")'),selected=await search();
   if(mode==='baseline'){check(selected.params.region==='Own synthetic A'&&!selected.params.creatorUserId&&selected.params.currentPage===2,'baseline-loses-ID-and-keeps-page2',{labelShown,request:selected});continue}
   check(labelShown&&selected.params.creatorUserId==='own-user-a'&&!('region'in selected.params)&&selected.params.currentPage===1,type+'-ID-query-first-page',{request:selected});
   await click('document.querySelector("[data-next]")');const next=await last();check(next.params.currentPage===2&&next.params.creatorUserId==='own-user-a',type+'-pagination-retains-ID',{});
   await pick('cancel');check((await search()).params.creatorUserId==='own-user-a',type+'-cancel-preserves-selection');
   await pick('b');const other=await search(type!=='我发起的');check(type==='我发起的'?other.noAPI&&other.empty:other.params.creatorUserId==='own-user-b'&&other.params.currentPage===1,type+'-switch-person',{request:other});
   await evaluate('document.querySelector(".el-select").dispatchEvent(new MouseEvent("mouseenter",{bubbles:false}))');await sleep(100);await until(()=>evaluate('!!document.querySelector(".el-select__clear")'));
   await click('document.querySelector(".el-select__clear")');const cleared=await search();check(!('creatorUserId'in cleared.params)&&!('region'in cleared.params),type+'-native-clear',{request:cleared});
   await pick('a');await pick('empty');check(!('creatorUserId'in(await search()).params),type+'-empty-selection-clears-ID');
   await pick('b');const n=await evaluate('window.__calls.length');await click('[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==="重置")');await until(()=>evaluate('window.__calls.length>'+n));const reset=await last();check(!('creatorUserId'in reset.params)&&reset.params.currentPage===1,type+'-reset',{request:reset});
   await click('document.querySelector("[data-route]")');const nav=await evaluate('window.__nav[window.__nav.length-1]');check(nav.path==='/own-detail'&&nav.query.id==='own-row'&&nav.query.flowId==='own-flow'&&nav.query.ownFixed==='retained',type+'-original-navigation');
   check((await last()).name===({'待办事宜':'pending','我已处理':'completed','流程监控':'monitor','我发起的':'launch'}[type])&&(await last()).params.flowCategory==='OWN_CATEGORY',type+'-API-category');
   if(type==='我发起的'){
    await evaluate('window.__identity.info=null');await pick('a');const recovered=await search();
    check(recovered.params.creatorUserId==='own-user-a'&&await evaluate('window.__identityFetches===1'),'my-initiated-normal-current-user-refresh');
   }
  }
  await fs.writeFile(out+'/'+mode+'.png',Buffer.from((await send('Page.captureScreenshot',{format:'png'},session)).data,'base64'));const errors=await evaluate('window.__errors');if(errors.length){await fs.writeFile(out+'/browser-errors.json',JSON.stringify(errors));throw Error('OWN_BROWSER_ERRORS')}
 }
 passed=true;
}catch(e){failure=String(e.message||e)}
finally{
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}}
 if(exitPromise)exit=await Promise.race([exitPromise,sleep(10000).then(()=>({timeout:true}))]);ws?.close();await new Promise(r=>server.close(r));
 await fs.writeFile(out+'/browser-terminal.json',JSON.stringify({exit,normalBrowserClosed:exit?.code===0,forced:false},null,2));
 await fs.writeFile(out+'/result.json',JSON.stringify({passed:passed&&exit?.code===0,failure,results,sourcePins,actualOriginalWorkflowParentSearchGenericGridAndElementPlus:true,testDoubles:Object.keys(doubles),nativeSDKHTTPResultsClaimedHere:false,publicChanged:false},null,2));
}
if(!passed||exit?.code!==0)throw Error(failure||'OWN_COMPONENT_OR_BROWSER_FAILED');console.log('ORIGINAL_WORKFLOW_INITIATOR_COMPONENT_PASSED',results.length);
