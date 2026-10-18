import test from 'node:test';
import assert from 'node:assert/strict';
import {chinaInput,workSummary} from '../src/reference-work-form.js';
test('China time survives UTC storage and switching types without double conversion',()=>{assert.equal(chinaInput('2026-10-18T01:00:00+00:00'),'2026-10-18T09:00');assert.equal(chinaInput('2026-10-18T09:00'),'2026-10-18T09:00');assert.equal(chinaInput(''),'');});
test('details show actual saved values and role members',()=>{const rows=workSummary({jobType:'动火作业',values:{动火方式:'模拟焊接',备注:''},people:{作业人员:[{姓名:'模拟甲',工种:'模拟检修'}],基层单位监护人:[]}});assert.deepEqual(rows,[['作业类型','动火作业'],['动火方式','模拟焊接'],['作业人员','模拟甲 / 模拟检修'],['基层单位监护人','未添加']]);});
