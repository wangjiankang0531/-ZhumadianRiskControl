import test from 'node:test';
import assert from 'node:assert/strict';
import {topics,categories,documentFingerprint,parseSpatialCatalog,spatialObject,inTopic,scopedObjects,topicCounts,catalogOrphans} from '../src/spatial_catalog.js';
const feature=(id,objectType=null)=>({id,name:id,type:'point',positions:[[1,2,3]],...(objectType?{business:{objectType,businessId:'TEST-'+id,sourceSystem:'QA'}}:{})});
const document={scene:'zhumadian',coordinates:{srs:'EPSG:32650',unit:'metre',axes:'east,north,up',origin:[225319.5,3648440.1,30.9]},layers:[{id:'first',visible:true,features:[feature('e','enterprise'),feature('v','video'),feature('u')]},{id:'second',visible:false,features:[feature('h','major-hazard')]}]};
const fp=await documentFingerprint(document);
const base={schema:'xnby.spatial.catalog.v1',scene:'zhumadian',layerFingerprint:fp,exportedAt:'2026-10-13T00:00:00Z',objects:[{spatialId:'u',category:'energy-meter',themes:['energy','monitoring']}]};
test('five required maps exist and unclassified original annotations remain accessible from all layers',()=>{
  assert.equal(Object.keys(topics).length,5);assert.equal(inTopic(feature('u'),'all'),true);assert.equal(inTopic(feature('u'),'energy'),false);
  assert.equal(spatialObject(feature('u')).category,'unregistered');
});
test('existing 13-type business associations provide default topic membership without requiring another file',()=>{
  assert.deepEqual(spatialObject(feature('h','major-hazard')).themes,['portrait','monitoring','emergency']);
  assert.equal(inTopic(feature('v','video'),'closed'),true);assert.equal(inTopic(feature('e','enterprise'),'energy'),false);
});
test('an independent energy registration can be shared between topics without changing DLG geometry or business identity',()=>{
  const before=JSON.stringify(document),catalog=parseSpatialCatalog(base),object=spatialObject(document.layers[0].features[2],catalog);
  assert.equal(object.category,'energy-meter');assert.deepEqual(object.themes,['energy','monitoring']);assert.equal(object.business,null);assert.equal(JSON.stringify(document),before);
});
test('topic totals count spatial features once per topic, include hidden layers, and do not infer enterprise or alarm statistics',()=>{
  const catalog=parseSpatialCatalog(base),counts=topicCounts(document.layers,catalog);
  assert.deepEqual(counts,{all:4,portrait:2,monitoring:3,closed:1,emergency:2,energy:1});
  assert.equal(scopedObjects(document.layers,'monitoring','energy-meter',catalog).length,1);
});
test('fingerprints ignore grouping, names, styling, visibility and object ordering',async()=>{
  const changed=structuredClone(document);changed.layers.reverse();changed.layers[1].features.reverse();changed.layers[1].visible=false;
  changed.layers[1].features[0].name='renamed';changed.layers[1].features[0].style={opacity:.3};
  changed.coordinates={origin:changed.coordinates.origin,axes:changed.coordinates.axes,unit:changed.coordinates.unit,srs:changed.coordinates.srs};
  assert.equal(await documentFingerprint(changed),fp);
});
test('fingerprints change when spatial id, geometry or source business/enterprise identity changes',async()=>{
  for(const edit of [d=>d.layers[0].features[0].id='other',d=>d.layers[0].features[0].positions[0][0]=9,d=>d.layers[0].features[0].business.sourceSystem='other',d=>d.layers[0].features[0].business.enterpriseId='enterprise']){
    const changed=structuredClone(document);edit(changed);assert.notEqual(await documentFingerprint(changed),fp);
  }
});
test('catalogs reject wrong schemas/scenes, non-hash identity, invalid UTC date and unknown fields',()=>{
  for(const patch of [{schema:'wrong'},{scene:'other'},{layerFingerprint:'x'.repeat(64)},{exportedAt:'2026-02-30T00:00:00Z'},{exportedAt:'2026-10-13T00:00:00+08:00'},{unexpected:true}])assert.throws(()=>parseSpatialCatalog({...base,...patch}));
});
test('catalogs reject duplicate spatial ids, invalid category, duplicate or unknown themes and unknown object fields',()=>{
  for(const objects of [[base.objects[0],base.objects[0]],[{spatialId:'u',category:'wrong'}],[{spatialId:'u',category:'energy-meter',themes:['energy','energy']}],[{spatialId:'u',category:'energy-meter',themes:['wrong']}],[{spatialId:'u',category:'energy-meter',themes:[]}],[{spatialId:'u',category:'energy-meter',extra:1}]])assert.throws(()=>parseSpatialCatalog({...base,objects}));
});
test('catalog inputs are isolated from later mutation and prototype-like ids are safe Map keys',()=>{
  const input=structuredClone(base);input.objects[0].spatialId='__proto__';const parsed=parseSpatialCatalog(input);input.objects[0].themes.push('closed');
  assert.deepEqual(parsed.byId.get('__proto__').themes,['energy','monitoring']);assert.equal(Object.hasOwn(categories,'__proto__'),false);
});
test('missing ids are reported, and template/empty catalogs do not imply classifications or records',()=>{
  const parsed=parseSpatialCatalog({...base,objects:[{spatialId:'missing',category:'parking'}]});assert.deepEqual(catalogOrphans(document.layers,parsed),['missing']);
  const empty=parseSpatialCatalog({...base,objects:[]});assert.equal(empty.byId.size,0);assert.equal(topicCounts(document.layers,empty).energy,0);
});
test('default categories cover new emergency and closed-management resources',()=>{
  assert.equal(inTopic(feature('parking'),'closed',parseSpatialCatalog({...base,objects:[{spatialId:'parking',category:'parking'}]})),true);
  assert.equal(inTopic(feature('team'),'emergency',parseSpatialCatalog({...base,objects:[{spatialId:'team',category:'emergency-team'}]})),true);
});
