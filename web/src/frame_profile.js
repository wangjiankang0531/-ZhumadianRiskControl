const stages=new Set(['profile_summary','frame_callback','frame_between_callbacks','profile_snapshot','profile_serialize','profile_dom','profile_console','lod_audit','diagnostic_console','frame_interval','frame_cpu','orbit','render_submit','annotations','maintain','coverage','source_upload','source_json','source_geometry','source_loaded_geometry','source_model_wait','source_load_wait','source_plan_wait','source_topology_wait','source_plan_cache_wait','source_plan_http_wait','source_plan_body_wait','source_plan_validation','source_plan_cost_wait','source_plan_memo_wait','source_gain_wait','source_stage_wait','source_bundle_wait','source_request_wait','source_scheduler_idle','source_retire','gpu_scene','budget_probe','allocation_slice','allocation_state','coverage_draw','coverage_readback','coverage_compute','upload_gl_texture','upload_gl_mipmap','upload_gl_buffer','upload_gl_program','startup_gl_texture','startup_gl_mipmap','startup_gl_buffer','startup_gl_program','startup_context_wait','startup_base_wait','startup_geometry_wait']);
export class FrameProfile{
 constructor({enabled=false,clock=()=>performance.now(),capacity=256}={}){if(!Number.isInteger(capacity)||capacity<8||capacity>1024)throw Error('Invalid frame profile bound');Object.assign(this,{enabled,clock,capacity});this.reset();}
 reset(label='initial'){this.label=String(label).slice(0,80);this.stages=new Map();this.previousFrame=null;}
 record(name,milliseconds){if(!this.enabled)return;if(!stages.has(name)||!Number.isFinite(milliseconds)||milliseconds<0)throw Error('Invalid frame profile sample');let s=this.stages.get(name);if(!s){s={count:0,total:0,max:0,over16:0,over50:0,values:[],cursor:0};this.stages.set(name,s);}s.count++;s.total+=milliseconds;s.max=Math.max(s.max,milliseconds);s.over16+=milliseconds>16.67;s.over50+=milliseconds>50;if(s.values.length<this.capacity)s.values.push(milliseconds);else{s.values[s.cursor]=milliseconds;s.cursor=(s.cursor+1)%this.capacity;}}
 measure(name,fn){if(!this.enabled)return fn();const start=this.clock();try{return fn();}finally{this.record(name,Math.max(0,this.clock()-start));}}
 measureAsync(name,fn){if(!this.enabled)return fn();const start=this.clock();let value;try{value=fn();}catch(error){this.record(name,Math.max(0,this.clock()-start));throw error;}return Promise.resolve(value).finally(()=>this.record(name,Math.max(0,this.clock()-start)));}
 frame(timestamp){if(!this.enabled)return;if(this.previousFrame!==null)this.record('frame_interval',Math.max(0,timestamp-this.previousFrame));this.previousFrame=timestamp;}
 snapshot(){const result={schema:'zhumadian.web.frame_profile.v1',phase:this.label,enabled:this.enabled,capacityPerStage:this.capacity,stages:{}};for(const [name,s] of this.stages){const v=[...s.values].sort((a,b)=>a-b);result.stages[name]={count:s.count,totalMs:s.total,meanMs:s.total/s.count,maxMs:s.max,p50RecentMs:v[Math.ceil(v.length*.5)-1],p95RecentMs:v[Math.ceil(v.length*.95)-1],recentSamples:v.length,over16:s.over16,over50:s.over50};}return result;}
}

export function webglDeviceInfo(gl){let renderer=null,vendor=null;try{const ext=gl.getExtension('WEBGL_debug_renderer_info');if(ext){renderer=gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);vendor=gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);}}catch{}return {renderer:typeof renderer==='string'?renderer.slice(0,512):null,vendor:typeof vendor==='string'?vendor.slice(0,256):null,source:'current_webgl_context',notOperatingSystemAdapterList:true};}

