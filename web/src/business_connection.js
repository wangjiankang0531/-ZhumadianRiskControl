import {knownPermissions} from './api_permissions.js';
import {readJSON} from './http_json.js';
// Only same-origin business APIs receive the in-memory access token.
import {documentFingerprint,categories,topics} from './spatial_catalog.js';
const error=code=>Object.assign(Error(code),{code});
const responseBytes=new WeakMap();
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
function profile(value,now){
  if(!value||typeof value.subject!=='string'||!value.subject||typeof value.tenant!=='string'||!hash(value.authorizationVersion)||typeof value.policyVersion!=='string'||!value.policyVersion||!knownPermissions(value.permissions)||!Array.isArray(value.enterprises)||value.enterprises.some(e=>typeof e!=='string'||!e)||new Set(value.enterprises).size!==value.enterprises.length||typeof value.allEnterprises!=='boolean'||typeof value.publicSpatial!=='boolean'||!Number.isInteger(value.expiresAt)||value.expiresAt*1000<=now)throw error('AUTH_EXPIRED');
  return JSON.stringify({subject:value.subject,tenant:value.tenant,permissions:[...value.permissions].sort(),enterprises:[...value.enterprises].sort(),allEnterprises:value.allEnterprises,publicSpatial:value.publicSpatial,policyVersion:value.policyVersion,authorizationVersion:value.authorizationVersion,expiresAt:value.expiresAt});
}
export async function viewerBundle(spatial,business){
  const groups=new Map(),registrations=[];
  for(const item of spatial.items){
    if(!item||typeof item.id!=='string'||typeof item.name!=='string'||!['point','line','region'].includes(item.type)||!['public_basic','enterprise'].includes(item.access)||!Array.isArray(item.themes)||item.themes.some(t=>!Object.hasOwn(topics,t))||item.category!=='unregistered'&&!Object.hasOwn(categories,item.category)||!item.style||!item.label||item.access==='public_basic'&&(Object.hasOwn(item,'business')||Object.hasOwn(item,'enterpriseId')))throw error('DATA_INVALID');
    const meta=item.layer;
    if(!meta||typeof meta.id!=='string'||!meta.id||typeof meta.name!=='string'||typeof meta.visible!=='boolean'||!Number.isInteger(meta.order)||meta.order<0||!Number.isInteger(item.drawOrder)||item.drawOrder<0)throw error('DATA_INVALID');
    const category=item.category;let layer=groups.get(meta.id);
    if(!layer){layer={id:meta.id,name:meta.name,visible:meta.visible,locked:true,features:[],order:meta.order};groups.set(meta.id,layer);}
    else if(layer.name!==meta.name||layer.visible!==meta.visible||layer.order!==meta.order)throw error('DATA_CHANGED');
    const feature={id:item.id,name:item.name,type:item.type,positions:item.positions,style:item.style,label:item.label};
    if(item.business)feature.business=item.business;layer.features.push({feature,order:item.drawOrder});
    if(category!=='unregistered')registrations.push({spatialId:item.id,category,themes:item.themes});
  }
  const document={schema:'hongtu.landscape.layers.v1',scene:'zhumadian',coordinates:spatial.coordinates,layers:[...groups.values()].sort((a,b)=>a.order-b.order).map(layer=>({id:layer.id,name:layer.name,visible:layer.visible,locked:true,features:layer.features.sort((a,b)=>a.order-b.order).map(entry=>entry.feature)}))};
  const fingerprint=await documentFingerprint(document);
  const catalog={schema:'xnby.spatial.catalog.v1',scene:'zhumadian',layerFingerprint:fingerprint,exportedAt:new Date().toISOString(),objects:registrations};
  const records=business?{schema:'xnby.business.records.v1',scene:'zhumadian',exportedAt:business.exportedAt,ttlHours:business.ttlHours,records:business.items.map(r=>Object.fromEntries(['sourceSystem','objectType','businessId','enterpriseId','name','updatedAt','attributes'].filter(k=>Object.hasOwn(r,k)).map(k=>[k,r[k]])))}:null;
  return {document,catalog,records};
}
export class BusinessConnection {
  #token=null;#generation=0;#controllers=new Set();#expiry=null;#sessionSignature='';
  constructor({fetcher=fetch,onClear=()=>{},onState=()=>{},onData=()=>{},now=()=>Date.now(),setTimer=(...args)=>setTimeout(...args),clearTimer=(...args)=>clearTimeout(...args)}={}){Object.assign(this,{fetcher,onClear,onState,onData,now,setTimer,clearTimer});this.session=null;}
  #cancel(){this.#generation++;for(const controller of this.#controllers)controller.abort();this.#controllers.clear();}
  disconnect(code='SIGNED_OUT'){
    this.#cancel();this.#token=null;this.session=null;this.#sessionSignature='';if(this.#expiry!==null)this.clearTimer(this.#expiry);this.#expiry=null;this.onClear();this.onState({state:'signed-out',code});
  }
  #failed(code){
    if(['UNAUTHENTICATED','FORBIDDEN','AUTH_EXPIRED'].includes(code)){this.disconnect(code);return;}
    this.#cancel();this.session=null;this.onClear();this.onState({state:'error',code});
  }
  async #get(path,generation){
    if(!this.#token||generation!==this.#generation)throw error('CANCELLED');
    const controller=new AbortController();this.#controllers.add(controller);const timer=this.setTimer(()=>controller.abort(),15000);
    try{
      const fetcher=this.fetcher;let response;try{response=await fetcher('/api/v1/'+path,{headers:{Authorization:'Bearer '+this.#token,Accept:'application/json'},credentials:'omit',cache:'no-store',redirect:'error',referrerPolicy:'no-referrer',signal:controller.signal});}catch{throw error('CONNECTION_FAILED');}
      if(generation!==this.#generation)throw error('CANCELLED');
      let payload;try{const parsed=await readJSON(response,16*1048576);payload=parsed.document;if(payload&&typeof payload==='object')responseBytes.set(payload,parsed.bytes);}catch{throw error('DATA_INVALID');}
      if(!response.ok)throw error([401,403,404,503].includes(response.status)&&typeof payload.error==='string'&&/^[A-Z_]{1,64}$/.test(payload.error)?payload.error:'CONNECTION_FAILED');
      if(!payload||typeof payload!=='object'||Array.isArray(payload))throw error('DATA_INVALID');return payload;
    }finally{this.clearTimer(timer);this.#controllers.delete(controller);}
  }
  async #pages(route,generation,policy,authorization,expectedVersion=null){
    const items=[],ids=new Set();let total=null,metadata=null,bytes=0;
    while(total===null||items.length<total){
      const offset=items.length,p=await this.#get(route+'?limit=200&offset='+offset,generation);bytes+=responseBytes.get(p)??0;if(bytes>32*1048576)throw error('DATA_TOO_LARGE');
      if(!Number.isInteger(p.total)||p.total<0||p.total>10000||p.offset!==offset||p.limit!==200||!Array.isArray(p.items)||p.items.length>200||p.total!==0&&p.items.length===0||p.policyVersion!==policy||p.authorizationVersion!==authorization||!hash(p.datasetVersion)||total!==null&&p.total!==total||expectedVersion&&p.datasetVersion!==expectedVersion||metadata&&p.datasetVersion!==metadata.datasetVersion)throw error('DATA_CHANGED');
      for(const item of p.items){const id=route==='spatial_objects'?item?.id:JSON.stringify([item?.sourceSystem,item?.objectType,item?.businessId]);if(typeof id!=='string'||ids.has(id))throw error('DATA_INVALID');ids.add(id);items.push(item);}
      total=p.total;metadata??=p;if(items.length>total)throw error('DATA_INVALID');
    }
    return {...metadata,items};
  }
  async connect(token){
    this.disconnect();if(typeof token!=='string'||!token||token.length>16384||/\s/u.test(token))throw error('UNAUTHENTICATED');this.#token=token;return this.refresh();
  }
  async refresh(){
    if(!this.#token)return false;this.#cancel();const generation=this.#generation;this.onClear();this.onState({state:'loading'});
    try{
      const session=await this.#get('session',generation),signature=profile(session,this.now());
      if(!session.permissions.includes('spatial:read'))throw error('FORBIDDEN');
      const spatial=await this.#pages('spatial_objects',generation,session.policyVersion,session.authorizationVersion);
      let business=null,businessState=session.permissions.includes('business:read')?'available':'forbidden';
      if(businessState==='available')try{business=await this.#pages('business_records',generation,session.policyVersion,session.authorizationVersion,spatial.datasetVersion);}catch(e){if(e.code!=='BUSINESS_SOURCE_NOT_CONFIGURED')throw e;businessState='unconfigured';}
      const finalSession=await this.#get('session',generation);if(profile(finalSession,this.now())!==signature)throw error('POLICY_CHANGED');
      const bundle=await viewerBundle(spatial,business);if(generation!==this.#generation)return false;
      this.session=session;this.#sessionSignature=signature;if(this.#expiry!==null)this.clearTimer(this.#expiry);
      this.#expiry=this.setTimer(()=>this.disconnect('AUTH_EXPIRED'),Math.max(1,session.expiresAt*1000-this.now()));
      await this.onData({...bundle,session,businessState,datasetVersion:spatial.datasetVersion});if(generation!==this.#generation)return false;
      this.onState({state:'ready',session,businessState});return true;
    }catch(e){if(generation===this.#generation)this.#failed(e.code??'DATA_INVALID');return false;}
  }
  async check(){
    if(!this.#token)return;const generation=this.#generation;
    try{const session=await this.#get('session',generation);if(generation!==this.#generation)return;if(!this.session||profile(session,this.now())!==this.#sessionSignature)await this.refresh();}
    catch(e){if(generation===this.#generation)this.#failed(e.code??'CONNECTION_FAILED');}
  }
}
