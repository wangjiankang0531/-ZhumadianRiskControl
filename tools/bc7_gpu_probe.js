const status=document.getElementById('status'),pre=document.getElementById('report'),canvas=document.getElementById('probe');
const report={schema:'xnby.bc7.gpu_probe.v1',passed:false,levels:[],errors:[],scope:'single_texture_hardware_decode_not_scene_quality'};
const sha=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
let gl,compressed,program,vao,framebuffer,output;
function check(where){const error=gl.getError();if(error!==gl.NO_ERROR)throw Error(where+': WebGL '+error);}
function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(s);gl.deleteShader(s);throw Error(message);}return s;}
try{
 const metadata=await fetch('/descriptor.json',{cache:'no-store'});if(!metadata.ok)throw Error('Descriptor unavailable');const descriptor=await metadata.json();
 const response=await fetch('/texture.bc7',{cache:'no-store'});if(!response.ok)throw Error('Payload unavailable');const payload=await response.arrayBuffer();
 if(payload.byteLength!==descriptor.payloadBytes||await sha(payload)!==descriptor.payloadSHA256)throw Error('GPU payload SHA mismatch');
 gl=canvas.getContext('webgl2',{antialias:false,alpha:false,depth:false,stencil:false,preserveDrawingBuffer:false});if(!gl)throw Error('WebGL2 unavailable');
 const extension=gl.getExtension('EXT_texture_compression_bptc');if(!extension)throw Error('BC7 unavailable');
 const debug=gl.getExtension('WEBGL_debug_renderer_info');report.renderer=debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 report.sourceSHA256=descriptor.sourceSHA256;report.sourceSize=descriptor.sourceSize;report.payloadBytes=payload.byteLength;
 const vs=shader(gl.VERTEX_SHADER,'#version 300 es\nprecision highp float;out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.0-1.0,0.0,1.0);}');
 const fs=shader(gl.FRAGMENT_SHADER,'#version 300 es\nprecision highp float;uniform sampler2D image;uniform float level;in vec2 uv;out vec4 color;void main(){color=textureLod(image,uv,level);}');
 program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 vao=gl.createVertexArray();gl.bindVertexArray(vao);gl.useProgram(program);gl.disable(gl.DITHER);gl.disable(gl.BLEND);gl.disable(gl.DEPTH_TEST);
 compressed=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,compressed);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST_MIPMAP_NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 gl.texStorage2D(gl.TEXTURE_2D,descriptor.mips.length,extension.COMPRESSED_RGBA_BPTC_UNORM_EXT,...descriptor.sourceSize);check('BC7 storage');
 for(const row of descriptor.mips){const raw=new Uint8Array(payload,row.offset,row.bytes);if(await sha(raw)!==row.sha256)throw Error('Mip SHA mismatch');gl.compressedTexSubImage2D(gl.TEXTURE_2D,row.level,0,0,row.width,row.height,extension.COMPRESSED_RGBA_BPTC_UNORM_EXT,raw);check('BC7 upload '+row.level);}
 gl.uniform1i(gl.getUniformLocation(program,'image'),0);framebuffer=gl.createFramebuffer();
 for(const row of descriptor.mips){
  output=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,output);gl.texStorage2D(gl.TEXTURE_2D,1,gl.RGBA8,row.width,row.height);gl.bindFramebuffer(gl.FRAMEBUFFER,framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,output,0);
  if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Incomplete decode target');
  gl.bindTexture(gl.TEXTURE_2D,compressed);gl.uniform1f(gl.getUniformLocation(program,'level'),row.level);gl.viewport(0,0,row.width,row.height);gl.drawArrays(gl.TRIANGLES,0,3);check('BC7 draw '+row.level);
  const pixels=new Uint8Array(row.width*row.height*4);gl.readPixels(0,0,row.width,row.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);check('BC7 readback '+row.level);
  const digest=await sha(pixels);report.levels.push({level:row.level,width:row.width,height:row.height,expectedSHA256:row.pillowDecodedSHA256,gpuSHA256:digest,exact:digest===row.pillowDecodedSHA256});
  gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,null,0);gl.deleteTexture(output);output=null;
 }
 report.passed=report.levels.length===descriptor.mips.length&&report.levels.every(row=>row.exact);
 if(!report.passed)report.errors.push('GPU output differs from independent Pillow reference');
}catch(error){report.errors.push(String(error.message??error));}
finally{
 if(gl){if(output)gl.deleteTexture(output);if(framebuffer)gl.deleteFramebuffer(framebuffer);if(compressed)gl.deleteTexture(compressed);if(program)gl.deleteProgram(program);if(vao)gl.deleteVertexArray(vao);gl.bindFramebuffer(gl.FRAMEBUFFER,null);report.cleanupGlError=gl.getError();report.ownedObjectsDeleted=true;canvas.width=canvas.height=1;}
 status.textContent=report.passed?'核验通过：所有 mip 与独立参考逐字节一致':'核验未通过';pre.textContent=JSON.stringify(report,null,2);
}
