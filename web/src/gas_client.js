import {knownPermissions} from './api_permissions.js';
import {readMaterialResponse} from './focus_material_protocol.js';
import {readJSON} from './http_json.js';
const fail=code=>Object.assign(new Error(code),{code});
export class GasClient {
  #token=null;#generation=0;#controllers=new Set();#expiry=null;#poll=null;
  constructor({fetcher=fetch,now=()=>Date.now(),setTimer=(...args)=>setTimeout(...args),clearTimer=(...args)=>clearTimeout(...args),onClear=()=>{}}={}){
    Object.assign(this,{fetcher,now,setTimer,clearTimer,onClear});this.session=null;
  }
  disconnect(code='SIGNED_OUT'){
    this.#generation++;for(const c of this.#controllers)c.abort();this.#controllers.clear();
    this.#token=null;this.session=null;
    if(this.#expiry!==null)this.clearTimer(this.#expiry);
    if(this.#poll!==null)this.clearTimer(this.#poll);
    this.#expiry=this.#poll=null;this.onClear(code);
  }
  #valid(session){
    if(!session||typeof session.subject!=='string'||!session.subject||typeof session.tenant!=='string'||!session.tenant||typeof session.policyVersion!=='string'||!session.policyVersion||!Array.isArray(session.enterprises)||session.enterprises.some(e=>typeof e!=='string'||!e)||new Set(session.enterprises).size!==session.enterprises.length||!knownPermissions(session.permissions)||!session.permissions.includes('gas:read')||typeof session.publicSpatial!=='boolean'||typeof session.allEnterprises!=='boolean'||typeof session.authorizationVersion!=='string'||!/^[a-f0-9]{64}$/.test(session.authorizationVersion)||!Number.isInteger(session.expiresAt)||session.expiresAt*1000<=this.now())throw fail('FORBIDDEN');
    if(session.gasWorkflow!==true)throw fail('GAS_NOT_CONFIGURED');
    return session;
  }
  async request(route,{method='GET',body,key,binary}={}){
    if(!/^(session|gas_alerts(?:\/[a-f0-9]{32}(?:\/(history|nearby|classify|verify|cooperate|handoff-request|archive|reopen|materials(?:\/[a-f0-9]{32})?))?)?)(\?[^#]*)?$/.test(route))throw fail('INVALID_ROUTE');
    const path=route.split('?')[0],write=method==='POST';
    if(!['GET','HEAD','POST'].includes(method)||write&&(!/^gas_alerts\/[a-f0-9]{32}\/(classify|verify|cooperate|handoff-request|archive|reopen|materials)$/.test(path)||body===undefined||typeof key!=='string'||!/^[a-f0-9]{32}$/.test(key))||!write&&(body!==undefined||/\/(classify|verify|cooperate|handoff-request|archive|reopen)$/.test(path)))throw fail('INVALID_ROUTE');
    if(!this.#token)throw fail('SIGNED_OUT');
    const generation=this.#generation,c=new AbortController();this.#controllers.add(c);
    const timer=this.setTimer(()=>c.abort(),binary||route.includes('/materials')?60000:15000);
    try{
      const headers={Authorization:'Bearer '+this.#token,Accept:binary?'application/octet-stream':'application/json'};
      if(body!==undefined){headers['Content-Type']='application/json';headers['Idempotency-Key']=key;}
      const fetcher=this.fetcher;
      const response=await fetcher('/api/v1/'+route,{method,body:body===undefined?undefined:JSON.stringify(body),headers,credentials:'omit',cache:'no-store',redirect:'error',referrerPolicy:'no-referrer',signal:c.signal});
      if(generation!==this.#generation)throw fail('CANCELLED');
      let data;
      if(binary&&response.ok){
        if(this.session&&response.headers.get('X-XNBY-Authorization-Version')!==this.session.authorizationVersion){this.disconnect('POLICY_CHANGED');throw fail('POLICY_CHANGED');}
        data=await readMaterialResponse(response,binary,()=>generation===this.#generation);
      }else data=(await readJSON(response,(route.includes('/nearby')?16:8)*1048576)).document;
      if(generation!==this.#generation)throw fail('CANCELLED');
      if(!response.ok){const code=typeof data?.error==='string'&&/^[A-Z_]{1,64}$/.test(data.error)?data.error:'CONNECTION_FAILED';if([401,403].includes(response.status))this.disconnect(code);throw fail(code);}
      if(!data||typeof data!=='object'||Array.isArray(data))throw fail('DATA_INVALID');
      if(this.session&&data.authorizationVersion!==this.session.authorizationVersion){this.disconnect('POLICY_CHANGED');throw fail('POLICY_CHANGED');}
      return data;
    }catch(error){if(generation!==this.#generation&&!error.code)throw fail('CANCELLED');throw error.code?error:fail('CONNECTION_FAILED');}
    finally{this.clearTimer(timer);this.#controllers.delete(c);}
  }
  async connect(token){
    this.disconnect();if(typeof token!=='string'||!token||token.length>16384||/\s/.test(token))throw fail('UNAUTHENTICATED');
    this.#token=token;
    try{
      this.session=this.#valid(await this.request('session'));
      this.#expiry=this.setTimer(()=>this.disconnect('AUTH_EXPIRED'),this.session.expiresAt*1000-this.now());
      this.#schedule();return this.session;
    }catch(error){this.disconnect(error.code);throw error;}
  }
  #schedule(){this.#poll=this.setTimer(()=>this.check(),15000);}
  async check(){
    if(!this.session)return;
    try{this.#valid(await this.request('session'));if(this.session)this.#schedule();}
    catch(error){if(this.session)this.disconnect(error.code);}
  }
  list(query={}){return this.request('gas_alerts?'+new URLSearchParams(query));}
  nearby(id,query){return this.request('gas_alerts/'+id+'/nearby?'+new URLSearchParams(query));}
  detail(id){return this.request('gas_alerts/'+id);}
  history(id,offset=0){return this.request('gas_alerts/'+id+'/history?limit=20&offset='+offset);}
  materials(id){return this.request('gas_alerts/'+id+'/materials');}
  downloadMaterial(id,metadata){return this.request('gas_alerts/'+id+'/materials/'+metadata.id,{binary:metadata});}
  write(id,action,body,key){return this.request('gas_alerts/'+id+'/'+action,{method:'POST',body,key});}
}
