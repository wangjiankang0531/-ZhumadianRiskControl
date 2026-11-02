import test from 'node:test';import assert from 'node:assert/strict';
import {completionBeforeRefinement} from '../src/source_completion_schedule.js';
const root=(id,score=1)=>({kind:'root',id,score}),family=(id,score=1)=>({kind:'family',id,score});
test('sampled visible missing roots finish before another full-view observation',()=>{assert.equal(completionBeforeRefinement([root(1),family(2)],()=>false),false);});
test('before refining covered roots, sparse-missed coverage is observed first',()=>{assert.equal(completionBeforeRefinement([family(1)],()=>true),true);});
test('root upgrades already resident do not conceal the remaining coverage opportunity',()=>{assert.equal(completionBeforeRefinement([root(1),family(2)],()=>true),true);});
test('zero-gain roots never starve the coverage observation',()=>{assert.equal(completionBeforeRefinement([root(1,0),family(2)],()=>false),true);});
test('no detail winner uses the established idle observation path instead',()=>{for(const candidates of [[],[root(1)],[family(1,0)]])assert.equal(completionBeforeRefinement(candidates,()=>true),false);});
test('input validation refuses invalid priorities, kinds, bounds and async root state',()=>{for(const c of [root(0),root(2347),root(1,NaN),root(1,-1),{...root(1),kind:'unknown'}])assert.throws(()=>completionBeforeRefinement([c],()=>true));assert.throws(()=>completionBeforeRefinement([root(1)],async()=>false));assert.throws(()=>completionBeforeRefinement(null,()=>true));assert.throws(()=>completionBeforeRefinement(Array(16385).fill(root(1)),()=>true));});
