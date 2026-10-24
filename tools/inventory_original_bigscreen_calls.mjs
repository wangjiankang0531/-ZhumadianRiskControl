/** Static callsite inventory only. Original modules are parsed, never imported or executed. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const [sourceRoot,parserFile,parserPin,output]=process.argv.slice(2);
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
if(sha(await fs.readFile(parserFile))!==parserPin)throw Error('EXPLICIT_EXISTING_PARSER_PIN_REQUIRED');
const parse=createRequire(import.meta.url)(path.resolve(parserFile)).parse;
async function files(dir){const result=[];for(const item of await fs.readdir(dir,{withFileTypes:true})){if(item.isSymbolicLink())throw Error('SOURCE_REDIRECTION_REJECTED');const p=path.join(dir,item.name);if(item.isDirectory())result.push(...await files(p));else if(/\.(js|vue)$/.test(p))result.push(p);}return result;}
const rows=[],sources=[];
for(const file of await files(path.join(sourceRoot,'src'))){
 const raw=await fs.readFile(file);if(raw.length>2*1024**2)throw Error('BOUNDED_SOURCE_REQUIRED');const text=raw.toString('utf8');if(!text.includes('utils/request'))continue;
 const script=file.endsWith('.vue')?(text.match(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/)?.[1]||''):text;
 const ast=parse(script,{sourceType:'module',plugins:['jsx','classProperties','decorators-legacy','dynamicImport']});
 const imports=new Map();for(const node of ast.program.body)if(node.type==='ImportDeclaration') {
  const module=node.source.value,kind=/\/utils\/request(?:\.js)?$/.test(module)?'mock':/\/utils\/request_real(?:\.js)?$/.test(module)?'business':/\/utils\/request_internal(?:\.js)?$/.test(module)?'bigscreen-backend':null;
  if(kind)for(const spec of node.specifiers)if(spec.type==='ImportSpecifier')imports.set(spec.local.name,{kind,method:spec.imported.name.toUpperCase()});
 }
 if(!imports.size)continue;sources.push({path:path.relative(sourceRoot,file).replaceAll('\\','/'),sha256:sha(raw)});
 function walk(node){if(!node||typeof node!=='object')return;if(node.type==='CallExpression'&&node.callee.type==='Identifier'&&imports.has(node.callee.name)){
  const entry=imports.get(node.callee.name),options=node.arguments[0];let route=null,prefix='',resolved=true;
  if(options?.type==='ObjectExpression'){const key=options.properties.find(p=>p.type==='ObjectProperty'&&(p.key.name||p.key.value)==='url');if(key?.value.type==='StringLiteral')route=key.value.value;}
  if(node.arguments.length>1){if(node.arguments[1].type==='StringLiteral')prefix=node.arguments[1].value;else resolved=false;}
  rows.push({source:path.relative(sourceRoot,file).replaceAll('\\','/'),kind:entry.kind,method:entry.method,route:resolved&&route!==null?prefix+route:null,dynamicOrUnresolved:!resolved||route===null});
 }
 for(const [key,value] of Object.entries(node)){if(['loc','start','end','extra','comments'].includes(key))continue;if(Array.isArray(value))for(const child of value)walk(child);else if(value&&typeof value==='object')walk(value);}}
 walk(ast.program);
}
const mockRoutes=[...new Set(rows.filter(r=>r.kind==='mock'&&r.method==='GET'&&r.route&&!r.dynamicOrUnresolved).map(r=>r.route))].sort();
const result={sourceFiles:sources,calls:rows,mockGETRoutes:mockRoutes,parserSHA256:parserPin,sourceExecuted:false,networkRequestsMade:0,fullCloneReady:false};await fs.mkdir(output);await fs.writeFile(path.join(output,'inventory.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({files:sources.length,calls:rows.length,mockGETRoutes:mockRoutes.length,unresolved:rows.filter(r=>r.dynamicOrUnresolved).length,byKind:Object.fromEntries(['mock','business','bigscreen-backend'].map(k=>[k,rows.filter(r=>r.kind===k).length]))}));
