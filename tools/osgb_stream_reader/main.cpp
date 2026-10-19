// Read-only OSGB source decoder. No cache, atlas writer, cleanup, GPU or network path.
#include <nlohmann/json.hpp>
#include <osg/Geode>
#include <osg/Geometry>
#include <osg/Matrix>
#include <osg/TexMat>
#include <osg/Texture>
#include <osg/TriangleIndexFunctor>
#include <osgDB/Callbacks>
#include <osgDB/Options>
#include <osgDB/Registry>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <stdexcept>
#include <vector>
#ifdef _WIN32
#  include <fcntl.h>
#  include <io.h>
#  include <windows.h>
#endif
namespace fs = std::filesystem;
using Json = nlohmann::json;
constexpr std::size_t maxSource = 32ull << 20;
constexpr std::size_t maxPayload = 128ull << 20;
constexpr std::size_t maxImage = 32ull << 20;
constexpr std::size_t maxVertices = 2000000;
constexpr std::size_t maxIndices = 6000000;
void require(bool value, const char* reason) {
  if (!value)
    throw std::runtime_error(reason);
}
class DenyExternal final : public osgDB::ReadFileCallback {
public:
  unsigned calls = 0;
  osgDB::ReaderWriter::ReadResult denied() {
    ++calls;
    return osgDB::ReaderWriter::ReadResult("external source reads are disabled");
  }
  osgDB::ReaderWriter::ReadResult openArchive(const std::string&,
                                              osgDB::ReaderWriter::ArchiveStatus,
                                              unsigned,
                                              const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readObject(const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readImage(const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readHeightField(const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readNode(const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readShader(const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::ReadResult readScript(const std::string&, const osgDB::Options*) override {
    return denied();
  }
};
class DenyWrites final : public osgDB::WriteFileCallback {
public:
  unsigned calls = 0;
  osgDB::ReaderWriter::WriteResult denied() {
    ++calls;
    return osgDB::ReaderWriter::WriteResult("all file writes are disabled");
  }
  osgDB::ReaderWriter::WriteResult writeObject(const osg::Object&, const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::WriteResult writeImage(const osg::Image&, const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::WriteResult writeHeightField(const osg::HeightField&,
                                                    const std::string&,
                                                    const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::WriteResult writeNode(const osg::Node&, const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::WriteResult writeShader(const osg::Shader&, const std::string&, const osgDB::Options*) override {
    return denied();
  }
  osgDB::ReaderWriter::WriteResult writeScript(const osg::Script&, const std::string&, const osgDB::Options*) override {
    return denied();
  }
};
void ordinary(const fs::path& path, bool directory) {
#ifdef _WIN32
  const auto attributes = GetFileAttributesW(path.c_str());
  require(attributes != INVALID_FILE_ATTRIBUTES, "source path is missing");
  require(!(attributes & FILE_ATTRIBUTE_REPARSE_POINT), "source links and junctions are forbidden");
  require(bool(attributes & FILE_ATTRIBUTE_DIRECTORY) == directory, "source file type does not match");
#else
  const auto state = fs::symlink_status(path);
  require(!fs::is_symlink(state), "source links are forbidden");
  require(directory ? fs::is_directory(state) : fs::is_regular_file(state), "source file type does not match");
#endif
}
fs::path sourcePath(const fs::path& root, const fs::path& relative) {
  require(root.is_absolute() && root.filename() == "Data", "expected an absolute Data directory");
  ordinary(root, true);
  require(!relative.is_absolute() && !relative.has_root_name(), "node path must be relative");
  std::vector<fs::path> components;
  for (const auto& part : relative)
    components.push_back(part);
  require(components.size() == 2, "node path must contain exactly Tile directory and source filename");
  const auto tile = components[0].u8string(), name = components[1].u8string();
  require(std::regex_match(tile, std::regex("Tile_[0-9]+")), "invalid tile directory");
  require(std::regex_match(name, std::regex(tile + "_L[0-9]+_0[0-9u]+\\.osgb")), "invalid source node name");
  auto folder = root / components[0];
  ordinary(folder, true);
  auto file = folder / components[1];
  ordinary(file, false);
  require(fs::file_size(file) > 0 && fs::file_size(file) <= maxSource, "source node size is outside bounds");
  return file;
}
struct Triangles {
  std::vector<std::uint32_t> values;
  unsigned vertices = 0;
  void operator()(unsigned a, unsigned b, unsigned c) {
    require(a < vertices && b < vertices && c < vertices, "triangle index exceeds vertex array");
    require(values.size() + 3 <= maxIndices, "source triangle count exceeds limit");
    values.insert(values.end(), {a, b, c});
  }
};
class Decoded final : public osg::NodeVisitor {
public:
  Decoded() : osg::NodeVisitor(TRAVERSE_ALL_CHILDREN) {
  }
  std::vector<std::uint8_t> payload;
  Json meshes = Json::array(), images = Json::array();
  std::map<const osg::Image*, std::size_t> imageIds;
  std::uint64_t triangles = 0, vertices = 0;
  template <class T> Json append(const std::vector<T>& data) {
    while (payload.size() % 4)
      payload.push_back(0);
    const auto bytes = data.size() * sizeof(T);
    require(bytes <= maxPayload && payload.size() <= maxPayload - bytes, "decoded payload exceeds limit");
    const auto offset = payload.size();
    const auto* first = reinterpret_cast<const std::uint8_t*>(data.data());
    if (bytes)
      payload.insert(payload.end(), first, first + bytes);
    return Json{{"offset", offset}, {"bytes", bytes}, {"count", data.size()}};
  }
  std::size_t imageId(osg::Image* image) {
    const auto found = imageIds.find(image);
    if (found != imageIds.end())
      return found->second;
    require(image && image->data() && image->s() > 0 && image->t() > 0 && image->r() == 1,
            "missing embedded 2D pixels");
    require(!image->isCompressed() && image->getDataType() == GL_UNSIGNED_BYTE,
            "this reader requires original byte RGB/RGBA pixels");
    const auto format = image->getPixelFormat();
    require(format == GL_RGB || format == GL_RGBA || format == GL_BGR || format == GL_BGRA,
            "unsupported embedded pixel format");
    const auto pixelCount = std::size_t(image->s()) * std::size_t(image->t());
    require(pixelCount <= maxImage / 4, "embedded image exceeds byte budget");
    std::vector<std::uint8_t> rgba(pixelCount * 4);
    const bool bgra = format == GL_BGR || format == GL_BGRA;
    const bool alpha = format == GL_RGBA || format == GL_BGRA;
    for (int y = 0; y < image->t(); ++y)
      for (int x = 0; x < image->s(); ++x) {
        const auto* src = image->data(x, y);
        auto* dst = rgba.data() + (std::size_t(y) * image->s() + x) * 4;
        dst[0] = src[bgra ? 2 : 0];
        dst[1] = src[1];
        dst[2] = src[bgra ? 0 : 2];
        dst[3] = alpha ? src[3] : 255;
      }
    const auto id = images.size();
    auto range = append(rgba);
    range["width"] = image->s();
    range["height"] = image->t();
    range["format"] = "rgba8";
    range["sourcePixelFormat"] = format;
    range["rowOrder"] = "source_storage";
    range["sourceOrigin"] = image->getOrigin() == osg::Image::TOP_LEFT ? "top_left" : "bottom_left";
    range["sourceMipLevels"] = image->getNumMipmapLevels();
    images.push_back(range);
    imageIds.emplace(image, id);
    return id;
  }
  osg::Texture* textureFor(osg::Geometry& geometry) {
    osg::Texture* texture = nullptr;
    for (auto* node : getNodePath())
      if (auto* state = node->getStateSet()) {
        if (auto* uvMatrix = dynamic_cast<osg::TexMat*>(state->getTextureAttribute(0, osg::StateAttribute::TEXMAT)))
          require(uvMatrix->getMatrix().isIdentity(), "nonidentity texture matrix needs an explicit UV adapter");
        require(state->getTextureAttributeList().size() <= 1,
                "multiple texture units require an explicit material adapter");
        if (auto* value = dynamic_cast<osg::Texture*>(state->getTextureAttribute(0, osg::StateAttribute::TEXTURE)))
          texture = value;
      }
    if (auto* state = geometry.getStateSet()) {
      if (auto* uvMatrix = dynamic_cast<osg::TexMat*>(state->getTextureAttribute(0, osg::StateAttribute::TEXMAT)))
        require(uvMatrix->getMatrix().isIdentity(), "nonidentity drawable texture matrix is unsupported");
      require(state->getTextureAttributeList().size() <= 1, "multiple drawable texture units are unsupported");
      if (auto* value = dynamic_cast<osg::Texture*>(state->getTextureAttribute(0, osg::StateAttribute::TEXTURE)))
        texture = value;
    }
    require(texture && texture->getNumImages() == 1, "each source drawable must have exactly one embedded image");
    return texture;
  }
  void apply(osg::Geode& geode) override {
    const auto matrix = osg::computeLocalToWorld(getNodePath());
    for (unsigned d = 0; d < geode.getNumDrawables(); ++d) {
      auto* geometry = geode.getDrawable(d)->asGeometry();
      require(geometry, "non-geometry source drawable is unsupported");
      const auto* positions = dynamic_cast<const osg::Vec3Array*>(geometry->getVertexArray());
      const auto* uv = dynamic_cast<const osg::Vec2Array*>(geometry->getTexCoordArray(0));
      require(positions && uv && positions->size() == uv->size() && !positions->empty(),
              "positions and UV arrays must match");
      require(positions->size() <= maxVertices && vertices + positions->size() <= maxVertices,
              "source vertex count exceeds limit");
      osg::TriangleIndexFunctor<Triangles> indices;
      indices.vertices = static_cast<unsigned>(positions->size());
      geometry->accept(indices);
      require(!indices.values.empty(), "source geometry has no triangles");
      for (unsigned p = 0; p < geometry->getNumPrimitiveSets(); ++p) {
        const auto mode = geometry->getPrimitiveSet(p)->getMode();
        require(mode == GL_TRIANGLES || mode == GL_TRIANGLE_STRIP || mode == GL_TRIANGLE_FAN,
                "non-triangle primitive topology is unsupported");
      }
      std::vector<float> world, texcoords;
      world.reserve(positions->size() * 3);
      texcoords.reserve(uv->size() * 2);
      osg::Vec3d lo(1e100, 1e100, 1e100), hi(-1e100, -1e100, -1e100);
      for (std::size_t i = 0; i < positions->size(); ++i) {
        const osg::Vec3d point = osg::Vec3d((*positions)[i]) * matrix;
        for (unsigned k = 0; k < 3; ++k) {
          require(std::isfinite(point[k]) && std::abs(point[k]) < 1e8, "invalid source vertex");
          lo[k] = std::min(lo[k], point[k]);
          hi[k] = std::max(hi[k], point[k]);
          world.push_back(static_cast<float>(point[k]));
        }
        for (unsigned k = 0; k < 2; ++k) {
          const auto value = (*uv)[i][k];
          require(std::isfinite(value), "invalid source UV");
          texcoords.push_back(value);
        }
      }
      const auto* colors = geometry->getColorArray();
      if (colors) {
        const auto* rgba = dynamic_cast<const osg::Vec4Array*>(colors);
        require(rgba, "unsupported source vertex color format");
        for (const auto& color : *rgba)
          for (unsigned k = 0; k < 4; ++k)
            require(color[k] == 1.f, "nonwhite source colors need an explicit material adapter");
      }
      auto* texture = textureFor(*geometry);
      const auto image = imageId(texture->getImage(0));
      const auto posRange = append(world), uvRange = append(texcoords), indexRange = append(indices.values);
      meshes.push_back(Json{{"positions", posRange},
                            {"uv", uvRange},
                            {"indices", indexRange},
                            {"image", image},
                            {"boundsMin", {lo.x(), lo.y(), lo.z()}},
                            {"boundsMax", {hi.x(), hi.y(), hi.z()}},
                            {"unlit", true},
                            {"vertexColorsWhite", true},
                            {"sampler",
                             {{"wrapS", texture->getWrap(osg::Texture::WRAP_S)},
                              {"wrapT", texture->getWrap(osg::Texture::WRAP_T)},
                              {"minFilter", texture->getFilter(osg::Texture::MIN_FILTER)},
                              {"magFilter", texture->getFilter(osg::Texture::MAG_FILTER)}}}});
      vertices += positions->size();
      triangles += indices.values.size() / 3;
      require(triangles * 3 <= maxIndices, "total source indices exceed limit");
    }
    traverse(geode);
  }
};
int execute(const std::vector<fs::path>& args) {
  try {
    require(args.size() == 4,
            "usage: zmd_osgb_stream_reader DATA_ROOT Tile_N/Tile_N_Lx_0u.osgb PRIVATE_PLUGIN_DIRECTORY");
    const auto file = sourcePath(args[1], args[2]);
    const auto plugins = args[3];
    ordinary(plugins, true);
#ifdef _WIN32
    require(SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS) != 0, "cannot restrict library search");
#endif
    auto* registry = osgDB::Registry::instance();
    registry->setLibraryFilePathList(osgDB::FilePathList{plugins.u8string()});
    registry->getDataFilePathList().clear();
    registry->setFileCache(nullptr);
    osg::ref_ptr<DenyExternal> reads = new DenyExternal;
    osg::ref_ptr<DenyWrites> writes = new DenyWrites;
    registry->setReadFileCallback(reads);
    registry->setWriteFileCallback(writes);
    osg::ref_ptr<osgDB::Options> options = new osgDB::Options;
    options->setPluginStringData("fileType", "Binary");
    options->setReadFileCallback(reads);
    options->setObjectCacheHint(osgDB::Options::CACHE_NONE);
    auto* reader = registry->getReaderWriterForExtension("osgb");
    require(reader, "OSGB reader plugin is unavailable");
    std::ifstream source(file, std::ios::binary);
    require(bool(source), "source file cannot be opened read-only");
    auto result = reader->readNode(source, options);
    osg::ref_ptr<osg::Node> node = result.getNode();
    require(node.valid(), "OSGB source decoding failed");
    Decoded decoded;
    node->accept(decoded);
    require(!decoded.meshes.empty() && reads->calls == 0 && writes->calls == 0,
            "source needs an external read or attempted a write");
    const Json header{{"schema", "zhumadian.osgb.memory.v1"},
                      {"node", args[2].generic_u8string()},
                      {"sourceBytes", fs::file_size(file)},
                      {"meshes", decoded.meshes},
                      {"images", decoded.images},
                      {"vertices", decoded.vertices},
                      {"triangles", decoded.triangles},
                      {"payloadBytes", decoded.payload.size()},
                      {"externalReadAttempts", reads->calls},
                      {"writeAttempts", writes->calls},
                      {"coordinates", "source_local_metres"},
                      {"uv", "source_unchanged"},
                      {"littleEndian", true}};
    const auto text = header.dump();
    require(text.size() <= 1048576, "source metadata exceeds limit");
    const std::uint64_t headerSize = text.size(), payloadSize = decoded.payload.size();
#ifdef _WIN32
    require(_setmode(_fileno(stdout), _O_BINARY) != -1, "cannot use binary stdout");
#endif
    std::cout.write("ZMDOSGB1", 8);
    std::cout.write(reinterpret_cast<const char*>(&headerSize), 8);
    std::cout.write(reinterpret_cast<const char*>(&payloadSize), 8);
    std::cout.write(text.data(), text.size());
    std::cout.write(reinterpret_cast<const char*>(decoded.payload.data()), decoded.payload.size());
    std::cout.flush();
    require(bool(std::cout), "output pipe failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
#ifdef _WIN32
int wmain(int argc, wchar_t** argv) {
  std::vector<fs::path> args;
  for (int i = 0; i < argc; ++i)
    args.emplace_back(argv[i]);
  return execute(args);
}
#else
int main(int argc, char** argv) {
  std::vector<fs::path> args;
  for (int i = 0; i < argc; ++i)
    args.emplace_back(fs::u8path(argv[i]));
  return execute(args);
}
#endif
