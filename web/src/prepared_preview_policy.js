import {LevelBoundsIndex} from './source_level_index.js';
import {supportsSourcePlans} from './source_descriptor_plan.js';
// Opt-in capability of the loopback prepared-only service, never inferred from
// URL flags, unrelated servers, or a generic read-only source service.
export function preparedPreviewCoverageFirst(health){
 return supportsSourcePlans(health)&&health.nativeReaderEnabled===false&&health.scope==='existing_verified_bundles_only'&&health.sourceCoveragePolicy==='prepared_visible_roots_first_v1';
}

// Build once from the already loaded, validated base catalog. It is an AABB
// camera-query index, not a fabricated fine-level topology or error metric.
export function createPreparedPreviewRootIndex(catalog){
 if(!Array.isArray(catalog?.root_records)||!catalog.root_records.length)throw Error('Missing prepared root catalog');
 return new LevelBoundsIndex(catalog.root_records.map(r=>({id:r.tile_id,tile:r.tile_id,boundsMin:r.bounds_min,boundsMax:r.bounds_max})));
}
