import {sourceGainMemoKey,SourceGainMemo} from './source_gain_memo.js';
import {geometryDigest,geometryPacketLimit} from './source_geometry_gain.js';
import {SourceLoadCancelled} from './lod_transaction.js';
export class SourceGainUnavailable extends Error{}
export class SourceGeometryGainWorker{
 constructor({createWorker=()=>new Worker(new URL('source-gain-worker.js',new URL('./',location.href)),{type:'module'}),timeout=30000,onStats=()=>{}}={}){this.createWorker=createWorker;this.timeout=timeout;this.onStats=onStats;this.next=0;this.worker=null;this.pending=null;this.memo=new SourceGainMemo();}
 cancel(){this.generation=(this.generation??0)+1;this.pending?.fail(new SourceLoadCancelled());}
 dispose(){this.cancel();this.worker?.terminate();this.worker=null;this.memo.clear();}
 async measure({marker,snapshot,loadFile,isCurrent}){
  if(this.busy)throw new SourceGainUnavailable('A geometry gain job is already active');this.busy=true;
  const generation=this.generation??0,wanted=()=>{if((this.generation??0)!==generation||!isCurrent())throw new SourceLoadCancelled();};
  try{
   wanted();const key=await sourceGainMemoKey(marker,snapshot);wanted();const cached=this.memo.get(key);
   if(cached){this.onStats({phase:'cached',bytes:0,memoBytes:this.memo.bytes});return {...cached,identity:'memo/'+key,memoHit:true};}
   const result=await this._measure({marker,snapshot,loadFile,isCurrent});wanted();this.memo.set(key,result);return {...result,memoHit:false};
  }finally{this.busy=false;}
 }
 async _measure({marker,snapshot,loadFile,isCurrent}){
  const generation=this.generation??0,wanted=()=>{if((this.generation??0)!==generation||!isCurrent())throw new SourceLoadCancelled();};wanted();
  const expected=marker.parts.reduce((sum,part)=>sum+['geometry.gltf','geometry.bin'].reduce((value,name)=>{const rows=part.files?.filter(f=>f.name===name)??[];if(rows.length!==1||!Number.isSafeInteger(rows[0].bytes)||rows[0].bytes<=0||rows[0].bytes>32*1048576)throw new SourceGainUnavailable('Invalid candidate geometry size');return value+rows[0].bytes;},0),0);
  if(expected>geometryPacketLimit)throw new SourceGainUnavailable('Candidate geometry exceeds CPU staging limit');
  const packets=[];let loaded=0,reported=false;
  try{
   for(const part of marker.parts){wanted();const json=await loadFile(part,'geometry.gltf');wanted();const binary=await loadFile(part,'geometry.bin');wanted();if(!(json instanceof ArrayBuffer)||!(binary instanceof ArrayBuffer))throw new SourceGainUnavailable('Invalid geometry response');loaded+=json.byteLength+binary.byteLength;if(loaded>expected||loaded>geometryPacketLimit)throw new SourceGainUnavailable('Geometry response exceeds declared bound');packets.push({directory:part.directory,json,binary});this.onStats({phase:'loading',bytes:loaded});}
   wanted();if(loaded!==expected)throw new SourceGainUnavailable('Geometry response differs from manifest');
   const id=++this.next,identity=String(id)+'/'+await geometryDigest(new TextEncoder().encode(JSON.stringify(marker)))+'/'+snapshot.cameraKey;wanted();
   if(!this.worker)this.worker=this.createWorker();
   return await new Promise((resolve,reject)=>{
    let interval,timer,finished=false;
    const settle=(error,result)=>{if(finished)return;finished=true;clearInterval(interval);clearTimeout(timer);this.pending=null;reported=true;this.onStats({phase:error instanceof SourceLoadCancelled?'cancelled':error?'failed':'complete',bytes:0,result,error:error?.message});if(error){this.worker?.terminate();this.worker=null;reject(error);}else resolve(result);};
    this.pending={id,fail:error=>settle(error)};
    this.worker.onmessage=event=>{if(event.data?.id!==id)return;try{wanted();if(!event.data.ok)throw new SourceGainUnavailable(event.data.error||'Geometry worker rejected candidate');const result=event.data.result;if(result?.identity!==identity||result.cameraKey!==snapshot.cameraKey||!Number.isFinite(result.gain)||result.gain<0)throw new SourceGainUnavailable('Geometry worker result identity differs');settle(null,result);}catch(error){settle(error);}};
    this.worker.onerror=()=>settle(new SourceGainUnavailable('Geometry worker failed'));
    interval=setInterval(()=>{try{wanted();}catch(error){settle(error);}},40);timer=setTimeout(()=>settle(new SourceGainUnavailable('Geometry worker timed out')),this.timeout);
    try{this.onStats({phase:'computing',bytes:loaded});this.worker.postMessage({id,identity,marker,snapshot,packets},[snapshot.samples.buffer,...packets.flatMap(p=>[p.json,p.binary])]);}catch(error){settle(error);}
   });
  }catch(error){if(!reported)this.onStats({phase:error instanceof SourceLoadCancelled?'cancelled':'failed',bytes:0,error:error.message});throw error;}
 }
}
