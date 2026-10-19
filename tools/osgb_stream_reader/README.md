# Read-only OSGB memory reader

This optional component reads a SHA-pinned original source node and returns bounded geometry and embedded RGBA pixels over stdout. It is separate from the legacy cache/atlas producers. It does not create converted asset files, clean caches, repair resources, run a GPU or fetch network data.

Build on the tested Windows x64 OSG 3.6.5 toolchain:

```text
cmake -S tools/osgb_stream_reader -B work/readonly_osgb/build -A x64 -DZMD_OSG_SOURCE=<OSG-source> -DZMD_OSG_BUILD=<OSG-build> -DZMD_JSON_INCLUDE=<nlohmann-include>
cmake --build work/readonly_osgb/build --config Release
```

The private runtime contains the existing verified OSG dependencies and only the osg, osg-serializers and jpeg plugins. It does not need the OBJ or RGB export plugins. Record and check runtime SHA values before use. No third-party binaries are committed here. Windows x64 was built and exercised; Linux compilation/deployment remains unverified.

```text
zmd_osgb_stream_reader.exe <absolute-Data-directory> Tile_1/Tile_1_L16_0u.osgb <private-plugin-directory>
```

Python client: `tools/osgb_memory_reader.py`. Source and executable SHA values are mandatory. The configured Data root is trusted server configuration; never accept filesystem paths from a web request. Parent traversal, absolute node paths, cross-tile names, source links/junctions and oversized files are rejected. External OSG read callbacks and all OSG write callbacks are denied; OSGB bytes are passed directly to the stream reader. Object/file caches are disabled. This is a source-code and access-contract restriction, not an OS-level sandbox for every dependency.

Frame: eight-byte `ZMDOSGB1`, little-endian uint64 JSON length, uint64 payload length, UTF-8 descriptor, payload. Limits: source 32 MiB, descriptor 1 MiB, payload 128 MiB, one RGBA image 32 MiB, 2 million vertices and 6 million indices. The Python parser checks identity, totals, ranges, overlap, topology indices and finite arrays. The OSGB parser allocates its own objects before post-decode image/geometry bounds can be checked; these limits are not a proven peak-RSS bound. Only already catalogued and SHA-verified project sources are in scope.

Supported: float32 positions and UVs, triangles/strips/fans, byte RGB/RGBA/BGR/BGRA embedded images, white vertex colours and identity texture matrices. Unsupported material/image features fail explicitly. Positions use the source local metre frame. UVs and image storage-row order stay paired and unchanged. No normals are synthesized; the delivered source material is unlit.

`tools/osgb_memory_gltf.py` creates immutable complete glTF resources in memory. Pixel data is encoded as lossless PNG without resizing, atlas packing or JPEG recompression. Raw RGBA is not duplicated inside the geometry buffer. Legacy GL_CLAMP is explicitly adapted to GL_CLAMP_TO_EDGE, matching the OSG Texture.cpp GL3/GLES branch. The source sampler is otherwise preserved. A completed builder rejects further writes. Its delivery-byte budget is distinct from GPU residency/upload budgets.

Runtime Python dependency: requirements.txt. Optional QA dependencies: requirements-qa.txt. Run the independent frame/pixel/ownership tests with the project's Python environment:

```text
python -I -B -X utf8 tools/test_osgb_memory_reader.py
```

This reader alone does not enable application LOD. Integration still requires complete-frontier identity, original-pixel cost planning, immutable leases, bounded download/upload/residency, family replacement/retirement and display-surface attachment. Existing strict native tests and budgets must stay unchanged. Do not treat a single-source or single-tile preview as whole-scene acceptance.


## Optional WEB source-frontier adapter

The independent source adapter is opt-in; the existing landscape-server default
does not select it automatically.

- osgb_memory_pages.py seals an entire source cut or direct-child family in RAM.
  Each source mesh keeps its original image, positions, UV and triangle indices.
  The explicit osgb_memory_png_v1 format uses geometry.gltf, geometry.bin and
  texture.png, with a position/UV/Uint32 layout; it is not a legacy JPEG atlas.
- readonly_source_memory_store.py binds fixed configured catalog/Data/runtime
  roots and pinned SHA values. One worker, at most 16 queued jobs, a 256 MiB
  retained-encoded/build-reservation budget, a 128 MiB per-build reservation,
  at most 256 leases and a 180 second renewable lease lifetime bound ownership.
  Failed requests are retained, not automatically retried by each client poll.
  This is not a hard process-RSS limit; decoded OSG and Python objects are extra.
- source_memory_http.MemorySourceHTTP may precede the existing landscape Handler
  in a server subclass, configured with memory_sources=MemorySourceStore(...),
  read_only_lod=True and allow_local_layer_database=False for a file-only preview.
  Metadata can return HTTP 202 while preparing. Payloads require the exact
  bundle's RAM lease. Missing/invalid RAM payloads never fall back to the old
  filesystem producer. Resolve only trusted deployment anchors at configuration
  time; catalogue file identities and descendant paths are still checked.
- WEB validates the new schema, PNG identity/dimensions, explicit sampler,
  triangle ownership and actual parsed geometry. It shares the original
  residency/upload allocator and complete-family replacement/restore logic.
  Original RGBA full mip bytes and actual WEB geometry bytes are reserved.
  Current GPU/page/root/family gates stay unchanged.
- Display-only billboard height follows the visible source triangles at fixed
  XY. User coordinates and source files are not rewritten.

The current acceptance is a real local WEB integration and one near/far/near
return, not the full native two-round/sixteen-station gate, all-enterprise
coverage, notebook deployment or default-version release.

Additional checks:

    python -m unittest discover -s tools -p test_source_memory_store.py
    python -m unittest discover -s tools -p test_source_memory_http.py
    node --test web/tests/source_memory_format.test.mjs web/tests/source_surface_height.test.mjs
