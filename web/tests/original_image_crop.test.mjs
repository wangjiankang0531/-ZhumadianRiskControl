import test from 'node:test';import assert from 'node:assert/strict';
import {decodeOriginalImage,originalImageStats,OriginalImageCropUnavailable} from '../src/original_image.js';
const blob=new Blob(['platform stub']),image=(width=4,height=3)=>({width,height,closed:0,close(){this.closed++;}});
test('crop decode passes original pixel rectangle without resizing or color conversion',async()=>{
 const before=originalImageStats().owned,bitmap=image();let args;
 const decoded=await decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],decodeBitmap:async(...values)=>{args=values;return bitmap;},loadImage:()=>{throw Error('legacy forbidden');}});
 assert.deepEqual(args,[blob,2,1,4,3,{imageOrientation:'from-image',premultiplyAlpha:'none',colorSpaceConversion:'none'}]);assert.equal(originalImageStats().owned,before+1);assert.equal(decoded.kind,'bitmap');decoded.dispose();decoded.dispose();assert.equal(bitmap.closed,1);assert.equal(originalImageStats().owned,before);
});
test('invalid or out-of-image crop is rejected before platform decode',async()=>{
 for(const crop of [[-1,0,4,3],[0,0,0,3],[15,0,4,3],[0,11,4,3],[0,0,4.5,3],[0,0,4],[0,0,NaN,3],{}])await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop,decodeBitmap:()=>{throw Error('must not decode');}}),/Invalid original image crop/);
});
test('unavailable bitmap support requires explicit full-image replanning without HTML fallback',async()=>{
 for(const options of [{decodeBitmap:null},{preferBitmap:false,decodeBitmap:async()=>image()}]){let legacy=0;await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],...options,loadImage:async()=>{legacy++;return image();}}),OriginalImageCropUnavailable);assert.equal(legacy,0);}
});
test('failed bitmap crop does not silently switch pixels or ownership',async()=>{
 const before=originalImageStats().owned;let legacy=0;await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],decodeBitmap:async()=>{throw Error('unsupported');},loadImage:async()=>{legacy++;}}),OriginalImageCropUnavailable);assert.equal(originalImageStats().owned,before);assert.equal(legacy,0);
});
test('wrong crop dimensions close bitmap before explicit replanning error',async()=>{
 const bitmap=image(16,12),before=originalImageStats().owned;await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],decodeBitmap:async()=>bitmap}),OriginalImageCropUnavailable);assert.equal(bitmap.closed,1);assert.equal(originalImageStats().owned,before);
});
test('cancellation after crop decode closes the late bitmap exactly once',async()=>{
 let current=true;const bitmap=image(),before=originalImageStats().owned;await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],stillWanted:()=>current,decodeBitmap:async()=>{current=false;return bitmap;}}),/no longer wanted/);assert.equal(bitmap.closed,1);assert.equal(originalImageStats().owned,before);
});
test('pre-start cancellation performs no crop decode',async()=>{
 await assert.rejects(decodeOriginalImage({blob,width:16,height:12,crop:[2,1,4,3],stillWanted:()=>false,decodeBitmap:()=>{throw Error('must not decode');}}),/no longer wanted/);
});
test('caller crop mutation during decode cannot alter admitted output dimensions',async()=>{
 const crop=[2,1,4,3],bitmap=image();let resolve;const promise=decodeOriginalImage({blob,width:16,height:12,crop,decodeBitmap:()=>new Promise(r=>{resolve=r;})});crop[2]=16;resolve(bitmap);const decoded=await promise;assert.equal(decoded.image.width,4);decoded.dispose();assert.equal(bitmap.closed,1);
});
