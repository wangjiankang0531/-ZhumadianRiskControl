import test from 'node:test';
import assert from 'node:assert/strict';
import {sha256,rgbaMipBytes,validatePreparedBc7,supportsPreparedBc7,uploadPreparedBc7,loadPreparedPhotograph,PreparedTextureContextError,PreparedTextureCancelled} from '../src/prepared_bc7.js';
async function fixture(){
 const payload=new Uint8Array(48).fill(31).buffer,source={sha256:'1'.repeat(64),width:4,height:4};
 const mips=[];for(const [level,size] of [4,2,1].entries())mips.push({level,width:size,height:size,offset:level*16,bytes:16,sha256:await sha256(new Uint8Array(payload,level*16,16)),accepted:true,quality:{rgbPSNR:50,rgbChannelP99:1,rgbMaxError:2}});
 return {source,payload,manifest:{schema:'xnby.bc7.mip_chain.v1',format:'BC7_UNORM_BLOCK',sourceSHA256:source.sha256,sourceSize:[4,4],payloadBytes:48,payloadSHA256:await sha256(payload),mips,accepted:true,qualityThresholds:{rgbPSNRMin:40,rgbChannelP99Max:16,rgbMaxErrorMax:96}}};
}
function options(f){return {reserve:async()=>({release(){}}),supported:true,source:f.source,loadManifest:async()=>f.manifest,loadPayload:async()=>f.payload,upload:async()=>({compressed:true}),loadFallback:async()=>({original:true})};}
test('complete prepared BC7 chain validates every mip and keeps payload views',async()=>{
 const f=await fixture(),p=await validatePreparedBc7(f.manifest,f.payload,f.source);assert.equal(p.bytes,48);assert.equal(p.mips.length,3);assert.equal(p.mips[0].data.buffer,f.payload);assert.equal(rgbaMipBytes(4,4),84);
});
test('source identity and dimensions must match trusted original',async()=>{
 const f=await fixture();for(const source of [{...f.source,sha256:'2'.repeat(64)},{...f.source,width:8}])await assert.rejects(validatePreparedBc7(f.manifest,f.payload,source));
});
test('WebGL top level requires multiples of four',async()=>{
 const f=await fixture();f.manifest.sourceSize=[3,4];await assert.rejects(validatePreparedBc7(f.manifest,f.payload,{...f.source,width:3}));
});
test('wrong whole payload or individual mip digest is rejected',async()=>{
 const f=await fixture();f.manifest.payloadSHA256='0'.repeat(64);await assert.rejects(validatePreparedBc7(f.manifest,f.payload,f.source));f.manifest.payloadSHA256=await sha256(f.payload);f.manifest.mips[1].sha256='0'.repeat(64);await assert.rejects(validatePreparedBc7(f.manifest,f.payload,f.source));
});
test('missing, extra, overlapping and incorrectly sized mips are rejected',async()=>{
 const f=await fixture();for(const edit of [m=>m.mips.pop(),m=>m.mips.push({...m.mips[2],level:3}),m=>m.mips[1].offset=0,m=>m.mips[0].bytes=32,m=>m.mips[1].width=4]){const m=structuredClone(f.manifest);edit(m);await assert.rejects(validatePreparedBc7(m,f.payload,f.source));}
});
test('unsupported hardware does not request compressed resources',async()=>{
 const f=await fixture(),o=options(f);o.supported=false;o.loadManifest=()=>{throw Error('must not download')};const r=await loadPreparedPhotograph(o);assert.equal(r.format,'rgba8');assert.equal(r.bytes,84);assert.equal(r.fallbackReason,'unsupported');
});
test('valid compressed resources use their actual mip byte budget',async()=>{
 const f=await fixture(),r=await loadPreparedPhotograph(options(f));assert.equal(r.format,'bc7');assert.equal(r.bytes,48);assert.equal(r.fallbackReason,null);
});
test('bad prepared bytes preserve the original image fallback and report reason',async()=>{
 const f=await fixture(),o=options(f),reasons=[];f.manifest.sourceSHA256='0'.repeat(64);o.onFallback=r=>reasons.push(r);o.upload=()=>{throw Error('must not upload')};const r=await loadPreparedPhotograph(o);assert.equal(r.format,'rgba8');assert.equal(r.texture.original,true);assert.deepEqual(reasons,['prepared_unavailable_or_invalid']);
});
test('upload rejection falls back once, failed original load is surfaced',async()=>{
 const f=await fixture(),o=options(f);o.upload=()=>{throw Error('driver rejection')};let calls=0;o.loadFallback=()=>{calls++;throw Error('original unavailable')};await assert.rejects(loadPreparedPhotograph(o),/original unavailable/);assert.equal(calls,1);
});
test('pre-existing or lost graphics context errors are not hidden by fallback',async()=>{
 const f=await fixture(),o=options(f);o.upload=()=>{throw new PreparedTextureContextError('context lost')};o.loadFallback=()=>{throw Error('must not fallback')};await assert.rejects(loadPreparedPhotograph(o),PreparedTextureContextError);
});
test('Three adapter uses sRGB complete explicit mips and disposes failed uploads',async()=>{
 const f=await fixture(),p=await validatePreparedBc7(f.manifest,f.payload,f.source);let disposed=0;const THREE={CompressedTexture:class{constructor(...args){this.args=args;}dispose(){disposed++;}},RGBA_BPTC_Format:36492,UnsignedByteType:1009,SRGBColorSpace:'srgb',LinearMipmapLinearFilter:1008,LinearFilter:1006,ClampToEdgeWrapping:1001};
 const gl={NO_ERROR:0,getError:()=>0,isContextLost:()=>false};const renderer={extensions:{has:()=>true},getContext:()=>gl,initTexture:t=>{assert.equal(t.colorSpace,'srgb');assert.equal(t.generateMipmaps,false);assert.equal(t.flipY,false);assert.equal(t.args[3],36492);}};
 assert.equal(supportsPreparedBc7(renderer),true);assert.equal(uploadPreparedBc7(THREE,renderer,p).needsUpdate,true);assert.equal(disposed,0);
 renderer.initTexture=()=>{throw Error('upload failure')};assert.throws(()=>uploadPreparedBc7(THREE,renderer,p));assert.equal(disposed,1);gl.getError=()=>1280;assert.throws(()=>uploadPreparedBc7(THREE,renderer,p),PreparedTextureContextError);assert.equal(disposed,1);
});

