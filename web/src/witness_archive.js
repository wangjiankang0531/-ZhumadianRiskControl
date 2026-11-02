import {readJSON} from './http_json.js';
const targets=[5000,20000,40000],SHA=/^[0-9a-f]{64}$/;
export function witnessArchiveEnabled(href){
 const u=new URL(href);return !u.username&&!u.password&&u.protocol==='http:'&&['127.0.0.1','localhost','[::1]'].includes(u.hostname)&&['qa','witness','witnessArchive'].every(k=>u.searchParams.get(k)==='1');
}
// QA-only same-origin PNG archive. The capability supplies a nonce, never an
// arbitrary upload URL. Each deadline is attempted once; failure stays visible.
export class WitnessArchive{
 #capability=null;#seen=new Set();#closed=false;#abort=new AbortController();
 constructor({href,fetcher=fetch,onUpdate=()=>{}}){this.enabled=witnessArchiveEnabled(href);this.base=new URL('./',href);this.fetcher=(...args)=>fetcher(...args);this.onUpdate=onUpdate;this.stats={attempted:0,archived:0,failed:0,pending:0};}
 snapshot(){return {enabled:this.enabled,closed:this.#closed,...this.stats};}
 #update(){try{this.onUpdate();}catch{this.stats.observerErrors=(this.stats.observerErrors??0)+1;}}
 async #cap(){
  if(!this.#capability)this.#capability=(async()=>{const response=await this.fetcher(new URL('qa/witness-capability.json',this.base).href,{cache:'no-store',credentials:'omit',redirect:'error',signal:this.#abort.signal});if(!response.ok)throw Error('Witness archive capability unavailable');const c=(await readJSON(response,4096)).document;if(c?.schema!=='xnby.witness_archive.v1'||!(/^[0-9a-f]{32}$/).test(c.nonce)||JSON.stringify(c.targets)!==JSON.stringify(targets))throw Error('Invalid witness archive capability');return c;})();
  return this.#capability;
 }
 async archive(record,blob){
  if(!this.enabled)return false;
  if(this.#seen.has(record.targetMs))return false;this.#seen.add(record.targetMs);this.stats.attempted++;this.stats.pending++;record.archiveStatus='pending';this.#update();
  try{
   if(this.#closed||!targets.includes(record.targetMs)||!Number.isFinite(record.actualElapsedMs)||record.actualElapsedMs<record.targetMs||record.actualElapsedMs>180000||!(blob instanceof Blob)||blob.type!=='image/png'||blob.size<=0||blob.size>8*1048576)throw Error('Invalid witness archive request');
   const capability=await this.#cap();if(this.#closed)throw Error('Witness archive closed');
   const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))].map(n=>n.toString(16).padStart(2,'0')).join('');if(this.#closed)throw Error('Witness archive closed');
   const response=await this.fetcher(new URL(`qa/witness/${record.targetMs}`,this.base).href,{method:'POST',headers:{'Content-Type':'image/png','X-Witness-Archive':capability.nonce,'X-Witness-Elapsed-Ms':String(record.actualElapsedMs)},body:blob,cache:'no-store',credentials:'omit',redirect:'error',signal:this.#abort.signal});
   if(response.status!==201)throw Error('Witness archive HTTP '+response.status);const receipt=(await readJSON(response,4096)).document;
   if(receipt?.targetMs!==record.targetMs||receipt.filename!==record.targetMs+'_scene.png'||receipt.bytes!==blob.size||!SHA.test(receipt.sha256)||receipt.sha256!==hash)throw Error('Witness archive receipt differs');
   record.archiveStatus='archived';record.archiveFile=receipt.filename;record.archiveSHA256=hash;record.archiveBytes=blob.size;this.stats.archived++;return true;
  }catch(error){record.archiveStatus='failed';record.archiveError=String(error.message??error).slice(0,512);this.stats.failed++;return false;}
  finally{this.stats.pending--;this.#update();}
 }
 dispose(){this.#closed=true;this.#abort.abort();}
}
