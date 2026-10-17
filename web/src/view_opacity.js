// Browsing controls do not rewrite the editor's DLG document.
export function opacityFromTransparency(percent) {
  const value = Number(percent);
  if (!Number.isFinite(value) || value < 0 || value > 100) throw new RangeError('透明度必须为 0–100%');
  return 1 - value / 100;
}
export function annotationWithOpacity(feature, opacity) {
  if (opacity === 1) return feature;
  return {...feature, style: {...feature.style,
    opacity: feature.style.opacity * opacity,
    fillOpacity: feature.style.fillOpacity * opacity},
    ...(feature.label ? {label: {...feature.label, opacity: feature.label.opacity * opacity}} : {})};
}
export function applyModelOpacity(group, opacity, visible = true) {
  group.visible = visible && opacity > 0;
  group.traverse(node => {
    if (!node.isMesh) return;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      if (!material) continue;
      const transparent = opacity < 1;
      if (material.transparent !== transparent) material.needsUpdate = true;
      material.opacity = opacity;
      material.transparent = transparent;
      material.depthWrite = !transparent;
    }
  });
}
