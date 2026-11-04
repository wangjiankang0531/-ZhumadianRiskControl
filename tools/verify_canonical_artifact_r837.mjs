import fs from 'node:fs/promises';import path from 'node:path';import{pathToFileURL}from'node:url';import{createRequire}from'node:module';
let gate='';for await(const c of process.stdin)gate+=c.toString();if(gate!=='VERIFY_FULL_ARTIFACT_R675\n')throw Error('ARTIFACT_GATE_REQUIRED');
const R='D:/Project/Zhumadian',root=R+'/work/canonical-bootstrap-full-r835/dist';
const{parseAst}=await import(pathToFileURL(R+'/Application/work/tianjin_native_20261023/emergency_pc/node_modules/rollup/dist/es/parseAst.js').href);
const require=createRequire(import.meta.url),deps=R+'/Application/work/tianjin_native_20261023/emergency_pc/node_modules';
const postcss=require(deps+'/postcss/lib/postcss.js'),tokenize=require(deps+'/postcss/lib/tokenize.js');
const tag='r823';
const proof=JSON.parse(await fs.readFile(R+'/work/canonical-bootstrap-full-r835/verified-bounded-full-build-r673.json','utf8'));
if(!proof.passed||!proof.completeBuildExecuted||proof.compiledFiles!==Object.keys(proof.files).length)throw Error('COMPLETE_BUILD_PROOF_REQUIRED');
const files=Object.keys(proof.files),refs=[],external=[],unresolvedDynamic=[];let javascript=0,css=0,html=0;
function ref(from,value,kind){
 if(typeof value!=='string'||!value||value.startsWith('#')||value.startsWith('data:')||value.startsWith('blob:'))return;
 if(/^(?:[a-z]+:)?\/\//i.test(value)){external.push({from,kind});return;}
 let name=value.split(/[?#]/)[0];if(name.startsWith('/zhumadian/emergency/branding-20261025/'))name=name.slice('/zhumadian/emergency/branding-20261025/'.length);
 else if(name.startsWith('/zhumadian/emergency/'))name=name.slice('/zhumadian/emergency/'.length);
 else if(name.startsWith('/'))name=name.slice(1);
 else if(!name.startsWith('assets/'))name=path.posix.join(path.posix.dirname(from),name);
 name=decodeURIComponent(path.posix.normalize(name));
 if(name.startsWith('../')||name.includes('\\')||!Object.hasOwn(proof.files,name))throw Error('MISSING_LOCAL_ARTIFACT:'+kind+':'+from+':'+value);
 refs.push({from,to:name,kind});
}
for(const name of files){
 if(!/\.(?:js|css|html)$/.test(name))continue;
 const source=await fs.readFile(root+'/'+name,'utf8');
 if(name.endsWith('.html')){
  html++;for(const m of source.matchAll(/(?:src|href)\s*=\s*["']([^"']+)["']/g))ref(name,m[1],'html');
 }else if(name.endsWith('.css')){
  css++;const cssTree=postcss.parse(source,{from:name});
  const urls=value=>{
   const scanner=tokenize(new postcss.Input(value)),tokens=[];while(!scanner.endOfFile())tokens.push(scanner.nextToken());
   for(let i=0;i<tokens.length;i++)if(tokens[i][0]==='word'&&tokens[i][1].toLowerCase()==='url'){
    const next=tokens[i+1];let value;
    if(next?.[0]==='brackets')value=next[1].slice(1,-1).trim();
    else if(next?.[0]==='('){const inside=[];let n=i+2;while(n<tokens.length&&tokens[n][0]!==')')inside.push(tokens[n++]);value=inside.filter(t=>t[0]!=='comment').map(t=>t[1]).join('').trim();}
    if(value===undefined)throw Error('UNPARSED_CSS_URL:'+name);
    if((value[0]==='"'||value[0]==="'")&&value.at(-1)===value[0])value=value.slice(1,-1);
    ref(name,value,'css-url');
   }
  };
  cssTree.walkDecls(d=>urls(d.value));cssTree.walkAtRules(r=>urls(r.params));
 }else{
  javascript++;const tree=parseAst(source);const stack=[tree];
  while(stack.length){
   const n=stack.pop();if(!n||typeof n!=='object')continue;
   if((n.type==='ImportDeclaration'||n.type==='ExportNamedDeclaration'||n.type==='ExportAllDeclaration')&&n.source)ref(name,n.source.value,'module');
   if(n.type==='ImportExpression'){
    if(n.source?.type==='Literal'&&typeof n.source.value==='string')ref(name,n.source.value,'dynamic-import');
    else unresolvedDynamic.push({from:name,kind:'computed-runtime-import'});
   }
   if(n.type==='Literal'&&typeof n.value==='string'&&/^(?:\/zhumadian\/emergency\/)?assets\//.test(n.value))ref(name,n.value,'vite-asset-literal');
   if(n.type==='NewExpression'&&n.callee?.type==='Identifier'&&n.callee.name==='URL'&&n.arguments?.[0]?.type==='Literal'&&n.arguments?.[1]?.type==='MemberExpression'&&n.arguments[1].object?.type==='MetaProperty')ref(name,n.arguments[0].value,'import-meta-url');
   for(const v of Object.values(n)){if(Array.isArray(v)){for(const x of v)if(x&&typeof x==='object')stack.push(x);}else if(v&&typeof v==='object')stack.push(v);}
  }
 }
}
if(!javascript||!css||html!==1||refs.length<javascript)throw Error('INCOMPLETE_ARTIFACT_GRAPH');
const report={passed:true,compiledFiles:files.length,javascriptParsed:javascript,cssChecked:css,htmlChecked:html,localReferencesChecked:refs.length,
 externalReferencesNotFetched:external.length,computedRuntimeImportsNotStaticallyProven:unresolvedDynamic.length,
 wholeCompiledArtifactUsed:true,originalAPIOrNormalUserWorkflowOrBrowserOrPublicAccepted:false};
await fs.writeFile('D:/CodexData/home/visualizations/2026/10/28/01a1836e-e4ee-7fb0-be6f-b24f2e2672e4/tencent-feedback-20261031/verified-canonical-artifact-r837.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
