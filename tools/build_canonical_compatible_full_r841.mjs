import fs from'node:fs/promises';import{pathToFileURL}from'node:url';
const R='D:/Project/Zhumadian',W=R+'/work/canonical-bootstrap-compatible-r841',P=R+'/work/user_feedback_20261031/event-research-level-r418/source',deps=R+'/Application/work/tianjin_native_20261023/emergency_pc/node_modules';
process.chdir(P);for(const k of Object.keys(process.env))if(k.startsWith('VITE_')||['NODE_OPTIONS','DEBUG'].includes(k))delete process.env[k];
Object.assign(process.env,{NODE_ENV:'production',BROWSER:'none',VITE_API_URL:'/zhumadian/api',VITE_APP_BASE_PATH:'/zhumadian/emergency',VITE_APP_NAME:'驻马店重大风险防控'});

const groupedPlan=JSON.parse(await fs.readFile("D:/CodexData/home/visualizations/2026/10/28/01a1836e-e4ee-7fb0-be6f-b24f2e2672e4/tencent-feedback-20261031/grouped-installer-r829-plan.private.json",'utf8'));
const mapRaw=await fs.readFile('D:/Project/Zhumadian/work/authenticated-installer-map-r828/emitted-modules.private.json');
const {createHash}=await import('node:crypto');
if(createHash('sha256').update(mapRaw).digest('hex')!=="c60f95fde0799d0ca7fab89d2cb9ce7fcbdb14b70018f6e382775614a9c0050d")throw Error('EXACT_ACTUAL_MODULE_MAP_REQUIRED');
const groupedModules=new Set(groupedPlan.lateModules),seenGroupedModules=new Set();
await fs.symlink(deps,P+'/node_modules','junction');
try{const{build}=await import(pathToFileURL(deps+'/vite/dist/node/index.js').href);await build({root:P,define:{'import.meta.env.BASE_URL':JSON.stringify('/zhumadian/emergency/')},plugins:[{name:'verify-explicit-authenticated-module-group-r829',async generateBundle(_options,bundle){
 if(seenGroupedModules.size!==groupedModules.size)throw Error('ALL_ACTUAL_LATE_MODULES_MUST_MATCH');
 const rows={};for(const [name,c] of Object.entries(bundle))if(c.type==='chunk')rows[name]={imports:c.imports,dynamicImports:c.dynamicImports,modules:Object.keys(c.modules)};
 const grouped=Object.values(rows).filter(r=>r.modules.some(m=>groupedModules.has(m)));
 if(grouped.length!==1||grouped[0].modules.some(m=>!groupedModules.has(m)))throw Error('EXACT_EXPLICIT_LATE_GROUP_REQUIRED');
 await fs.writeFile(W+'/emitted-modules.private.json',JSON.stringify(rows,null,2)+'\n',{flag:'wx'});
 await fs.writeFile(W+'/grouping-proof.json',JSON.stringify({passed:true,lateModuleCount:groupedModules.size,sourceLateChunkCount:groupedPlan.lateChunks.length,groupedChunks:1,earlyModulesMoved:false,onlyExplicitManualChunks:true})+'\n',{flag:'wx'});
}}],configFile:P+'/vite.config.ts',cacheDir:W+'/cache',base:'/zhumadian/emergency/branding-20261025/',esbuild:{drop:['console','debugger']},build:{outDir:W+'/dist',emptyOutDir:false,sourcemap:false,rollupOptions:{output:{onlyExplicitManualChunks:true,manualChunks(id){if(groupedModules.has(id)){seenGroupedModules.add(id);return 'authenticated-components';}},entryFileNames:'assets/js/wf-[name]-[hash].js',chunkFileNames:'assets/js/wf-[name]-[hash].js'}}}})}finally{await fs.unlink(P+'/node_modules')}
