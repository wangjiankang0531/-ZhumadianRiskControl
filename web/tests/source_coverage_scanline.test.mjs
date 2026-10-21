import test from 'node:test';import assert from 'node:assert/strict';
import {coverageInteriorLoss} from '../src/source_coverage.js';
import {legacyCoverageInteriorLoss} from '../tools/benchmark_coverage_mask.mjs';
test('scanline matches the prior integral oracle over 10000 random masks including clipped narrow neighborhoods',()=>{
 let seed=218176;const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
 for(let trial=0;trial<10000;trial++){const w=1+Math.floor(rnd()*53),h=1+Math.floor(rnd()*37),p=new Uint8Array(w*h*4),c=p.slice(),parentChance=trial%4===0?1:trial%4===1?0:rnd(),childChance=trial%5===0?0:rnd();for(let i=0;i<p.length;i+=4){p[i]=rnd()<parentChance?1+Math.floor(rnd()*255):0;c[i]=rnd()<childChance?1+Math.floor(rnd()*255):0;p[i+3]=c[i+3]=255;}assert.deepEqual(coverageInteriorLoss(p,c,w,h),legacyCoverageInteriorLoss(p,c,w,h));}
});
test('every corner, empty mask, full mask and all dimensions below the five-row window retain exact counts',()=>{
 for(const w of [1,2,3,4,5,6,31])for(const h of [1,2,3,4,5,6,37]){const p=new Uint8Array(w*h*4);for(let i=0;i<p.length;i+=4)p[i]=255;assert.deepEqual(coverageInteriorLoss(p,p,w,h),{loss:0,parentPixels:w*h});assert.deepEqual(coverageInteriorLoss(p,new Uint8Array(p.length),w,h),{loss:w*h,parentPixels:w*h});for(const [cx,cy] of [[0,0],[w-1,0],[0,h-1],[w-1,h-1]]){const c=p.slice();for(let y=Math.max(0,cy-5);y<=Math.min(h-1,cy+5);y++)for(let x=Math.max(0,cx-5);x<=Math.min(w-1,cx+5);x++)c[(y*w+x)*4]=0;assert.deepEqual(coverageInteriorLoss(p,c,w,h),legacyCoverageInteriorLoss(p,c,w,h));}}
});
test('maximum supported viewport preserves exact counts without area-sized integral scratch',()=>{const w=4096,h=2160,p=new Uint8Array(w*h*4),c=p.slice();for(let i=0;i<p.length;i+=4)p[i]=255;assert.deepEqual(coverageInteriorLoss(p,c,w,h),{loss:w*h,parentPixels:w*h});});
test('invalid dimensions and mask types fail closed exactly as the prior contract',()=>{for(const [p,c,w,h] of [[new Uint8Array(4),new Uint8Array(4),0,1],[new Uint8Array(4),new Uint8Array(4),4097,1],[new Uint8Array(4),new Uint8Array(3),1,1],[new Uint16Array(4),new Uint8Array(4),1,1]])assert.throws(()=>coverageInteriorLoss(p,c,w,h));});
