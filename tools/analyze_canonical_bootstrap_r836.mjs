import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';

const R='D:/Project/Zhumadian',V=path.dirname(process.argv[1]);
const output=V+'/canonical-bootstrap-analysis-r836';
const {parseAst}=await import(pathToFileURL(R+'/Application/work/tianjin_native_20261023/emergency_pc/node_modules/rollup/dist/es/parseAst.js').href);
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=p=>fs.readFile(p,'utf8').then(JSON.parse);
const oldRoot=R+'/work/user_feedback_20261031/original-online-integration-r475/full-build-r525';
const newRoot=R+'/work/canonical-bootstrap-full-r835';
const oldProof=await read(oldRoot+'/verified-bounded-full-build-r674.json');
const newProof=await read(newRoot+'/verified-bounded-full-build-r673.json');
if(!oldProof.passed||!newProof.passed||!newProof.sourceRestored||!newProof.terminal.actualJobDescendantsZeroBeforeClose)throw Error('ACTUAL_COMPLETE_BUILD_AND_TERMINAL_REQUIRED');
const before=await read(oldRoot+'/actual-compiled-source-files.json'),after=await read(newRoot+'/actual-compiled-source-files.json');
const changed=[...new Set([...Object.keys(before),...Object.keys(after)])].filter(n=>JSON.stringify(before[n])!==JSON.stringify(after[n]));
if(JSON.stringify([...changed].sort())!==JSON.stringify(['src/OriginalAuthenticatedInstallerR817.ts','src/global-import.ts','src/router/index.ts']))throw Error('EXACT_THREE_INSTALLER_SOURCES_REQUIRED');

async function analyze(root,proof){
 const files=proof.files,graph=new Map(),login=[],homes=[],installers=[],rawByName=new Map();
 const normalize=(from,value)=>{
  if(!value.endsWith('.js'))return null;
  let name=value.startsWith('/zhumadian/emergency/')?value.slice('/zhumadian/emergency/'.length):path.posix.normalize(path.posix.join(path.posix.dirname(from),value));
  if(name.startsWith('../')||!Object.hasOwn(files,name))throw Error('UNRESOLVED_LOCAL_JS_IMPORT:'+from+':'+value);
  return name;
 };
 let jsCount=0,staticEdges=0,dynamicEdges=0;
 for(const [name,pin] of Object.entries(files)){
  const raw=await fs.readFile(root+'/dist/'+name);
  if(raw.length!==pin.bytes||sha(raw)!==pin.sha256)throw Error('COMPILED_ARTIFACT_DRIFT');
  if(!name.endsWith('.js'))continue;
  jsCount++;rawByName.set(name,raw);const source=raw.toString('utf8');
  if(source.includes('login-wrapper'))login.push(name);
  if(source.includes('data-workflow-route'))homes.push(name);
  if(name.includes('wf-authenticated-components-'))installers.push(name);
  const refs={static:[],dynamic:[]},stack=[parseAst(source)];
  while(stack.length){
   const n=stack.pop();
   if(!n||typeof n!=='object')continue;
   if(['ImportDeclaration','ExportNamedDeclaration','ExportAllDeclaration'].includes(n.type)&&n.source){
    const v=normalize(name,n.source.value);if(v){refs.static.push(v);staticEdges++;}
   }
   if(n.type==='ImportExpression'&&n.source?.type==='Literal'&&typeof n.source.value==='string'){
    const v=normalize(name,n.source.value);if(v){refs.dynamic.push(v);dynamicEdges++;}
   }
   for(const v of Object.values(n)){if(Array.isArray(v)){for(const x of v)if(x&&typeof x==='object')stack.push(x);}else if(v&&typeof v==='object')stack.push(v);}
  }
  graph.set(name,refs);
 }
 const html=(await fs.readFile(root+'/dist/index.html','utf8'));
 const entries=[...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)].map(m=>m[1]).filter(x=>x.endsWith('.js'));
 if(entries.length!==1||login.length!==1||homes.length!==1||installers.length>1)throw Error('EXACT_LOGIN_AND_ENTRY_CHUNK_REQUIRED');
 const entry=entries[0].replace(/^\/zhumadian\/emergency\/(?:branding-20261025\/)?/,'');
 function closure(seeds){
  const seen=new Set(),stack=[...seeds];
  while(stack.length){const name=stack.pop();if(seen.has(name))continue;if(!graph.has(name))throw Error('MISSING_CHUNK');seen.add(name);stack.push(...graph.get(name).static);}
  const names=[...seen].sort();return {files:names.length,bytes:names.reduce((s,n)=>s+rawByName.get(n).length,0),
   gzipBytes:names.reduce((s,n)=>s+gzipSync(rawByName.get(n)).length,0),names};
 }
 return {compiledFiles:Object.keys(files).length,javascriptParsed:jsCount,staticEdges,dynamicEdges,entry,
  loginChunk:login[0],entryClosure:closure([entry]),loginClosure:closure([entry,login[0]]),authenticatedHomeBootstrapClosure:closure([entry,login[0],homes[0],...installers])};
}
const baseline=await analyze(oldRoot,oldProof),candidate=await analyze(newRoot,newProof);
const proof={passed:true,onlyChangedCompiledSources:changed,allCompiledArtifactHashesMatched:true,
 allLocalStaticAndLiteralDynamicJSImportsResolved:true,baseline,candidate,
 initialLoginJSReductionBytes:baseline.loginClosure.bytes-candidate.loginClosure.bytes,
 initialLoginGzipReductionBytes:baseline.loginClosure.gzipBytes-candidate.loginClosure.gzipBytes,
 actualBrowserOrAuthenticatedRoutesAccepted:false,publicChanged:false};
await fs.mkdir(output);await fs.writeFile(output+'/result.json',JSON.stringify(proof,null,2)+'\n');
console.log(JSON.stringify({...proof,baseline:{...baseline,entryClosure:{...baseline.entryClosure,names:undefined},loginClosure:{...baseline.loginClosure,names:undefined}},candidate:{...candidate,entryClosure:{...candidate.entryClosure,names:undefined},loginClosure:{...candidate.loginClosure,names:undefined}}}));
