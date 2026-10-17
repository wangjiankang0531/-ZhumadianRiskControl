import test from 'node:test';
import assert from 'node:assert/strict';
import {LayerLoading} from '../src/layer_loading.js';
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return{promise,resolve,reject}};
test('a late default fetch cannot overwrite a manually opened layer file',async()=>{
  const loader=new LayerLoading(),defaultRead=deferred();let current='previous';
  const pending=loader.load(()=>defaultRead.promise,value=>current=value);
  assert.equal(await loader.load(async()=>'manual',value=>current=value),true);
  defaultRead.resolve('default');assert.equal(await pending,false);assert.equal(current,'manual');
});
test('two file reads finishing out of order preserve the latest user choice',async()=>{
  const loader=new LayerLoading(),first=deferred(),second=deferred();let current='previous';
  const a=loader.load(()=>first.promise,value=>current=value),b=loader.load(()=>second.promise,value=>current=value);
  second.resolve('second');await b;first.resolve('first');assert.equal(await a,false);assert.equal(current,'second');
});
test('a validation error retains the last adopted document and is surfaced',async()=>{
  const loader=new LayerLoading();let current={id:'valid'};const before=current;
  await assert.rejects(loader.load(async()=>({id:'invalid'}),()=>{throw Error('图层格式无效')}),/格式无效/);
  assert.equal(current,before);
});
test('an obsolete failed fetch does not report a misleading error over a successful file load',async()=>{
  const loader=new LayerLoading(),first=deferred();let current='previous';
  const pending=loader.load(()=>first.promise,value=>current=value);
  await loader.load(async()=>'manual',value=>current=value);first.reject(Error('network'));assert.equal(await pending,false);assert.equal(current,'manual');
});
test('failed newest reads preserve current state and cancel older pending replacements',async()=>{
  const loader=new LayerLoading(),first=deferred();let current='saved';
  const pending=loader.load(()=>first.promise,value=>current=value);
  await assert.rejects(loader.load(async()=>{throw Error('bad JSON')},value=>current=value),/bad JSON/);
  first.resolve('older');assert.equal(await pending,false);assert.equal(current,'saved');
});
