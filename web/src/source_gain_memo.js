import {geometryDigest} from './source_geometry_gain.js';
import {sourceBundleIdentity} from './source_residency.js';
// The complete input identity, including exact Float64 sample bytes and camera
// matrices, is required. A similar camera or unchanged parent name is not enough.
export async function sourceGainMemoKey(marker,snapshot){
 if(!(snapshot?.samples instanceof Float64Array))throw Error('Invalid memo snapshot');
 const samples=await geometryDigest(new Uint8Array(snapshot.samples.buffer,snapshot.samples.byteOffset,snapshot.samples.byteLength));
 return geometryDigest(new TextEncoder().encode(JSON.stringify({model:'gpu_visible_pixels_cpu_child_triangles_v1',source:sourceBundleIdentity(marker),snapshot:{...snapshot,samples}})));
}
export class SourceGainMemo{
 constructor({maxBytes=4*1048576,maxEntries=256}={}){if(!Number.isSafeInteger(maxBytes)||maxBytes<=0||!Number.isSafeInteger(maxEntries)||maxEntries<=0)throw Error('Invalid memo bound');this.maxBytes=maxBytes;this.maxEntries=maxEntries;this.bytes=0;this.entries=new Map();}
 get(key){const entry=this.entries.get(key);if(!entry)return null;this.entries.delete(key);this.entries.set(key,entry);return JSON.parse(entry.json);}
 set(key,value){
  if(!/^[0-9a-f]{64}$/.test(key)||!Number.isFinite(value?.gain)||value.gain<0)throw Error('Invalid memo result');
  const json=JSON.stringify(value),bytes=new TextEncoder().encode(json).byteLength+key.length;
  const prior=this.entries.get(key);if(prior){this.entries.delete(key);this.bytes-=prior.bytes;}
  if(bytes>this.maxBytes)return false;
  while(this.entries.size&&(this.entries.size>=this.maxEntries||this.bytes+bytes>this.maxBytes)){const [old,entry]=this.entries.entries().next().value;this.entries.delete(old);this.bytes-=entry.bytes;}
  this.entries.set(key,{json,bytes});this.bytes+=bytes;return true;
 }
 clear(){this.entries.clear();this.bytes=0;}
}
