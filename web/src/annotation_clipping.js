// Clip overlay geometry before perspective division. This never changes saved coordinates.
const finitePoint = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
const samePoint = (a, b) => Math.abs(a[0] - b[0]) <= 1e-7 && Math.abs(a[1] - b[1]) <= 1e-7;
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const distance = (v, plane) => v[0] * plane[0] + v[1] * plane[1] + v[2] * plane[2] + v[3] * plane[3];
const planesFor = (width, height, padding) => [[1, 0, 0, 1 + 2 * padding / width], [-1, 0, 0, 1 + 2 * padding / width],
  [0, 1, 0, 1 + 2 * padding / height], [0, -1, 0, 1 + 2 * padding / height], [0, 0, 1, 1], [0, 0, -1, 1]];

function segment(a, b, planes) {
  let low = 0, high = 1;
  for (const plane of planes) {
    const da = distance(a, plane), db = distance(b, plane);
    if (da < 0 && db < 0) return null;
    if (da < 0) low = Math.max(low, da / (da - db));
    else if (db < 0) high = Math.min(high, da / (da - db));
    if (low > high) return null;
  }
  return [mix(a, b, low), mix(a, b, high)];
}
function polygon(points, planes) {
  let ring = points;
  for (const plane of planes) {
    const next = [];
    if (!ring.length) break;
    let previous = ring.at(-1), previousDistance = distance(previous, plane);
    for (const current of ring) {
      const currentDistance = distance(current, plane);
      if ((previousDistance >= 0) !== (currentDistance >= 0))
        next.push(mix(previous, current, previousDistance / (previousDistance - currentDistance)));
      if (currentDistance >= 0) next.push(current);
      previous = current; previousDistance = currentDistance;
    }
    ring = next;
  }
  return ring;
}
function compact(points) {
  const result = [];
  for (const p of points) if (!result.length || !samePoint(result.at(-1), p)) result.push(p);
  if (result.length > 1 && samePoint(result[0], result.at(-1))) result.pop();
  return result;
}

export function clipAnnotationGeometry(type, positions, matrix, width, height, paddingPx = 0) {
  if (!['line', 'region'].includes(type) || !Array.isArray(positions) || positions.length < (type === 'line' ? 2 : 3) ||
      !positions.every(finitePoint) || !matrix || matrix.length !== 16 || !Array.from(matrix).every(Number.isFinite) ||
      !Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0 ||
      !Number.isFinite(paddingPx) || paddingPx < 0 || paddingPx > 128)
    throw new TypeError('Invalid annotation clipping input');
  const transformed = positions.map(([x, y, z]) => [matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
    matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
    matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14],
    matrix[3] * x + matrix[7] * y + matrix[11] * z + matrix[15]]);
  if (!transformed.every(v => v.every(Number.isFinite))) throw new TypeError('Non-finite annotation projection');
  const project = (v, padding) => {
    if (v[3] <= 0) return null;
    const p = [(v[0] / v[3] + 1) * width / 2, (1 - v[1] / v[3]) * height / 2];
    return p.every(Number.isFinite) ? [Math.max(-padding, Math.min(width + padding, p[0])),
      Math.max(-padding, Math.min(height + padding, p[1]))] : null;
  };
  const strokePaths = [], planes = planesFor(width, height, paddingPx);
  let current = null;
  for (let i = 0, n = type === 'region' ? transformed.length : transformed.length - 1; i < n; i++) {
    const part = segment(transformed[i], transformed[(i + 1) % transformed.length], planes);
    const points = part?.map(v => project(v, paddingPx));
    if (!points || points.some(p => !p) || samePoint(points[0], points[1])) { current = null; continue; }
    if (current && samePoint(current.at(-1), points[0])) current.push(points[1]);
    else { current = points; strokePaths.push(current); }
  }
  // Join only truly adjacent original edges across a region's starting vertex.
  if (type === 'region' && strokePaths.length > 1 && samePoint(strokePaths.at(-1).at(-1), strokePaths[0][0])) {
    const tail = strokePaths.pop(); strokePaths[0] = [...tail, ...strokePaths[0].slice(1)];
  }
  const fillRings = [];
  if (type === 'region') {
    const projected = polygon(transformed, planesFor(width, height, 0)).map(v => project(v, 0));
    if (projected.every(Boolean)) {
      const ring = compact(projected);
      const twiceArea = ring.reduce((area, p, i) => { const q = ring[(i + 1) % ring.length]; return area + p[0] * q[1] - q[0] * p[1]; }, 0);
      if (ring.length >= 3 && Math.abs(twiceArea) > 1e-8) fillRings.push(ring);
    }
  }
  return {strokePaths, fillRings};
}

export function traceAnnotationPaths(ctx, paths, close = false) {
  for (const points of paths) {
    if (!points.length) continue;
    ctx.moveTo(...points[0]);
    const closed = close && points.length > 2 && samePoint(points[0], points.at(-1));
    for (let i = 1; i < points.length - Number(closed); i++) ctx.lineTo(...points[i]);
    if (closed) ctx.closePath();
  }
}
