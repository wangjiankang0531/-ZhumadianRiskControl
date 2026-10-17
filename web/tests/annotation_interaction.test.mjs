import test from 'node:test';
import assert from 'node:assert/strict';
import { matchesFeature, buildHitTarget, pickAnnotation, distanceToSegment, insideRing, ClickGesture } from '../src/annotation_interaction.js';

const layer = { name: '道路与应急区域', visible: true };
const style = { opacity: 1, fillOpacity: 0.25, sizePx: 32, widthPx: 4 };
const feature = (type, id = type, extra = {}) => ({ id, name: '泰山路 Risk Ａ', type, style: { ...style, ...extra } });
const target = (type, points, extra = {}) => buildHitTarget(feature(type, type, extra), layer, points);
const ring = [[0, 0], [100, 0], [100, 100], [0, 100]];
const picked = (items, p) => pickAnnotation(items.filter(Boolean), p)?.feature.id ?? null;

test('search handles Chinese, full-width text, type and AND terms without mutating source', () => {
  const f = feature('point'); const before = JSON.stringify([f, layer]);
  assert.equal(matchesFeature(f, layer, '泰山 ＲＩＳＫ a', 'point'), true);
  assert.equal(matchesFeature(f, layer, '应急区域', 'all'), true);
  assert.equal(matchesFeature(f, layer, '泰山 新乡', 'all'), false);
  assert.equal(matchesFeature(f, layer, '', 'line'), false);
  assert.equal(matchesFeature(f, layer, 'point', 'all'), true);
  assert.equal(JSON.stringify([f, layer]), before);
});

test('point hit size follows marker size and ignores distant clicks', () => {
  assert.equal(picked([target('point', [[50, 50]])], [68, 50]), 'point');
  assert.equal(picked([target('point', [[50, 50]])], [75, 50]), null);
  assert.equal(picked([target('point', [[50, 50]], { sizePx: 64 })], [75, 50]), 'point');
});

test('line hit follows segment endpoints and displayed width', () => {
  const points = [[10, 10], [100, 10]];
  assert.equal(picked([target('line', points)], [50, 15]), 'line');
  assert.equal(picked([target('line', points)], [50, 25]), null);
  assert.equal(picked([target('line', points, { widthPx: 32 })], [50, 25]), 'line');
  assert.equal(picked([target('line', points)], [120, 10]), null);
  assert.equal(distanceToSegment([20, 20], [10, 10], [10, 10]), Math.hypot(10, 10));
});

test('region interior respects fill alpha; zero alpha outline is not independently selectable', () => {
  assert.equal(picked([target('region', ring)], [50, 50]), 'region');
  assert.equal(picked([target('region', ring, { opacity: 0, fillOpacity: 0.2 })], [50, 50]), 'region');
  assert.equal(picked([target('region', ring, { fillOpacity: 0 })], [50, 50]), null);
  assert.equal(picked([target('region', ring, { fillOpacity: 0 })], [2, 50]), 'region');
  assert.equal(target('region', ring, { opacity: 0, fillOpacity: 0 }), null);
});

test('concave polygons do not select the cut-out or depend on vertex winding', () => {
  const concave = [[0, 0], [100, 0], [100, 100], [60, 100], [60, 40], [40, 40], [40, 100], [0, 100]];
  for (const points of [concave, [...concave].reverse()]) {
    assert.equal(insideRing([50, 80], points), false);
    assert.equal(picked([target('region', points)], [50, 80]), null);
    assert.equal(picked([target('region', points)], [50, 20]), 'region');
  }
});

test('unprojected or fully transparent geometry cannot intercept clicks', () => {
  assert.equal(target('point', [null]), null);
  assert.equal(target('line', [[1, 1], null]), null);
  assert.equal(target('point', [[50, 50]], { opacity: 0 }), null);
});

test('visible independent text labels remain selectable when their geometry is transparent or clipped', () => {
  const f = feature('point', 'label-only', { opacity: 0 });
  const t = buildHitTarget(f, layer, [null], [40, 10, 120, 30]);
  assert.equal(picked([t], [80, 20]), 'label-only');
  assert.equal(picked([t], [20, 20]), null);
});

test('point and line hits take precedence over overlapping filled regions; ties respect drawing order', () => {
  const p = target('point', [[50, 50]]), l = target('line', [[0, 50], [100, 50]]), r = target('region', ring);
  assert.equal(picked([p, l, r], [50, 50]), 'point');
  assert.equal(picked([l, r], [80, 50]), 'line');
  const upper = buildHitTarget(feature('point', 'upper'), layer, [[50, 50]]);
  assert.equal(picked([p, upper], [50, 50]), 'upper');
});

const event = (pointerId = 1, x = 20, y = 20, at = 0, extra = {}) => ({ pointerId, clientX: x, clientY: y, timeStamp: at, button: 0, isPrimary: true, ...extra });
test('a brief primary click selects; right click and long press do not', () => {
  const g = new ClickGesture(); g.begin(event()); assert.equal(g.end(event(1, 22, 21, 100)), true);
  g.begin(event(1, 20, 20, 200, { button: 2 })); assert.equal(g.end(event(1, 20, 20, 300)), false);
  g.begin(event(1, 20, 20, 400)); assert.equal(g.end(event(1, 20, 20, 1800)), false);
});

test('dragging away and returning is still a drag', () => {
  const g = new ClickGesture(); g.begin(event()); g.move(event(1, 80, 20, 100));
  assert.equal(g.end(event(1, 20, 20, 200)), false);
});

test('two-pointer zoom and cancelled pointer gestures cannot select', () => {
  const g = new ClickGesture(); g.begin(event()); g.begin(event(2, 40, 40, 10, { isPrimary: false }));
  assert.equal(g.end(event(2, 40, 40, 100)), false); assert.equal(g.end(event(1, 20, 20, 110)), false);
  g.begin(event(1, 20, 20, 200)); g.cancel(event(1)); assert.equal(g.end(event(1, 20, 20, 300)), false);
  g.begin(event(1, 20, 20, 400)); g.cancel(); assert.equal(g.end(event(1, 20, 20, 450)), false);
});
