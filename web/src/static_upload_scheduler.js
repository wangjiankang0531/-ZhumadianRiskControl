// Static upload chunks already bound synchronous work to 4 MiB. Yield a browser
// task between chunks so a throttled animation clock cannot stall preparation.
// This controls scheduling only; no GPU admission, byte limit or sampling changes.
export class StaticUploadScheduler {
 #pending=new Map();#next=0;#closed=false;#channel=null;
 #backend;#postTask;#requestFrame;#cancelFrame;#clock;
 #stats={started:0,completed:0,cancelled:0,failed:0,peakPending:0,totalWaitMs:0,maxWaitMs:0};
 constructor({mode='task',postTask=globalThis.scheduler?.postTask?.bind(globalThis.scheduler),createChannel=typeof MessageChannel==='function'?()=>new MessageChannel():null,requestFrame=globalThis.requestAnimationFrame?.bind(globalThis),cancelFrame=globalThis.cancelAnimationFrame?.bind(globalThis),clock=()=>performance.now()}={}){
  if(!['task','frame'].includes(mode)||typeof clock!=='function')throw Error('Invalid static upload scheduler');
  this.mode=mode;this.#clock=clock;this.#postTask=postTask;this.#requestFrame=requestFrame;this.#cancelFrame=cancelFrame;
  if(mode==='task'&&typeof postTask==='function')this.#backend='postTask';
  else if(mode==='task'&&typeof createChannel==='function'){
   this.#channel=createChannel();this.#channel.port1.onmessage=event=>this.#finish(event.data);this.#backend='messageChannel';
  }else if(typeof requestFrame==='function'&&typeof cancelFrame==='function')this.#backend='animationFrame';
  else throw Error('Static upload scheduler unavailable');
 }
 wait(){
  if(this.#closed)return Promise.reject(Error('Static upload scheduler closed'));
  if(this.#pending.size>=2)return Promise.reject(Error('Static upload scheduler concurrency exceeded'));
  const id=++this.#next;this.#stats.started++;
  return new Promise((resolve,reject)=>{
   const item={resolve,reject,start:this.#clock(),frame:null};this.#pending.set(id,item);this.#stats.peakPending=Math.max(this.#stats.peakPending,this.#pending.size);
   try{
    if(this.#backend==='postTask')Promise.resolve(this.#postTask(()=>this.#finish(id),{priority:'user-visible'})).catch(error=>this.#fail(id,error));
    else if(this.#backend==='messageChannel')this.#channel.port2.postMessage(id);
    else item.frame=this.#requestFrame(()=>this.#finish(id));
   }catch(error){this.#fail(id,error);}
  });
 }
 #finish(id){const item=this.#pending.get(id);if(!item)return;this.#pending.delete(id);const ms=Math.max(0,this.#clock()-item.start);this.#stats.completed++;this.#stats.totalWaitMs+=ms;this.#stats.maxWaitMs=Math.max(this.#stats.maxWaitMs,ms);item.resolve();}
 #fail(id,error){const item=this.#pending.get(id);if(!item)return;this.#pending.delete(id);this.#stats.failed++;item.reject(error);}
 snapshot(){return {mode:this.mode,backend:this.#backend,closed:this.#closed,pending:this.#pending.size,...this.#stats,scope:'per_await_task_waits_overlap_between_two_static_jobs; not_upload_CPU_or_GPU_time'};}
 dispose(){
  if(this.#closed)return;this.#closed=true;
  for(const item of this.#pending.values()){if(item.frame!==null)this.#cancelFrame(item.frame);this.#stats.cancelled++;item.reject(Error('Static upload scheduler closed'));}
  this.#pending.clear();if(this.#channel){this.#channel.port1.onmessage=null;this.#channel.port1.close();this.#channel.port2.close();this.#channel=null;}
 }
}
