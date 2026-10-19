import test from 'node:test';
import assert from 'node:assert/strict';
import {validateLandscapeDocument as validate} from '../src/landscape_document.js';
import {LayerLoading} from '../src/layer_loading.js';

const style=()=>({icon:'pin',pattern:'solid',sizePx:32,widthPx:4,color:'#22D3EE',fillColor:'#00AABB',opacity:0,fillOpacity:.25});
const label=()=>({visible:false,text:'合成标牌',fontPx:16,color:'#FFFFFF',opacity:.8,offset:[12,-16]});
const fixture=()=>({schema:'hongtu.landscape.layers.v1',scene:'zhumadian',coordinates:{srs:'EPSG:32650',unit:'metre',axes:'east,north,up',origin:[225319.5,3648440.1,30.9]},layers:[{id:'layer',name:'合成验证层',visible:true,locked:false,features:[
  {id:'point',name:'自定义图标',type:'point',positions:[[0,0,0]],style:{...style(),icon:'custom',iconData:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNQuvzuPwAF4QLj/AHgLgAAAABJRU5ErkJggg=='},label:label()},
  {id:'line',name:'虚线',type:'line',positions:[[-10,0,0],[10,0,1]],style:{...style(),pattern:'dash',widthPx:32,opacity:.45}},
  {id:'region',name:'凹区域',type:'region',positions:[[0,0,0],[8,0,0],[8,8,0],[4,4,0],[0,8,0]],style:{...style(),pattern:'dot',fillOpacity:0},label:{...label(),visible:true}},
]}]});
const invalid={numericFeatureId:d=>d.layers[0].features[0].id=123,numericLayerId:d=>d.layers[0].id=123,nullLabel:d=>d.layers[0].features[0].label=null,falseLabel:d=>d.layers[0].features[0].label=false,arrayColor:d=>d.layers[0].features[0].style.color=['#22D3EE'],arrayLabelColor:d=>d.layers[0].features[0].label.color=['#FFFFFF']};

test('DLG JSON round trip preserves custom icon, independent label alpha, point/line/concave region and layer state',()=>{
  const original=fixture(),raw=JSON.stringify(original),restored=JSON.parse(raw);
  assert.equal(validate(restored),restored);assert.equal(JSON.stringify(restored),raw);assert.deepEqual(restored,original);
  assert.equal(restored.layers[0].features[0].style.opacity,0);assert.equal(restored.layers[0].features[0].label.opacity,.8);
});
test('reject values formerly coerced by browser but invalid for EXE fields',()=>{
  for(const [name,change] of Object.entries(invalid)){const d=fixture();change(d);assert.throws(()=>validate(d),undefined,name);}
});
test('invalid newest document never replaces existing layers, styles, geometry or selection owner',async()=>{
  const loader=new LayerLoading();let current=fixture();const before=current,raw=JSON.stringify(current);
  for(const change of Object.values(invalid)){
    const next=fixture();change(next);
    await assert.rejects(loader.load(async()=>next,value=>{validate(value);current=structuredClone(value);}));
    assert.equal(current,before);assert.equal(JSON.stringify(current),raw);
  }
});
test('absent label remains a supported legacy document; an explicitly invalid label is not treated as absent',()=>{
  const d=fixture();delete d.layers[0].features[0].label;assert.equal(validate(d),d);
  for(const value of [null,false,0,'',[],{}]){const copy=structuredClone(d);copy.layers[0].features[0].label=value;assert.throws(()=>validate(copy));}
});
test('duplicates across layers, malformed coordinates and self-crossing regions remain rejected',()=>{
  for(const change of [d=>d.layers.push({...structuredClone(d.layers[0]),id:'second'}),d=>d.layers[0].features[0].positions[0][0]='0',d=>d.layers[0].features[2].positions=[[0,0,0],[10,10,0],[0,10,0],[10,0,0]]]){const d=fixture();change(d);assert.throws(()=>validate(d));}
});
test('documents must contain object records rather than array/null placeholders',()=>{
  for(const d of [null,[],false,{...fixture(),layers:[null]},{...fixture(),layers:[[]]}])assert.throws(()=>validate(d));
  const d=fixture();d.layers[0].features=[null];assert.throws(()=>validate(d));
});
test('existing WEB layer capacity and valid style bounds remain unchanged',()=>{
  const d=fixture();d.layers=Array.from({length:1000},(_,i)=>({id:'layer'+i,name:'合成层',visible:false,locked:true,features:[]}));
  assert.equal(validate(d),d);d.layers.push({id:'overflow',name:'overflow',visible:false,locked:true,features:[]});assert.throws(()=>validate(d));
  const e=fixture();Object.assign(e.layers[0].features[1].style,{widthPx:.5,sizePx:8,opacity:1,fillOpacity:1});assert.equal(validate(e),e);
});
