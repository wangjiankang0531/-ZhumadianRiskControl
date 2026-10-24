/** Run the actual original/adapted interceptor with synthetic cookies and a network-free fake Axios. */
import fs from 'node:fs/promises';
import vm from 'node:vm';
import path from 'node:path';
import {createRequire} from 'node:module';
import {adapt,ORIGINAL_MOCK_BASE} from './adapt_original_bigscreen_requests.mjs';
const [serviceFile,requestFile,parserFile,output]=process.argv.slice(2);
const parse=createRequire(import.meta.url)(path.resolve(parserFile)).parse;
const service=await fs.readFile(serviceFile),request=await fs.readFile(requestFile),beforeService=Buffer.from(service),beforeRequest=Buffer.from(request);
const own='http://127.0.0.1:18891';let checks=0;
function requireTrue(value){if(!value)throw Error('BIGSCREEN_REQUEST_ADAPTER_CHECK_FAILED');checks++;}
function interceptor(source,token='own-synthetic-probe-token'){
 const ast=parse(source,{sourceType:'module'});let classic=source;
 for(const item of [...ast.program.body].reverse()) {
  if(item.type==='ImportDeclaration')classic=classic.slice(0,item.start)+classic.slice(item.end);
  else if(item.type==='ExportDefaultDeclaration'){requireTrue(item.declaration.type==='Identifier'&&item.declaration.name==='Service');classic=classic.slice(0,item.start)+'globalThis.__OwnService=Service;'+classic.slice(item.end);}
  else requireTrue(item.type==='ClassDeclaration'&&item.id.name==='Service');
 }
 let requestCallback;const fake={interceptors:{request:{use(fn){requestCallback=fn;}},response:{use(){}}}};
 const sandbox={URL,window:{location:{href:own+'/reference-bigscreen/',origin:own}},axios:{create(){return fake;}},Cookies:{get(){return token;}},store:{},errorCode:{},Notification:{},loadingUtil:{},console:{log(){}}};vm.runInNewContext(classic,sandbox,{timeout:1000});new sandbox.__OwnService('/unused');return requestCallback;
}
const old=interceptor(service.toString('utf8'));let requestObject={baseURL:ORIGINAL_MOCK_BASE,url:'/patrol/inspectover',headers:{}};requireTrue(old(requestObject).headers.Authorization==='bearer own-synthetic-probe-token');
const changed=adapt(service,request,'/zhumadian/api/reference-mock',parse),next=interceptor(changed.serviceCode);
for(const [baseURL,url,authorized] of [
 ['/zhumadian/api/serv','/overview',true],[own+'/zhumadian/api/serv','/overview',true],
 [ORIGINAL_MOCK_BASE,'/patrol/inspectover',false],['https://example.invalid','/api',false],
 ['/same','//example.invalid/api',false],['http://127.0.0.1:18893','/hikvideo/query',false],
 ['https://127.0.0.1:18891','/api',false],[undefined,'/api',true],
 ['https://example.invalid',own+'/api',true],['/same','http://127.0.0.1:18891@example.invalid/api',false],
 ['/same','http://[',false],['/same','//127.0.0.1:18891/api',true]
]) {
 const item={baseURL,url,headers:{'X-Owned-Probe':'same'}};const result=next(item);requireTrue((result.headers.Authorization==='bearer own-synthetic-probe-token')===authorized);requireTrue(result.headers['X-Owned-Probe']==='same');
}
const missing=interceptor(changed.serviceCode,null);requireTrue(!missing({baseURL:'/api',url:'/x',headers:{}}).headers.Authorization);
requireTrue(changed.requestCode.includes('"/zhumadian/api/reference-mock"')&&!changed.requestCode.includes(ORIGINAL_MOCK_BASE));
for(const invalid of ['https://example.invalid','//example.invalid','/a/../b','/a?x=1']){let rejected=false;try{adapt(service,request,invalid,parse);}catch(e){rejected=true;}requireTrue(rejected);}
let mismatch=false;try{adapt(Buffer.from(service.toString()+' '),request,'/own',parse);}catch(e){mismatch=true;}requireTrue(mismatch);
requireTrue((await fs.readFile(serviceFile)).equals(beforeService)&&(await fs.readFile(requestFile)).equals(beforeRequest));
const result={checks,originalWouldAttachSyntheticTokenToExternalMock:true,adaptedOnlyAttachesCookieTokenToOwnOrigin:true,mockRepointedToOwnMount:true,realCookiesOrCredentialsRead:false,networkRequestsMade:0,currentBuildModified:false,backendMockDataProvided:false,fullCloneReady:false};await fs.mkdir(output);await fs.writeFile(path.join(output,'receipt.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
