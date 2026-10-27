import {validateHybridTexture,uploadHybridRaw,HYBRID_EXPLICIT_LOD_GLSL} from '../web/src/prepared_hybrid_texture.js';
import {sha256} from '../web/src/prepared_bc7.js';
const status=document.getElementById('status'),pre=document.getElementById('report'),canvas=document.getElementById('probe');
const report={schema:'xnby.hybrid.gpu_proof.v1',passed:false,levels:[],transitions:[],errors:[],scope:'single_hybrid_texture_not_scene_acceptance',trackedTextureBytes:0};
let gl,pair,program,vao,framebuffer,output,referenceTexture;const shaders=new Set();
function check(where){const error=gl.getError();if(error!==gl.NO_ERROR)throw Error(where+': GL '+error);}
function shader(type,source){const object=gl.createShader(type);shaders.add(object);gl.shaderSource(object,source);gl.compileShader(object);if(!gl.getShaderParameter(object,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(object));return object;}
function metrics(a,b){let squared=0,maximum=0;const hist=new Uint32Array(256);for(let i=0;i<a.length;i++)if(i%4!==3){const e=Math.abs(a[i]-b[i]);squared+=e*e;maximum=Math.max(maximum,e);hist[e]++;}const count=a.length/4*3,mse=squared/count;let p99=0,sum=0;for(let i=0;i<256;i++){sum+=hist[i];if(sum>=Math.ceil(count*.99)){p99=i;break;}}return {rgbPSNR:mse===0?999:10*Math.log10(255*255/mse),rgbChannelP99:p99,rgbMaxError:maximum};}
try{
 const fetchJson=async name=>{const r=await fetch(name,{cache:'no-store'});if(!r.ok)throw Error('Fixture HTTP '+r.status);return r.json();},fetchBytes=async name=>{const r=await fetch(name,{cache:'no-store'});if(!r.ok)throw Error('Fixture HTTP '+r.status);return r.arrayBuffer();};
 const [descriptor,prefix,tail,reference,refdata]=await Promise.all([fetchJson('/descriptor.json'),fetchBytes('/prefix.bc7'),fetchBytes('/tail.rgba'),fetchJson('/reference.json'),fetchBytes('/reference.rgba')]);
 const prepared=await validateHybridTexture(descriptor,prefix,tail,{sha256:descriptor.sourceSHA256,width:descriptor.sourceSize[0],height:descriptor.sourceSize[1]});
 if(refdata.byteLength!==reference.payloadBytes||await sha256(refdata)!==reference.payloadSHA256)throw Error('Independent original reference differs');
 for(const row of reference.mips)if(await sha256(new Uint8Array(refdata,row.offset,row.bytes))!==row.sha256)throw Error('Reference mip SHA differs');
 gl=canvas.getContext('webgl2',{antialias:false,alpha:false,depth:false,stencil:false});if(!gl)throw Error('WebGL2 unavailable');const debug=gl.getExtension('WEBGL_debug_renderer_info');report.renderer=debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 const vs=shader(gl.VERTEX_SHADER,'#version 300 es\nprecision highp float;out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.0-1.0,0.0,1.0);}');
 const fs=shader(gl.FRAGMENT_SHADER,`#version 300 es
 precision highp float;uniform sampler2D prefixImage;uniform sampler2D tailImage;uniform sampler2D originalImage;uniform float lod;uniform float tailStart;uniform float referenceStart;uniform bool original;uniform bool displayTransfer;in vec2 uv;out vec4 color;
 ${HYBRID_EXPLICIT_LOD_GLSL}
 vec3 toDisplay(vec3 value){return mix(1.055*pow(max(value,vec3(0.0)),vec3(1.0/2.4))-0.055,value*12.92,lessThanEqual(value,vec3(0.0031308)));}
 void main(){vec4 value=original?textureLod(originalImage,uv,max(0.0,lod-referenceStart)):hybridAtLod(prefixImage,tailImage,uv,lod,tailStart);if(displayTransfer)value.rgb=toDisplay(value.rgb);color=value;}`);
 program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));for(const s of shaders)gl.deleteShader(s);shaders.clear();
 vao=gl.createVertexArray();gl.bindVertexArray(vao);gl.useProgram(program);gl.disable(gl.DITHER);gl.disable(gl.BLEND);gl.disable(gl.DEPTH_TEST);framebuffer=gl.createFramebuffer();
 for(const [name,unit] of [['prefixImage',0],['tailImage',1],['originalImage',2]])gl.uniform1i(gl.getUniformLocation(program,name),unit);
 gl.uniform1f(gl.getUniformLocation(program,'tailStart'),prepared.tailStartLevel);gl.uniform1f(gl.getUniformLocation(program,'referenceStart'),reference.startLevel);
 const bindPair=()=>{gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,pair.prefix);gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,pair.tail);gl.activeTexture(gl.TEXTURE2);gl.bindTexture(gl.TEXTURE_2D,referenceTexture??pair.tail);};
 const draw=(width,height,lod,original=false,display=false)=>{
  output=gl.createTexture();gl.activeTexture(gl.TEXTURE3);gl.bindTexture(gl.TEXTURE_2D,output);gl.texStorage2D(gl.TEXTURE_2D,1,gl.RGBA8,width,height);gl.bindFramebuffer(gl.FRAMEBUFFER,framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,output,0);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Incomplete target');
  bindPair();gl.uniform1f(gl.getUniformLocation(program,'lod'),lod);gl.uniform1i(gl.getUniformLocation(program,'original'),original?1:0);gl.uniform1i(gl.getUniformLocation(program,'displayTransfer'),display?1:0);gl.viewport(0,0,width,height);gl.drawArrays(gl.TRIANGLES,0,3);check('hybrid draw');const pixels=new Uint8Array(width*height*4);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);check('hybrid read');gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,null,0);gl.deleteTexture(output);output=null;return pixels;
 };
 pair=uploadHybridRaw(gl,prepared);report.trackedTextureBytes=pair.bytes;report.sourceSize=[prepared.width,prepared.height];report.tailStartLevel=prepared.tailStartLevel;
 for(const row of prepared.mips){const pixels=draw(row.width,row.height,row.level),digest=await sha256(pixels);report.levels.push({level:row.level,width:row.width,height:row.height,format:row.format,expectedSHA256:row.decodedRgbaSHA256,gpuSHA256:digest,exact:digest===row.decodedRgbaSHA256});}
 pair.dispose();pair=null;
 pair=uploadHybridRaw(gl,prepared,{srgb:true,linear:true});referenceTexture=gl.createTexture();gl.activeTexture(gl.TEXTURE2);gl.bindTexture(gl.TEXTURE_2D,referenceTexture);const refbase=reference.mips[0];
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAX_LEVEL,reference.mips.length-1);gl.texStorage2D(gl.TEXTURE_2D,reference.mips.length,gl.SRGB8_ALPHA8,refbase.width,refbase.height);
 for(const [level,row] of reference.mips.entries())gl.texSubImage2D(gl.TEXTURE_2D,level,0,0,row.width,row.height,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(refdata,row.offset,row.bytes));check('original reference upload');
 const boundary={};
 const start=prepared.tailStartLevel,last=prepared.mips.length-1;
 const levels=[...new Set([start-1,start-.999,start-.75,start-.5,start-.25,start-.001,start,start+.001,start+.5,start+1,Math.max(start,last-1.5),last-1,last])].filter(level=>level>=0).sort((a,b)=>a-b);
 for(const level of levels){
  const actual=draw(refbase.width,refbase.height,level,false,true),expected=draw(refbase.width,refbase.height,level,true,true),quality=metrics(actual,expected),tailExact=level>=prepared.tailStartLevel?quality.rgbMaxError===0:null;
  report.transitions.push({level,...quality,tailExact,passed:quality.rgbPSNR>=40&&quality.rgbChannelP99<=16&&quality.rgbMaxError<=96&&tailExact!==false});if(level===start-.001||level===start+.001)boundary[String(level)]={actual,expected};
 }
 const actualStep=metrics(boundary[String(start-.001)].actual,boundary[String(start+.001)].actual),referenceStep=metrics(boundary[String(start-.001)].expected,boundary[String(start+.001)].expected);report.boundary={actualMaxStep:actualStep.rgbMaxError,referenceMaxStep:referenceStep.rgbMaxError,allowedMaxStep:referenceStep.rgbMaxError+1,passed:actualStep.rgbMaxError<=referenceStep.rgbMaxError+1};
 report.passed=report.levels.length===prepared.mips.length&&report.levels.every(row=>row.exact)&&report.transitions.every(row=>row.passed)&&report.boundary.passed;
 if(!report.passed)report.errors.push('Hybrid level, display quality or boundary comparison failed');
}catch(error){report.errors.push(String(error.message??error));}
finally{
 if(gl){pair?.dispose();if(output)gl.deleteTexture(output);if(referenceTexture)gl.deleteTexture(referenceTexture);if(framebuffer)gl.deleteFramebuffer(framebuffer);if(program)gl.deleteProgram(program);if(vao)gl.deleteVertexArray(vao);for(const s of shaders)gl.deleteShader(s);gl.bindFramebuffer(gl.FRAMEBUFFER,null);report.cleanupGlError=gl.getError();report.ownedObjectsDeleted=true;canvas.width=canvas.height=1;}
 status.textContent=report.passed?'核验通过：完整链与层级交界处符合门槛':'核验未通过';pre.textContent=JSON.stringify(report,null,2);
}