test('every texture is reserved before loading/upload and released exactly once',async()=>{
 const f=await fixture(),o=options(f);let held=0,releases=0,disposals=0;
 o.reserve=async({bytes})=>{held+=bytes;return {release(){held-=bytes;releases++;}};};
 o.upload=async()=>{assert.equal(held,48);return {dispose(){disposals++;}};};
 const r=await loadPreparedPhotograph(o);assert.equal(held,48);r.dispose();r.dispose();assert.equal(held,0);assert.equal(releases,1);assert.equal(disposals,1);
});
test('larger original fallback must be re-admitted, never exceed the shared budget',async()=>{
 const f=await fixture(),o=options(f);let held=0,jpegLoads=0;
 o.reserve=async({bytes})=>{if(held+bytes>60)throw Error('budget exceeded');held+=bytes;return {release(){held-=bytes;}};};
 o.upload=async()=>{throw Error('upload failed');};o.loadFallback=async()=>{jpegLoads++;return {};};
 await assert.rejects(loadPreparedPhotograph(o),/budget exceeded/);assert.equal(held,0);assert.equal(jpegLoads,0);
});
test('cancellation after asynchronous upload disposes only the staged texture',async()=>{
 const f=await fixture(),o=options(f);let wanted=true,held=0,disposed=0;
 o.stillWanted=()=>wanted;o.reserve=async({bytes})=>{held+=bytes;return {release(){held-=bytes;}};};
 o.upload=async()=>{wanted=false;return {dispose(){disposed++;}};};o.loadFallback=()=>{throw Error('must not fallback');};
 await assert.rejects(loadPreparedPhotograph(o),PreparedTextureCancelled);assert.equal(held,0);assert.equal(disposed,1);
});
test('a real shared budget callback is mandatory',async()=>{
 const f=await fixture(),o=options(f);delete o.reserve;await assert.rejects(loadPreparedPhotograph(o),/reservation is required/);
});

test('a throwing texture disposal still releases budget and cannot run twice',async()=>{
 const f=await fixture(),o=options(f);let held=0,disposals=0;
 o.reserve=async({bytes})=>{held+=bytes;return {release(){held-=bytes;}};};
 o.upload=async()=>({dispose(){disposals++;throw Error('dispose failed');}});
 const r=await loadPreparedPhotograph(o);assert.equal(held,48);assert.throws(()=>r.dispose(),/dispose failed/);assert.equal(held,0);r.dispose();assert.equal(disposals,1);
});

test('missing failed relaxed and nonfinite quality is rejected for every mip',async()=>{
 const f=await fixture();
 for(const mutate of [m=>delete m.accepted,m=>m.accepted=false,m=>m.accepted=1,m=>m.mips[1].accepted=false,m=>delete m.mips[1].quality,m=>delete m.qualityThresholds,m=>m.qualityThresholds.rgbPSNRMin=39,m=>m.qualityThresholds.rgbChannelP99Max=17,m=>m.qualityThresholds.rgbMaxErrorMax=97,m=>m.mips[1].quality.rgbPSNR=39.999,m=>m.mips[1].quality.rgbPSNR=NaN,m=>m.mips[1].quality.rgbPSNR=Infinity,m=>m.mips[1].quality.rgbChannelP99=true,m=>m.mips[1].quality.rgbMaxError=97]){
  const manifest=structuredClone(f.manifest);mutate(manifest);await assert.rejects(validatePreparedBc7(manifest,f.payload,f.source),/quality/);
 }
});
test('failed quality falls back before compressed payload download or GPU reservation',async()=>{
 const f=await fixture(),o=options(f),reservations=[];f.manifest.mips[1].quality.rgbPSNR=39;
 o.loadPayload=()=>{throw Error('must not request rejected compressed bytes');};o.upload=()=>{throw Error('must not upload');};o.reserve=async request=>{reservations.push(request);return {release(){}};};
 const result=await loadPreparedPhotograph(o);assert.equal(result.format,'rgba8');assert.equal(result.fallbackReason,'prepared_unavailable_or_invalid');assert.deepEqual(reservations,[{format:'rgba8',bytes:84}]);result.dispose();
});
