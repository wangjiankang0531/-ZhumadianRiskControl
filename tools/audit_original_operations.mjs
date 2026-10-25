/** Read original Vue/TS syntax without executing the original application. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

export const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
export function parsers(root){
  const req=createRequire(path.join(path.resolve(root),'package.json'));
  const sfc=req('@vue/compiler-sfc');
  const dep=createRequire(req.resolve('@vue/compiler-sfc'));
  return {sfc,babel:dep('@babel/parser'),versions:{vueCompiler:sfc.version,babel:dep('@babel/parser/package.json').version}};
}
export function safeFile(root,relative){
  if(!relative||path.isAbsolute(relative)||relative.split(/[\\/]/).includes('..'))throw Error('SOURCE_PATH_REJECTED');
  const base=fs.realpathSync(root),file=fs.realpathSync(path.join(base,relative));
  if(!file.startsWith(base+path.sep)||!fs.statSync(file).isFile())throw Error('SOURCE_ESCAPE_REJECTED');
  return file;
}
function walk(node,visit){
  if(!node||typeof node!=='object')return;
  if(Array.isArray(node)){for(const item of node)walk(item,visit);return;}
  if(node.type)visit(node);
  for(const [key,value] of Object.entries(node))if(!['loc','start','end','extra','comments','leadingComments','trailingComments','innerComments'].includes(key))walk(value,visit);
}
function expression(source,node){return source.slice(node.start,node.end);}
function names(node){const found=new Set();walk(node,n=>{if(n.type==='Identifier')found.add(n.name);});return found;}
function parseJS(source,p,lang='tsx'){return p.babel.parse(source,{sourceType:'unambiguous',plugins:lang==='ts'?['typescript']:['typescript','jsx'],errorRecovery:false});}
const isApiModule=value=>/^@\/(?:api|service)\//.test(value);
function property(n){return n?.type==='Identifier'?n.name:n?.value;}
function literal(n){
  if(n?.type==='StringLiteral')return n.value;
  if(n?.type==='TemplateLiteral')return n.quasis.map((v,i)=>v.value.cooked+(i<n.expressions.length?'${dynamic}':'')).join('');
  if(n?.type==='BinaryExpression'&&n.operator==='+'){const a=literal(n.left),b=literal(n.right);return a===null&&b===null?null:(a??'${dynamic}')+(b??'${dynamic}');}
  return null;
}
function endpoint(value){
  if(typeof value!=='string')return null;
  if(/^https?:\/\//i.test(value))return {kind:'external',sha256:sha(value),queryOmitted:true};
  return {kind:value.includes('${dynamic}')?'dynamic':'literal',path:value.split(/[?#]/)[0],queryOmitted:/[?#]/.test(value)};
}
export function apiExports(source,p,lang='ts'){
  const ast=parseJS(source,p,lang),result={};
  for(const statement of ast.program.body){
    if(statement.type!=='ExportNamedDeclaration'||!statement.declaration)continue;
    const dec=statement.declaration;
    const entries=dec.type==='VariableDeclaration'?dec.declarations.map(d=>[d.id?.name,d.init]):dec.type==='FunctionDeclaration'?[[dec.id?.name,dec]]:[];
    for(const [name,body] of entries){if(!name||!body)continue;const requests=[];
      walk(body,n=>{if(n.type!=='CallExpression')return;
        const callee=n.callee;let method=null,url=null;
        if(callee.type==='MemberExpression'&&['get','post','put','delete','patch','download','upload'].includes(property(callee.property))){method=property(callee.property).toUpperCase();url=literal(n.arguments[0]);}
        else if(['Identifier','MemberExpression'].includes(callee.type)&&n.arguments[0]?.type==='ObjectExpression'){
          const props=n.arguments[0].properties;const u=props.find(v=>property(v.key)==='url'),m=props.find(v=>property(v.key)==='method');
          if(u){url=literal(u.value);method=(literal(m?.value)||'UNSPECIFIED').toUpperCase();}
        }
        if(url!==null&&method)requests.push({method,url:endpoint(url),line:n.loc.start.line});
      });result[name]=requests;
    }
  }return result;
}
function resolveImport(root,from,specifier){
  let relative;
  if(specifier.startsWith('@/'))relative='src/'+specifier.slice(2);
  else if(specifier.startsWith('.'))relative=path.relative(root,path.resolve(path.dirname(from),specifier));
  else return null;
  for(const suffix of ['', '.ts','.js','.tsx','.jsx','/index.ts','/index.js','.vue','/index.vue']){
    const candidate=relative+suffix;
    if(fs.existsSync(path.join(root,candidate))&&fs.statSync(path.join(root,candidate)).isFile())try{return safeFile(root,candidate);}catch(e){if(e.message==='SOURCE_ESCAPE_REJECTED')throw e;}
  }return null;
}
function textOf(node){
  if(node.type===2)return node.content;
  if(node.type===5)return '{{'+node.content.content+'}}';
  return (node.children||[]).map(textOf).join(' ').replace(/\s+/g,' ').trim();
}
export function analyzeVue(source,p,{filename='synthetic.vue',apiLoader=()=>null}={}){
  const parsed=p.sfc.parse(source,{filename});if(parsed.errors.length)throw Error('SFC_PARSE_FAILED: '+parsed.errors.map(e=>String(e.message||e)).join(';'));
  const descriptor=parsed.descriptor,imports=[],bindings=new Map(),api=new Map(),scripts=[];
  for(const block of [descriptor.script,descriptor.scriptSetup].filter(Boolean)){
    const ast=parseJS(block.content,p,block.lang||'js');scripts.push({ast,source:block.content,line:block.loc.start.line-1});
    for(const statement of ast.program.body){
      if(statement.type==='ImportDeclaration'){
        const row={module:statement.source.value,typeOnly:statement.importKind==='type'||statement.specifiers.every(s=>s.importKind==='type'),names:statement.specifiers.map(s=>({local:s.local.name,imported:s.imported?.name||s.imported?.value||(s.type==='ImportNamespaceSpecifier'?'*':'default')}))};imports.push(row);
        const exported=row.typeOnly?null:apiLoader(row.module);
        if(exported)for(const s of row.names)api.set(s.local,{module:row.module,export:s.imported,requests:exported[s.imported]||[],resolved:Object.hasOwn(exported,s.imported)});
      }
      if(statement.type==='FunctionDeclaration'&&statement.id)bindings.set(statement.id.name,statement);
      if(statement.type==='VariableDeclaration')for(const d of statement.declarations)if(d.id.type==='Identifier'&&d.init)bindings.set(d.id.name,d.init);
    }
  }
  function trace(handler){
    let node;try{node=p.babel.parseExpression(handler,{plugins:['typescript','jsx']});}catch{return {parseable:false,apiReferences:[],routeCandidates:[]};}
    const todo=[...names(node)],seen=new Set(),references=[],routes=[];
    while(todo.length&&seen.size<512){const name=todo.pop();if(seen.has(name))continue;seen.add(name);
      if(api.has(name))references.push({binding:name,...api.get(name)});
      const body=bindings.get(name);if(!body)continue;
      for(const id of names(body))if(!seen.has(id))todo.push(id);
      walk(body,n=>{if(n.type==='ObjectProperty'&&property(n.key)==='path'){const value=literal(n.value);if(value)routes.push(endpoint(value));}});
    }
    return {parseable:true,apiReferences:references,routeCandidates:routes};
  }
  const controls=[],events=[],templateApiBindings=[],componentTags=new Set();
  function template(node,ancestors=[]){
    if(node.type===1){
      const props=node.props||[],guards=props.filter(a=>a.type===7&&['if','else-if','else','show','auth','permission','hasPermi','hasPerm'].includes(a.name)).map(a=>({directive:a.name,expression:a.exp?.content??null}));
      const inherited=[...ancestors,...guards];
      for(const prop of props)if(prop.type===7&&prop.name==='bind'&&prop.exp){const references=trace(prop.exp.content);if(references.apiReferences.length)templateApiBindings.push({tag:node.tag,property:prop.arg?.content||'dynamic',line:prop.loc.start.line,...references});}
      if(node.tagType===1)componentTags.add(node.tag);
      const handlers=props.filter(a=>a.type===7&&a.name==='on').map(a=>({event:a.arg?.content||'dynamic',handler:a.exp?.content||'',line:a.loc.start.line,...trace(a.exp?.content||'')}));
      const row={tag:node.tag,label:textOf(node).slice(0,200),line:node.loc.start.line,conditions:inherited,disabled:props.filter(a=>(a.type===6&&a.name==='disabled')||(a.type===7&&a.name==='bind'&&a.arg?.content==='disabled')).map(a=>a.exp?.content??a.value?.content??true),events:handlers};
      if(/(?:button|btn|link|table-action)$/i.test(node.tag)||node.tag==='button'||handlers.some(h=>['click','tap','confirm','submit','ok','cancel'].includes(h.event)))controls.push(row);
      for(const h of handlers)events.push({...h,tag:node.tag,label:row.label,conditions:inherited});
      for(const child of node.children||[])template(child,inherited);return;
    }
    for(const child of node.children||[])template(child,ancestors);
  }
  if(descriptor.template?.ast)template(descriptor.template.ast);
  function apiBindingsFor(row){return row.names.every(s=>api.has(s.local)&&api.get(s.local).resolved);}
  const apiReferences=[];
  for(const {ast,line} of scripts)walk(ast.program.body.filter(s=>s.type!=='ImportDeclaration'),n=>{if(n.type==='Identifier'&&api.has(n.name))apiReferences.push({binding:n.name,line:n.loc.start.line+line,...api.get(n.name)});});
  return {unresolvedApiImports:imports.filter(i=>!i.typeOnly&&isApiModule(i.module)&&!apiBindingsFor(i)),controls,events,templateApiBindings,componentTags:[...componentTags],imports,apiBindings:[...api].map(([binding,v])=>({binding,...v})),apiReferences,scriptBlocks:scripts.length,templatePresent:!!descriptor.template,roleVisibilityVerified:false,functionalParityVerified:false};
}
function vueFiles(root){
  const src=path.join(root,'src'),files=[];
  function visit(folder){for(const entry of fs.readdirSync(folder,{withFileTypes:true})){const file=path.join(folder,entry.name);if(entry.isSymbolicLink())throw Error('SOURCE_TREE_LINK_REJECTED');if(entry.isDirectory())visit(file);else if(entry.isFile()&&entry.name.endsWith('.vue'))files.push(safeFile(root,path.relative(root,file)));}}
  visit(src);return files.sort();
}
export function auditProjects(config,p){
  const projects=[],sourcePins={};let totalPages=0;
  for(const [name,rootValue] of Object.entries(config.projects)){
    const root=fs.realpathSync(rootValue),apiCache=new Map(),pages=[],files=vueFiles(root);
    if(files.length>2000)throw Error('SOURCE_PAGE_LIMIT');
    const read=file=>{const stat=fs.statSync(file);if(stat.size>2*1048576)throw Error('SOURCE_FILE_LIMIT');const raw=fs.readFileSync(file);const key=name+'/'+path.relative(root,file).replaceAll('\\','/');sourcePins[key]={bytes:raw.length,sha256:sha(raw),file};return raw.toString('utf8');};
    for(const file of files){
      const relative=path.relative(root,file).replaceAll('\\','/');
      try{const source=read(file);const analyzed=analyzeVue(source,p,{filename:relative,apiLoader:specifier=>{
        if(!isApiModule(specifier))return null;
        const apiFile=resolveImport(root,file,specifier);if(!apiFile)return null;
        if(!apiCache.has(apiFile))apiCache.set(apiFile,apiExports(read(apiFile),p,path.extname(apiFile)==='.ts'?'ts':'tsx'));return apiCache.get(apiFile);
      }});pages.push({file:relative,sha256:sourcePins[name+'/'+relative].sha256,parsed:true,...analyzed});}
      catch(error){pages.push({file:relative,parsed:false,error:String(error.message),functionalParityVerified:false});}
    }
    const matched=(config.menuModules||[]).filter(m=>m.project===name&&m.type==='2').map(m=>({name:m.name,metadataAncestry:m.metadataAncestry,roleVisibilityVerified:false,sourceCandidates:m.sourceViewCandidates.map(c=>({file:c.path,priorSHA256:c.sha256,currentSHA256:sourcePins[name+'/'+c.path]?.sha256??null,sourceUnchanged:sourcePins[name+'/'+c.path]?.sha256===c.sha256})),functionalParityVerified:false}));
    projects.push({project:name,vueFiles:files.length,parsedPages:pages.filter(p=>p.parsed).length,parseFailures:pages.filter(p=>!p.parsed).length,controlCandidates:pages.reduce((n,p)=>n+(p.controls?.length||0),0),eventBindings:pages.reduce((n,p)=>n+(p.events?.length||0),0),apiModules:apiCache.size,menuModules:matched,pages});totalPages+=files.length;
  }
  for(const pin of Object.values(sourcePins))if(sha(fs.readFileSync(pin.file))!==pin.sha256)throw Error('SOURCE_CHANGED_DURING_AUDIT');
  const pins=Object.fromEntries(Object.entries(sourcePins).map(([key,{bytes,sha256}])=>[key,{bytes,sha256}]));
  return {recordedAt:new Date().toISOString(),parserVersions:p.versions,projects,totalVueFiles:totalPages,sourceSHA256:pins,sourceFilesRechecked:Object.keys(pins).length,originalCodeExecuted:false,networkRequestsPerformed:false,sourceDatabaseConnected:false,roleVisibilityVerified:false,allActionsEnumerated:false,functionalParityVerified:false,fullCloneReady:false,limitations:['Syntax candidates are not runtime-visible buttons or successful operations.','Shared component internals, dynamic actions, namespace/re-export API wrappers and runtime-generated permissions require separate review.','Menus reflect prior sealed metadata; current roles and source changes remain explicit.']};
}
function main(){
  const args=process.argv.slice(2),options={};for(let i=0;i<args.length;i+=2){if(!args[i]?.startsWith('--')||!args[i+1])throw Error('Use --config --parser-root --output');options[args[i].slice(2)]=args[i+1];}
  if(!options.config||!options['parser-root']||!options.output)throw Error('Use --config --parser-root --output');
  if(fs.existsSync(options.output))throw Error('FRESH_OUTPUT_REQUIRED');
  const config=JSON.parse(fs.readFileSync(options.config,'utf8').replace(/^\uFEFF/,''));const result=auditProjects(config,parsers(options['parser-root']));
  fs.writeFileSync(options.output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({totalVueFiles:result.totalVueFiles,sourceFilesRechecked:result.sourceFilesRechecked,projects:result.projects.map(({project,vueFiles,parsedPages,parseFailures,controlCandidates,eventBindings,apiModules})=>({project,vueFiles,parsedPages,parseFailures,controlCandidates,eventBindings,apiModules})),functionalParityVerified:false}));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main();
