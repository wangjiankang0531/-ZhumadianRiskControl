import {StaticUploadScheduler} from './static_upload_scheduler.js';

// Source pages keep the same ordered upload and transaction. Only the yield and
// the next work notification leave the animation clock. Work is demand-driven,
// coalesced, and rate-limited; an indivisible visibility/probe call can exceed a
// slice, so this is not a hard main-thread time limit.
export class SourceWorkScheduler {
 #tasks;#requested=false;#scheduled=false;#closed=false;#timer=null;#last=-Infinity;
 #run;#error;#clock;#setTimer;#clearTimer;#interval;
 #stats={requests:0,coalesced:0,runs:0,errors:0,pageYields:0};
 constructor({mode='frame',run,onError=()=>{},clock=()=>performance.now(),intervalMs=32,setTimer=globalThis.setTimeout.bind(globalThis),clearTimer=globalThis.clearTimeout.bind(globalThis),taskScheduler=null}={}){
  if(!['task','frame'].includes(mode)||typeof run!=='function'||typeof onError!=='function'||!Number.isFinite(intervalMs)||intervalMs<16||intervalMs>1000)throw Error('Invalid source work scheduler');
  this.mode=mode;this.#run=run;this.#error=onError;this.#clock=clock;this.#interval=intervalMs;this.#setTimer=setTimer;this.#clearTimer=clearTimer;this.#tasks=taskScheduler??new StaticUploadScheduler({mode});
 }
 yield(){if(this.#closed)return Promise.reject(Error('Source work scheduler closed'));this.#stats.pageYields++;return this.#tasks.wait();}
 request(){
  if(this.#closed||this.mode!=='task')return;
  this.#stats.requests++;if(this.#requested||this.#scheduled)this.#stats.coalesced++;
  this.#requested=true;this.#queue();
 }
 #queue(){
  if(this.#closed||this.#scheduled||!this.#requested)return;
  this.#scheduled=true;
  void (async()=>{
   const delay=Math.max(0,this.#interval-(this.#clock()-this.#last));
   if(delay)await new Promise(resolve=>{this.#timer={id:this.#setTimer(()=>{this.#timer=null;resolve();},delay),resolve};});
   if(this.#closed)return;await this.#tasks.wait();if(this.#closed)return;
   this.#requested=false;this.#last=this.#clock();this.#stats.runs++;
   const again=this.#run();if(typeof again!=='boolean')throw Error('Source work continuation must be boolean');
   if(again)this.#requested=true;
  })().catch(error=>{if(!this.#closed){this.#stats.errors++;this.#requested=false;try{this.#error(error);}catch{}}}).finally(()=>{this.#scheduled=false;this.#queue();});
 }
 snapshot(){return {mode:this.mode,closed:this.#closed,requested:this.#requested,scheduled:this.#scheduled,intervalMs:this.#interval,...this.#stats,tasks:this.#tasks.snapshot(),scope:'source_page_yields_and_coalesced_work_notifications; no_extra_source_transactions_or_budget_relaxation; indivisible_work_may_exceed_slice'};}
 dispose(){if(this.#closed)return;this.#closed=true;this.#requested=false;if(this.#timer){this.#clearTimer(this.#timer.id);const resolve=this.#timer.resolve;this.#timer=null;resolve();}this.#tasks.dispose();}
}
