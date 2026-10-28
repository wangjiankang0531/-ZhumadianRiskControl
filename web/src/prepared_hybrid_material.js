import {isValidatedHybridTexture} from './prepared_hybrid_texture.js';
import {isValidatedHybridOverlap} from './prepared_hybrid_overlap.js';
import {sha256,PreparedTextureCancelled,PreparedTextureContextError} from './prepared_bc7.js';
const identities=new WeakMap(),materials=new WeakMap();
const require=(ok,message)=>{if(!ok)throw Error('Hybrid material: '+message);};
export const HYBRID_LOD_ORACLE_SIZE=2048;
export const HYBRID_LOD_ORACLE_BYTES=5592405;
// A shared full-chain R8 image carries a constant level number in every mip.
// Sampling it with source-sized gradients asks this GPU's own anisotropic
// sampler for its filtered level, rather than guessing a driver LOD formula.
export const HYBRID_GRADIENT_GLSL=`
uniform sampler2D xnbyHybridTail;
uniform sampler2D xnbyHybridLevels;
uniform vec2 xnbyHybridSourceSize;
uniform vec2 xnbyHybridTailGradient;
uniform float xnbyHybridBlendStart;
vec4 xnbyHybridSample(vec2 uv){
 vec2 dx=dFdx(uv),dy=dFdy(uv);
 vec2 levelScale=xnbyHybridSourceSize/2048.0;
 float level=textureGrad(xnbyHybridLevels,vec2(0.5),dx*levelScale,dy*levelScale).r*(255.0/16.0);
 vec4 prefix=textureGrad(map,uv,dx,dy);
 vec4 tail=textureGrad(xnbyHybridTail,uv,dx*xnbyHybridTailGradient,dy*xnbyHybridTailGradient);
 return mix(prefix,tail,clamp(level-xnbyHybridBlendStart,0.0,1.0));
}
`;
export function hybridSceneTextureIdentity(texture){return identities.get(texture)??null;}
export function applyHybridSceneMaterial(material){
 const identity=identities.get(material?.map),previous=materials.get(material);if(previous){require(previous===identity,'material map changed after binding');return true;}if(!identity)return false;
 require(typeof material.onBeforeCompile==='function'&&typeof material.customProgramCacheKey==='function','unsupported material');
 const oldCompile=material.onBeforeCompile,oldKey=material.customProgramCacheKey.bind(material);
 const key=oldKey();
 material.onBeforeCompile=function(shader,renderer){
  oldCompile.call(this,shader,renderer);
  require(identities.get(this.map)===identity,'material map changed before compile');
  require(shader.fragmentShader.includes('#include <map_fragment>')&&shader.fragmentShader.includes('void main() {'),'unsupported Three shader layout');
  Object.assign(shader.uniforms,{xnbyHybridTail:{value:identity.tail},xnbyHybridLevels:{value:identity.oracle},xnbyHybridSourceSize:{value:identity.sourceSize},xnbyHybridTailGradient:{value:identity.tailGradient},xnbyHybridBlendStart:{value:identity.blendStartLevel}});
  shader.fragmentShader=shader.fragmentShader.replace('void main() {',HYBRID_GRADIENT_GLSL+'\nvoid main() {').replace('#include <map_fragment>','diffuseColor *= xnbyHybridSample(vMapUv);');
 };
 material.customProgramCacheKey=()=>key+'|xnby.hybrid.hardware-gradient.v1';
 material.needsUpdate=true;materials.set(material,identity);return true;
}
export function createHybridSceneContext({THREE,renderer,reserve,anisotropy=Math.min(16,renderer.capabilities.getMaxAnisotropy())}){
 require(typeof reserve==='function','shared budget required');
 require(Number.isFinite(anisotropy)&&anisotropy>=1&&anisotropy<=renderer.capabilities.getMaxAnisotropy(),'invalid anisotropy');
 require(renderer.capabilities.maxTextureSize>=HYBRID_LOD_ORACLE_SIZE&&renderer.extensions.has('EXT_texture_compression_bptc'),'device unavailable');
 const gl=renderer.getContext(),pairs=new Set(),pins=new Set();let oracleRecord=null,closed=false;
 const contextOkay=()=>{if(gl.isContextLost?.()||gl.getError()!==gl.NO_ERROR)throw new PreparedTextureContextError('Hybrid material GL context unavailable');};
 const configure=(texture,colorSpace)=>{texture.colorSpace=colorSpace;texture.flipY=false;texture.generateMipmaps=false;texture.minFilter=THREE.LinearMipmapLinearFilter;texture.magFilter=THREE.LinearFilter;texture.wrapS=texture.wrapT=THREE.ClampToEdgeWrapping;texture.anisotropy=anisotropy;texture.unpackAlignment=1;texture.needsUpdate=true;};
 function cleanupOracle(record){if(record.references!==0||!record.done)return;record.texture?.dispose();record.texture=null;record.lease?.release();record.lease=null;if(oracleRecord===record)oracleRecord=null;}
 async function acquireOracle(){
  require(!closed,'context closed');
  let record=oracleRecord;
  if(!record){
   record={references:0,texture:null,lease:null,done:false};oracleRecord=record;
   record.ready=(async()=>{try{
    record.lease=await reserve({format:'hybrid_lod_oracle',bytes:HYBRID_LOD_ORACLE_BYTES});require(typeof record.lease?.release==='function','invalid shared reservation');require(!closed,'context closed');contextOkay();
    const mips=[];for(let width=HYBRID_LOD_ORACLE_SIZE,level=0;;width>>=1,level++){mips.push({width,height:width,data:new Uint8Array(width*width).fill(level*16)});if(width===1)break;}
    const first=mips[0];record.texture=new THREE.DataTexture(first.data,first.width,first.height,THREE.RedFormat,THREE.UnsignedByteType);record.texture.mipmaps=mips;configure(record.texture,THREE.NoColorSpace);renderer.initTexture(record.texture);contextOkay();
   }catch(error){record.error=error;throw error;}finally{record.done=true;cleanupOracle(record);}})();
  }
  record.references++;
  let live=true;const release=()=>{if(live){live=false;record.references--;cleanupOracle(record);}};
  try{await record.ready;require(!closed,'context closed');return {texture:record.texture,release};}
  catch(error){release();throw error;}
 }
 return {
  async pin(){const handle=await acquireOracle();pins.add(handle);let live=true;return {release(){if(live){live=false;pins.delete(handle);handle.release();}}};},
  async load(prepared,{overlap,stillWanted=()=>true}={}){
   require(isValidatedHybridTexture(prepared),'unverified texture');require(!closed,'context closed');
   require(isValidatedHybridOverlap(overlap)&&overlap.sourceSHA256===prepared.sourceSHA256&&overlap.basePayloadSHA256===prepared.payloadSHA256,'verified original overlap required');
   const wanted=()=>{if(closed||!stillWanted())throw new PreparedTextureCancelled('Hybrid material no longer wanted');};
   // Typed arrays stay mutable even when their descriptors are frozen. Recheck
   // every admitted mip before allocating a scene resource.
   wanted();for(const row of [...prepared.mips,...overlap.mips]){require(await sha256(row.data)===row.sha256,'mip changed after validation');wanted();}
   let oracle,lease,prefix,tail,disposed=false;
   const release=(prefixAlreadyDisposing=false)=>{if(disposed)return;disposed=true;pairs.delete(result);identities.delete(prefix);if(!prefixAlreadyDisposing)prefix?.dispose();tail?.dispose();lease?.release();oracle?.release();};
   const dispose=()=>release(false),result={dispose};
   try{
    const bytes=prepared.bytes+overlap.bytes;oracle=await acquireOracle();wanted();lease=await reserve({format:'hybrid_overlap',bytes});require(typeof lease?.release==='function','invalid pair reservation');wanted();contextOkay();
    const prefixRows=prepared.mips.filter(r=>r.format==='bc7').map(r=>({data:r.data,width:r.width,height:r.height}));
    prefix=new THREE.CompressedTexture(prefixRows,prepared.width,prepared.height,THREE.RGBA_BPTC_Format,THREE.UnsignedByteType);configure(prefix,THREE.SRGBColorSpace);renderer.initTexture(prefix);contextOkay();wanted();
    const tailRows=[...overlap.mips,...prepared.mips.filter(r=>r.format==='rgba8')].map(r=>({data:r.data,width:r.width,height:r.height})),base=tailRows[0];
    tail=new THREE.DataTexture(base.data,base.width,base.height,THREE.RGBAFormat,THREE.UnsignedByteType);tail.mipmaps=tailRows;configure(tail,THREE.SRGBColorSpace);renderer.initTexture(tail);contextOkay();wanted();
    const identity=Object.freeze({format:'bc7_rgba_overlap',bytes,payloadSHA256:prepared.payloadSHA256,overlapSHA256:overlap.payloadSHA256,sourceSHA256:prepared.sourceSHA256,tailStartLevel:prepared.tailStartLevel,blendStartLevel:overlap.startLevel,tail,oracle:oracle.texture,sourceSize:new THREE.Vector2(prepared.width,prepared.height),tailGradient:new THREE.Vector2(prepared.width/(base.width*2**overlap.startLevel),prepared.height/(base.height*2**overlap.startLevel)),anisotropy});
    identities.set(prefix,identity);prefix.addEventListener('dispose',()=>release(true));Object.assign(result,{texture:prefix,tail,identity,bytes,format:'bc7_rgba_overlap'});pairs.add(result);return result;
   }catch(error){dispose();throw error;}
  },
  snapshot(){return {closed,pairs:pairs.size,anisotropy,oracleReferences:oracleRecord?.references??0,oracleBytes:oracleRecord?.texture?HYBRID_LOD_ORACLE_BYTES:0};},
  dispose(){if(closed)return;closed=true;for(const pair of [...pairs])pair.dispose();for(const pin of pins)pin.release();pins.clear();if(oracleRecord)cleanupOracle(oracleRecord);}
 };
}
