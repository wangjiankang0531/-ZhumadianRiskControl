import test from 'node:test';
import assert from 'node:assert/strict';
import {SourceRefinementTurns,chooseFeasibleSourceCandidate,SourceAllocationScan} from '../src/source_allocation.js';
const texture={key:'texture',kind:'family',id:1,score:.1,cost:10,textureScore:.1};
const geometry={key:'geometry',kind:'family',id:2,score:10,cost:10,textureScore:0};
const choose=(turns,candidates=[texture,geometry],feasible=()=>true)=>chooseFeasibleSourceCandidate(candidates,{indexed:true,hasRoot:()=>true,textureFirst:turns.textureFirst,feasible});

test('alternating refinement opportunities advance only after successful family commit',()=>{
 const turns=new SourceRefinementTurns({mode:'alternating'});
 for(let i=0;i<20;i++){assert.equal(choose(turns),texture);assert.equal(turns.snapshot().familyCommits,0);}
 turns.committedFamily();assert.equal(choose(turns),geometry);assert.deepEqual(turns.snapshot(),{mode:'alternating',familyCommits:1,textureFirst:false});
 turns.committedFamily();assert.equal(choose(turns),texture);assert.equal(turns.snapshot().familyCommits,2);
});

test('legacy disabled and hard texture modes keep their exact selection across commits',()=>{
 for(const [mode,expected] of [['disabled',geometry],['always',texture]]){const turns=new SourceRefinementTurns({mode});for(let i=0;i<4;i++){assert.equal(choose(turns),expected);turns.committedFamily();}}
 assert.equal(new SourceRefinementTurns().textureFirst,false);for(const mode of ['alternate',null,1])assert.throws(()=>new SourceRefinementTurns({mode}));
});

test('unseeded root coverage precedes either refinement opportunity without consuming a turn',()=>{
 const turns=new SourceRefinementTurns({mode:'alternating'}),root={key:'root',kind:'root',id:3,score:.001,cost:1000};
 for(let i=0;i<2;i++){assert.equal(chooseFeasibleSourceCandidate([texture,geometry,root],{indexed:true,hasRoot:id=>id!==3,textureFirst:turns.textureFirst,feasible:()=>true}),root);assert.equal(turns.snapshot().familyCommits,i);turns.committedFamily();}
});

test('infeasible texture or metadata-only selection cannot advance fairness state',()=>{
 const turns=new SourceRefinementTurns({mode:'alternating'});assert.equal(choose(turns,[texture,geometry],c=>c!==texture),geometry);assert.equal(turns.textureFirst,true);
 const unknown={...texture,cost:null};assert.equal(choose(turns,[unknown,geometry],()=>{throw Error('metadata may not allocate');}),unknown);assert.equal(turns.snapshot().familyCommits,0);
 const snapshot=turns.snapshot();snapshot.familyCommits=99;snapshot.textureFirst=false;assert.equal(turns.textureFirst,true);assert.equal(turns.snapshot().familyCommits,0);
});

test('time-sliced probe cancellation preserves the same next refinement opportunity',()=>{
 const turns=new SourceRefinementTurns({mode:'alternating'});let now=0;const scan=new SourceAllocationScan([texture,geometry],{indexed:true,hasRoot:()=>true,textureFirst:turns.textureFirst,feasible:()=>{now+=5;return false;}});
 assert.equal(scan.step({budgetMs:4,clock:()=>now}).done,false);assert.equal(scan.step({clock:()=>now,isCurrent:()=>false}).cancelled,true);assert.equal(turns.textureFirst,true);assert.equal(turns.snapshot().familyCommits,0);
});
