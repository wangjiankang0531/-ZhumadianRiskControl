import {BufferAttribute} from 'three';
// Retain the original CPU arrays/getters while using the renderer's public
// external-buffer attribute contract. No vertex/index/UV reordering or packing.
class StaticGpuAttribute extends BufferAttribute {
 constructor(original,buffer,type){super(original.array,original.itemSize,original.normalized);this.name=original.name;this.usage=original.usage;this.gpuType=original.gpuType;this.isGLBufferAttribute=true;this.buffer=buffer;this.type=type;this.elementSize=original.array.BYTES_PER_ELEMENT;}
}
export async function uploadStaticGeometry({geometry,gl,maxChunkBytes=4*1048576,yieldFrame=()=>new Promise(resolve=>requestAnimationFrame(resolve)),stillWanted=()=>true,verify=false,clock=()=>performance.now(),onProgress=()=>{}}){
 if(!geometry?.isBufferGeometry||!gl?.COPY_WRITE_BUFFER||!Number.isInteger(maxChunkBytes)||maxChunkBytes<4||maxChunkBytes>4*1048576||maxChunkBytes%4)throw Error('Invalid static upload contract');
 const originals=[...Object.entries(geometry.attributes),['$index',geometry.index]],buffers=[],stats={bytes:0,chunks:0,verifiedBytes:0,maxChunkMs:0,maxAllocateMs:0,attributes:0};let installed=false,disposed=false;
 const current=name=>name==='$index'?geometry.index:geometry.getAttribute(name),set=(name,value)=>name==='$index'?geometry.setIndex(value):geometry.setAttribute(name,value);
 const wanted=()=>{if(!stillWanted())throw Error('Static geometry upload cancelled');};
 const bound=fn=>{const prior=gl.getParameter(gl.COPY_WRITE_BUFFER_BINDING);try{return fn();}finally{gl.bindBuffer(gl.COPY_WRITE_BUFFER,prior);}};
 const cleanup=()=>{if(disposed)return;disposed=true;if(installed)for(const entry of buffers)if(current(entry.name)===entry.attribute)set(entry.name,entry.original);for(const entry of buffers)gl.deleteBuffer(entry.buffer);geometry.removeEventListener('dispose',cleanup);};
 try{
  if(originals.some(([,a])=>!a||a.isInterleavedBufferAttribute||a.isGLBufferAttribute||!(a.array instanceof Float32Array||a.array instanceof Uint32Array)||a.array.byteLength===0)||Object.keys(geometry.morphAttributes).length)throw Error('Static upload requires original Float32/Uint32 non-morph arrays');
  for(const [name,original] of originals){wanted();const version=original.version,type=original.array instanceof Float32Array?gl.FLOAT:gl.UNSIGNED_INT,buffer=gl.createBuffer();if(!buffer)throw Error('Static buffer allocation failed');const entry={name,original,version,buffer,attribute:new StaticGpuAttribute(original,buffer,type)};buffers.push(entry);
   // COPY_WRITE first would classify an index buffer as other-data in WebGL2.
   // Classify through a temporary VAO, restoring the renderer's current VAO.
   if(name==='$index'){const prior=gl.getParameter(gl.VERTEX_ARRAY_BINDING),vao=gl.createVertexArray();if(!vao)throw Error('Index VAO allocation failed');try{gl.bindVertexArray(vao);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,buffer);if(gl.getError()!==gl.NO_ERROR)throw Error('Index buffer classification failed');}finally{gl.bindVertexArray(prior);gl.deleteVertexArray(vao);}}
   bound(()=>{gl.bindBuffer(gl.COPY_WRITE_BUFFER,buffer);const start=clock();gl.bufferData(gl.COPY_WRITE_BUFFER,original.array.byteLength,gl.STATIC_DRAW);stats.maxAllocateMs=Math.max(stats.maxAllocateMs,clock()-start);if(gl.getError()!==gl.NO_ERROR)throw Error('Static buffer allocation GL error');});await yieldFrame();
   for(let offset=0;offset<original.array.byteLength;offset+=maxChunkBytes){wanted();const length=Math.min(maxChunkBytes,original.array.byteLength-offset),bytes=new Uint8Array(original.array.buffer,original.array.byteOffset+offset,length);
    bound(()=>{gl.bindBuffer(gl.COPY_WRITE_BUFFER,buffer);const start=clock();gl.bufferSubData(gl.COPY_WRITE_BUFFER,offset,bytes);stats.maxChunkMs=Math.max(stats.maxChunkMs,clock()-start);if(gl.getError()!==gl.NO_ERROR)throw Error('Static buffer upload GL error');if(verify){const read=new Uint8Array(length);gl.getBufferSubData(gl.COPY_WRITE_BUFFER,offset,read);if(gl.getError()!==gl.NO_ERROR)throw Error('Static readback GL error');for(let i=0;i<length;i++)if(read[i]!==bytes[i])throw Error('Static GPU byte differs at '+name+'/'+(offset+i));stats.verifiedBytes+=length;}});
    stats.bytes+=length;stats.chunks++;onProgress({...stats});await yieldFrame();
   }
  }
  wanted();if(buffers.some(e=>current(e.name)!==e.original||e.original.version!==e.version))throw Error('Static geometry changed during upload');
  for(const entry of buffers)set(entry.name,entry.attribute);installed=true;stats.attributes=buffers.length;
  // Register before the renderer sees the geometry. Restore CPU attributes before
  // its disposal listener runs, so this owner deletes each external buffer once.
  geometry.addEventListener('dispose',cleanup);onProgress({...stats});return {stats:{...stats},dispose:cleanup};
 }catch(error){cleanup();throw error;}
}
