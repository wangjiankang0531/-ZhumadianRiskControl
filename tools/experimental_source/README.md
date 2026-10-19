# Reproducible read-only landscape experiments

These overlays retain the exact source bytes used for the tested Windows candidates without merging the older asset/cache/BC7 investigation changes in the working tree. They contain source code only. They do not include GIS, enterprise records, DLG, images, DLLs, executables, databases, credentials, or deployment selections.

## Materialize committed source

From the application repository, use a fresh output directory:

```powershell
python tools/materialize_experimental_source.py --overlay=native_readonly_depth --output=work/review_native_depth
python tools/materialize_experimental_source.py --overlay=osgb_readonly_roi --output=work/review_osgb_roi
```

The tool reads committed Git blobs, validates every baseline SHA, checks patch paths, applies the overlay in an isolated temporary source tree, restores the tested line-ending recipe, and validates every output SHA. It refuses an existing output or a destination outside project `work/`. It never modifies the working tree or scene assets, builds/runs software, starts a service, or changes a release. Scratch sources remain available for diagnosis. A future changed native baseline must be selected explicitly with a matching `--base-ref`; byte mismatches are refused.

## Native read-only source/depth overlay

`native_readonly_depth` materializes the native editor and its complete source-page adapter. It consumes SHA-pinned original-image pages and complete source-family leases from a read-only loopback source service (default port 8828; validated numeric `ZMD_SOURCE_MEMORY_PORT` override). The candidate chunk decoder has no legacy asset conversion fallback. Original position/UV/index/pixel data, source samplers, complete cuts and the existing 512/384/32 MiB ledger limits are checked. The ordinary source service implementation is in `readonly_source_memory_store.py` and `source_memory_http.py`.

The actual scene and source-ID pass both use reversed floating depth, `z' = w-z`, Greater comparison and zero clear. The old X/Y/W rows and clipping interval are preserved. Annotation and picking rays retain the same physical camera. This is a rendering precision change, not a relaxed identity gate. Two recorded static views each passed 25 independent original-triangle rays and 25 GPU source/depth samples. The original two-cycle, sixteen-station native traversal also passed with depth six and exact far-end resource return. Earlier failed candidates remain recorded privately.

This is a Windows experiment, still dependent on a separately configured local read-only source service and local assets. It is not a standalone portable package, default release, whole-area or Linux acceptance. Build it using the application's native CMake target and the matching engine source/libraries (including the text-label module); materialization itself does not configure those build dependencies. The live development integration remains isolated from older held experiments.

## Bounded original-pixel ROI overlay

`osgb_readonly_roi` materializes the independent reader source and CMake file. Existing four-argument full-image behavior keeps its 32 MiB image limit. Two explicit additional modes use separate frame identities:

* `--geometry-only`: `ZMDGEO01`, `zhumadian.osgb.geometry.v1`; original triangle geometry and UV with image dimensions, no pixel arrays.
* `--crop=image,x,y,width,height`: `ZMDROI01`, `zhumadian.osgb.rgba_crop.v1`; only the requested original RGBA rectangle, at most 32 MiB. Coordinates and image IDs are bounded, source row order is retained, and pixels are never resampled.

The stream reader keeps external-read and all-write callbacks denied. Source paths, private plugin identity and caller source hashes still need to be pinned by the host. The CMake options are the same `ZMD_OSG_SOURCE`, `ZMD_OSG_BUILD`, and `ZMD_JSON_INCLUDE` inputs documented for the base reader.

Six real crop pages were checked byte-for-byte against independent original JPEG decoding, with zero changed RGBA bytes; the geometry plan retained all original triangles and UV and kept every physical page below 32 MiB including the native vertex/index/full-mip cost. Five invalid crop requests were refused. A one-off earlier shared-file start failure and an initially incomplete diagnostic were retained; they do not establish an antivirus cause. The corrected audit records every process result. Crop scene material/UV-transform integration and GPU acceptance are still pending, so this overlay alone does not fix large-image scene loading.


## Original-pixel crop scene overlay (experimental)

`native_readonly_crop` materializes the isolated native editor with the same reverse-depth fix and explicit `osgb_memory_png_crop_v2` consumption (default loopback 8829). Its original vertex position/UV arrays are retained. Crop offsets/scales travel as versioned material parameters; a source requiring periodic seam padding or mipmapped crop gutters is refused. The renderer validates actual texture mip counts immediately after allocation. Non-mip source filters allocate only level zero; geometry and those actual image bytes share the unchanged page/root/global limits.

The Python `osgb_cropped_pages.py` reader pins the ROI executable/plugins and source catalog, preserves complete source ownership, builds lossless PNG pages in RAM and never invokes the legacy asset producer. The WEB adapter validates crop bounds, UV transforms, sampler, actual mip policy and immutable restoration identity before whole-family commit. Existing v1 pages keep their own format and full-mip allocation contract. No database schema changes are involved.

Four original large-image sibling nodes were checked triangle-by-triangle and pixel-by-pixel, then all six pages were independently matched against the native CPU decoder. A real browser showed the complete previously blocked child family. The new native two-cycle traversal and original-geometry/GPU static checks are still in progress at the time of this source snapshot; this overlay is not a default or notebook release. Three separate read-only source requests also recorded Windows shared-file start failures and were retained without automatic retry; their cause has not been established. Old security-held binaries and asset writers are not part of this runtime.
