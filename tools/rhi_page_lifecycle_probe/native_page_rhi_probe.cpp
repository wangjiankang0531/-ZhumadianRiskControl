#include <hongtu/renderer/native_source_frontier.hpp>
#include <hongtu/rhi/RHIDevice.h>
#include <nlohmann/json.hpp>
#include <vulkan/vulkan.h>

#include "production/native_retained_page_draw.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
using namespace HongTu::RHI;
using Json = nlohmann::json;
static void require(bool value, const char* message) {
  if (!value)
    throw std::runtime_error(message);
}
struct Vertex {
  std::array<float, 3> position, normal;
  std::array<float, 2> uv;
};
struct Image {
  int width = 128, height = 128;
  std::vector<uint8_t> rgba;
};
struct Cpu {
  Image image;
  std::vector<Vertex> vertices;
  std::vector<uint32_t> indices;
  uint64_t payload = 0;
};
struct Span {
  uint32_t part = 0, first = 0, count = 6;
};
struct Source {
  int depth = 0;
  uint32_t triangles = 2;
  std::vector<std::string> children;
  std::vector<Span> spans{{}};
};
struct Part {
  RHIBufferPtr vertices, indices;
  RHITexturePtr texture;
  RHITextureViewPtr view;
  RHIDescriptorSetPtr descriptor;
  uint64_t payload = 0, originalPageBytes = 0, pageIdentity = 0;
  uint32_t indexCount = 0;
};
struct Resident {
  uint64_t payload = 0, retiredBasePayload = 0;
  std::vector<Part> parts;
  std::map<std::string, Source> sources;
  std::map<std::string, Resident> families;
  std::unique_ptr<hongtu::renderer::NativeSourceFrontier> sourceCut;
};
struct CpuBundle {
  std::vector<Cpu> parts;
  std::map<std::string, Source> sources;
};
#include "production/native_retained_page_identity.inl"
struct Harness {
  RHIDevice* device;
  std::map<int, Resident> resident;
  uint64_t payload = 0, familyCommits = 0;
  bool familyTicket = false, familyStaged = false, staged = false;
  struct Pending {
    bool valid() const {
      return false;
    }
  } familyPending, pending;
  struct Request {
    int id = -1;
  } familyRequest;
  int stagingId = -1, pendingId = -1;
  bool visibilityScheduling() const {
    return true;
  }
  bool visibleRootGuardEnabled() const {
    return true;
  }
#include "production/native_retained_page_lifecycle.inl"
  RetainedPageResourceSnapshot captureRetainedPageResources() const {
    const auto d = device->getDescriptorAllocationInfo();
    const auto m = device->getMemoryBudgetInfo();
    return {d.available, d.liveSets, m.allocatorAllocationBytes, m.allocatorAllocationCount};
  }
};
static Json allocation(RHIDevice* d) {
  auto m = d->getMemoryBudgetInfo();
  auto s = d->getDescriptorAllocationInfo();
  require(s.available, "Descriptor statistics required");
  return {{"allocationBytes", m.allocatorAllocationBytes},
          {"allocationCount", m.allocatorAllocationCount},
          {"blockBytes", m.allocatorBlockBytes},
          {"liveDescriptors", s.liveSets},
          {"descriptorFreeFailures", s.freeFailures}};
}
static std::vector<uint32_t> spirv(const char* path) {
  std::ifstream f(path, std::ios::binary | std::ios::ate);
  require(bool(f), "Missing shader");
  auto size = f.tellg();
  require(size > 0 && size % 4 == 0, "Invalid shader size");
  std::vector<uint32_t> code(size_t(size) / 4);
  f.seekg(0);
  f.read(reinterpret_cast<char*>(code.data()), size);
  require(bool(f), "Shader read failed");
  return code;
}
static Cpu pixels(std::array<uint8_t, 4> color) {
  Cpu c;
  c.vertices = {{{-1, -1, 0}, {0, 0, 1}, {0, 0}},
                {{1, -1, 0}, {0, 0, 1}, {1, 0}},
                {{1, 1, 0}, {0, 0, 1}, {1, 1}},
                {{-1, 1, 0}, {0, 0, 1}, {0, 1}}};
  c.indices = {0, 1, 2, 0, 2, 3};
  c.image.rgba.resize(128 * 128 * 4);
  for (size_t i = 0; i < c.image.rgba.size(); i += 4)
    std::copy(color.begin(), color.end(), c.image.rgba.begin() + i);
  c.payload = c.vertices.size() * sizeof(Vertex) + c.indices.size() * 4 + c.image.rgba.size();
  return c;
}
static RHIBufferPtr hostBuffer(RHIDevice* d, const void* data, size_t bytes, BufferUsageFlagBits use) {
  BufferDesc desc;
  desc.size = bytes;
  desc.usage = static_cast<BufferUsageFlags>(use);
  desc.memoryProperties = MemoryPropertyFlagBits::HostVisible | MemoryPropertyFlagBits::HostCoherent;
  auto b = d->createBuffer(desc);
  require(bool(b), "Buffer allocation failed");
  auto p = b->map();
  require(p != nullptr, "Buffer map failed");
  std::memcpy(p, data, bytes);
  b->unmap();
  return b;
}
static Part upload(RHIDevice* d, const Cpu& c, const RHIDescriptorSetLayoutPtr& layout, const RHISamplerPtr& sampler) {
  Part p;
  p.vertices = hostBuffer(d, c.vertices.data(), c.vertices.size() * sizeof(Vertex), BufferUsageFlagBits::Vertex);
  p.indices = hostBuffer(d, c.indices.data(), c.indices.size() * 4, BufferUsageFlagBits::Index);
  TextureDesc t;
  t.extent = {128, 128, 1};
  t.usage = static_cast<TextureUsageFlags>(TextureUsageFlagBits::Sampled) |
            static_cast<TextureUsageFlags>(TextureUsageFlagBits::TransferDst) |
            static_cast<TextureUsageFlags>(TextureUsageFlagBits::TransferSrc);
  p.texture = d->createTexture(t);
  require(bool(p.texture), "Texture allocation failed");
  RHIDevice::MipData mip{};
  mip.width = 128;
  mip.height = 128;
  mip.depth = 1;
  mip.data = c.image.rgba.data();
  mip.dataSize = c.image.rgba.size();
  d->uploadTextureData(p.texture, {mip});
  p.view = p.texture->createView();
  require(bool(p.view), "Texture view failed");
  DescriptorSetDesc desc;
  DescriptorBinding binding;
  binding.binding = 0;
  binding.type = DescriptorType::CombinedImageSampler;
  binding.textureView = p.view;
  binding.sampler = sampler;
  desc.bindings.push_back(binding);
  p.descriptor = d->createDescriptorSet(layout, desc);
  require(bool(p.descriptor), "Descriptor allocation failed");
  p.payload = p.originalPageBytes = c.payload;
  p.pageIdentity = nativePageIdentity(c);
  p.indexCount = uint32_t(c.indices.size());
  return p;
}
static std::vector<uint8_t> render(RHIDevice* d,
                                   const RHIOffscreenTargetPtr& target,
                                   const RHIPipelinePtr& pipeline,
                                   const RHIPipelineLayoutPtr& layout,
                                   const Part& p,
                                   const std::vector<hongtu::asset::MeshIndexRange>& hidden = {}) {
  const auto ranges = nativeRetainedPageDrawRanges(p, hidden);
  auto cmd = d->createCommandBuffer();
  auto fence = d->createFence();
  cmd->begin();
  Rect2D area{{0, 0}, {64, 64}};
  cmd->beginRenderPass(target->getRenderPass(), target->getFramebuffer(), area, {{0, 0, 0, 1}, {1, 0, 0, 0}});
  cmd->setViewport({0, 0, 64, 64, 0, 1});
  cmd->setScissor(area);
  cmd->bindPipeline(pipeline);
  if (!ranges.empty()) {
    cmd->bindDescriptorSet(0, p.descriptor, layout);
    cmd->bindVertexBuffer(0, p.vertices);
    cmd->bindIndexBuffer(p.indices);
    for (const auto& r : ranges)
      cmd->drawIndexed(r.count, 1, r.first);
  }
  cmd->endRenderPass();
  cmd->end();
  d->submit({cmd}, {}, {}, fence);
  fence->wait();
  cmd.reset();
  fence.reset();
  std::vector<uint8_t> data;
  uint32_t w = 0, h = 0;
  require(target->readbackToBuffer(data, w, h) && w == 64 && h == 64, "GPU target readback failed");
  return data;
}
static void exactColor(const std::vector<uint8_t>& data, std::array<uint8_t, 4> color) {
  require(data.size() == 64 * 64 * 4, "Pixel length mismatch");
  for (size_t i = 0; i < data.size(); ++i)
    require(data[i] == color[i % 4], "Rendered pixels differ");
}
static bool validationAvailable() {
  uint32_t n = 0;
  require(vkEnumerateInstanceLayerProperties(&n, nullptr) == VK_SUCCESS, "Layer enumeration failed");
  std::vector<VkLayerProperties> layers(n);
  require(vkEnumerateInstanceLayerProperties(&n, layers.data()) == VK_SUCCESS, "Layer enumeration failed");
  return std::any_of(layers.begin(), layers.end(), [](const auto& l) {
    return std::string(l.layerName) == "VK_LAYER_KHRONOS_validation";
  });
}
int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: probe vertex.spv fragment.spv result.json\n";
    return 2;
  }
  auto factory = Backend::createFactory(Backend::Type::Vulkan);
  RHIDevice* device = nullptr;
  Json report;
  try {
    require(factory != nullptr, "Factory creation failed");
    const bool validation = validationAvailable();
    device = factory->createDevice(validation);
    require(device != nullptr, "Device creation failed");
    report["validationLayerEnabled"] = validation;
    report["device"] = device->getProperties().deviceName;
    {
      auto target = device->createOffscreenTarget(64, 64);
      require(bool(target), "Offscreen target failed");
      DescriptorSetLayoutDesc dl;
      dl.bindings.push_back(
          {0, 1, static_cast<ShaderStageFlags>(ShaderStageFlagBits::Fragment), DescriptorType::CombinedImageSampler});
      auto descriptorLayout = device->createDescriptorSetLayout(dl);
      PipelineLayoutDesc pl;
      pl.setLayouts = {descriptorLayout};
      auto pipelineLayout = device->createPipelineLayout(pl);
      auto sampler = device->createSampler({});
      ShaderDesc vd;
      vd.stage = ShaderStageFlagBits::Vertex;
      vd.spirvCode = spirv(argv[1]);
      ShaderDesc fd;
      fd.stage = ShaderStageFlagBits::Fragment;
      fd.spirvCode = spirv(argv[2]);
      auto vs = device->createShader(vd), fs = device->createShader(fd);
      GraphicsPipelineDesc pd;
      pd.shaders = {vs, fs};
      pd.vertexInput.bindings = {{0, sizeof(Vertex), false}};
      pd.vertexInput.attributes = {{0, 0, Format::R32G32_SFLOAT, 0}};
      pd.rasterization.cullMode = CullMode::None;
      pd.depthStencil.depthTestEnable = false;
      pd.depthStencil.depthWriteEnable = false;
      pd.colorBlendAttachments.push_back({});
      pd.pipelineLayout = pipelineLayout;
      pd.renderPass = target->getRenderPass();
      auto pipeline = device->createGraphicsPipeline(pd);
      require(bool(pipeline), "Pipeline creation failed");
      const auto baseline = allocation(device);
      report["baseline"] = baseline;
      const auto parent = pixels({255, 0, 0, 255}), child = pixels({0, 255, 0, 255});
      Harness h{device};
      Resident root;
      root.parts.push_back(upload(device, parent, descriptorLayout, sampler));
      root.sources.emplace("parent", Source{0, 2, {"child"}, {{0, 0, 6}}});
      root.payload = parent.payload;
      root.sourceCut = std::make_unique<hongtu::renderer::NativeSourceFrontier>(
          std::vector<hongtu::renderer::NativeSourceNode>{{"parent", {"child"}}, {"child", {}}},
          "parent",
          std::set<std::string>{"parent"},
          root.payload,
          4 * parent.payload);
      h.payload = root.payload;
      h.resident.emplace(0, std::move(root));
      auto& ready = h.resident.at(0);
      exactColor(render(device, target, pipeline, pipelineLayout, ready.parts[0]), {255, 0, 0, 255});
      h.retireHiddenBasePages();
      require(ready.parts[0].payload == parent.payload, "Visible parent retired");
      report["visibleParentPreserved"] = true;
      Resident family;
      family.parts.push_back(upload(device, child, descriptorLayout, sampler));
      family.sources.emplace("child", Source{1, 2, {}, {{0, 0, 6}}});
      family.payload = child.payload;
      ready.families.emplace("parent", std::move(family));
      const auto ticket = ready.sourceCut->prepare("parent", {"child"}, child.payload, 1);
      require(bool(ticket) && ready.sourceCut->markPartReady(*ticket, 0) && ready.sourceCut->commit(*ticket),
              "Full child cut commit failed");
      ready.payload += child.payload;
      h.payload += child.payload;
      ++h.familyCommits;
      h.familyTicket = true;
      h.familyRequest.id = 0;
      h.retireHiddenBasePages();
      require(ready.parts[0].payload == parent.payload, "Active family lane not deferred");
      h.familyTicket = false;
      h.familyRequest.id = -1;
      const auto before = allocation(device);
      auto green = render(device, target, pipeline, pipelineLayout, ready.families.at("parent").parts[0]);
      exactColor(green, {0, 255, 0, 255});
      device->waitIdle();
      h.retireHiddenBasePages();
      const auto retired = allocation(device);
      require(ready.parts[0].payload == 0 && !ready.parts[0].descriptor && !ready.parts[0].texture,
              "Parent resources still present");
      require(h.hiddenSourcePageRetirements == 1 && h.payload == child.payload, "Retirement accounting failed");
      require(before.at("liveDescriptors").get<uint64_t>() == retired.at("liveDescriptors").get<uint64_t>() + 1,
              "Descriptor not actually freed");
      require(before.at("allocationCount").get<uint64_t>() == retired.at("allocationCount").get<uint64_t>() + 3,
              "GPU allocations not actually freed");
      require(before.at("allocationBytes").get<uint64_t>() >=
                  retired.at("allocationBytes").get<uint64_t>() + parent.payload,
              "Allocation bytes not released");
      exactColor(render(device, target, pipeline, pipelineLayout, ready.families.at("parent").parts[0]),
                 {0, 255, 0, 255});
      exactColor(render(device, target, pipeline, pipelineLayout, ready.parts[0], {{0, 6}}), {0, 0, 0, 255});
      bool refused = false;
      try {
        render(device, target, pipeline, pipelineLayout, ready.parts[0]);
      } catch (const std::logic_error&) {
        refused = true;
      }
      require(refused, "Visible retired page was not refused before binding");
      report["beforeRetirement"] = before;
      report["afterRetirement"] = retired;
      report["retirementEvents"] = h.retainedPageResourceEvents.size();
      report["visibleChildPixelsPreserved"] = true;
      report["hiddenPageDrawSkipped"] = true;
      report["visibleRetiredPageRefused"] = true;
      report["activeUploadDeferred"] = true;
      CpuBundle decoded{{parent}, ready.sources};
      auto changed = decoded;
      changed.parts[0].image.rgba[0] ^= 1;
      bool identityRefused = false;
      try {
        nativePageRestorePlan(ready, changed, "parent");
      } catch (const std::logic_error&) {
        identityRefused = true;
      }
      require(identityRefused, "Changed parent pixels accepted");
      const auto plan = nativePageRestorePlan(ready, decoded, "parent");
      require(plan.parts == std::vector<size_t>{0} && plan.bytes == parent.payload, "Parent restore plan mismatch");
      ready.parts[0] = upload(device, decoded.parts[0], descriptorLayout, sampler);
      ready.retiredBasePayload -= plan.bytes;
      ready.payload += plan.bytes;
      h.payload += plan.bytes;
      ready.sourceCut->reset(ready.sourceCut->visible(), ready.payload);
      require(Harness::sourcePagesAvailable(ready, "parent"), "Restored parent not available");
      exactColor(render(device, target, pipeline, pipelineLayout, ready.parts[0]), {255, 0, 0, 255});
      report["physicalParentRestorePixelsExact"] = true;
      report["changedPixelsRefused"] = true;
      report["productionAsynchronousRestoreControllerExercised"] = false;
      device->waitIdle();
      h.resident.clear();
      const auto cleared = allocation(device);
      require(cleared.at("allocationCount") == baseline.at("allocationCount") &&
                  cleared.at("allocationBytes") == baseline.at("allocationBytes") &&
                  cleared.at("liveDescriptors") == baseline.at("liveDescriptors"),
              "Resources leaked after full clear");

      // Shared physical page: refining one source must retain its visible sibling.
      {
        Harness shared{device};
        Resident base;
        const auto blue = pixels({0, 0, 255, 255});
        base.parts.push_back(upload(device, parent, descriptorLayout, sampler));
        base.sources.emplace("p", Source{1, 1, {"c"}, {{0, 0, 3}}});
        base.sources.emplace("q", Source{1, 1, {"d"}, {{0, 3, 3}}});
        base.payload = parent.payload;
        base.sourceCut = std::make_unique<hongtu::renderer::NativeSourceFrontier>(
            std::vector<hongtu::renderer::NativeSourceNode>{
                {"root", {"p", "q"}}, {"p", {"c"}}, {"q", {"d"}}, {"c", {}}, {"d", {}}},
            "root",
            std::set<std::string>{"p", "q"},
            base.payload,
            4 * parent.payload);
        shared.payload = base.payload;
        shared.resident.emplace(0, std::move(base));
        auto& r = shared.resident.at(0);
        const auto refine = [&](const std::string& source, const std::string& leaf, const Cpu& cpu) {
          Resident f;
          f.parts.push_back(upload(device, cpu, descriptorLayout, sampler));
          f.sources.emplace(leaf, Source{2, 2, {}, {{0, 0, 6}}});
          f.payload = cpu.payload;
          r.families.emplace(source, std::move(f));
          const auto t = r.sourceCut->prepare(source, {leaf}, cpu.payload, 1);
          require(bool(t) && r.sourceCut->markPartReady(*t, 0) && r.sourceCut->commit(*t), "Shared-page cut failed");
          r.payload += cpu.payload;
          shared.payload += cpu.payload;
          ++shared.familyCommits;
        };
        refine("p", "c", child);
        device->waitIdle();
        shared.retireHiddenBasePages();
        require(r.parts[0].payload == parent.payload && shared.hiddenSourcePageRetirements == 0,
                "Visible sibling lost shared physical page");
        refine("q", "d", blue);
        device->waitIdle();
        const auto sharedBefore = allocation(device);
        shared.retireHiddenBasePages();
        const auto sharedAfter = allocation(device);
        require(r.parts[0].payload == 0 && shared.hiddenSourcePageRetirements == 1,
                "Fully replaced shared page retained");
        require(
            sharedBefore.at("liveDescriptors").get<uint64_t>() == sharedAfter.at("liveDescriptors").get<uint64_t>() + 1,
            "Shared page descriptor not freed");
        exactColor(render(device, target, pipeline, pipelineLayout, r.families.at("p").parts[0]), {0, 255, 0, 255});
        exactColor(render(device, target, pipeline, pipelineLayout, r.families.at("q").parts[0]), {0, 0, 255, 255});
        report["sharedPageVisibleSiblingPreserved"] = true;
        report["fullyReplacedSharedPageReleased"] = true;
        device->waitIdle();
        shared.resident.clear();
      }
      report["churnObservations"] = Json::array();
      for (int i = 0; i < 32; ++i) {
        auto p = upload(device, (i % 2) ? child : parent, descriptorLayout, sampler);
        exactColor(render(device, target, pipeline, pipelineLayout, p),
                   (i % 2) ? std::array<uint8_t, 4>{0, 255, 0, 255} : std::array<uint8_t, 4>{255, 0, 0, 255});
        device->waitIdle();
        p = {};
        const auto a = allocation(device);
        report["churnObservations"].push_back(a);
        require(a.at("blockBytes").get<uint64_t>() <= before.at("blockBytes").get<uint64_t>(),
                "Allocator block growth during churn");
        require(a.at("allocationCount") == baseline.at("allocationCount") &&
                    a.at("allocationBytes") == baseline.at("allocationBytes") &&
                    a.at("liveDescriptors") == baseline.at("liveDescriptors") &&
                    a.at("descriptorFreeFailures").get<uint64_t>() == 0,
                "Churn allocation drift");
      }
      report["churnCycles"] = 32;
      report["final"] = allocation(device);
      report["fullLandscapeOrTwentySecondQualityAccepted"] = false;
      report["passed"] = true;
    }
    device->waitIdle();
    factory->destroyDevice(device);
    device = nullptr;
    Backend::destroyFactory(factory);
    factory = nullptr;
    std::ofstream out(argv[3]);
    out << report.dump(2) << '\n';
    require(bool(out), "Result write failed");
    std::cout << "PAGE_RHI_LIFECYCLE_PASS\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "PAGE_RHI_LIFECYCLE_FAIL: " << e.what() << '\n';
    if (device) {
      device->waitIdle();
      factory->destroyDevice(device);
    }
    if (factory)
      Backend::destroyFactory(factory);
    return 1;
  }
}
