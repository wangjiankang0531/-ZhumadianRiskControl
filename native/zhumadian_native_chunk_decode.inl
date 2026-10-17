#include "zhumadian_owned_worker.inl"
#include "zhumadian_cache_read_lock.inl"
// Complete source frontier split into bounded geometry/atlas uploads.
ZhumadianNativeCpu decodeZhumadianNativeChunks(int tile,
                                               int depth,
                                               bool buildPicking = false,
                                               const std::string& parent = {}) {
  ZhumadianNativeCpu result;
  try {
#ifdef _WIN32
    const fs::path repo = fs::absolute(resolveProjectPath("tools/convert_zhumadian_native_chunks.py")).parent_path().parent_path();
    const char* configured = std::getenv("HT_NATIVE_PYTHON");
    const char* profile = std::getenv("USERPROFILE");
    const fs::path portablePython = repo / "runtime/python/python.exe";
    const fs::path python = configured ? fs::path(configured)
                            : fs::exists(portablePython)
                                ? portablePython
                                : fs::path(profile ? profile : "") /
                                      ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
    if (!fs::exists(python))
      throw std::runtime_error("Native chunk decoder Python runtime unavailable");
    const auto cache = repo / "work/zhumadian_native_chunk_cache";
    ZhumadianCacheReadLock tileLease(cache / ".locks" / ("tile_" + std::to_string(tile) + ".lock"));
    const bool family = !parent.empty();
    if (family && !std::regex_match(parent, std::regex("Tile_[0-9]+_L[0-9]+_0[0-9u]+\\.osgb")))
      throw std::runtime_error("Invalid source family parent");
    const std::string receiptName = "native_family_" + std::to_string(GetCurrentProcessId()) + "_tile_" +
                                    std::to_string(tile) + "_depth_" + std::to_string(depth) + ".json";
    const auto script = family ? "convert_zhumadian_native_family.py" : "convert_zhumadian_native_chunks.py";
    std::wstring command = L"\"" + python.wstring() + L"\" -X utf8 \"" + (repo / "tools" / script).wstring() +
                           L"\" --tile=" + std::to_wstring(tile);
    if (family)
      command += L" --parent=" + std::wstring(parent.begin(), parent.end()) + L" --receipt-name=" +
                 std::wstring(receiptName.begin(), receiptName.end());
    else
      command += L" --depth=" + std::to_wstring(depth);
    const DWORD code = runOwnedNativeChunkWorker(python, command, repo, tile, depth);
    fs::path folder = repo / "work/zhumadian_native_chunk_cache" /
                      ("tile_" + std::to_string(tile) + "_depth_" + std::to_string(depth));
    if (family && fs::exists(repo / "work/zhumadian_native_chunk_cache" / receiptName)) {
      const auto receiptFile = repo / "work/zhumadian_native_chunk_cache" / receiptName;
      nlohmann::json receipt;
      std::ifstream receiptInput(receiptFile);
      receiptInput >> receipt;
      const auto directory = receipt.at("directory").get<std::string>();
      if (!std::regex_match(directory, std::regex("family_tile_" + std::to_string(tile) + "_[0-9a-f]{16}")) ||
          receipt.at("parent") != parent)
        throw std::runtime_error("Invalid owned source family receipt");
      folder = receiptFile.parent_path() / directory;
      receiptInput.close();
      fs::remove(receiptFile);
    }
    ZhumadianCacheReadLock bundleLease(cache / ".locks" / (folder.filename().string() + ".lock"));
    if (code != 0) {
      nlohmann::json failure;
      std::ifstream error(folder / "failure.json");
      if (error) {
        error >> failure;
        throw std::runtime_error(failure.at("reason").get<std::string>());
      }
      throw std::runtime_error("Native chunk frontier conversion failed or timed out");
    }
    nlohmann::json stamp;
    std::ifstream input(folder / "complete.json");
    input >> stamp;
    if (stamp.at("tile_id") != tile || stamp.at("parts").empty() || stamp.at("parts").size() > 64 ||
        (!family && (stamp.at("schema") != "hongtu.osgb_native_chunk_bundle.v1" || stamp.at("depth") != depth ||
                     !stamp.at("complete_frontier").get<bool>())) ||
        (family && (stamp.at("schema") != "xnby.osgb_native_family.v1" || stamp.at("replacement_parent") != parent ||
                    !stamp.at("complete_sibling_family").get<bool>())))
      throw std::runtime_error("Incomplete native source bundle marker");
    uint64_t indices = 0;
    auto picking = buildPicking && !stamp.contains("source_nodes")
                       ? std::make_shared<hongtu::renderer::TriangleBvh>(stamp.at("indices").get<size_t>() / 3)
                       : nullptr;
    for (const auto& item : stamp.at("parts")) {
      const std::string directory = item.at("directory");
      if (!std::regex_match(directory, std::regex("part_[0-9]{3}")))
        throw std::runtime_error("Native part path escapes bundle");
      const auto partFolder = folder / directory;
      ZhumadianNativeCpu part;
      part.payload = item.at("gpu_payload_bytes");
      if (!part.payload || part.payload > 32ull * 1024 * 1024)
        throw std::runtime_error("Native part exceeds upload limit");
      hongtu::asset::GltfLoader loader;
      auto model = loader.load(gltfPathUtf8(partFolder / "geometry.gltf"));
      if (!model || model->meshes.size() != 1)
        throw std::runtime_error("Native part glTF decode failed");
      const auto& mesh = model->meshes.front();
      if (mesh.positions.size() != item.at("vertices").get<size_t>() ||
          mesh.indices.size() != item.at("indices").get<size_t>() || mesh.indices.empty() || mesh.indices.size() % 3 ||
          mesh.normals.size() != mesh.positions.size() || mesh.uvs.size() != mesh.positions.size())
        throw std::runtime_error("Native part attributes/counts changed");
      for (size_t i = 0; i < mesh.positions.size(); ++i) {
        const auto p = mesh.positions[i], n = mesh.normals[i];
        const auto uv = mesh.uvs[i];
        if (!std::isfinite(p.x + p.y + p.z + n.x + n.y + n.z + uv.x + uv.y))
          throw std::runtime_error("Nonfinite native part geometry");
        part.vertices.push_back({p,
                                 {1, 1, 1},
                                 glm::length(n) > .001f ? glm::normalize(n) : glm::vec3(0, 0, 1),
                                 uv,
                                 1.5f,
                                 {-2, 0, .92f, 5}});
      }
      part.indices = mesh.indices;
      const int atlasSide = item.at("atlas_size").get<int>();
      const bool tightAtlas = item.value("atlas_layout_policy", std::string{}) == "tight_square_gutter4_v1" &&
                              atlasSide >= 16 && atlasSide <= 2048 && atlasSide % 8 == 0;
      if (std::any_of(
              part.indices.begin(), part.indices.end(), [&](uint32_t i) { return i >= part.vertices.size(); }) ||
          !loadRgbaImage(partFolder / "atlas.jpg", part.image) ||
          part.image.width != item.at("atlas_size").get<int>() ||
          part.image.height != item.at("atlas_size").get<int>() ||
          (part.image.width != 1024 && part.image.width != 2048 && !tightAtlas))
        throw std::runtime_error("Native part indices/image changed");
      if (picking)
        for (size_t i = 0; i < part.indices.size(); i += 3)
          picking->addTriangle(part.vertices[part.indices[i]].position,
                               part.vertices[part.indices[i + 1]].position,
                               part.vertices[part.indices[i + 2]].position);
      uint64_t textureBytes = 0;
      for (int side = part.image.width; side > 0; side /= 2)
        textureBytes += uint64_t(side) * side * 4;
      if (part.payload != part.vertices.size() * sizeof(Vertex) + part.indices.size() * sizeof(uint32_t) + textureBytes)
        throw std::runtime_error("Native physical upload accounting differs from marker");
      result.payload += part.payload;
      indices += part.indices.size();
      result.parts.push_back(std::move(part));
    }
    if (result.payload != stamp.at("gpu_payload_bytes").get<uint64_t>() ||
        indices != stamp.at("indices").get<uint64_t>() || result.payload > (family ? 256ull : 384ull) * 1024 * 1024)
      throw std::runtime_error("Native parts do not form the complete bounded frontier");
    result.depth = depth;
    result.texel = stamp.at("texel_world_p90_m");
    result.edge = stamp.at("longest_edge_p90_m");
    result.frontier = family ? stamp.at("source_nodes").size() : stamp.at("frontier_count").get<uint32_t>();
    result.replacementParent = parent;
    if (stamp.contains("source_nodes")) {
      std::vector<std::vector<hongtu::asset::MeshIndexRange>> ownership(result.parts.size());
      std::map<std::string, size_t> directories;
      for (size_t i = 0; i < stamp.at("parts").size(); ++i)
        if (!directories.emplace(stamp.at("parts").at(i).at("directory").get<std::string>(), i).second)
          throw std::runtime_error("Duplicate source upload part");
      for (const auto& record : stamp.at("source_nodes")) {
        ZhumadianNativeSource node;
        node.name = record.at("name");
        node.children = record.at("children").get<std::vector<std::string>>();
        node.depth = record.at("depth");
        node.triangles = record.at("triangles");
        node.edge = record.at("longest_edge_p90_m");
        node.texel = record.at("texel_world_p90_m");
        if (!record.at("bounds_min").is_null()) {
          for (int axis = 0; axis < 3; ++axis) {
            node.low[axis] = record.at("bounds_min").at(axis);
            node.high[axis] = record.at("bounds_max").at(axis);
            if (!std::isfinite(node.low[axis]) || !std::isfinite(node.high[axis]) || node.high[axis] < node.low[axis])
              throw std::runtime_error("Invalid source node bounds");
          }
          node.hasBounds = true;
        }
        auto nodePicking = buildPicking ? std::make_shared<hongtu::renderer::TriangleBvh>(node.triangles) : nullptr;
        uint64_t sourceIndices = 0;
        for (const auto& span : record.at("spans")) {
          const auto partId = directories.at(span.at("part").get<std::string>());
          const uint32_t first = span.at("first"), count = span.at("count");
          const auto& part = result.parts.at(partId);
          if (!count || first % 3 || count % 3 || uint64_t(first) + count > part.indices.size())
            throw std::runtime_error("Source index range escapes upload part");
          node.spans.push_back({partId, first, count});
          ownership[partId].push_back({first, count});
          sourceIndices += count;
          if (nodePicking)
            for (uint32_t offset = first; offset < first + count; offset += 3)
              nodePicking->addTriangle(part.vertices[part.indices[offset]].position,
                                       part.vertices[part.indices[offset + 1]].position,
                                       part.vertices[part.indices[offset + 2]].position);
        }
        if (sourceIndices != uint64_t(node.triangles) * 3)
          throw std::runtime_error("Source index ownership omits triangles");
        if (nodePicking) {
          nodePicking->build();
          node.picking = std::move(nodePicking);
        }
        if (!result.sources.emplace(node.name, std::move(node)).second)
          throw std::runtime_error("Duplicate native source node");
      }
      for (size_t i = 0; i < ownership.size(); ++i) {
        auto& ranges = ownership[i];
        std::sort(ranges.begin(), ranges.end(), [](auto a, auto b) { return a.first < b.first; });
        uint64_t cursor = 0;
        for (auto range : ranges) {
          if (range.first != cursor)
            throw std::runtime_error("Source spans overlap or leave a gap");
          cursor += range.count;
        }
        if (cursor != result.parts[i].indices.size())
          throw std::runtime_error("Source spans leave uncovered indices");
      }
      nlohmann::json master, catalog;
      std::ifstream masterInput(repo / "data/showcase/zhumadian_native_hierarchy.json");
      masterInput >> master;
      for (const auto& rootRecord : master.at("root_records"))
        if (rootRecord.at("tile_id") == tile) {
          std::ifstream catalogInput(repo / rootRecord.at("catalog").get<std::string>());
          catalogInput >> catalog;
          if (rootRecord.at("sha256") != stamp.at("stamp").at("catalog_sha256"))
            throw std::runtime_error("Source topology differs from converted data");
          break;
        }
      result.sourceRoot = catalog.at("root");
      for (const auto& record : catalog.at("nodes"))
        result.topology.push_back({record.at("name"), record.at("children").get<std::vector<std::string>>()});
    }
    if (!result.sources.empty()) {
      hongtu::renderer::NativeSourceFrontier::Cut cut;
      for (const auto& [name, node] : result.sources)
        cut.insert(name);
      hongtu::renderer::NativeSourceFrontier checked(
          result.topology, family ? parent : result.sourceRoot, cut, result.payload, 384ull * 1048576);
    }
    if (picking) {
      picking->build();
      if (picking->triangleCount() != indices / 3)
        throw std::runtime_error("Picking mesh omits native frontier triangles");
      result.picking = std::move(picking);
    }
    result.valid = std::isfinite(result.texel) && result.texel > 0 && std::isfinite(result.edge) && result.edge > 0 &&
                   result.frontier > 0;
#else
    throw std::runtime_error("Native chunk decoder requires Windows OSGB runtime");
#endif
  } catch (const std::exception& error) {
    result = {};
    result.error = error.what();
  }
  return result;
}
