#include <osg/Geode>
#include <osg/Group>
#include <osg/Texture>
#include <osg/TriangleFunctor>
#include <osgDB/ReadFile>
#include <osgDB/Registry>
#include <osgDB/WriteFile>
#include <osgUtil/Optimizer>

#include <filesystem>
#include <vector>
#include <fstream>
#include <iostream>
#include <map>

struct CountTriangle {
  unsigned long long count = 0;
  void operator()(const osg::Vec3&, const osg::Vec3&, const osg::Vec3&, bool = false) {
    ++count;
  }
};

class SourceTriangles : public osg::NodeVisitor {
public:
  SourceTriangles() : osg::NodeVisitor(TRAVERSE_ALL_CHILDREN) {
  }
  void apply(osg::Geode& geode) override {
    for (unsigned i = 0; i < geode.getNumDrawables(); ++i) {
      osg::TriangleFunctor<CountTriangle> counter;
      geode.getDrawable(i)->accept(counter);
      count += counter.count;
    }
    traverse(geode);
  }
  unsigned long long count = 0;
};

// Rewrite only the in-memory export copy. Embedded historical absolute image
// names must never determine where the OBJ writer writes output textures.
class LocalImages : public osg::NodeVisitor {
public:
  LocalImages() : osg::NodeVisitor(TRAVERSE_ALL_CHILDREN) {
  }
  void rename(osg::StateSet* state) {
    if (!state)
      return;
    for (unsigned unit = 0; unit < state->getTextureAttributeList().size(); ++unit) {
      auto* texture = dynamic_cast<osg::Texture*>(state->getTextureAttribute(unit, osg::StateAttribute::TEXTURE));
      if (!texture)
        continue;
      for (unsigned face = 0; face < texture->getNumImages(); ++face) {
        auto* image = texture->getImage(face);
        if (!image)
          continue;
        if (!image->data())
          throw std::runtime_error("referenced texture has no embedded pixels");
        auto result = images.emplace(image, images.size());
        image->setFileName("texture_" + std::to_string(result.first->second) + ".rgb");
      }
    }
  }
  void apply(osg::Node& node) override {
    rename(node.getStateSet());
    traverse(node);
  }
  void apply(osg::Geode& geode) override {
    rename(geode.getStateSet());
    for (unsigned i = 0; i < geode.getNumDrawables(); ++i)
      rename(geode.getDrawable(i)->getStateSet());
    traverse(geode);
  }
  std::map<osg::Image*, size_t> images;
};

int exportNodes(const std::vector<std::filesystem::path>& args) {
  const auto argc = args.size();
  try {
    if (argc == 2 && args[1] == "--capabilities") {
      std::cout << "{\"schema\":\"xnby.osgb.exporter.v1\",\"unicode_source_paths\":true,"
                   "\"unicode_output_directories\":true,\"ascii_output_basename\":true}\n";
      return 0;
    }
    if (argc != 3 && argc != 4)
      throw std::runtime_error("usage: ht_osgb_exporter source-list.txt output.obj [source-triangle-counts.tsv]");
    std::ifstream list(args[1]);
    if (!list)
      throw std::runtime_error("cannot read source list");
    osg::ref_ptr<osg::Group> group = new osg::Group;
    std::ofstream audit;
    if (argc == 4) {
      audit.open(args[3]);
      if (!audit)
        throw std::runtime_error("cannot write source triangle audit");
    }
    std::string path;
    while (std::getline(list, path)) {
      if (!path.empty() && path.back() == '\r')
        path.pop_back();
      if (path.empty())
        continue;
      // Open UTF-8 paths with the native filesystem API. The OSG binary
      // reader consumes bytes, so Windows never needs a source junction.
      const auto source = std::filesystem::u8path(path);
      std::ifstream bytes(source, std::ios::binary);
      if (!bytes)
        throw std::runtime_error("cannot open source node: " + path);
      auto* reader = osgDB::Registry::instance()->getReaderWriterForExtension("osgb");
      if (!reader)
        throw std::runtime_error("OSGB reader plugin is unavailable");
      osg::ref_ptr<osgDB::Options> inputOptions = new osgDB::Options;
      inputOptions->setPluginStringData("fileType", "Binary");
      inputOptions->getDatabasePathList().push_front(source.parent_path().u8string());
      auto result = reader->readNode(bytes, inputOptions);
      osg::ref_ptr<osg::Node> node = result.getNode();
      if (!node)
        throw std::runtime_error("cannot read source node: " + path);
      if (audit) {
        SourceTriangles triangles;
        node->accept(triangles);
        audit << path << '\t' << triangles.count << '\n';
      }
      group->addChild(node);
    }
    if (!group->getNumChildren())
      throw std::runtime_error("empty source list");
    // Native-frontier auditing requires one source group per file. The default
    // optimizer merges adjacent drawables across those source boundaries.
    if (argc == 3) {
      osgUtil::Optimizer optimizer;
      optimizer.optimize(group);
    }
    LocalImages visitor;
    group->accept(visitor);
    osg::ref_ptr<osgDB::Options> options = new osgDB::Options("OutputTextureFiles");
    // OBJ and embedded image basenames are ASCII; the containing directory
    // may be Unicode. Relative OSG writes use the native current directory.
    const auto output = std::filesystem::absolute(args[2]);
    const auto filename = output.filename().u8string();
    if (filename.empty() || filename.find_first_not_of(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-") != std::string::npos)
      throw std::runtime_error("OBJ basename must use ASCII letters, digits, dot, underscore or hyphen");
    std::filesystem::current_path(output.parent_path());
    if (!osgDB::writeNodeFile(*group, filename, options))
      throw std::runtime_error("OBJ export failed");
    std::cout << "Exported " << group->getNumChildren() << " nodes, " << visitor.images.size()
              << " textures with local filenames\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}


#ifdef _WIN32
int wmain(int argc, wchar_t** argv) {
  std::vector<std::filesystem::path> args;
  for (int i = 0; i < argc; ++i)
    args.emplace_back(argv[i]);
  return exportNodes(args);
}
#else
int main(int argc, char** argv) {
  std::vector<std::filesystem::path> args;
  for (int i = 0; i < argc; ++i)
    args.emplace_back(std::filesystem::u8path(argv[i]));
  return exportNodes(args);
}
#endif
