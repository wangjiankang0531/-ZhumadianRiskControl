import test from 'node:test';import assert from 'node:assert/strict';
import {StaticUploadScheduler} from '../src/static_upload_scheduler.js';
import {uploadStaticGeometry} from '../src/static_geometry_upload.js';
import {BufferGeometry,BufferAttribute} from 'three';
test('tasks finish without any animation frame and preserve a task boundary for both upload jobs',async()=>{
 const tasks=[];let now=0;const s=new StaticUploadScheduler({postTask:(f,options)=>{assert.equal(options.priority,'user-visible');tasks.push(f);return Promise.resolve();},requestFrame:()=>{throw Error('frame must not be requested');},clock:()=>now});
 let done=0;const a=s.wait().then(()=>done++),b=s.wait().then(()=>done++);assert.equal(done,0);assert.equal(s.snapshot().pending,2);await assert.rejects(s.wait(),/concurrency/);
 now=8;tasks.shift()();await a;assert.equal(done,1);now=12;tasks.shift()();await b;assert.equal(done,2);assert.equal(s.snapshot().totalWaitMs,20);assert.equal(s.snapshot().maxWaitMs,12);s.dispose();
});
test('fallback channel completes independently of RAF, ignores stale messages and closes both ports',async()=>{
 const posted=[];let closed=0;const channel={port1:{onmessage:null,close(){closed++;}},port2:{postMessage(id){posted.push(id);},close(){closed++;}}};
 const s=new StaticUploadScheduler({postTask:null,createChannel:()=>channel,requestFrame:()=>{throw Error('no frame');}});const pending=s.wait();channel.port1.onmessage({data:posted.shift()});await pending;channel.port1.onmessage({data:1});assert.equal(s.snapshot().completed,1);s.dispose();s.dispose();assert.equal(closed,2);assert.equal(s.snapshot().backend,'messageChannel');
});
test('dispose rejects both pending jobs and late task completion cannot resume upload',async()=>{
 const callbacks=[];const s=new StaticUploadScheduler({postTask:f=>{callbacks.push(f);return Promise.resolve();}});let resumed=0;const promises=[s.wait().then(()=>resumed++),s.wait().then(()=>resumed++)];const all=Promise.allSettled(promises);s.dispose();assert.ok((await all).every(x=>x.status==='rejected'));callbacks.forEach(f=>f());assert.equal(resumed,0);assert.equal(s.snapshot().cancelled,2);assert.equal(s.snapshot().pending,0);await assert.rejects(s.wait(),/closed/);
});
test('a rejected or synchronously failing browser task rejects its waiter without retaining it',async()=>{
 for(const postTask of [()=>Promise.reject(Error('queue rejected')),()=>{throw Error('queue rejected');}]){const s=new StaticUploadScheduler({postTask});await assert.rejects(s.wait(),/queue rejected/);assert.equal(s.snapshot().pending,0);assert.equal(s.snapshot().failed,1);s.dispose();}
});
test('explicit frame control and legacy fallback cancel outstanding RAF handles',async()=>{
 for(const mode of ['frame','task']){const cancelled=[];const s=new StaticUploadScheduler({mode,postTask:null,createChannel:null,requestFrame:()=>37,cancelFrame:id=>cancelled.push(id)});const pending=s.wait();const checked=assert.rejects(pending,/closed/);s.dispose();await checked;assert.deepEqual(cancelled,[37]);assert.equal(s.snapshot().backend,'animationFrame');}
 assert.throws(()=>new StaticUploadScheduler({mode:'invalid'}),/Invalid/);assert.throws(()=>new StaticUploadScheduler({postTask:null,createChannel:null,requestFrame:null}),/unavailable/);
});
test('closing the scheduler while geometry yields releases owned GL buffers without installing attributes',async()=>{
 const geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(new Float32Array([0,0,0,1,1,1]),3));geometry.setIndex(new BufferAttribute(new Uint32Array([0,1,0]),1));const original=geometry.attributes.position;let allocated=0,deleted=0;
 const gl={COPY_WRITE_BUFFER:1,COPY_WRITE_BUFFER_BINDING:2,FLOAT:3,UNSIGNED_INT:4,STATIC_DRAW:5,NO_ERROR:0,getParameter:()=>null,bindBuffer(){},createBuffer(){allocated++;return {};},deleteBuffer(){deleted++;},bufferData(){},getError:()=>0};
 const s=new StaticUploadScheduler({postTask:()=>Promise.resolve()});const upload=uploadStaticGeometry({geometry,gl,yieldFrame:()=>s.wait()});s.dispose();await assert.rejects(upload,/closed/);assert.equal(allocated,1);assert.equal(deleted,1);assert.equal(geometry.attributes.position,original);
});
