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

Four original large-image sibling nodes were checked triangle-by-triangle and pixel-by-pixel, then all six pages were independently matched against the native CPU decoder. A real browser showed the complete previously blocked child family. The integrated owned-worker variant passed the original two-cycle traversal and three independent original-geometry/GPU static views. This overlay is not a default or notebook release. Earlier per-node process creation runs recorded shared-file start failures and remain preserved; the exact external cause has not been established. Old security-held binaries and asset writers are not part of this runtime.


## Owned read-only stdio source worker (experimental)

`osgb_readonly_stdio` materializes the independently built reader used by `osgb_stdio_worker.py`. It retains the original read-only full-image, geometry-only and bounded ROI modes and adds a fixed-root `--stdio-worker-v1` session. Bounded requests are serialized through one private child process; protocol errors and source refusals are explicit. The Python host pins the complete runtime and source identities, verifies the handshake, applies a Windows Job Object kill-on-close policy, bounds frames and stderr, and never automatically restarts a failed worker. Each request clears its private OSG object cache. It does not write scene assets or invoke the older held asset producer.

One actual worker decoded all twelve sources that had previously failed during per-node process creation, then forty repeated frames matched and five invalid crop/mode requests were refused. The owner-exit fixture left no child process. Those checks address the process lifecycle and original-source identity; they do not establish an antivirus cause or whole-scene acceptance. The integrated worker subsequently passed the original two-cycle, sixteen-station native traversal with no decode errors, unchanged depth-six and 512/384/32 MiB gates, and exact far-end resource return. Three static views passed 75 independent original-triangle rays and 75 GPU source/depth probes, including the previously oversized source family. Browser interaction and portable/notebook acceptance remain separate gates. The previous failed runs and their caches remain preserved. This Windows implementation is not a default, notebook or Linux release. No SQL schema changes are involved.


## Relocatable source service candidate

`portable_source_runtime.py` verifies an exact bounded payload manifest, private reader DLL identities, the packaged Python/Pillow codec and an explicit installed original-Data binding before starting a loopback-only service. A unique owner launch file records readiness and shutdown; only the matching local owner can request shutdown. The source worker remains serial, bounded and owned. Code, runtime, base resources and original Data are protected against Python writes. User DLG initializes once from a merged enterprise/road snapshot and subsequent user edits are retained. The server reads that workspace without rewriting it. Database schemas and business ownership are unchanged.

`build_portable_source_package.py` assembles a fresh candidate beneath project work/, verifies copied bytes, includes private CRT dependencies and selected notices, and refuses DLG coordinate or identity conflicts. It reuses an explicitly bound installed GIS directory instead of copying it. Eighteen package/lifecycle/merge tests passed. A private-runtime case and a separate diagnostic in a relocated Unicode/space directory delivered eighteen identical payload files and six identical native-decoded pages; owner shutdown left no source worker. One earlier relocated native invocation exited without captured diagnostics; its failed run is retained and its cause is unresolved. Later help/DLG/CPU diagnostics succeeded and do not erase that failure.

This is a service/relocation experiment. The service assembly alone does not prove native ownership; the separate native-owned overlay below adds that behavior. Independent interactive/GPU/notebook acceptance remains pending. Do not describe this assembly or the successful CPU diagnostic as a standalone editor release. No GIS, user DLG, business records, binaries or deployment bindings are included in these committed sources.


## Native-owned packaged source runtime (experimental)

`native_owned_runtime` materializes the original-pixel crop/reversed-depth editor together with its packaged-runtime owner. Package discovery uses the executable's Unicode path; packaged resource resolution stays beneath `resources/`. Before starting the pinned private Python interpreter, the native host checks declared file identities, creates a kill-on-close Job Object, restricts inherited handles, creates the child suspended, assigns it to that job, and resumes it. It validates a unique launch/PID/package identity and loopback HTTP status before supplying the actual ephemeral port to the decoder. There is no automatic process restart or asset-generation fallback. An explicitly configured external development service is left running.

Actual native CPU cases started and stopped the service without any pre-started development process, decoded the same six original family pages with matching geometry/UV/index/pixel identities, and retained user-edited DLG after copying the package into a Unicode/space directory. Damaged declared code and a missing local Data binding were refused. Terminating a native owner while its source reader was alive left neither service nor reader alive. A first external-service observer used a nonexistent audit URL; that harness failure remains recorded and the existing service was independently verified using its actual read-only endpoint.

The package still needs independent GPU traversal/static acceptance, interactive DLG save/reopen and the existing SQLite publishing connection, followed by notebook deployment and the public-portal/local-scene handoff. The source overlay itself neither packages local GIS/business/DLG data nor changes a default release. Earlier unrelated security-held asset writers are not included. The editor now enables visible-area LOD by default; source-consuming startup refuses a missing package and pre-child failures have their own journal phase. The default-enabled candidate passed the original two-cycle traversal without a command-line visibility override; its own three static original-triangle/GPU checks also passed. Native window/docking and business-binding UI probes passed in a separate SQLite-enabled package; arbitrary project Save As/publication and notebook acceptance remain separate.


## SQLite publication of portable editor layers

`portable_layer_workspace.py` binds the portable runtime to a new `UserData/BusinessData/layers.sqlite` using the existing schema/repository, tenant and document version contract. Reloading the editor workspace publishes its exact saved bytes and materialized layer/feature rows with compare-and-swap revisions. Unknown/older schemas and linked or wrong-kind paths are refused before the normal repository constructor can upgrade or repair them. A partial or invalid editor save returns an explicit error and retains the last valid database snapshot. No original GIS, code or default DLG is rewritten by the service. Source read-only status is separate from mutable business storage.

Twenty-four portable tests cover lossless point/line/region publication, version history, reopen, invalid-save retention, refusal of incompatible databases, archive restoration and generated MySQL BLOB data. The existing eight database-contract tests pass using the project's existing service virtual environment; a first invocation with an interpreter missing PyJWT was an environment failure and remains recorded separately. There is no schema/index/tenant ownership change. MySQL and Linux/Apache runtime acceptance remain pending. This connection currently follows the fixed editor workspace; arbitrary Save As/current-project selection and native interactive save commands still need their end-to-end handoff checks.

The actual private SQLite package also passed native save-function �� HTTP publication byte identity, version-two service restart, archive restore and generated MySQL BLOB checks. Its owned native window probe covered eight maximized/hidden/left/right/resized states, and the binding UI probe covered apply/undo/redo/refusal/save-function reopen while retaining the user workspace bytes. These probes do not cover new-project paths or file-dialog/save-button publication.
