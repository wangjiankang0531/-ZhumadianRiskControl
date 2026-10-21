import test from 'node:test';
import assert from 'node:assert/strict';
import {referenceRoute,homeShortcuts} from '../src/reference-home.js';
import {referenceCommandURL,referenceLocalDeployment,referenceSceneURL} from '../src/reference-deployment.js';
const catalog=[{id:'risk-unit'},{id:'events'},{id:'special-work'},{id:'approval-todo'}];
test('login root opens navigation home while direct MIS routes remain reachable',()=>{
 assert.equal(referenceRoute('',catalog),'home');
 assert.equal(referenceRoute('#home',catalog),'home');
 assert.equal(referenceRoute('#dashboard',catalog),'dashboard');
 assert.equal(referenceRoute('#events',catalog),'events');
 assert.equal(referenceRoute('#not-an-app',catalog),'home');
});
test('shortcuts cannot navigate to absent modules',()=>{
 assert.deepEqual(homeShortcuts(catalog).map(v=>v[1]),['risk-unit','special-work','events','dashboard']);
});
test('local scene destination contains only the fixed scenario, never a public login token',()=>{
 assert.equal(referenceCommandURL({mode:'public-business',csrf:'private'}),'http://127.0.0.1:8767/?topic=emergency&mode=command');
 assert.equal(referenceCommandURL({commandURL:'http://localhost:8825/?mode=command&topic=emergency'}),'http://localhost:8825/?mode=command&topic=emergency');
 for(const commandURL of ['https://127.0.0.1:8767/?topic=emergency&mode=command','http://192.168.250.252:8767/?topic=emergency&mode=command','http://127.0.0.1:80/?topic=emergency&mode=command','http://user:pass@127.0.0.1:8767/?topic=emergency&mode=command','http://127.0.0.1:8767/?topic=emergency&mode=command&token=private','http://127.0.0.1:8767/?topic=emergency&mode=command#secret','http://127.0.0.1:8767/other?topic=emergency&mode=command','http://127.0.0.1:8767/?topic=emergency&topic=other','javascript:alert(1)'])assert.throws(()=>referenceCommandURL({commandURL}));
});

test('explicit indexed local entry retains LEVEL flags in both homepage links',()=>{
 const commandURL='http://127.0.0.1:8768/?topic=emergency&mode=command&levelIndex=1&levelCut=1';
 const d=referenceLocalDeployment(null,{hostname:'127.0.0.1',commandURL});
 assert.equal(referenceCommandURL(d),commandURL);
 assert.equal(referenceSceneURL(d),'http://127.0.0.1:8768/?levelIndex=1&levelCut=1');
 assert.equal(referenceSceneURL(null),'http://127.0.0.1:8767/');
});
test('public deployment and nonlocal pages cannot adopt local HTML overrides',()=>{
 const pub={mode:'public-business',csrf:'must-stay-here'};
 assert.equal(referenceLocalDeployment(pub,{hostname:'localhost',commandURL:'bad'}),pub);
 assert.equal(referenceLocalDeployment(null,{hostname:'example.test',commandURL:'bad'}),null);
 assert.equal(referenceLocalDeployment(null,{hostname:'localhost'}),null);
});
test('indexed scene flags must be complete, unique and equal one',()=>{
 const base='http://127.0.0.1:8768/?topic=emergency&mode=command';
 for(const suffix of ['&levelIndex=1','&levelCut=1','&levelIndex=0&levelCut=1','&levelIndex=1&levelCut=0','&levelIndex=1&levelCut=1&token=private','&levelIndex=1&levelIndex=1'])assert.throws(()=>referenceCommandURL({commandURL:base+suffix}));
});
