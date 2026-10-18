import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseRefinementCandidate as choose} from '../src/source_allocation.js';
const c=(key,score,cost)=>({key,score,cost});
test('metadata costs are learned before committing a known GPU allocation',()=>{const known=c('root/a',30,30),unknown=c('family/b',2,null);assert.equal(choose([known,unknown]),unknown);assert.equal(choose([known,{...unknown,cost:10}]),known);});
test('budget efficiency can beat larger absolute gain without changing bytes or gains',()=>{const large=c('root/a',30,30),efficient=c('family/b',20,10);assert.equal(choose([large,efficient]),efficient);assert.deepEqual(large,c('root/a',30,30));});
test('a measured child residual can yield to another candidate before GPU upload',()=>{const upper=c('family/a',30,10),other=c('root/b',20,10);assert.equal(choose([upper,other]),upper);assert.equal(choose([{...upper,score:5},other]),other);});
test('zero visible benefit never triggers metadata or allocation',()=>{assert.equal(choose([c('a',0,null),c('b',0,5)]),null);});
test('tie order is stable across root and family enumeration order',()=>{const a=c('family/a',4,2),b=c('root/b',8,4),d=c('family/d',8,4);assert.equal(choose([a,b,d]),d);assert.equal(choose([d,a,b]),d);});
test('unknown cost selection is deterministic and visible gain ordered',()=>{const a=c('a',2,null),b=c('b',3,null);assert.equal(choose([a,b]),b);assert.equal(choose([b,a]),b);});
test('invalid or duplicate candidates cannot silently undervalue resources',()=>{for(const value of [c('a',1,0),c('a',1,-1),c('a',1,Infinity),c('a',1,1.5),c('a',NaN,1),c('',1,1)])assert.throws(()=>choose([value]));assert.throws(()=>choose([c('a',1,2),c('a',2,3)]));});

test('lazy metadata and upper-bound refinement selects the same winner as exhaustive actual gain per byte',()=>{
 let seed=71237;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/2**32;};
 for(let trial=0;trial<80;trial++){
  const truth=Array.from({length:24},(_,i)=>{const score=random()*4;return c('candidate/'+i,score,1+Math.floor(random()*1000000));});
  const pending=truth.map(t=>({...t,score:t.score+random()*3,cost:null,measured:false}));let winner=null,steps=0;
  while(steps++<=pending.length*2+1){const best=choose(pending);if(!best)break;const actual=truth.find(t=>t.key===best.key);if(best.cost===null){best.cost=actual.cost;continue;}if(!best.measured){best.score=actual.score;best.measured=true;continue;}winner=best;break;}
  assert.ok(steps<=pending.length*2+1);assert.equal(winner?.key,choose(truth)?.key);
 }
});
