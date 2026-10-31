import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const src='D:/Project/Zhumadian/Application/work/tianjin_native_20261023/security_pc';
const root='D:/Project/Zhumadian/work/user_feedback_20261031/workplace-chart-r1';
const req=createRequire(src+'/package.json');
const esbuild=req('esbuild'),sfc=req('@vue/compiler-sfc'),sass=req('sass');
const oldChart=src+'/src/views/workplace/components/Analysis/Chart3.vue',oldWrapper=src+'/src/components/ECharts/index.vue';
const oldTask=src+'/src/views/workplace/components/TaskList/index.vue',oldStats=src+'/src/views/workplace/components/Statistics/index.vue';
const proof=process.argv[2]||'browser-proof';
if(!/^[a-z0-9-]+$/.test(proof))throw Error('OWN_PROOF_NAME_REQUIRED');
await fs.mkdir(root+'/'+proof,{recursive:false});
const output=root+'/'+proof;
const entry=[
 "import {createApp,h,ref,nextTick} from 'vue';",
 "import {ElRadioGroup,ElRadioButton,ElTable,ElTableColumn,ElIcon} from 'element-plus';",
 "import {ArrowRight} from '@element-plus/icons-vue';",
 "import 'element-plus/dist/index.css';",
 "import Chart3 from '"+oldChart+"';",
 "import Wrapper from '"+oldWrapper+"';",
 "import TaskList from '"+oldTask+"';",
 "import Statistics from '"+oldStats+"';",
 "import echarts from '@/components/ECharts/config';",
 "window.__calls=[];window.__responses=[];window.__errors=[];window.__nav=[];window.__taskCalls=[];",
 "window.addEventListener('error',e=>window.__errors.push(e.message));",
 "window.addEventListener('unhandledrejection',e=>window.__errors.push(String(e.reason)));",
 "window.__fixture=[{name:'泄漏',value:1},{name:'物体打击',value:1},{name:'特种设备事故',value:2},{name:'触电',value:1},{name:'车辆伤害',value:1},{name:'高处坠落',value:2}];",
 "const width=ref(320),shown=ref(true),hidden=ref(true),statsWidth=ref(1200),taskWidth=ref(320);",
 "const app=createApp({setup(){return()=>h('main',[",
 " h('section',{id:'card',style:{width:width.value+'px'}},shown.value?h(Chart3):null),",
 " h('section',{id:'other',style:{width:'500px'}},h(Wrapper,{width:'calc(100% - 16px)',height:'180px',option:{series:[]}})),",
 " h('section',{id:'hidden',style:{display:hidden.value?'none':'block',width:'260px',height:'180px'}},h(Wrapper,{option:{series:[]}})),",
 " h('section',{id:'stats',style:{width:statsWidth.value+'px'}},h(Statistics)),",
 " h('section',{id:'task',style:{width:taskWidth.value+'px'}},h(TaskList))",
 "])}});",
 "for(const [name,c] of Object.entries({ElRadioGroup,ElRadioButton,ElTable,ElTableColumn,ElIcon,ArrowRight}))app.component(name,c);app.mount('#app');",
 "window.__chart=()=>echarts.getInstanceByDom(document.querySelector('#card #echarts'));",
 "window.__other=()=>echarts.getInstanceByDom(document.querySelector('#other #echarts'));",
 "window.__hidden=()=>echarts.getInstanceByDom(document.querySelector('#hidden #echarts'));",
 "window.__setWidth=async w=>{width.value=w;await nextTick()};",
 "window.__setTextWidths=async(w,t)=>{statsWidth.value=w;taskWidth.value=t;await nextTick()};",
 "window.__showHidden=async()=>{hidden.value=false;await nextTick()};",
 "window.__remount=async data=>{shown.value=false;await nextTick();window.__fixture=data;shown.value=true;await nextTick()};",
 "window.__dispose=async()=>{shown.value=false;await nextTick();window.dispatchEvent(new Event('resize'))};",
 "window.__period=async i=>{document.querySelectorAll('.el-radio-group input[type=radio]')[i].click();await nextTick()};",
 "window.__ready=true;"
].join('\n');
await fs.writeFile(root+'/entry.js',entry);
for(const candidate of [false,true]){
 const mode=candidate?'candidate':'baseline';
 const plugin={name:'actual-vue-sfc',setup(build){
  build.onResolve({filter:/^@\/api\/workplace\/index$/},()=>({path:'synthetic-api',namespace:'fixture'}));
  build.onLoad({filter:/.*/,namespace:'fixture'},args=>({loader:'js',contents:args.path==='task-api'?'export async function getTaskList(p){window.__taskCalls.push(p);return{data:{records:[{inspectionTasks:{planName:"合成巡检计划完整名称",inspectionStatus:"0"},inspectionDateStart:"2026-10-31 12:34:56"}]}}}':args.path==='task-user'?'export function useUserStore(){return{info:{departmentId:"fixture-dept"}}}':args.path==='task-router'?'export function useRouter(){return{push:p=>window.__nav.push(p)}}':'export async function getAnalysis3(args){window.__calls.push(args);const r=window.__responses.shift();if(r?.delay)await new Promise(s=>setTimeout(s,r.delay));return{data:r?r.data:window.__fixture}};export async function getStatistics1(){return{data:{totalNumber:1234567,currentNumber:0,qoqNumber:-12.5}}};export async function getStatistics2(){return{totalHiddenDanger:1234567,lastWeekTotal:0,monthOnMonthRatio:12.5}};export async function getStatistics3(){return{pendingRectificationCount:1234567,rectifyingCount:0,inApprovalCount:2}};export async function getStatistics4(){return{data:{totalNumber:1234567,currentNumber:0,qoqNumber:-12.5}}}'}));
  build.onResolve({filter:/^@\/api\/intelligentInspection\/task$/},()=>({path:'task-api',namespace:'fixture'}));
  build.onResolve({filter:/^@\/store\/modules\/user$/},()=>({path:'task-user',namespace:'fixture'}));
  build.onResolve({filter:/^vue-router$/},args=>args.importer.endsWith('/TaskList.vue')||args.importer.replaceAll('\\','/').endsWith('/TaskList/index.vue')?{path:'task-router',namespace:'fixture'}:undefined);
  build.onResolve({filter:/^@\//},args=>{
   const p=path.resolve(src+'/src',args.path.slice(2));
   if(args.path==='@/components/ECharts/config')return{path:p+'/index.ts'};
   if(candidate&&p.replaceAll('\\','/')===oldWrapper)return{path:root+'/ECharts.vue'};
   return{path:p};
  });
  build.onResolve({filter:/\.vue$/},args=>{
   let file=path.isAbsolute(args.path)?args.path:path.resolve(args.resolveDir,args.path);
   if(candidate&&file.replaceAll('\\','/')===oldChart)file=root+'/Chart3.vue';
   if(candidate&&file.replaceAll('\\','/')===oldWrapper)file=root+'/ECharts.vue';
   if(candidate&&file.replaceAll('\\','/')===oldTask)file=root+'/TaskList.vue';
   if(candidate&&file.replaceAll('\\','/')===oldStats)file=root+'/Statistics.vue';
   return{path:file};
  });
  build.onLoad({filter:/\.vue$/},async args=>{
   const text=await fs.readFile(args.path,'utf8'),id='data-v-'+createHash('sha256').update(args.path).digest('hex').slice(0,8);
   const descriptor=sfc.parse(text,{filename:args.path}).descriptor;
   const script=sfc.compileScript(descriptor,{id,genDefaultAs:'__sfc__',inlineTemplate:true,templateOptions:{transformAssetUrls:true}});
   const css=descriptor.styles.map(style=>sfc.compileStyle({source:style.lang==='scss'?sass.compileString(style.content).css:style.content,id,scoped:style.scoped,filename:args.path}).code).join('\n');
   return{loader:'ts',resolveDir:path.dirname(args.path),contents:script.content+'\n__sfc__.__scopeId='+JSON.stringify(id)+';\nexport default __sfc__;\nif(typeof document!=="undefined"){let s=document.createElement("style");s.textContent='+JSON.stringify(css)+';document.head.append(s)}'};
  });
 }};
 await esbuild.build({entryPoints:[root+'/entry.js'],outdir:output+'/'+mode,bundle:true,format:'esm',platform:'browser',
  nodePaths:[src+'/node_modules'],plugins:[plugin],logLevel:'warning',loader:{'.svg':'dataurl'},
  define:{'process.env.NODE_ENV':'"production"','__VUE_OPTIONS_API__':'true','__VUE_PROD_DEVTOOLS__':'false','__VUE_PROD_HYDRATION_MISMATCH_DETAILS__':'false'}});
}
const html=mode=>'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/'+mode+'/entry.css"><style>body{margin:20px;font:14px Arial,"Microsoft YaHei",sans-serif}section{box-sizing:border-box;}.card{padding:16px;border:1px solid #ddd;background:#fff;box-sizing:border-box}#other,#hidden{margin-top:20px}</style></head><body><div id="app"></div><script type="module" src="/'+mode+'/entry.js"></script></body></html>';
const server=http.createServer(async(req,res)=>{try{const p=new URL(req.url,'http://localhost').pathname;
 if(p==='/baseline'||p==='/candidate'){res.setHeader('Content-Type','text/html;charset=utf-8');res.end(html(p.slice(1)));return;}
 const file=path.resolve(output,'.'+p);if(!file.startsWith(path.resolve(output)+path.sep))throw Error('SCOPE');
 res.setHeader('Content-Type',p.endsWith('.css')?'text/css':'text/javascript');res.end(await fs.readFile(file));
 }catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base='http://127.0.0.1:'+server.address().port,profile=output+'/layout-chrome-profile';
let chrome,ws,session,seq=0;const pending=new Map(),rows=[],textRows=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms=20000){const end=Date.now()+ms;while(!await fn()){if(Date.now()>end)throw Error('WAIT_TIMEOUT');await sleep(40)}}
function send(method,params={},sessionId){return new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP_TIMEOUT_'+method))},15000);pending.set(id,{resolve:x=>{clearTimeout(timer);resolve(x)},reject});ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error('OWN_JS_'+JSON.stringify(r.exceptionDetails));return r.result.value}
const measure='('+(()=>{
 const c=window.__chart(),legend=c.getModel().getComponent('legend'),view=c.getViewOfComponentModel(legend);
 const b=view.group.getBoundingRect(),p=view.group.transformCoordToGlobal(b.x,b.y);
 const rect={left:p[0],top:p[1],right:p[0]+b.width,bottom:p[1]+b.height};
 const series=c.getModel().getSeriesByIndex(0),layout=series.getData().getItemLayout(0);
 const pie=layout?{left:layout.cx-layout.r,top:layout.cy-layout.r,right:layout.cx+layout.r,bottom:layout.cy+layout.r}:null;
 const overlap=pie&&Math.min(pie.right,rect.right)-Math.max(pie.left,rect.left)>1&&Math.min(pie.bottom,rect.bottom)-Math.max(pie.top,rect.top)>1;
 const option=c.getOption();
 return{innerWidth,containerWidth:document.querySelector('#card #echarts').clientWidth,chartWidth:c.getWidth(),legend:rect,pie,overlap:!!overlap,total:option.title[0].text,
  validLegendValues:option.legend[0].data.every(n=>!String(option.legend[0].formatter(n)).match(/NaN|Infinity/)),
  canvasInsideContainer:c.getWidth()<=document.querySelector('#card #echarts').clientWidth+1,errors:window.__errors.slice()};
}).toString()+')()';
let passed=false,baseline;
const textMeasure='('+(()=>{
 const root=document.querySelector('#stats .statistics'),r=root.getBoundingClientRect();
 const labels=[...root.querySelectorAll('.statistics-item_title span,.num,.statistics-item_content_data_bottom')];
 const cells=[...document.querySelectorAll('#task .el-table__header .cell')];
 return{statisticsWidth:r.width,statisticsNoHorizontalOverflow:root.scrollWidth<=root.clientWidth+1,
  statisticsItems:root.querySelectorAll('.statistics-item').length,
  allStatisticLabelsFit:labels.every(e=>{const b=e.getBoundingClientRect(),p=e.closest('.statistics-item').getBoundingClientRect();return b.left>=p.left-1&&b.right<=p.right+1&&e.scrollHeight<=e.clientHeight+1}),
  taskHeadersSingleLine:cells.length===3&&cells.every(e=>e.clientHeight<=parseFloat(getComputedStyle(e).lineHeight)+2&&e.scrollWidth<=e.clientWidth+1),
  exactEventTotalVisible:root.querySelectorAll('.statistics-item')[3].textContent.includes('1234567'),
  taskTimePreserved:document.querySelector('#task').textContent.includes('2026-10-31 12:34:56'),
  taskColumnsPreserved:cells.map(e=>e.textContent.trim()),errors:window.__errors.slice()};
}).toString()+')()';
try{
 chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
 let active;await until(async()=>{try{active=(await fs.readFile(profile+'/DevToolsActivePort','utf8')).trim().split('\n');return true}catch{return false}});
 ws=new WebSocket('ws://127.0.0.1:'+active[0]+active[1]);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(p)m.error?p.reject(Error('CDP_ERROR')):p.resolve(m.result)}});
 const t=await send('Target.createTarget',{url:'about:blank'});session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 await send('Runtime.enable',{},session);await send('Page.enable',{},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1920,height:1300,deviceScaleFactor:1,mobile:false},session);
 for(const mode of ['baseline','candidate']){
  await send('Page.navigate',{url:base+'/'+mode},session);
  await until(()=>evaluate('window.__ready&&window.__chart()?.getOption().series?.[0]?.data?.length===6'));
  await sleep(600);
  const first=await evaluate(measure);
  if(mode==='baseline'){
   baseline=first;const shot=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(output+'/baseline.png',Buffer.from(shot.data,'base64'));
   baseline.text=await evaluate(textMeasure);
   if(!first.overlap)throw Error('ORIGINAL_OVERLAP_NOT_REPRODUCED');
   await evaluate('window.__setWidth(600)');await sleep(500);baseline.containerResize=await evaluate(measure);continue;
  }
  const normal=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(output+'/candidate-normal-six-categories.png',Buffer.from(normal.data,'base64'));
  for(const [w,t] of [[1536,420],[1200,350],[960,320],[720,280],[360,320],[280,420]]){
   await evaluate('window.__setTextWidths('+w+','+t+')');await sleep(350);
   const row=await evaluate(textMeasure);textRows.push({...row,requestedStatisticsWidth:w,requestedTaskWidth:t});
   if(!row.statisticsNoHorizontalOverflow||!row.allStatisticLabelsFit||!row.taskHeadersSingleLine||!row.exactEventTotalVisible||!row.taskTimePreserved||row.statisticsItems!==4||row.errors.length)throw Error('WORKPLACE_TEXT_LAYOUT_REJECTED_'+w);
  }
  await evaluate('document.querySelector("#task .task-header_more").click()');
  if(!await evaluate('window.__nav.at(-1)?.path==="/intelligentInspection/task"&&window.__taskCalls[0].createDept==="fixture-dept"'))throw Error('TASK_ORIGINAL_NAV_OR_FILTER_CHANGED');
  for(const width of [320,600,260,421,420,800,320]){
   await evaluate('window.__setWidth('+width+')');await sleep(700);
   const row=await evaluate(measure);row.outerCardWidth=width;rows.push(row);
   if(row.overlap||!row.canvasInsideContainer||row.chartWidth!==row.containerWidth||row.errors.length)throw Error('CHART_LAYOUT_REJECTED_'+width);
  }
  const other=await evaluate('({width:window.__other()?.getWidth(),height:window.__other()?.getHeight()})');
  if(other.width!==484||other.height!==180)throw Error('CSS_DIMENSION_PROPS_REJECTED');
  await evaluate('window.__showHidden()');await sleep(500);
  if(!await evaluate('window.__hidden()?.getWidth()===260&&window.__hidden()?.getHeight()===180'))throw Error('HIDDEN_CONTAINER_INIT_REJECTED');
  await evaluate('window.__remount([{name:"空值类别",value:0},{name:"无效计数",value:"bad"},{name:"负值",value:-1}])');await sleep(700);
  const zero=await evaluate(measure);if(zero.total!=='0'||!zero.validLegendValues||zero.overlap)throw Error('ZERO_OR_INVALID_DATA_REJECTED');rows.push({...zero,scenario:'zero-and-invalid'});
  await evaluate('window.__remount([])');await sleep(600);
  if(!await evaluate('window.__chart().getOption().title[0].text==="0"'))throw Error('EMPTY_DATA_REJECTED');
  await evaluate('window.__responses=[{data:[{name:"陈旧",value:100}],delay:200},{data:[{name:"最新",value:2}],delay:5}];window.__period(1)');
  await sleep(30);await evaluate('window.__period(2)');
  await sleep(650);if(!await evaluate('window.__chart().getOption().title[0].text==="2"&&window.__calls.length>=5'))throw Error('DATE_FILTER_RACE_REJECTED');
  const shot=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(output+'/candidate.png',Buffer.from(shot.data,'base64'));
  await evaluate('window.__setWidth(500);window.__dispose()');await sleep(500);
  if(!await evaluate('window.__errors.length===0'))throw Error('POST_DISPOSE_ERROR');
 }
 passed=true;console.log('ACTUAL_VUE_ECHARTS_CONTAINER_LAYOUT_PASSED');
}finally{
 if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close')}catch{}ws.close()}
 if(chrome)await until(()=>chrome.exitCode!==null,15000);
 await new Promise(r=>server.close(r));
 await fs.writeFile(output+'/result.json',JSON.stringify({passed,baseline,candidateCases:rows,textCases:textRows,actualVueSFCAndInstalledECharts:true,syntheticAPIOnly:true,sameWindowWidthDuringContainerChanges:true,normalBrowserClosed:chrome?.exitCode===0,chromeExitCode:chrome?.exitCode,originalSourceOrFormalOrPublicChanged:false,originalSheetChanged:false},null,2));
}
