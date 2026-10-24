/** Deployment-only source adapter: original API behavior, own mock mount, same-origin cookie token. */
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

export const SERVICE_SHA256='f444eec2d25a4b5bc15c2801489d14acccf81b9af85af49311ab42ae80240fb6';
export const REQUEST_SHA256='d54701009b43043ae9da52cf93b70946b7e6198068317bc029a7f683d9dced54';
export const ORIGINAL_MOCK_BASE='https://mock.apipost.net/mock/42471b1e0ce0000';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');

export function adapt(service,request,mockBase,parse) {
 if(sha(service)!==SERVICE_SHA256||sha(request)!==REQUEST_SHA256)throw Error('PINNED_ORIGINAL_BIGSCREEN_REQUEST_SOURCES_REQUIRED');
 if(!/^\/[A-Za-z0-9_/-]+$/.test(mockBase)||mockBase.includes('//')||mockBase.includes('..'))throw Error('EXPLICIT_OWN_MOCK_MOUNT_REQUIRED');
 const original=service.toString('utf8'),mock=request.toString('utf8');
 const anchor=/if\s*\(\s*token\s*\)\s*\{\s*req\.headers\[['"]Authorization['"]\]\s*=\s*['"]bearer ['"]\s*\+\s*token;\s*\}/g;
 if([...original.matchAll(anchor)].length!==1)throw Error('ONE_ORIGINAL_COOKIE_HEADER_BLOCK_REQUIRED');
 const replacement=`let ownOrigin = false;
                try {
                    const base = new URL(req.baseURL || window.location.href, window.location.href);
                    ownOrigin = new URL(req.url || "", base).origin === window.location.origin;
                } catch (_) {}
                if (token && ownOrigin) {
                    req.headers['Authorization'] = 'bearer ' + token;
                }`;
 const serviceCode=original.replace(anchor,replacement);
 const literal=JSON.stringify(ORIGINAL_MOCK_BASE);
 if(mock.split(literal).length!==2)throw Error('ONE_ORIGINAL_MOCK_BASE_REQUIRED');
 const requestCode=mock.replace(literal,JSON.stringify(mockBase));
 for(const source of [serviceCode,requestCode])parse(source,{sourceType:'module'});
 return {serviceCode,requestCode};
}

async function main(){
 const args=Object.fromEntries(Array.from({length:(process.argv.length-2)/2},(_,i)=>[process.argv[2+i*2],process.argv[3+i*2]]));
 for(const name of ['--service-source','--request-source','--mock-base','--parser','--parser-sha256','--output'])if(!args[name])throw Error('EXPLICIT_ADAPTER_ARGUMENTS_REQUIRED');
 if(sha(await fs.readFile(args['--parser']))!==args['--parser-sha256'])throw Error('EXISTING_PARSER_PIN_MISMATCH');
 const require=createRequire(import.meta.url),parse=require(path.resolve(args['--parser'])).parse;
 const service=await fs.readFile(args['--service-source']),request=await fs.readFile(args['--request-source']);
 const {serviceCode,requestCode}=adapt(service,request,args['--mock-base'],parse);
 await fs.mkdir(args['--output']);
 await fs.writeFile(path.join(args['--output'],'service.js'),serviceCode,{flag:'wx'});await fs.writeFile(path.join(args['--output'],'request.js'),requestCode,{flag:'wx'});
 const result={sourceServiceSHA256:sha(service),sourceRequestSHA256:sha(request),parserSHA256:args['--parser-sha256'],adaptedServiceSHA256:sha(serviceCode),adaptedRequestSHA256:sha(requestCode),mockBase:args['--mock-base'],originalSourceModified:false,originalAuthenticationProtocolChanged:false,onlyCookieDerivedTokenAttachmentScopedToSameOrigin:true,externalMockStillCalledDirectly:false,appliedToCurrentBuild:false,backendMockDataProvided:false,fullCloneReady:false};
 await fs.writeFile(path.join(args['--output'],'receipt.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
