import test from 'node:test';
import assert from 'node:assert/strict';
import {inTopic,spatialObject,topicCounts} from '../src/spatial_catalog.js';
import {inSceneTopic,scopedSceneObjects,sceneTopicCounts} from '../src/spatial_scene_scope.js';
const feature=(id,objectType)=>({id,type:'point',positions:[[1,2,3]],business:{objectType,businessId:id,sourceSystem:'QA'}});
const enterprise=feature('company','enterprise'),boundary={...feature('boundary','enterprise-boundary'),type:'area'},team=feature('team','emergency-team'),energy=feature('energy','energy-meter');
const layers=[{id:'available',visible:true,features:[enterprise,boundary,team,energy]}];
test('emergency scene includes enterprise context while original registration and business identity remain unchanged',()=>{
 const before=JSON.stringify(layers),membership=spatialObject(enterprise).themes;
 assert.equal(inTopic(enterprise,'emergency'),false);assert.equal(inSceneTopic(enterprise,'emergency'),true);assert.equal(inSceneTopic(boundary,'emergency'),true);
 assert.deepEqual(scopedSceneObjects(layers,'emergency').map(row=>row.feature.id),['company','boundary','team']);
 assert.equal(sceneTopicCounts(layers).emergency,3);assert.equal(topicCounts(layers).emergency,1);assert.deepEqual(spatialObject(enterprise).themes,membership);assert.equal(JSON.stringify(layers),before);
});
test('context consumes only provided authorized objects, keeps category scope and does not promote unrelated notes or resources',()=>{
 assert.equal(inSceneTopic({id:'note',type:'point'},'emergency'),false);assert.equal(inSceneTopic(energy,'emergency'),false);
 assert.deepEqual(scopedSceneObjects(layers,'emergency','emergency-team').map(row=>row.feature.id),['team']);
 assert.deepEqual(scopedSceneObjects(layers,'emergency','enterprise').map(row=>row.feature.id),['company']);
 assert.deepEqual(scopedSceneObjects([], 'emergency'),[]);assert.equal(sceneTopicCounts([]).emergency,0);
 for(const topic of ['all','portrait','monitoring','closed','energy'])assert.equal(sceneTopicCounts(layers)[topic],topicCounts(layers)[topic]);
});
test('explicit catalog category governs context without mutating its independent theme assignment',()=>{
 const catalog={byId:new Map([['company',{category:'energy-meter',themes:['energy']}],['energy',{category:'enterprise',themes:['portrait']}]])};
 assert.equal(inSceneTopic(enterprise,'emergency',catalog),false);assert.equal(inSceneTopic(energy,'emergency',catalog),true);assert.deepEqual(catalog.byId.get('energy').themes,['portrait']);
});
test('hidden layer context remains in registered totals and keeps its layer visibility available for rendering',()=>{
 const hidden={id:'hidden',visible:false,features:[enterprise]};const result=scopedSceneObjects([hidden],'emergency');assert.equal(result.length,1);assert.equal(result[0].layer.visible,false);
});
