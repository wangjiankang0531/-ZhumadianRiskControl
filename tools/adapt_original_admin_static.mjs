// Deployment-only edits to a pinned original static build; never evaluate original JavaScript.
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
const require=createRequire(import.meta.url);
const {parse}=require(process.argv[2]);
const input=JSON.parse(readFileSync(0,'utf8'));
const base=input.base;
if(typeof base!=='string'||base.length>128||!/^\/[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/.test(base))throw Error('Explicit safe deployment base required');
const names=new Set(input.assetPaths),dirs=new Set();
for(const path of names){const parts=path.split('/');parts.pop();while(parts.length){dirs.add(parts.join('/'));parts.pop();}}
const mapURL=value=>{
 if(typeof value!=='string'||!value.startsWith('/')||value.startsWith('//'))return value;
 const rawPath=value.split(/[?#]/)[0].slice(1);
 if(names.has(rawPath)||dirs.has(rawPath.replace(/\/$/,'')))return base+value;
 if(/^\/(?:static|assets|fonts)\//.test(value)&&[...names].some(name=>name.startsWith(rawPath)))return base+value;
 return value;
};
const visit=(node,fn)=>{if(!node||typeof node!=='object')return;if(typeof node.type==='string')fn(node);for(const [key,value] of Object.entries(node)){if(['loc','start','end','extra','comments','tokens'].includes(key))continue;if(Array.isArray(value))for(const child of value)visit(child,fn);else if(value&&typeof value==='object')visit(value,fn);}};
const result=[];const counts={routerBase:0,appRouterBase:0,preloadBase:0,appPathname:0,apiBase:0,assetURL:0,templateAssetURL:0,pathnameHelper:0};
for(const file of input.files){
 const source=file.text;const changes=[];
 const edit=(start,end,text,kind)=>{if(source.slice(start,end)===text)return;changes.push({start,end,text,kind});counts[kind]++;};
 if(file.path.endsWith('.html')){
  const pattern=/\b(?:src|href)\s*=\s*(["'])(\/[^"']*)\1/g;let match;
  while((match=pattern.exec(source))!==null){const mapped=mapURL(match[2]);if(mapped!==match[2]){const start=match.index+match[0].indexOf(match[2]);edit(start,start+match[2].length,mapped,'assetURL');}}
 }else if(file.path.endsWith('.css')){
  const pattern=/url\(\s*(["']?)(\/[^\s"')]+)\1\s*\)/g;let match;
  while((match=pattern.exec(source))!==null){const mapped=mapURL(match[2]);if(mapped!==match[2]){const start=match.index+match[0].indexOf(match[2]);edit(start,start+match[2].length,mapped,'assetURL');}}
 }else if(file.path.endsWith('.js')){
  const ast=parse(source,{sourceType:'unambiguous',allowReturnOutsideFunction:true,allowAwaitOutsideFunction:true});
  visit(ast,node=>{
   if(node.type==='StringLiteral'){
    const mapped=mapURL(node.value);if(mapped!==node.value)edit(node.start,node.end,JSON.stringify(mapped),'assetURL');
   }
   if(node.type==='TemplateElement'&&typeof node.value.cooked==='string'&&mapURL(node.value.cooked)!==node.value.cooked){
    edit(node.start,node.start,base,'templateAssetURL');
   }
   if(file.path==='static/js/index-26528473.js'){
    if(node.type==='VariableDeclarator'&&node.id.type==='Identifier'&&node.id.name==='VITE_PUBLIC_PATH'){
     if(node.init?.type!=='StringLiteral'||node.init.value!=='/')throw Error('Unexpected original router base');
     edit(node.init.start,node.init.end,JSON.stringify(base+'/'),'routerBase');
    }
    if(node.type==='AssignmentExpression'&&node.left.type==='Identifier'&&node.left.name==='VITE_PUBLIC_PATH'){
     if(node.right?.type!=='BinaryExpression'||node.right.operator!=='+'||node.right.left.type!=='StringLiteral'||node.right.left.value!=='/'||node.right.right.type!=='Identifier'||node.right.right.name!=='appId')throw Error('Unexpected original sub-application router base');
     edit(node.right.left.start,node.right.left.end,JSON.stringify(base+'/'),'appRouterBase');
    }
    if(node.type==='VariableDeclarator'&&node.id.type==='Identifier'&&node.id.name==='assetsURL'){
     let found=0;visit(node.init,n=>{if(n.type==='ReturnStatement'&&n.argument?.type==='BinaryExpression'&&n.argument.operator==='+'&&n.argument.left.type==='StringLiteral'&&n.argument.left.value==='/'){edit(n.argument.left.start,n.argument.left.end,JSON.stringify(base+'/'),'preloadBase');found++;}});
     if(found!==1)throw Error('Unexpected original preload URL helper');
    }
    if(node.type==='FunctionDeclaration'&&node.id?.name==='getJnpfAppId'){
     if(source.includes('__xnbyAdminPathname'))throw Error('Deployment helper already present');
     const helper='function __xnbyAdminPathname(){const path=window.location.pathname,base='+JSON.stringify(base)+';return path===base?"/":path.startsWith(base+"/")?path.slice(base.length):path;}\n';
     edit(node.start,node.start,helper,'pathnameHelper');let found=0;
     visit(node.body,n=>{if(n.type==='MemberExpression'&&!n.computed&&n.property.type==='Identifier'&&n.property.name==='pathname'&&n.object.type==='MemberExpression'&&!n.object.computed&&n.object.property.type==='Identifier'&&n.object.property.name==='location'&&n.object.object.type==='Identifier'&&n.object.object.name==='window'){edit(n.start,n.end,'__xnbyAdminPathname()','appPathname');found++;}});
     if(found!==2)throw Error('Unexpected original sub-application path reader');
    }
   }
   if(file.path==='_app.config.js'&&node.type==='ObjectProperty'&&((node.key.type==='Identifier'&&node.key.name==='VITE_GLOB_API_URL')||(node.key.type==='StringLiteral'&&node.key.value==='VITE_GLOB_API_URL'))){
    if(node.value.type!=='StringLiteral'||node.value.value!=='')throw Error('Original API base differs');
    edit(node.value.start,node.value.end,JSON.stringify(base),'apiBase');
   }
  });
 }
 if(!changes.length)continue;
 const ascending=[...changes].sort((a,b)=>a.start-b.start||a.end-b.end);
 for(let i=1;i<ascending.length;i++)if(ascending[i].start<ascending[i-1].end)throw Error('Overlapping deployment edits');
 let text=source;for(const change of [...ascending].reverse())text=text.slice(0,change.start)+change.text+text.slice(change.end);
 if(file.path.endsWith('.js'))parse(text,{sourceType:'unambiguous',allowReturnOutsideFunction:true,allowAwaitOutsideFunction:true});
 result.push({path:file.path,text,patches:ascending.map(({start,end,kind})=>({start,end,kind}))});
}
if(counts.routerBase!==1||counts.appRouterBase!==1||counts.preloadBase!==1||counts.pathnameHelper!==1||counts.appPathname!==2||counts.apiBase!==1)throw Error('Pinned original deployment structure not matched exactly');
process.stdout.write(JSON.stringify({base,counts,files:result,originalJavaScriptEvaluated:false}));
