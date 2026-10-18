import {LoadingManager} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

export function leasedAssetURL(url,token,base){
  if(!/^[0-9a-f]{32}$/.test(token))throw Error('航拍读取租约无效');
  const resolved=new URL(url,base),origin=new URL(base).origin;
  if(resolved.origin===origin&&resolved.pathname.startsWith('/native/'))resolved.searchParams.set('lease',token);
  return resolved.href;
}
export class LeasedDownloads{
  constructor(token,base=location.href,fetcher=fetch){
    if(!/^[0-9a-f]{32}$/.test(token))throw Error('航拍读取租约无效');
    this.token=token;this.fetcher=(...args)=>fetcher(...args);this.base=base;
    const manager=new LoadingManager();manager.setURLModifier(url=>leasedAssetURL(url,token,base));this.loader=new GLTFLoader(manager);
  }
  load(url){return this.loader.loadAsync(url);}
  async read(url){if(!this.token)throw Error('航拍读取租约已释放');const response=await this.fetcher(leasedAssetURL(url,this.token,this.base),{cache:'no-store'});if(!response.ok)throw Error('航拍源文件HTTP '+response.status);return response.arrayBuffer();}
  release(){if(!this.token)return;const token=this.token;this.token=null;return Promise.resolve().then(()=>this.fetcher(new URL(`api/lod-lease/${token}/release`,this.base).href,{method:'POST',keepalive:true})).catch(()=>{});}
}
