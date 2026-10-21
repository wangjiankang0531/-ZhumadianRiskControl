const methods={texImage2D:'upload_gl_texture',texSubImage2D:'upload_gl_texture',texStorage2D:'upload_gl_texture',compressedTexImage2D:'upload_gl_texture',compressedTexSubImage2D:'upload_gl_texture',generateMipmap:'upload_gl_mipmap',bufferData:'upload_gl_buffer',bufferSubData:'upload_gl_buffer',compileShader:'upload_gl_program',linkProgram:'upload_gl_program',getProgramParameter:'upload_gl_program',getActiveUniform:'upload_gl_program',getActiveAttrib:'upload_gl_program',getUniformLocation:'upload_gl_program',getAttribLocation:'upload_gl_program'};
// Synchronous CPU time spent inside calls, including any driver wait. Not GPU
// elapsed time. Wrappers exist only during this one private staging render.
export function profileSourceUpload(gl,fn,{enabled=false,clock=()=>performance.now(),record=()=>{},onSample=()=>{}}={}){
 if(!enabled)return fn();const installed=[],sample={scope:'CPU_inside_upload_GL_calls_not_GPU_time',methods:{},instrumentationErrors:[]};
 const report=()=>{try{onSample(sample);}catch{}};
 const restore=()=>{for(const [name,descriptor] of installed.reverse())try{if(descriptor)Object.defineProperty(gl,name,descriptor);else delete gl[name];}catch{sample.instrumentationErrors.push('restore/'+name);}};
 try{for(const [name,stage] of Object.entries(methods)){const original=gl?.[name];if(typeof original!=='function')continue;const descriptor=Object.getOwnPropertyDescriptor(gl,name);if(descriptor&&!descriptor.configurable){sample.instrumentationErrors.push('unavailable/'+name);continue;}
   Object.defineProperty(gl,name,{configurable:true,writable:true,value:function(...args){let start;try{start=clock();}catch{}try{return original.apply(gl,args);}finally{try{const elapsed=clock()-start;if(Number.isFinite(elapsed)&&elapsed>=0){const prior=sample.methods[name]??{calls:0,totalMs:0,maxMs:0};prior.calls++;prior.totalMs+=elapsed;prior.maxMs=Math.max(prior.maxMs,elapsed);sample.methods[name]=prior;try{record(stage,elapsed);}catch{sample.instrumentationErrors.push('record/'+name);}}}catch{}}}});installed.push([name,descriptor]);}
 }catch{sample.instrumentationErrors.push('setup');restore();report();return fn();}
 try{return fn();}finally{restore();report();}
}
