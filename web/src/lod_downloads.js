import {LoadingManager} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

export function leasedAssetURL(url,token,base){
  if(!/^[0-9a-f]{32}$/.test(token))throw Error('航拍读取租约无效');
  const resolved=new URL(url,base),origin=new URL(base).origin;
  if(resolved.origin===origin&&resolved.pathname.startsWith('/native/'))resolved.searchParams.set('lease',token);
  return resolved.href;
}
export class LeasedDownloads{
  #geometry=new Map();#geometryBytes=0;
  constructor(token,base=location.href,fetcher=fetch,{geometryCacheBytes=0,onGeometryStats=()=>{}}={}){
    if(!/^[0-9a-f]{32}$/.test(token))throw Error('航拍读取租约无效');
    if(!Number.isSafeInteger(geometryCacheBytes)||geometryCacheBytes<0||geometryCacheBytes>32*1048576||typeof onGeometryStats!=='function')throw Error('Invalid source geometry cache bound');
    this.geometryLimit=geometryCacheBytes;this.onGeometryStats=onGeometryStats;this.geometryStats={hits:0,misses:0,evictions:0,peakBytes:0};
    this.token=token;this.fetcher=(...args)=>fetcher(...args);this.base=base;
    const manager=new LoadingManager();manager.setURLModifier(url=>leasedAssetURL(url,token,base));this.loader=new GLTFLoader(manager);
  }
  load(url){return this.loader.loadAsync(url);}
  geometrySnapshot(){return {...this.geometryStats,bytes:this.#geometryBytes,entries:this.#geometry.size,limit:this.geometryLimit,released:this.token===null,scope:'unverified_leased_bytes_only_callers_still_check_SHA'};}
  #publishGeometry(){try{this.onGeometryStats(this.geometrySnapshot());}catch{this.geometryStats.observerErrors=(this.geometryStats.observerErrors??0)+1;}}
  async read(url){
    if(!this.token)throw Error('航拍读取租约已释放');
    const token=this.token,resolved=leasedAssetURL(url,token,this.base);let eligible=false;
    if(this.geometryLimit){const parsed=new URL(resolved);eligible=parsed.origin===new URL(this.base).origin&&/^\/native\/(?:tile_\d+_depth_\d+|family_tile_\d+_[0-9a-f]{16})\/part_\d{3}\/geometry\.(?:gltf|bin)$/.test(parsed.pathname);}
    if(eligible&&this.#geometry.has(resolved)){const bytes=this.#geometry.get(resolved);this.#geometry.delete(resolved);this.#geometry.set(resolved,bytes);this.geometryStats.hits++;this.#publishGeometry();return bytes.slice(0);}
    if(eligible)this.geometryStats.misses++;
    const response=await this.fetcher(resolved,{cache:'no-store'});if(!response.ok)throw Error('航拍源文件HTTP '+response.status);const bytes=await response.arrayBuffer();
    if(eligible){
      if(this.token!==token)throw Error('航拍读取租约已释放');
      if(!(bytes instanceof ArrayBuffer))throw Error('Invalid leased geometry bytes');
      // Return a separate buffer: a gain worker transfers/detaches its input.
      // The cache is request-owned, bounded and not a SHA verification authority.
      if(bytes.byteLength>0&&bytes.byteLength<=this.geometryLimit){
        const prior=this.#geometry.get(resolved);if(prior){this.#geometryBytes-=prior.byteLength;this.#geometry.delete(resolved);}
        while(this.#geometry.size&&(this.#geometryBytes+bytes.byteLength>this.geometryLimit||this.#geometry.size>=128)){const [key,value]=this.#geometry.entries().next().value;this.#geometry.delete(key);this.#geometryBytes-=value.byteLength;this.geometryStats.evictions++;}
        this.#geometry.set(resolved,bytes);this.#geometryBytes+=bytes.byteLength;this.geometryStats.peakBytes=Math.max(this.geometryStats.peakBytes,this.#geometryBytes);this.#publishGeometry();return bytes.slice(0);
      }
      this.#publishGeometry();
    }
    return bytes;
  }
  release(){if(!this.token)return;const token=this.token;this.token=null;this.#geometry.clear();this.#geometryBytes=0;if(this.geometryLimit)this.#publishGeometry();return Promise.resolve().then(()=>this.fetcher(new URL(`api/lod-lease/${token}/release`,this.base).href,{method:'POST',keepalive:true})).catch(()=>{});}
}
