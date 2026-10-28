import {StaticUploadScheduler} from './static_upload_scheduler.js';

// Every notification yields a browser task. Only explicitly cached, rejected
// metadata may continue inside a bounded window; uploads keep ordinary pacing.
// Time is checked between indivisible operations, not a hard CPU deadline.
export class SourceWorkScheduler {
 #tasks;#requested=false;#scheduled=false;#closed=false;#timer=null;#last=-Infinity;
 #run;#error;#clock;#setTimer;#clearTimer;#interval;
 #metadata;#sliceMs;#maxSteps;#sliceStart=null;#steps=0;#continuation=null;
 #stats={requests:0,coalesced:0,runs:0,errors:0,pageYields:0,metadataRequests:0,metadataFastRuns:0,metadataFallbacks:0,maxMetadataStartMs:0};
 constructor({mode='frame',run,onError=()=>{},clock=()=>performance.now(),intervalMs=32,setTimer=globalThis.setTimeout.bind(globalThis),clearTimer=globalThis.clearTimeout.bind(globalThis),taskScheduler=null,metadataContinuation=false,metadataSliceMs=4,metadataMaxSteps=4}={}){
  if(!['task','frame'].includes(mode)||typeof run!=='function'||typeof onError!=='function'||!Number.isFinite(intervalMs)||intervalMs<16||intervalMs>1000||typeof metadataContinuation!=='boolean'||!Number.isFinite(metadataSliceMs)||metadataSliceMs<=0||metadataSliceMs>4||!Number.isInteger(metadataMaxSteps)||metadataMaxSteps<1||metadataMaxSteps>4)throw Error('Invalid source work scheduler');
  this.mode=mode;this.#run=run;this.#error=onError;this.#clock=clock;this.#interval=intervalMs;this.#setTimer=setTimer;this.#clearTimer=clearTimer;this.#tasks=taskScheduler??new StaticUploadScheduler({mode});this.#metadata=metadataContinuation;this.#sliceMs=metadataSliceMs;this.#maxSteps=metadataMaxSteps;
 }
 yield(){if(this.#closed)return Promise.reject(Error('Source work scheduler closed'));this.#stats.pageYields++;return this.#tasks.wait();}
 #eligible(current){if(!this.#metadata||this.mode!=='task'||this.#sliceStart===null||this.#steps>=this.#maxSteps||typeof current!=='function'||current()!==true)return false;const elapsed=this.#clock()-this.#sliceStart;return Number.isFinite(elapsed)&&elapsed>=0&&elapsed<this.#sliceMs;}
 requestMetadataContinuation(isCurrent){
  if(typeof isCurrent!=='function')throw Error('Missing metadata continuation guard');
  if(this.#closed||this.mode!=='task')return;
  this.#stats.metadataRequests++;this.#continuation=isCurrent;this.request();
 }
 request(){
  if(this.#closed||this.mode!=='task')return;
  this.#stats.requests++;if(this.#requested||this.#scheduled)this.#stats.coalesced++;
  this.#requested=true;this.#queue();
 }
 #pace(){const delay=Math.max(0,this.#interval-(this.#clock()-this.#last));return delay?new Promise(resolve=>{this.#timer={id:this.#setTimer(()=>{this.#timer=null;resolve();},delay),resolve};}):null;}
 #queue(){
  if(this.#closed||this.#scheduled||!this.#requested)return;
  this.#scheduled=true;
  void (async()=>{
   const current=this.#continuation;this.#continuation=null;let fast=this.#eligible(current);
   if(!fast){const pace=this.#pace();if(pace)await pace;}
   if(this.#closed)return;await this.#tasks.wait();if(this.#closed)return;
   // Input, crypto work and browser scheduling may outlive the initial window.
   if(fast&&!this.#eligible(current)){fast=false;const pace=this.#pace();if(pace)await pace;if(this.#closed)return;await this.#tasks.wait();if(this.#closed)return;}
   const now=this.#clock();
   if(fast){this.#steps++;this.#stats.metadataFastRuns++;this.#stats.maxMetadataStartMs=Math.max(this.#stats.maxMetadataStartMs,now-this.#sliceStart);}
   else{if(current)this.#stats.metadataFallbacks++;this.#sliceStart=now;this.#steps=0;}
   this.#continuation=null;this.#requested=false;this.#last=now;this.#stats.runs++;
   const again=this.#run();if(typeof again!=='boolean')throw Error('Source work continuation must be boolean');
   if(again)this.#requested=true;
  })().catch(error=>{if(!this.#closed){this.#stats.errors++;this.#requested=false;this.#continuation=null;try{this.#error(error);}catch{}}}).finally(()=>{this.#scheduled=false;this.#queue();});
 }
 snapshot(){return {mode:this.mode,closed:this.#closed,requested:this.#requested,scheduled:this.#scheduled,intervalMs:this.#interval,metadataContinuation:this.#metadata,metadataSliceMs:this.#sliceMs,metadataMaxSteps:this.#maxSteps,...this.#stats,tasks:this.#tasks.snapshot(),scope:'task_yields_with_bounded_cached_metadata_continuation; no_extra_transactions_or_budget_relaxation; indivisible_work_may_exceed_slice'};}
 dispose(){if(this.#closed)return;this.#closed=true;this.#requested=false;this.#continuation=null;if(this.#timer){this.#clearTimer(this.#timer.id);const resolve=this.#timer.resolve;this.#timer=null;resolve();}this.#tasks.dispose();}
}
