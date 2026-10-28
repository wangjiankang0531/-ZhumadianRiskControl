import test from 'node:test';import assert from 'node:assert/strict';
import {planRenderQuality,applyRenderQualityPlan} from '../src/render_quality.js';
const defaults={width:1280,height:585,devicePixelRatio:1,maxRenderbufferSize:16384,samples:4};
test('standard mode preserves established device ratios even when the new high-quality cap is smaller',()=>{
 for(const devicePixelRatio of [.75,1,1.25,1.5,2,3])for(const [width,height] of [[1280,585],[3840,2160]]){const p=planRenderQuality({...defaults,width,height,devicePixelRatio});assert.equal(p.ratio,Math.min(devicePixelRatio,1.5));assert.equal(p.drawWidth,Math.floor(width*p.ratio));assert.equal(p.drawHeight,Math.floor(height*p.ratio));}
});
test('actual diagnostic viewport admits double raster density without changing source demand dimensions',()=>{const p=planRenderQuality({...defaults,mode:'high'});assert.equal(p.ratio,2);assert.equal(p.drawWidth,2560);assert.equal(p.drawHeight,1170);assert.equal(p.width,1280);assert.equal(p.height,585);assert.equal(p.estimatedFramebufferBytes,131788800);assert.ok(p.estimatedFramebufferBytes<=p.budgetBytes);});
test('larger windows adapt high quality to the byte estimate and hardware dimension limit',()=>{
 for(const [width,height,maxRenderbufferSize,samples] of [[1920,866,16384,4],[3200,1800,4096,0],[800,600,1024,4],[4096,2160,8192,8]]){const p=planRenderQuality({...defaults,width,height,maxRenderbufferSize,samples,mode:'high'});assert.ok(p.ratio>=p.standardRatio);if(p.highAvailable){assert.ok(p.drawWidth<=maxRenderbufferSize);assert.ok(p.drawHeight<=maxRenderbufferSize);assert.ok(p.estimatedFramebufferBytes<=p.budgetBytes);}else assert.equal(p.ratio,p.standardRatio);}
});
test('conservative floor rounding stays within caps for many viewports and MSAA counts',()=>{for(let width=317;width<4000;width+=137)for(let height=251;height<2200;height+=173)for(const samples of [0,2,4,8]){const p=planRenderQuality({...defaults,width,height,samples,mode:'high'});if(p.highAvailable)assert.ok(p.estimatedFramebufferBytes<=p.budgetBytes&&p.drawWidth<=defaults.maxRenderbufferSize&&p.drawHeight<=defaults.maxRenderbufferSize);}});
test('switching quality and resizing back is deterministic and keeps the source viewport unchanged',()=>{const initial=planRenderQuality({...defaults,mode:'high'});const standard=planRenderQuality(defaults);assert.equal(standard.ratio,1);planRenderQuality({...defaults,mode:'high',width:2200,height:1300});assert.deepEqual(planRenderQuality({...defaults,mode:'high'}),initial);});
test('invalid dimensions, device limits and modes cannot request an unbounded target',()=>{for(const change of [{mode:'ultra'},{width:0},{height:NaN},{samples:-1},{samples:1.5},{devicePixelRatio:Infinity},{devicePixelRatio:0},{maxRenderbufferSize:0},{budgetBytes:0}])assert.throws(()=>planRenderQuality({...defaults,...change}),/Invalid/);});

test('mode and portrait/landscape resizes never allocate an intermediate canvas larger than old or final',()=>{
 for(const [oldW,oldH,newW,newH] of [[7680,4320,1280,585],[2560,1170,1920,866],[900,2400,2400,900],[3000,500,500,3000],[1280,585,1280,585]]){
  const plan=planRenderQuality({...defaults,width:newW,height:newH,mode:'high'}),limit=Math.max(oldW*oldH,plan.drawWidth*plan.drawHeight);let w=oldW,h=oldH,calls=0;const allocations=[],canvas={style:{},get width(){return w;},set width(v){w=v;allocations.push(w*h);},get height(){return h;},set height(v){h=v;allocations.push(w*h);}};
  const renderer={domElement:canvas,setPixelRatio(){assert.fail('would allocate old window at new ratio');},setSize(){assert.fail('would allocate new window at old ratio');},setDrawingBufferSize(width,height,ratio){calls++;assert.equal(width,plan.width);assert.equal(height,plan.height);assert.equal(ratio,plan.ratio);canvas.width=Math.floor(width*ratio);canvas.height=Math.floor(height*ratio);}};
  applyRenderQualityPlan(renderer,plan);assert.equal(calls,1);assert.equal(w,plan.drawWidth);assert.equal(h,plan.drawHeight);assert.ok(allocations.every(n=>n<=limit));assert.deepEqual(canvas.style,{width:plan.width+'px',height:plan.height+'px'});
 }
});
