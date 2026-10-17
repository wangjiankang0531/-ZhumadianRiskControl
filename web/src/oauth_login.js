import {readJSON} from './http_json.js';
// OAuth authorization-code + S256 PKCE. Tokens remain in memory; ID tokens are not used as API credentials.
const transactionKey='xnby.oauth.transaction.v1';
const error=code=>Object.assign(Error(code),{code});
const plain=v=>v&&typeof v==='object'&&!Array.isArray(v);
const loopback=url=>['127.0.0.1','localhost','[::1]'].includes(url.hostname);
export function portalConfiguration(value,origin){
  if(!plain(value)||value.schema!=='xnby.portal.config.v1'||Object.keys(value).some(k=>!['schema','mode','oauth','development','publicOrigin'].includes(k)))throw error('CONFIG_INVALID');
  if(value.mode==='local')return {mode:'local'};
  if(value.mode!=='authenticated'||!plain(value.oauth))throw error('CONFIG_INVALID');
  const o=value.oauth,required=['issuer','clientId','authorizationEndpoint','tokenEndpoint','scope'];
  if(Object.keys(o).some(k=>!required.includes(k))||required.some(k=>typeof o[k]!=='string'||!o[k]||o[k].length>2048))throw error('CONFIG_INVALID');
  if(typeof value.development!=='undefined'&&typeof value.development!=='boolean')throw error('CONFIG_INVALID');
  const app=new URL(origin),development=value.development===true&&loopback(app);
  if(value.publicOrigin!==undefined&&(typeof value.publicOrigin!=='string'||value.publicOrigin!==app.origin))throw error('CONFIG_INVALID');
  if(app.protocol!=='https:'&&!(development&&app.protocol==='http:'))throw error('CONFIG_INVALID');
  for(const field of ['issuer','authorizationEndpoint','tokenEndpoint']){
    let u;try{u=new URL(o[field]);}catch{throw error('CONFIG_INVALID');}
    if(u.username||u.password||u.hash||u.search||u.protocol!=='https:'&&!(field!=='issuer'&&development&&loopback(u)&&u.protocol==='http:'))throw error('CONFIG_INVALID');
  }
  if(!/^[^\s\x00-\x1f\x7f]{1,256}$/u.test(o.clientId)||/[\x00-\x1f\x7f]/u.test(o.scope))throw error('CONFIG_INVALID');
  return {mode:'authenticated',oauth:{...o},development};
}
export async function readPortalConfiguration(fetcher,origin){
  let response;try{response=await fetcher('/application/config.json',{cache:'no-store',credentials:'omit',redirect:'error',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(10000)});}catch{throw error('CONFIG_UNAVAILABLE');}
  if(response.status===404)return {mode:'local'};
  if(!response.ok)throw error('CONFIG_UNAVAILABLE');
  try{const result=await readJSON(response,16384);return portalConfiguration(result.document,origin);}catch{throw error('CONFIG_INVALID');}
}
const base64=bytes=>btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
export class OAuthLogin {
  constructor(configuration,{storage,fetcher,cryptoApi=crypto,now=()=>Date.now(),redirectUri}){
    this.oauth=configuration.oauth;this.storage=storage;this.fetcher=fetcher;this.crypto=cryptoApi;this.now=now;this.redirectUri=redirectUri;
    const uri=new URL(redirectUri);if(uri.search||uri.hash||uri.username||uri.password)throw error('CONFIG_INVALID');
    this.signature=JSON.stringify({oauth:this.oauth,redirectUri});
  }
  async begin(){
    const verifier=base64(this.crypto.getRandomValues(new Uint8Array(48))),state=base64(this.crypto.getRandomValues(new Uint8Array(32)));
    const challenge=base64(new Uint8Array(await this.crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))));
    try{this.storage.setItem(transactionKey,JSON.stringify({state,verifier,at:this.now(),signature:this.signature}));}catch{throw error('LOGIN_STORAGE_UNAVAILABLE');}
    const url=new URL(this.oauth.authorizationEndpoint);url.search=new URLSearchParams({response_type:'code',client_id:this.oauth.clientId,redirect_uri:this.redirectUri,scope:this.oauth.scope,state,code_challenge:challenge,code_challenge_method:'S256',prompt:'select_account'}).toString();return url.href;
  }
  async complete(callback){
    let transaction;try{transaction=JSON.parse(this.storage.getItem(transactionKey));this.storage.removeItem(transactionKey);}catch{throw error('LOGIN_INVALID');}
    const p=callback.searchParams;
    if([...p.keys()].some(k=>!['code','state','iss','error','error_description','error_uri','session_state'].includes(k))||[...new Set(p.keys())].some(k=>p.getAll(k).length!==1)||!plain(transaction)||transaction.signature!==this.signature||typeof transaction.at!=='number'||this.now()<transaction.at||this.now()-transaction.at>300000||p.get('state')!==transaction.state||typeof transaction.verifier!=='string'||!/^[A-Za-z0-9_-]{43,128}$/.test(transaction.verifier)||p.get('iss')!==this.oauth.issuer||callback.origin+callback.pathname!==this.redirectUri||callback.hash)throw error('LOGIN_INVALID');
    if(p.has('error'))throw error('LOGIN_CANCELLED');
    const code=p.get('code');if(!code||code.length>4096||/[\x00-\x20\x7f]/u.test(code))throw error('LOGIN_INVALID');
    const fetcher=this.fetcher;let response;try{response=await fetcher(this.oauth.tokenEndpoint,{method:'POST',credentials:'omit',cache:'no-store',redirect:'error',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(15000),headers:{'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'},body:new URLSearchParams({grant_type:'authorization_code',client_id:this.oauth.clientId,redirect_uri:this.redirectUri,code_verifier:transaction.verifier,code}).toString()});}catch{throw error('LOGIN_UNAVAILABLE');}
    if(!response.ok)throw error('LOGIN_REJECTED');
    let result;try{result=(await readJSON(response,65536)).document;}catch{throw error('LOGIN_REJECTED');}
    if(!plain(result)||typeof result.token_type!=='string'||result.token_type.toLowerCase()!=='bearer'||typeof result.access_token!=='string'||result.access_token.length>16384||!result.access_token||/\s/u.test(result.access_token))throw error('LOGIN_REJECTED');
    return result.access_token;
  }
  cancel(){this.storage.removeItem(transactionKey);}
}
