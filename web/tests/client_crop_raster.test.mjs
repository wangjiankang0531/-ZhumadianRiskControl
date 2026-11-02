import test from 'node:test';import assert from 'node:assert/strict';
import {clientCropRasterGate} from '../src/source_client_crop.js';
test('legacy multisample pixel-center interpolation keeps complete images despite an explicit crop request',()=>{
 for(const samples of [1,2,4,8]){const p=clientCropRasterGate({requested:true,bitmapAvailable:true,samples});assert.equal(p.enabled,false);assert.equal(p.blockedReason,'multisample_pixel_center_footprint_unproven');assert.equal(p.rasterSamples,samples);assert.equal(p.requested,true);}
});
test('a verified zero-sample context permits only explicit bitmap-supported crop opt-in',()=>{
 assert.equal(clientCropRasterGate({requested:true,bitmapAvailable:true,samples:0}).enabled,true);assert.equal(clientCropRasterGate({requested:false,bitmapAvailable:true,samples:0}).enabled,false);assert.equal(clientCropRasterGate({requested:true,bitmapAvailable:false,samples:0}).blockedReason,'bitmap_crop_unavailable');
});
test('unknown or malformed raster sample counts fail closed without changing the requested policy',()=>{
 for(const samples of [null,undefined,-1,NaN,Infinity,1.5,'0',65]){const p=clientCropRasterGate({requested:true,bitmapAvailable:true,samples});assert.equal(p.enabled,false);assert.equal(p.rasterSamples,null);assert.equal(p.blockedReason,'raster_samples_unknown');}
 assert.throws(()=>clientCropRasterGate({requested:1,bitmapAvailable:true,samples:0}),/opt-in/);
});
test('default disabled mode carries no blocked warning and does not imply a new sampling baseline',()=>{
 const p=clientCropRasterGate();assert.equal(p.enabled,false);assert.equal(p.requested,false);assert.equal(p.blockedReason,null);assert.match(p.scope,/legacy_pixel_center/);assert.ok(Object.isFrozen(p));
});
