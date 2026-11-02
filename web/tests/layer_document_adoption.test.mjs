import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createContext,runInContext} from 'node:vm';
import * as landscape from '../src/landscape_document.js';
import {LayerLoading} from '../src/layer_loading.js';

// Exercise the actual viewer transition without starting WebGL or a landscape reader.
const viewer=readFileSync(new URL('../src/viewer.js',import.meta.url),'utf8');
const start=viewer.indexOf('function openDocument(doc,name){');
const end=viewer.indexOf('\nfunction text(',start);
assert.ok(start>=0&&end>start,'viewer openDocument boundary must remain explicit');
assert.equal(viewer.indexOf('function openDocument(doc,name){',start+1),-1);
const transition=viewer.slice(start,end);
const document=()=>({schema:'hongtu.landscape.layers.v1',scene:'zhumadian',coordinates:{srs:'EPSG:32650',unit:'metre',axes:'east,north,up',origin:[225319.5,3648440.1,30.9]},layers:[{id:'layer',name:'Synthetic',visible:true,locked:false,features:[]}]});

function harness(){
  const old=document(),calls=[],nodes=new Map(['feature-search','feature-type','file-name'].map(id=>[id,{value:'old-filter',textContent:'old-file'}]));
  const ctx=createContext({validate:landscape.validateLandscapeDocument,prepareLayers:doc=>landscape.prepareLandscapeDocument(doc),structuredClone,
    layersDoc:old,signOffsets:new Map([['point',[40,20]]]),signPrevious:new Map([['point',{x:1,y:2}]]),signLayoutKey:'old-layout',
    signMetrics:new Map([['point',{width:30}]]),signPlacements:new Map([['point',{x:3,y:4}]]),signLayoutResult:{old:true},signPreferenceKey:'old-preferences',
    layerOpacities:new Map([['layer',.3]]),selected:{id:'point'},selectedLayer:{id:'layer'},hitTargets:[{id:'point'}],
    tintedCache:new Map([['old','tint']]),imageCache:new Map([['old','image']]),spatialFingerprint:'old-fingerprint',spatialFingerprintPromise:null,
    drag:{active:true},cancelSignDrag:()=>{calls.push('cancelDrag');ctx.drag=null;},$:id=>nodes.get(id),clearSelection:()=>calls.push('clearSelection'),
    spatialNotice:message=>calls.push(['notice',message]),documentFingerprint:async()=>{calls.push('fingerprint');return 'new-fingerprint';},
    loadSignPreferences:()=>calls.push('loadPreferences'),rebuildLayerUI:()=>calls.push('rebuild'),message:value=>calls.push(['message',value])});
  runInContext(transition,ctx);
  const snapshot=()=>JSON.stringify({doc:ctx.layersDoc,offsets:[...ctx.signOffsets],previous:[...ctx.signPrevious],layoutKey:ctx.signLayoutKey,
    metrics:[...ctx.signMetrics],placements:[...ctx.signPlacements],layout:ctx.signLayoutResult,preference:ctx.signPreferenceKey,
    opacities:[...ctx.layerOpacities],selected:ctx.selected,selectedLayer:ctx.selectedLayer,hits:ctx.hitTargets,tints:[...ctx.tintedCache],
    images:[...ctx.imageCache],fingerprint:ctx.spatialFingerprint,drag:ctx.drag,nodes:[...nodes]});
  return {ctx,old,calls,nodes,snapshot,open:doc=>ctx.openDocument(doc,'new-file')};
}

test('invalid DLG preserves the existing document, drag, manual signs, filters, caches and selection',async()=>{
  for(const change of [d=>d.schema='invalid',d=>d.coordinates.origin[0]=0,d=>d.layers[0].visible='true']){
    const h=harness(),before=h.snapshot(),next=document();change(next);
    await assert.rejects(new LayerLoading().load(async()=>next,h.open));
    assert.equal(h.ctx.layersDoc,h.old);assert.equal(h.snapshot(),before);assert.deepEqual(h.calls,[]);
  }
});

test('clone failure also leaves every existing browsing state untouched',async()=>{
  const h=harness(),before=h.snapshot(),next=document();next.extra=()=>{};
  assert.equal(landscape.validateLandscapeDocument(next),next);
  await assert.rejects(new LayerLoading().load(async()=>next,h.open),{name:'DataCloneError'});
  assert.equal(h.ctx.layersDoc,h.old);assert.equal(h.snapshot(),before);assert.deepEqual(h.calls,[]);
});

test('valid DLG commits a detached clone and resets the previous document state',async()=>{
  const h=harness(),next=document(),raw=JSON.stringify(next);
  assert.equal(await new LayerLoading().load(async()=>next,h.open),true);
  await h.ctx.spatialFingerprintPromise;
  assert.notEqual(h.ctx.layersDoc,next);assert.deepEqual(h.ctx.layersDoc,next);assert.equal(JSON.stringify(next),raw);
  for(const name of ['signOffsets','signPrevious','signMetrics','signPlacements','layerOpacities','tintedCache','imageCache'])assert.equal(h.ctx[name].size,0,name);
  for(const name of ['signLayoutKey','signPreferenceKey'])assert.equal(h.ctx[name],'',name);
  for(const name of ['signLayoutResult','selected','selectedLayer','drag'])assert.equal(h.ctx[name],null,name);
  assert.equal(h.ctx.hitTargets.length,0);assert.equal(h.nodes.get('feature-search').value,'');assert.equal(h.nodes.get('feature-type').value,'all');
  assert.equal(h.nodes.get('file-name').textContent,'new-file');assert.equal(h.ctx.spatialFingerprint,'new-fingerprint');
  next.layers[0].name='changed outside viewer';assert.equal(h.ctx.layersDoc.layers[0].name,'Synthetic');
  assert.equal(h.calls.filter(v=>v==='cancelDrag').length,1);assert.ok(h.calls.includes('loadPreferences'));
});

test('a failed newer read does not let a late older valid read replace the current document',async()=>{
  const h=harness(),before=h.snapshot(),loader=new LayerLoading();let finish;
  const older=loader.load(()=>new Promise(resolve=>{finish=resolve;}),h.open);
  const invalid=document();invalid.layers=null;
  await assert.rejects(loader.load(async()=>invalid,h.open));finish(document());
  assert.equal(await older,false);assert.equal(h.ctx.layersDoc,h.old);assert.equal(h.snapshot(),before);assert.deepEqual(h.calls,[]);
});

test('the real viewer facade resolves validate from its actual named module imports',()=>{
  const imported=viewer.match(/import \{([^}]+)\} from '\.\/landscape_document\.js';/);
  assert.ok(imported,'landscape document import must exist');
  const bindings={};
  for(const specifier of imported[1].split(',')){
    const parts=specifier.trim().split(/\s+as\s+/);
    assert.equal(typeof landscape[parts[0]],'function');bindings[parts[1]??parts[0]]=landscape[parts[0]];
  }
  const ctx=createContext({...bindings,window:{},telemetry:{},openDocument(){},preset(){},locate(){},layersDoc:document(),selected:null,resident:new Map(),camera:{position:{toArray:()=>[0,0,0]}}});
  const facade=viewer.indexOf('window.hongtuViewer=');assert.ok(facade>=0);
  runInContext(viewer.slice(facade),ctx);
  assert.equal(ctx.window.hongtuViewer.validate,landscape.validateLandscapeDocument);
  const doc=document();assert.equal(ctx.window.hongtuViewer.validate(doc),doc);
});
