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
