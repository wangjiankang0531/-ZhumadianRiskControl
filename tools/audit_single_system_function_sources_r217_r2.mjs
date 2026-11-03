import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const R='D:/Project/Zhumadian',O=R+'/work/single-system-function-register-r217/source-r2';
const referenceRoot=R+'/Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包';
const projects={security_pc:referenceRoot+'/安全风险管控平台前台代码/security-risk-web',emergency_pc:referenceRoot+'/敏捷应急管理前台代码/agile-emergency-response-dev'};
const config=JSON.parse(await fs.readFile(R+'/Document/Deployment/emergency_plan_report_20261030/frontend-build-config-v2.json','utf8'));
const require=createRequire(config.project.replaceAll('\\','/')+'/package.json');
const {parse}=require('@vue/compiler-sfc'),ts=require('typescript');
const digest=b=>createHash('sha256').update(b).digest('hex');
const allowedMethods=new Set(['get','post','put','delete','patch','head','download','upload']);
const text=n=>n.type===2?n.content:n.type===5?'{{'+n.content.content+'}}':(n.children??[]).map(text).join('').trim();
function literal(node,sf,constants,depth=0){
 if(!node||depth>8)return null;
 if(ts.isStringLiteral(node)||ts.isNoSubstitutionTemplateLiteral(node))return node.text;
 if(ts.isIdentifier(node))return constants.has(node.text)?literal(constants.get(node.text),sf,constants,depth+1):null;
 if(ts.isParenthesizedExpression(node)||ts.isAsExpression(node))return literal(node.expression,sf,constants,depth+1);
 if(ts.isBinaryExpression(node)&&node.operatorToken.kind===ts.SyntaxKind.PlusToken){const a=literal(node.left,sf,constants,depth+1),b=literal(node.right,sf,constants,depth+1);return a!==null&&b!==null?a+b:a!==null&&(a.startsWith('/')||/^https?:\/\//i.test(a))?a+'{parameter}':null;}
 if(ts.isTemplateExpression(node)){let s=node.head.text;for(const span of node.templateSpans){const fixed=literal(span.expression,sf,constants,depth+1);s+=(fixed??'{parameter}')+span.literal.text;}return s;}
 return null;
}
function normalizeURL(value){
 if(typeof value!=='string')return {path:null,dynamicUnresolved:true};
 if(/^https?:\/\//i.test(value)){const u=new URL(value);return {path:u.pathname,externalOriginHash:digest(u.origin).slice(0,16),dynamicUnresolved:true,queryKeys:[...new Set(u.searchParams.keys())].sort()};}
 if(!value.startsWith('/')||value.startsWith('//'))return {path:null,dynamicUnresolved:true};
 const [beforeHash]=value.split('#'),[rawPath,query]=beforeHash.split('?'),parts=rawPath.split('/');
 if(parts.some(x=>x==='.'||x==='..'))return {path:null,dynamicUnresolved:true};
 const normalized=parts.map(x=>/^\{[^}]+\}$/.test(x)?'{parameter}':/^[0-9a-f]{32}$/i.test(x)||/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(x)?'{fixed-id}':x).join('/');
 return {path:normalized,queryKeys:query?[...new Set(query.split('&').map(x=>x.split('=')[0]))].sort():[],hasParameterizedPath:normalized.includes('{'),fixedIdHidden:normalized.includes('{fixed-id}'),dynamicUnresolved:false};
}
function scriptFacts(content,name,lineOffset=0,kind=ts.ScriptKind.TS){
 const sf=ts.createSourceFile(name,content,ts.ScriptTarget.Latest,true,kind),imports=[],calls=[],constants=new Map(),invocations=[];
 const line=n=>sf.getLineAndCharacterOfPosition(n.getStart(sf)).line+1+lineOffset;
 function collect(n){
  if(ts.isVariableDeclaration(n)&&ts.isIdentifier(n.name)&&n.initializer)constants.set(n.name.text,n.initializer);
  if(ts.isImportDeclaration(n)&&ts.isStringLiteral(n.moduleSpecifier)){
   const bindings=[];const c=n.importClause;
   if(c?.name)bindings.push({local:c.name.text,imported:'default'});
   if(c?.namedBindings&&ts.isNamedImports(c.namedBindings))for(const e of c.namedBindings.elements)bindings.push({local:e.name.text,imported:e.propertyName?.text??e.name.text});
   if(c?.namedBindings&&ts.isNamespaceImport(c.namedBindings))bindings.push({local:c.namedBindings.name.text,imported:'*'});
   imports.push({module:n.moduleSpecifier.text,bindings,line:line(n),typeOnly:!!c?.isTypeOnly});
  }
  ts.forEachChild(n,collect);
 }
 collect(sf);
 const clients=new Set(imports.filter(i=>/utils\/(request|http)|axios/.test(i.module)).flatMap(i=>i.bindings.map(b=>b.local)));
 function visit(n){
  if(ts.isCallExpression(n)){
   if(n.expression.kind===ts.SyntaxKind.ImportKeyword&&n.arguments[0]){const module=literal(n.arguments[0],sf,constants);if(module)imports.push({module,bindings:[],line:line(n),dynamic:true});}
   if(ts.isIdentifier(n.expression))invocations.push(n.expression.text);
   else if(ts.isPropertyAccessExpression(n.expression))invocations.push(n.expression.getText(sf));
   const e=n.expression;
   if(ts.isPropertyAccessExpression(e)&&ts.isIdentifier(e.expression)&&clients.has(e.expression.text)&&allowedMethods.has(e.name.text)){
    let owner=n.parent,chosen=null;
    while(owner){
     if((ts.isVariableDeclaration(owner)||ts.isFunctionDeclaration(owner))&&owner.name){chosen=owner;const declaration=ts.isVariableDeclaration(owner)?owner.parent?.parent:owner;if(declaration?.modifiers?.some(m=>m.kind===ts.SyntaxKind.ExportKeyword))break;}
     owner=owner.parent;
    }
    owner=chosen;
    const value=literal(n.arguments[0],sf,constants),url=normalizeURL(value),method=e.name.text;
    calls.push({function:owner?.name?.getText(sf)??'',requestKind:method,transportMethod:method==='download'?'GET':method==='upload'?null:method.toUpperCase(),...url,line:line(n),staticStringOrTemplateResolved:value!==null});
   }
  }
  ts.forEachChild(n,visit);
 }
 visit(sf);
 return {imports,calls,invocations:[...new Set(invocations)],scriptParseErrors:sf.parseDiagnostics.map(d=>({code:d.code,line:sf.getLineAndCharacterOfPosition(d.start??0).line+1+lineOffset}))};
}
function vueFacts(raw,name){
 const parsed=parse(raw.toString('utf8'),{filename:name}),d=parsed.descriptor,actions=[],components=new Set(),forms=[],dynamicEvents=[];
 function visit(n,ancestors=[]){
  if(n.type===1){
   const directives=(n.props??[]).filter(p=>p.type===7),conditions=ancestors.concat(directives.filter(p=>['if','else-if','show','auth','permission'].includes(p.name)).map(p=>({kind:p.name,expression:p.exp?.content??''})));
   if(/^[A-Z]|-/.test(n.tag))components.add(n.tag);
   const click=directives.find(p=>p.name==='on'&&p.arg?.content==='click');
   if(click)actions.push({element:n.tag,label:text(n),handler:click.exp?.content??'',conditions,line:n.loc.start.line+(d.template?.loc.start.line??1)-1});
   for(const p of directives)if(p.name==='on'&&p.arg?.type!==4)dynamicEvents.push({element:n.tag,line:n.loc.start.line+(d.template?.loc.start.line??1)-1});
   if(n.tag==='el-form')forms.push({line:n.loc.start.line+(d.template?.loc.start.line??1)-1,model:directives.find(p=>p.name==='bind'&&p.arg?.content==='model')?.exp?.content??null});
   for(const child of n.children??[])visit(child,conditions);return;
  }
  for(const child of n.children??[])visit(child,ancestors);
 }
 if(d.template?.ast)visit(d.template.ast);
 const scripts=[d.script,d.scriptSetup].filter(Boolean).map(s=>scriptFacts(s.content,name,s.loc.start.line-1,s.lang==='tsx'?ts.ScriptKind.TSX:ts.ScriptKind.TS));
 return {actions,componentTags:[...components].sort(),forms,dynamicEvents,imports:scripts.flatMap(s=>s.imports),calls:scripts.flatMap(s=>s.calls),invocations:[...new Set(scripts.flatMap(s=>s.invocations))],scriptParseErrors:scripts.flatMap(s=>s.scriptParseErrors),sfcParseErrors:parsed.errors.map(e=>({code:e.code??'SFC_ERROR',line:e.loc?.start?.line??null}))};
}
function keyFor(call){return call.path&&!call.dynamicUnresolved?[call.requestKind,call.path,call.queryKeys.join('&')].join('|'):null;}
function selfTest(){
 let passed=0;const check=(value,name)=>{if(!value)throw Error('SOURCE_AUDIT_FIXTURE_FAILED_'+name);passed++;};
 const v=vueFacts(Buffer.from('<template><section v-if="canEdit"><!-- <button @click="remove">删除</button> --><button @click="save">保存</button></section></template>'),'fixture.vue');
 check(v.actions.length===1&&v.actions[0].label==='保存','commented-control-excluded');check(v.actions[0].conditions.some(c=>c.expression==='canEdit'),'ancestor-permission-retained');
 const s=scriptFacts('import request from "@/utils/request";const p="/serv/items";export const get= id=>request.get(`${p}/${id}`);const m=new Map();m.get("/not-http");','fixture.ts');
 check(s.calls.length===1&&s.calls[0].path==='/serv/items/{parameter}','real-http-import-and-template-only');
 const a=normalizeURL('/serv/items/1234567890abcdef1234567890abcdef?type=1&name=x');check(a.path==='/serv/items/{fixed-id}'&&a.queryKeys.join(',')==='name,type','ids-and-query-values-not-exported');
 check(keyFor({...s.calls[0],requestKind:'get'})!==keyFor({...s.calls[0],requestKind:'post'}),'different-methods-retained');
 check(keyFor({...s.calls[0],path:'/serv/items/getPage'})!==keyFor({...s.calls[0],path:'/serv/experts/getPage'}),'different-entities-retained');
 check(normalizeURL('https://example.invalid/serv/items?token=private-fixture').dynamicUnresolved,'external-service-not-merged');
 check(normalizeURL('/serv/../other').dynamicUnresolved,'parent-path-refused');
 check(scriptFacts('import request from "@/utils/request";/*request.post("/inactive");*/export const go=()=>request.get("/serv/live");','fixture.ts').calls.length===1,'commented-api-excluded');
 const nested=scriptFacts('import request from "@/utils/request";export const load=async()=>{const res=await request.get("/serv/items/getPage");return res};','nested.ts');
 check(nested.calls[0].function==='load','exported-api-function-not-inner-response-variable');
 const concatenated=scriptFacts('import request from "@/utils/request";export const load=id=>request.get("/serv/items/"+id+"/details");','concat.ts');
 check(concatenated.calls[0].path==='/serv/items/{parameter}/details','dynamic-concatenated-path-retained');
 console.log(JSON.stringify({passed:true,parserCases:passed,sourceFilesOrRuntimeChanged:false}));
}
async function files(root){const out=[];for(const e of await fs.readdir(root,{withFileTypes:true})){const p=root+'/'+e.name;if(e.isSymbolicLink())throw Error('SOURCE_REPARSE_REFUSED');if(e.isDirectory())out.push(...await files(p));else if(e.isFile()&&/\.(vue|ts|tsx|js)$/.test(e.name))out.push(p);}return out.sort();}
function entryViews(project,relative){
 const n=relative.replace(/^src\/views\//,'').split('/')[0];
 if(project==='emergency_pc')return n==='emergencyResponse'?['M02','M07']:n==='workflow'?['M02','M07','M08']:['M02'];
 const mapping={hiddenInvestigate:'M03',intelligentInspection:'M04',work:'M05',majorHazard:'M06',workflow:'M08'};return mapping[n]?['M01',mapping[n]]:['M01'];
}
async function audit(){
 try{await fs.access(O);throw Error('FRESH_SINGLE_SYSTEM_REGISTER_REQUIRED');}catch(e){if(e.code!=='ENOENT')throw e;}
 const records=[],sourcePins={},fileSet=new Set();
 for(const[project,root]of Object.entries(projects))for(const file of await files(root+'/src')){
  const stat=await fs.lstat(file);if(!stat.isFile()||stat.size>4*1024**2)throw Error('REGULAR_BOUNDED_SOURCE_REQUIRED');const raw=await fs.readFile(file),relative=path.posix.relative(root,file),id=project+':'+relative;
  let facts;if(file.endsWith('.vue'))facts=vueFacts(raw,file);else facts={actions:[],componentTags:[],forms:[],dynamicEvents:[],sfcParseErrors:[],...scriptFacts(raw.toString('utf8'),file,0,file.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS)};
  sourcePins[id]={sha256:digest(raw),bytes:raw.length,mtime:stat.mtimeMs};fileSet.add(id);records.push({id,project,path:relative,...facts});
 }
 function resolve(project,from,module){let base;if(module.startsWith('@/'))base='src/'+module.slice(2);else if(module.startsWith('.'))base=path.posix.normalize(path.posix.join(path.posix.dirname(from),module));else return null;if(!base.startsWith('src/'))return null;for(const suffix of ['','.ts','.tsx','.vue','.js','/index.ts','/index.vue','/index.js'])if(fileSet.has(project+':'+base+suffix))return project+':'+base+suffix;return null;}
 const byId=new Map(records.map(r=>[r.id,r]));
 for(const record of records)for(const imported of record.imports)imported.resolvedSource=resolve(record.project,record.path,imported.module);
 const groups=new Map(),unresolved=[],views=[];
 for(const record of records){
  for(const call of record.calls){const k=keyFor(call),location={project:record.project,path:record.path,line:call.line,function:call.function,requestKind:call.requestKind,transportMethod:call.transportMethod};
   if(!k){unresolved.push({...location,pathPattern:call.path,dynamicUnresolved:call.dynamicUnresolved,externalOriginHash:call.externalOriginHash??null});continue;}
   if(!groups.has(k))groups.set(k,{candidateID:'API-'+digest(k).slice(0,16),pathPattern:call.path,requestKind:call.requestKind,transportMethod:call.transportMethod,queryKeys:call.queryKeys,declarations:[],associatedViewSources:[],manualStateRoleAndEntityReviewRequired:true,backendRegistrationAndTransportNotVerifiedByStaticScan:true,accepted:false});
   groups.get(k).declarations.push(location);
  }
 }
 const callsBySource=new Map();for(const g of groups.values())for(const d of g.declarations){const id=d.project+':'+d.path;if(!callsBySource.has(id))callsBySource.set(id,new Set());callsBySource.get(id).add(g.candidateID);}
 for(const record of records.filter(r=>r.path.startsWith('src/views/')&&r.path.endsWith('.vue'))){
  const seen=new Set(),stack=[record.id],candidates=new Set(),missing=new Set();
  while(stack.length&&seen.size<512){const id=stack.pop();if(seen.has(id))continue;seen.add(id);for(const c of callsBySource.get(id)??[])candidates.add(c);const node=byId.get(id);for(const i of node?.imports??[]){if(i.typeOnly)continue;if(i.resolvedSource)stack.push(i.resolvedSource);else if(i.module.startsWith('@/')||i.module.startsWith('.'))missing.add(i.module);}}
  const view={id:record.id,project:record.project,path:record.path,entryPerspectives:entryViews(record.project,record.path),activeClickBindings:record.actions,apiModuleReachabilityCandidates:[...candidates].sort(),dependencyFilesVisited:seen.size,dependencyTraversalBoundHit:stack.length>0,unresolvedLocalImports:[...missing].sort(),functionInvocationAndRuntimeUsageNotProven:true};views.push(view);
 }
 const candidates=[...groups.values()].sort((a,b)=>a.pathPattern.localeCompare(b.pathPattern)||a.requestKind.localeCompare(b.requestKind));const byCandidate=new Map(candidates.map(c=>[c.candidateID,c]));
 for(const v of views)for(const id of v.apiModuleReachabilityCandidates)byCandidate.get(id).associatedViewSources.push({project:v.project,path:v.path,entryPerspectives:v.entryPerspectives});
 for(const record of records){const file=projects[record.project]+'/'+record.path,raw=await fs.readFile(file),stat=await fs.lstat(file),pin=sourcePins[record.id];if(digest(raw)!==pin.sha256||stat.mtimeMs!==pin.mtime)throw Error('ORIGINAL_SOURCE_CHANGED_DURING_AUDIT');}
 const summary={schema:'xnby.r217.single-system-source-candidate-register.v1',at:new Date().toISOString(),logicalInformationSystems:1,entranceCountUsedAsWorkDenominator:false,sourceFiles:records.length,vueViewSources:views.length,activeTemplateClickBindings:views.reduce((n,v)=>n+v.activeClickBindings.length,0),httpCallDeclarations:records.reduce((n,r)=>n+r.calls.length,0),normalizedContractCandidates:candidates.length,contractCandidatesWithMultipleDeclarations:candidates.filter(c=>c.declarations.length>1).length,contractCandidatesAcrossTechnicalPortals:candidates.filter(c=>new Set(c.declarations.map(d=>d.project)).size>1).length,unresolvedHTTPCallDeclarations:unresolved.length,sfcParseErrors:records.reduce((n,r)=>n+r.sfcParseErrors.length,0),scriptParseErrors:records.reduce((n,r)=>n+r.scriptParseErrors.length,0),viewSourcesWithUnresolvedLocalImports:views.filter(v=>v.unresolvedLocalImports.length).length,sourceFilesUnchanged:true,templateAndScriptCommentsExcludedByAST:true,APIContractCandidatesAreNotAtomicBusinessFunctions:true,apiModuleReachabilityIsNotActualFunctionInvocationProof:true,roleStateVariantsAndBackendMappingsNeedReview:true,originalSDKDynamicViewsAndRuntimeMenusNotFullyEnumerated:true,progressDenominatorComplete:false,completedFunctionalPercentage:null,sourceDatabaseAccountsSessionsBusinessRowsOrUserAssetsRead:false,productPublicOrDesktopChanged:false,fullCloneReady:false,parserPackages:{vue:require('@vue/compiler-sfc/package.json').version,typescript:ts.version}};
 await fs.mkdir(O,{recursive:true});for(const[name,data]of Object.entries({'summary.json':summary,'contract-candidates.json':candidates,'view-actions-and-dependencies.json':views,'source-graph.json':records,'source-pins.json':sourcePins,'unresolved-http-calls.json':unresolved}))await fs.writeFile(O+'/'+name,JSON.stringify(data,null,2)+'\n');console.log(JSON.stringify(summary));
}
if(process.argv.includes('--self-test'))selfTest();else await audit();
