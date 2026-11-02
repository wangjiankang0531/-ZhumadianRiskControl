import {businessSearchText} from './business_binding.js';
// Screen-space interaction for the annotation overlay. Geometry stays in local metres.
export const featureTypeNames = { point: '点', line: '线', region: '区域' };

export function matchesFeature(feature, layer, query = '', type = 'all', extraText = '') {
  if (type !== 'all' && feature.type !== type) return false;
  const normal = value => String(value ?? '').normalize('NFKC').toLocaleLowerCase('zh-CN');
  const haystack = [feature.name, feature.id, featureTypeNames[feature.type], layer.name, businessSearchText(feature), extraText].map(normal).join(' ');
  return normal(query).trim().split(/\s+/u).filter(Boolean).every(word => haystack.includes(word));
}

export function distanceToSegment(point, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const lengthSquared = dx * dx + dy * dy;
  const t = lengthSquared ? Math.max(0, Math.min(1,
    ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / lengthSquared)) : 0;
  return Math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy);
}

export function insideRing(point, points) {
  let inside = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const a = points[i], b = points[j];
    if ((a[1] > point[1]) !== (b[1] > point[1]) &&
        point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}

const insideBox = (point, box) => box && point[0] >= box[0] && point[0] <= box[2] &&
  point[1] >= box[1] && point[1] <= box[3];

const finiteScreenPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const validPath = (path, minimum) => Array.isArray(path) && path.length >= minimum && path.every(finiteScreenPoint);
export function buildHitTarget(feature, layer, points, labelBox = null, geometry = null) {
  const complete = points.length > 0 && points.every(finiteScreenPoint);
  const strokePaths = feature.type === 'point' ? [] : geometry ?
    (geometry.strokePaths ?? []).filter(path => validPath(path, 2)) : complete ?
      [feature.type === 'region' ? [...points, points[0]] : points] : [];
  const fillRings = feature.type !== 'region' ? [] : geometry ?
    (geometry.fillRings ?? []).filter(path => validPath(path, 3)) : complete ? [points] : [];
  const body = (feature.type === 'point' ? complete : strokePaths.length > 0) && feature.style.opacity > 0;
  const fill = fillRings.length > 0 && feature.style.fillOpacity > 0;
  if (!body && !fill && !labelBox) return null;
  const tolerance = feature.type === 'point' ? feature.style.sizePx / 2 + 4 : Math.max(6, feature.style.widthPx / 2 + 4);
  const visible = [...(body ? feature.type === 'point' ? points : strokePaths.flat() : []), ...(fill ? fillRings.flat() : [])];
  let bounds = visible.length ? [Infinity, Infinity, -Infinity, -Infinity] : [...labelBox];
  for (const p of visible) {
    bounds[0] = Math.min(bounds[0], p[0] - tolerance);
    bounds[1] = Math.min(bounds[1], p[1] - tolerance);
    bounds[2] = Math.max(bounds[2], p[0] + tolerance);
    bounds[3] = Math.max(bounds[3], p[1] + tolerance);
  }
  if (labelBox) bounds = [Math.min(bounds[0], labelBox[0]), Math.min(bounds[1], labelBox[1]),
    Math.max(bounds[2], labelBox[2]), Math.max(bounds[3], labelBox[3])];
  const segments = strokePaths.flatMap(path => path.slice(1).map((p, i) => [path[i], p]));
  return { feature, layer, points, body, fill, labelBox, bounds, tolerance, segments, fillRings };
}

export function pickAnnotation(targets, point) {
  let winner = null, priority = 0;
  // Prefer small point/line targets over region interiors. Ties use the drawn order.
  for (let i = targets.length - 1; i >= 0; i--) {
    const target = targets[i];
    if (!insideBox(point, target.bounds)) continue;
    let hit = insideBox(point, target.labelBox) ? 4 : 0;
    const p = target.points;
    if (target.body && target.feature.type === 'point' &&
        Math.abs(point[0] - p[0][0]) <= target.tolerance &&
        Math.abs(point[1] - p[0][1]) <= target.tolerance) hit = Math.max(hit, 3);
    else if (target.body && target.feature.type !== 'point') {
      for (const [a, b] of target.segments) {
        if (distanceToSegment(point, a, b) <= target.tolerance) {
          hit = Math.max(hit, 2);
          break;
        }
      }
    }
    if (target.fill && target.fillRings.some(ring => insideRing(point, ring))) hit = Math.max(hit, 1);
    if (hit > priority) { winner = target; priority = hit; }
    if (priority === 4) break;
  }
  return winner;
}

export class ClickGesture {
  constructor() { this.active = new Set(); this.stroke = null; }
  begin(event) {
    this.active.add(event.pointerId);
    if (this.active.size !== 1) { this.stroke = null; return; }
    this.stroke = event.button === 0 && event.isPrimary ? {
      id: event.pointerId, x: event.clientX, y: event.clientY, at: event.timeStamp, moved: false,
    } : null;
  }
  move(event) {
    if (this.stroke?.id === event.pointerId &&
        Math.hypot(event.clientX - this.stroke.x, event.clientY - this.stroke.y) > 5) this.stroke.moved = true;
  }
  end(event) {
    this.move(event);
    const stroke = this.stroke;
    const click = stroke?.id === event.pointerId && !stroke.moved && this.active.size === 1 &&
      event.timeStamp - stroke.at <= 1000;
    this.active.delete(event.pointerId);
    if (stroke?.id === event.pointerId) this.stroke = null;
    return Boolean(click);
  }
  cancel(event) {
    if (event) this.active.delete(event.pointerId);
    else this.active.clear();
    this.stroke = null;
  }
}
