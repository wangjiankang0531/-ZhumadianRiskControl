/** Rewrite only pinned deployment endpoint values; retain original renderer branch and UI settings. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const args=Object.fromEntries(Array.from({length:(process.argv.length-2)/2},(_,i)=>[process.argv[2+i*2],process.argv[3+i*2]]));
for(const name of ['--source','--parser','--parser-sha256','--origin','--output'])if(!args[name])throw Error('EXPLICIT_RUNTIME_CONFIG_ARGUMENTS_REQUIRED');
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const source=await fs.readFile(args['--source']);if(sha(source)!=='3557c2aa806e684156ea4a0798794e5593c5d23e146c16acc463655e22f1eb53')throw Error('ORIGINAL_PUBLIC_CONFIG_PIN_MISMATCH');
if(sha(await fs.readFile(args['--parser']))!==args['--parser-sha256']||args['--parser-sha256']!=='82d72e197e27bf909ae10ffc8d1a969aeb94fe96ec96c4e9cb685a0a8229e40c')throw Error('PARSER_PIN_MISMATCH');
const origin=new URL(args['--origin']);if(origin.protocol!=='http:'||origin.hostname!=='127.0.0.1'||!origin.port||Number(origin.port)<1024||origin.username||origin.password||origin.pathname!=='/'||origin.search||origin.hash)throw Error('EXPLICIT_OWN_LOOPBACK_ORIGIN_REQUIRED');
const parse=createRequire(import.meta.url)(path.resolve(args['--parser'])).parse;
const ast=parse(source.toString('utf8'),{sourceType:'script'});const declaration=ast.program.body.find(n=>n.type==='VariableDeclaration')?.declarations.find(n=>n.id.name==='config');if(declaration?.init.type!=='ObjectExpression')throw Error('ORIGINAL_CONFIG_OBJECT_REQUIRED');
const properties=new Map(declaration.init.properties.map(p=>[p.key.name||p.key.value,p]));if(properties.get('isExlorer')?.value.value!==false)throw Error('ORIGINAL_CLOUD_RENDERER_BRANCH_REQUIRED');
const values={server:origin.host,dtsLib:'/zhumadian/unavailable-renderer/libac',wsAddress:`ws://${origin.host}/zhumadian/api/serv/websocket/`,collaborateWsAddress:`ws://${origin.host}/zhumadian/api/bigscreen/collaborate/`,internalService:'/zhumadian/api/bigscreen',realService:'/zhumadian/api/serv',difyOrigin:origin.origin,difyURL:'/zhumadian/unavailable/dify'};
const edits=Object.entries(values).map(([key,value])=>{const node=properties.get(key)?.value;if(node?.type!=='StringLiteral')throw Error('EXACT_ORIGINAL_ENDPOINT_FIELD_REQUIRED');return {start:node.start,end:node.end,text:JSON.stringify(value)};}).sort((a,b)=>b.start-a.start);
let code=source.toString('utf8');for(const edit of edits)code=code.slice(0,edit.start)+edit.text+code.slice(edit.end);const updated=parse(code,{sourceType:'script'});const updatedProperties=new Map(updated.program.body.find(n=>n.type==='VariableDeclaration').declarations.find(n=>n.id.name==='config').init.properties.map(p=>[p.key.name||p.key.value,p]));
for(const [key,value] of Object.entries(values))if(updatedProperties.get(key)?.value.value!==value)throw Error('UPDATED_ENDPOINT_BINDING_MISMATCH');
for(const [key,value] of properties)if(!(key in values)){const next=updatedProperties.get(key);if(!next||source.toString('utf8').slice(value.start,value.end)!==code.slice(next.start,next.end))throw Error('NON_ENDPOINT_CONFIG_CHANGED');}
await fs.mkdir(args['--output']);await fs.writeFile(path.join(args['--output'],'config.js'),code,{flag:'wx'});
const receipt={sourceSHA256:sha(source),runtimeSHA256:sha(code),changedEndpointFields:Object.keys(values),allOtherOriginalPropertiesUnchanged:true,originalRendererModeChanged:false,originalDtsClientSubstituted:false,originalRendererAvailable:false,rendererEntryExplicitlyUnavailable:true,sameOriginBackendAndCollaboration:true,originalSourceModified:false,fullCloneReady:false};await fs.writeFile(path.join(args['--output'],'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(receipt));
