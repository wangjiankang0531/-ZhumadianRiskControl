import {profileSourceUpload} from './source_upload_profile.js';
// Short, opt-in CPU GL diagnostics for the original static scene. Never GPU time.
export class StartupProfile {
 constructor({enabled=false,clock=()=>performance.now(),record=()=>{},durationMs=30000,capacity=32}={}){
  if(!Number.isFinite(durationMs)||durationMs<=0||durationMs>60000||!Number.isInteger(capacity)||capacity<1||capacity>64)throw Error('Invalid startup diagnostic bounds');
  Object.assign(this,{enabled,clock,record,durationMs,capacity});this.start=enabled?clock():null;this.frames=0;this.events=[];this.marks=[];this.dropped=0;this.errors=0;this.max=null;
 }
 mark(name){if(this.enabled&&this.marks.length<16)this.marks.push({name:String(name).slice(0,80),milliseconds:Math.max(0,this.clock()-this.start)});}
 render(gl,fn,describe=()=>null){if(!this.enabled||this.clock()-this.start>this.durationMs)return fn();this.frames++;
  return profileSourceUpload(gl,fn,{enabled:true,clock:this.clock,record:(name,ms)=>this.record(name.replace('upload_gl_','startup_gl_'),ms),onSample:sample=>{
   this.errors+=sample.instrumentationErrors.length;if(!Object.keys(sample.methods).length)return;
   const event={milliseconds:Math.max(0,this.clock()-this.start),totalMs:Object.values(sample.methods).reduce((n,m)=>n+m.totalMs,0),methods:sample.methods,state:describe()};
   if(!this.max||event.totalMs>this.max.totalMs)this.max=event;
   if(this.events.length<this.capacity)this.events.push(event);else this.dropped++;
  }});
 }
 snapshot(){return {enabled:this.enabled,durationMs:this.durationMs,frames:this.frames,marks:this.marks.map(x=>({...x})),events:this.events.map(x=>structuredClone(x)),dropped:this.dropped,instrumentationErrors:this.errors,max:this.max&&structuredClone(this.max),scope:'startup_static_scene_synchronous_CPU_GL_calls_not_GPU_elapsed'};}
}
