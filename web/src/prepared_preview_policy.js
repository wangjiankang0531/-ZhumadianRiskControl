import {LevelBoundsIndex} from './source_level_index.js';
import {supportsSourcePlans} from './source_descriptor_plan.js';
// Explicit capability of the verified loopback previews, never inferred from
// URL flags or a generic read-only service. Original-data composition preserves
// the same visible-root scheduling policy without claiming to be prepared-only.
export function preparedPreviewCoverageFirst(health){
 if(!supportsSourcePlans(health)||health.nativeReaderEnabled!==false||health.sourceCoveragePolicy!=='prepared_visible_roots_first_v1')return false;
 if(health.scope==='existing_verified_bundles_only')return true;
 const data=health.pythonOriginalSources;
 if(!(health.scope==='verified_prepared_and_explicit_python_original_sources'&&Number.isSafeInteger(health.preparedSourceCount)&&health.preparedSourceCount>=1&&health.preparedSourceCount<=4&&data?.enabled===true&&data.assetWritesEnabled===false&&/^[0-9a-f]{64}$/.test(data.readerIdentity??'')))return false;
 if(Object.hasOwn(data,'tileSelection'))return data.tileSelection==='sealed_index_missing_prepared_v1'&&data.tileCount===2346&&data.preparedFirst===true&&!Object.hasOwn(data,'tiles')&&/^[0-9a-f]{64}$/.test(data.indexIdentity??'')&&/^[0-9a-f]{64}$/.test(data.sourceManifestSHA256??'');
 return Array.isArray(data.tiles)&&data.tiles.length>0&&data.tiles.length<=256&&data.tiles.every(v=>Number.isSafeInteger(v)&&v>=1&&v<=2346)&&new Set(data.tiles).size===data.tiles.length;
}

// A format boundary is available only with the complete pinned original-data
// capability and the same independently loaded LEVEL and source identities.
export function preparedOriginalFormatTransitions(health,index){
 const data=health?.pythonOriginalSources;
 return preparedPreviewCoverageFirst(health)&&data?.tileSelection==='sealed_index_missing_prepared_v1'&&index?.identity===data.indexIdentity&&index?.sourceManifestSHA256===data.sourceManifestSHA256;
}

// Build once from the already loaded, validated base catalog. It is an AABB
// camera-query index, not a fabricated fine-level topology or error metric.
export function createPreparedPreviewRootIndex(catalog){
 if(!Array.isArray(catalog?.root_records)||!catalog.root_records.length)throw Error('Missing prepared root catalog');
 return new LevelBoundsIndex(catalog.root_records.map(r=>({id:r.tile_id,tile:r.tile_id,boundsMin:r.bounds_min,boundsMax:r.bounds_max})));
}