export class SceneGpuTimer{
 constructor(gl,profile){this.gl=gl;this.profile=profile;this.pending=[];this.dropped=0;this.disjoint=0;this.error=null;try{this.extension=profile.enabled?gl.getExtension('EXT_disjoint_timer_query_webgl2'):null;}catch(error){this.error=String(error.message);}this.supported=!!this.extension;}
 poll(){if(!this.supported)return;const g=this.gl;try{if(g.getParameter(this.extension.GPU_DISJOINT_EXT)){this.disjoint++;this.clear();return;}while(this.pending.length&&g.getQueryParameter(this.pending[0],g.QUERY_RESULT_AVAILABLE)){const q=this.pending.shift();try{const ns=g.getQueryParameter(q,g.QUERY_RESULT);if(Number.isFinite(ns)&&ns>=0)this.profile.record('gpu_scene',ns/1e6);}finally{g.deleteQuery(q);}}}catch(error){this.error=String(error.message);this.clear();this.supported=false;}}
 measure(fn){if(!this.supported)return fn();this.poll();if(!this.supported)return fn();if(this.pending.length>=8){this.dropped++;return fn();}const g=this.gl;let q;try{q=g.createQuery();if(q)g.beginQuery(this.extension.TIME_ELAPSED_EXT,q);}catch(error){if(q)g.deleteQuery(q);q=null;this.error=String(error.message);this.supported=false;}if(!q){this.dropped++;return fn();}try{return fn();}finally{try{g.endQuery(this.extension.TIME_ELAPSED_EXT);this.pending.push(q);}catch(error){g.deleteQuery(q);this.error=String(error.message);this.supported=false;}}}
 clear(){for(const q of this.pending)this.gl.deleteQuery(q);this.pending=[];}
 reset(){this.clear();this.dropped=0;this.disjoint=0;}
 snapshot(){return {supported:this.supported,pending:this.pending.length,dropped:this.dropped,disjoint:this.disjoint,error:this.error,scope:'asynchronous_GPU_time_for_main_scene_only_not_entire_frame'};}
 dispose(){this.clear();this.supported=false;}
}

// Synchronous animate body, including report publication after frame_cpu.
// Between callbacks includes browser scheduling and any other main-thread work;
// it is not CPU idle time and these nested statistics must not be added.
export class FrameCallbackTiming {
 constructor(profile){this.profile=profile;this.endedAt=null;}
 run(fn){if(!this.profile.enabled)return fn();const start=this.profile.clock();if(this.endedAt!==null)this.profile.record('frame_between_callbacks',Math.max(0,start-this.endedAt));try{return fn();}finally{const end=this.profile.clock();this.profile.record('frame_callback',Math.max(0,end-start));this.endedAt=end;}}
 reset(){this.endedAt=null;}
}
export class MainThreadTaskAudit {
 constructor({enabled=false,Observer=globalThis.PerformanceObserver,capacity=64}={}){
  if(typeof enabled!=='boolean'||!Number.isInteger(capacity)||capacity<1||capacity>128)throw Error('Invalid main-thread task audit');
  Object.assign(this,{enabled,capacity});this.supported=false;this.closed=false;this.error=null;this.observer=null;this.events=[];this.count=0;this.totalMs=0;this.maxMs=0;this.overwritten=0;this.invalid=0;
  if(!enabled||!Observer?.supportedEntryTypes?.includes('longtask'))return;
  try{this.observer=new Observer(list=>{for(const entry of list.getEntries())this.record(entry);});this.observer.observe({type:'longtask',buffered:true});this.supported=true;}catch(error){this.error=String(error.message).slice(0,512);this.observer?.disconnect();this.observer=null;}
 }
 record(entry){if(this.closed||!this.enabled)return;const {startTime,duration}=entry;if(!Number.isFinite(startTime)||startTime<0||!Number.isFinite(duration)||duration<0){this.invalid++;return;}this.count++;this.totalMs+=duration;this.maxMs=Math.max(this.maxMs,duration);this.events.push({startMs:startTime,durationMs:duration});if(this.events.length>this.capacity){this.events.shift();this.overwritten++;}}
 snapshot(){return {enabled:this.enabled,supported:this.supported,closed:this.closed,error:this.error,count:this.count,totalMs:this.totalMs,maxMs:this.maxMs,overwritten:this.overwritten,invalid:this.invalid,events:this.events.map(e=>({...e})),scope:'browser-reported main-thread long tasks; no source attribution, GPU usage or idle-time inference'};}
 dispose(){this.observer?.disconnect();this.observer=null;this.closed=true;}
}
