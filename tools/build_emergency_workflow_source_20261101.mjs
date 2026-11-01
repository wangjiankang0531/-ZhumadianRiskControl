import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const revision=process.argv[2]||'r1';if(!['r1','r2','r3','r4','r5','r6','r7'].includes(revision))throw Error('SOURCE_REVISION_REQUIRED');
const R='D:/Project/Zhumadian',P=R+'/Application/work/tianjin_native_20261023/emergency_pc',W=R+'/work/user_feedback_20261031/emergency-workflow-source-'+revision,source=W+'/source';
const metadata=JSON.parse(await fs.readFile(W+'/source-closure.json','utf8'));
if(!metadata.workflowUIFromSuppliedSafetySource||metadata.stubViewsReplaced!==2)throw Error('OWN_SOURCE_SCOPE');
process.chdir(source);for(const k of Object.keys(process.env))if(k.startsWith('VITE_')||['NODE_OPTIONS','DEBUG'].includes(k))delete process.env[k];
Object.assign(process.env,{NODE_ENV:'production',BROWSER:'none',VITE_API_URL:'/zhumadian/api',VITE_APP_BASE_PATH:'/zhumadian/emergency',VITE_APP_NAME:'驻马店重大风险防控'});
const {build}=await import(pathToFileURL(P+'/node_modules/vite/dist/node/index.js').href);
const dependencyLink=source+'/node_modules';let ownedDependencyLink=false;
try{const entry=await fs.lstat(dependencyLink);if(!entry.isSymbolicLink()||await fs.realpath(dependencyLink)!==await fs.realpath(P+'/node_modules'))throw Error('UNEXPECTED_SOURCE_DEPENDENCY_LAYOUT');}
catch(error){if(error.code!=='ENOENT')throw error;await fs.symlink(P+'/node_modules',dependencyLink,'junction');ownedDependencyLink=true;}
try{await build({root:source,configFile:source+'/vite.config.ts',cacheDir:W+'/cache',base:'/zhumadian/emergency/',esbuild:{drop:['console','debugger']},
 build:{outDir:W+'/dist',emptyOutDir:false,sourcemap:false,rollupOptions:{output:{entryFileNames:'assets/js/wf-[name]-[hash].js',chunkFileNames:'assets/js/wf-[name]-[hash].js'}}}});}finally{if(ownedDependencyLink)await fs.unlink(dependencyLink);}
const files={};async function walk(folder,relative=''){for(const d of await fs.readdir(folder,{withFileTypes:true})){const n=relative?relative+'/'+d.name:d.name;if(d.isSymbolicLink())throw Error('REDIRECTED_BUILD_OUTPUT');if(d.isDirectory())await walk(folder+'/'+d.name,n);else{const raw=await fs.readFile(folder+'/'+d.name);files[n]={bytes:raw.length,sha256:createHash('sha256').update(raw).digest('hex')};}}}
await walk(W+'/dist');await fs.writeFile(W+'/build-result.json',JSON.stringify({sourceClosureSHA256:createHash('sha256').update(await fs.readFile(W+'/source-closure.json')).digest('hex'),buildPassed:true,files,fileCount:Object.keys(files).length,
 sourceBuildNotPublished204ByteIdentity:true,fullWorkflowUIFromOriginalSafetySources:true,sourceAndManualPreviewUnchanged:true,workflowTaskContextSource:!!metadata.taskContextAdaptations,normalLoginListDetailApprovalOrCallbackAccepted:false,publicInstalled:false,fullCloneReady:false},null,2));
console.log(JSON.stringify({buildPassed:true,files:Object.keys(files).length,actualWorkflowUIAccepted:false}));
