import {ensureSourceWanted,SourceLoadCancelled} from './lod_transaction.js';

// One speculative metadata task, including cancelled work that has not settled.
// The supplied reader must only read a plan; this class never grants a lease,
// reads page payloads, reserves GPU memory, or commits a cut.
export class SourcePlanLookahead{
 constructor({enabled=false}={}){this.enabled=enabled;this.job=null;this.stats={started:0,completed:0,taken:0,failed:0,cancelled:0,discarded:0};}
 snapshot(){const j=this.job;return {...this.stats,enabled:this.enabled,pending:!!j&&!j.settled,ready:!!j&&j.settled&&!j.cancelled,claimed:!!j?.claimed,cancelledPending:!!j?.cancelled&&!j.settled,key:j?.key??null};}
 refresh(){const j=this.job;if(j&&!j.cancelled&&!j.stillWanted())this.cancel();}
 cancel(){const j=this.job;if(!j)return Promise.resolve();if(!j.cancelled){j.cancelled=true;this.stats.cancelled++;}if(j.settled&&!j.claimed)this.job=null;return j.done;}
 start({key,read,stillWanted}){
  if(!this.enabled)return false;
  if(typeof key!=='string'||!key||key.length>1024||typeof read!=='function'||typeof stillWanted!=='function')throw Error('Invalid source plan lookahead');
  this.refresh();if(this.job?.settled&&!this.job.claimed&&this.job.key!==key){this.stats.discarded++;this.job=null;}
  if(this.job||!stillWanted())return false;
  const j={key,stillWanted,cancelled:false,settled:false,claimed:false};this.job=j;this.stats.started++;
  const wanted=()=>!j.cancelled&&stillWanted();
  // Install the error handler before any asynchronous read starts.
  j.done=Promise.resolve().then(()=>{ensureSourceWanted(wanted);return read(wanted);}).then(plan=>{
   ensureSourceWanted(wanted);this.stats.completed++;return {plan};
  }).catch(error=>{if(error instanceof SourceLoadCancelled){if(!j.cancelled){j.cancelled=true;this.stats.cancelled++;}}else this.stats.failed++;return {error};}).then(outcome=>{
   j.settled=true;if(j.cancelled&&!j.claimed&&this.job===j)this.job=null;return outcome;
  });return true;
 }
 async take(key,stillWanted){
  ensureSourceWanted(stillWanted);this.refresh();const j=this.job;
  if(!j||j.key!==key||j.cancelled||j.claimed)return null;
  j.claimed=true;
  try{const outcome=await j.done;ensureSourceWanted(stillWanted);if(j.cancelled)throw new SourceLoadCancelled();if(outcome.error)throw outcome.error;this.stats.taken++;return {plan:outcome.plan};}
  finally{if(this.job===j)this.job=null;}
 }
}
