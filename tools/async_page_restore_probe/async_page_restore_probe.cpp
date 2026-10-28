#define main page_lifecycle_component_main
#include "native_page_rhi_probe.cpp"
#undef main
#include <glm/glm.hpp>
#include <hongtu/renderer/native_geometry_lod.hpp>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <future>
#include <mutex>
#include <thread>

struct AsyncSource : Source {
  bool hasBounds = true;
  glm::vec3 low{-1, -1, 0}, high{1, 1, 0};
  float edge = .1f, texel = 0;
};
using ZhumadianNativeSource = AsyncSource;
struct ZhumadianNativeCpu : Cpu {
  bool valid = true;
  int depth = 0;
  std::string error;
  std::vector<ZhumadianNativeCpu> parts;
  std::map<std::string, AsyncSource> sources;
};
struct AsyncResident {
  int depth = 0;
  uint64_t payload = 0, retiredBasePayload = 0;
  std::vector<Part> parts;
  std::map<std::string, AsyncSource> sources;
  std::map<std::string, AsyncResident> families;
  std::shared_ptr<hongtu::renderer::NativeSourceFrontier> sourceCut;
  std::vector<hongtu::renderer::NativeSourceNode> topology;
};
struct Decoder {
  ZhumadianNativeCpu answer;
  std::promise<void> promise;
  std::shared_future<void> gate = promise.get_future().share();
  std::mutex mutex;
  std::condition_variable cv;
  bool entered = false, released = false;
  std::atomic<int> calls{0};
  void enter() {
    ++calls;
    {
      std::lock_guard lock(mutex);
      entered = true;
    }
    cv.notify_all();
  }
  void waitEntered() {
    std::unique_lock lock(mutex);
    require(cv.wait_for(lock, std::chrono::seconds(2), [&] { return entered; }), "Decoder thread not entered");
  }
  void release() {
    if (!released) {
      released = true;
      promise.set_value();
    }
  }
};
static std::shared_ptr<Decoder> currentDecoder;
static ZhumadianNativeCpu decodeZhumadianNativeChunks(int tile, int depth, bool picking, const std::string& parent) {
  auto decoder = currentDecoder;
  require(decoder && tile == 1 && depth == 0 && picking && parent.empty(), "Unexpected synthetic decode request");
  decoder->enter();
  decoder->gate.wait();
  return decoder->answer;
}
struct ShowcaseMaterialTextureBinding {
  RHIDescriptorSetLayoutPtr layout;
  RHISamplerPtr sampler;
};
struct AsyncHarness {
  using Resident = AsyncResident;
  RHIDevice* device;
  std::map<int, Resident> resident;
  uint64_t payload = 0, budget = 1048576, rootCap = 1048576;
  int focusId = 0;
  std::map<int, int> desired;
  std::set<int> failed;
  struct Root {
    int tile = 1;
  };
  std::map<int, Root> roots{{0, {1}}};
  std::future<ZhumadianNativeCpu> pending;
  std::optional<ZhumadianNativeCpu> staged;
  int pendingId = -1, stagingId = -1;
  std::future<ZhumadianNativeCpu> familyPending;
  std::optional<ZhumadianNativeCpu> familyStaged;
  Resident familyGpu;
  struct FamilyTarget {
    int id = -1, depth = 0;
    std::string parent;
  };
  FamilyTarget familyRequest, familyDesired;
  std::shared_ptr<hongtu::renderer::NativeSourceFrontier> familyCut;
  std::optional<hongtu::renderer::NativeSourceFrontier::Ticket> familyTicket;
  size_t familyNext = 0;
  std::set<std::pair<int, std::string>> familyFailed;
  uint64_t familyCommits = 0, familyCoarsenings = 0, familyCancellations = 0, evictions = 0, failures = 0, requests = 0,
           uploads = 0, maxUpload = 0, partUploads = 0, peakPayload = 0;
  int uploadAttempts = 0, failUploadAt = 0;
  std::vector<std::string> outcomes;
  bool visibilityScheduling() const {
    return true;
  }
  bool visibleRootGuardEnabled() const {
    return true;
  }
  uint64_t rootBudget(int) const {
    return rootCap;
  }
  void recordOutcome(const std::string& outcome, int, int, const std::string&, const std::string&) {
    outcomes.push_back(outcome);
  }
  Part uploadFamilyPart(RHIDevice* d, const ShowcaseMaterialTextureBinding& material, const ZhumadianNativeCpu& cpu) {
    if (++uploadAttempts == failUploadAt)
      throw std::runtime_error("Injected synthetic second-part upload failure");
    return upload(d, cpu, material.layout, material.sampler);
  }
#include "production/native_retained_page_lifecycle.inl"
  RetainedPageResourceSnapshot captureRetainedPageResources() const {
    const auto d = device->getDescriptorAllocationInfo();
    const auto m = device->getMemoryBudgetInfo();
    return {d.available, d.liveSets, m.allocatorAllocationBytes, m.allocatorAllocationCount};
  }
#include "production/native_family_restore_controls.inl"
#include "production/native_retained_parent_restore.inl"
};
struct Scenario {
  std::shared_ptr<Decoder> decoder = std::make_shared<Decoder>();
  AsyncHarness h;
  struct ReleaseOnExit {
    std::shared_ptr<Decoder> d;
    ~ReleaseOnExit() {
      d->release();
    }
  } release;
  Scenario(RHIDevice* d, const ShowcaseMaterialTextureBinding& material) : h{d}, release{decoder} {
    require(!currentDecoder || currentDecoder.use_count() <= 1, "Prior decoder still active");
    currentDecoder = decoder;
    const auto make = [](std::array<uint8_t, 4> color) {
      ZhumadianNativeCpu c;
      static_cast<Cpu&>(c) = pixels(color);
      return c;
    };
    auto red = make({255, 0, 0, 255}), blue = make({0, 0, 255, 255}), green = make({0, 255, 0, 255});
    AsyncSource parent;
    parent.depth = 0;
    parent.triangles = 2;
    parent.children = {"child"};
    parent.spans = {{0, 0, 3}, {1, 3, 3}};
    AsyncSource child;
    child.depth = 1;
    child.triangles = 2;
    child.spans = {{0, 0, 6}};
    AsyncResident ready;
    ready.parts.push_back(upload(d, red, material.layout, material.sampler));
    ready.parts.push_back(upload(d, blue, material.layout, material.sampler));
    ready.sources.emplace("parent", parent);
    ready.payload = red.payload + blue.payload;
    ready.topology = {{"parent", {"child"}}, {"child", {}}};
    ready.sourceCut = std::make_shared<hongtu::renderer::NativeSourceFrontier>(
        ready.topology, "parent", std::set<std::string>{"parent"}, ready.payload, 4 * red.payload);
    AsyncResident family;
    family.depth = 1;
    family.parts.push_back(upload(d, green, material.layout, material.sampler));
    family.sources.emplace("child", child);
    family.payload = green.payload;
    ready.families.emplace("parent", std::move(family));
    auto ticket = ready.sourceCut->prepare("parent", {"child"}, green.payload, 1);
    require(bool(ticket) && ready.sourceCut->markPartReady(*ticket, 0) && ready.sourceCut->commit(*ticket),
            "Scenario child cut failed");
    ready.payload += green.payload;
    h.payload = ready.payload;
    h.familyCommits = 1;
    h.desired[0] = 0;
    h.resident.emplace(0, std::move(ready));
    d->waitIdle();
    h.retireHiddenBasePages();
    require(h.resident.at(0).parts[0].payload == 0 && h.resident.at(0).parts[1].payload == 0,
            "Parent pages not retired");
    decoder->answer.parts = {red, blue};
    decoder->answer.sources = {{"parent", parent}};
    decoder->answer.payload = red.payload + blue.payload;
  }
  bool frame(const ShowcaseMaterialTextureBinding& material, glm::vec3 camera = {100000, 100000, 100000}) {
    h.device->waitIdle();
    return h.serviceRetainedParentPages(h.device, material, camera, 60, 64);
  }
  void finishDecode() {
    decoder->release();
    h.familyPending.wait();
  }
};
static void childVisible(Scenario& s,
                         RHIDevice* d,
                         const RHIOffscreenTargetPtr& target,
                         const RHIPipelinePtr& pipeline,
                         const RHIPipelineLayoutPtr& layout) {
  require(s.h.resident.contains(0) && s.h.resident.at(0).sourceCut->visible() == std::set<std::string>{"child"},
          "Complete visible child cut lost");
  exactColor(render(d, target, pipeline, layout, s.h.resident.at(0).families.at("parent").parts[0]), {0, 255, 0, 255});
}
int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "usage: async_probe baseline|fixed vertex.spv fragment.spv result.json\n";
    return 2;
  }
  const bool baselineMode = std::string(argv[1]) == "baseline";
  if (!baselineMode && std::string(argv[1]) != "fixed")
    return 2;
  auto factory = Backend::createFactory(Backend::Type::Vulkan);
  RHIDevice* device = nullptr;
  Json report;
  report["cases"] = Json::array();
  try {
    require(factory != nullptr, "Factory unavailable");
    const bool validation = validationAvailable();
    device = factory->createDevice(validation);
    require(device != nullptr, "Device unavailable");
    report["validationLayerEnabled"] = validation;
    report["device"] = device->getProperties().deviceName;
    {
      auto target = device->createOffscreenTarget(64, 64);
      DescriptorSetLayoutDesc dl;
      dl.bindings.push_back(
          {0, 1, static_cast<ShaderStageFlags>(ShaderStageFlagBits::Fragment), DescriptorType::CombinedImageSampler});
      auto descriptorLayout = device->createDescriptorSetLayout(dl);
      PipelineLayoutDesc pl;
      pl.setLayouts = {descriptorLayout};
      auto pipelineLayout = device->createPipelineLayout(pl);
      auto sampler = device->createSampler({});
      ShowcaseMaterialTextureBinding material{descriptorLayout, sampler};
      ShaderDesc vd;
      vd.stage = ShaderStageFlagBits::Vertex;
      vd.spirvCode = spirv(argv[2]);
      ShaderDesc fd;
      fd.stage = ShaderStageFlagBits::Fragment;
      fd.spirvCode = spirv(argv[3]);
      GraphicsPipelineDesc pd;
      pd.shaders = {device->createShader(vd), device->createShader(fd)};
      pd.vertexInput.bindings = {{0, sizeof(Vertex), false}};
      pd.vertexInput.attributes = {{0, 0, Format::R32G32_SFLOAT, 0}};
      pd.rasterization.cullMode = CullMode::None;
      pd.depthStencil.depthTestEnable = false;
      pd.depthStencil.depthWriteEnable = false;
      pd.colorBlendAttachments.push_back({});
      pd.pipelineLayout = pipelineLayout;
      pd.renderPass = target->getRenderPass();
      auto pipeline = device->createGraphicsPipeline(pd);
      require(bool(pipeline), "Pipeline failed");
      auto fixedAllocation = allocation(device);
      if (baselineMode) {
        Scenario s(device, material);
        childVisible(s, device, target, pipeline, pipelineLayout);
        s.h.parentRestoreFailed.insert({0, "parent"});
        s.frame(material);
        require(s.h.resident.empty() && s.h.evictions == 1 && s.h.payload == 0,
                "Expected original complete-child eviction not reproduced");
        report["originalFailureEvictsCompleteChildCut"] = true;
        report["decoderCalls"] = s.decoder->calls.load();
      } else {
        {
          Scenario s(device, material);
          s.h.parentRestoreFailed.insert({0, "parent"});
          const auto original = s.h.payload;
          for (int i = 0; i < 3; ++i) {
            s.frame(material);
            childVisible(s, device, target, pipeline, pipelineLayout);
          }
          require(s.h.payload == original && s.h.evictions == 0 && s.decoder->calls == 0,
                  "Failed parent altered current cut or retried");
          report["cases"].push_back("known_parent_failure_keeps_child_cut");
        }
        {
          Scenario s(device, material);
          const auto bytes = s.h.payload;
          require(s.frame(material), "Async restore did not start");
          s.decoder->waitEntered();
          childVisible(s, device, target, pipeline, pipelineLayout);
          s.finishDecode();
          s.frame(material);
          require(s.h.familyStaged && s.h.familyNext == 1 && s.h.parentPageRestorations == 0,
                  "Partial restore published early");
          childVisible(s, device, target, pipeline, pipelineLayout);
          s.frame(material);
          auto& r = s.h.resident.at(0);
          require(r.sourceCut->visible() == std::set<std::string>{"parent"} && r.families.empty() &&
                      s.h.parentPageRestorations == 2 && s.h.partUploads == 2 && s.h.requests == 1,
                  "Complete async restore not atomically committed");
          exactColor(render(device, target, pipeline, pipelineLayout, r.parts[0]), {255, 0, 0, 255});
          exactColor(render(device, target, pipeline, pipelineLayout, r.parts[1]), {0, 0, 255, 255});
          require(s.h.payload == 2 * bytes, "Restored payload mismatch");
          report["cases"].push_back("two_page_async_decode_upload_atomic_restore");
        }
        for (int mode = 0; mode < 3; ++mode) {
          Scenario s(device, material);
          if (mode == 0) {
            s.decoder->answer.valid = false;
            s.decoder->answer.error = "Injected synthetic decode failure";
          } else if (mode == 1)
            s.decoder->answer.parts[0].image.rgba[0] ^= 1;
          else
            s.decoder->answer.sources.at("parent").spans[0].count = 6;
          require(s.frame(material), "Failure scenario did not schedule");
          s.decoder->waitEntered();
          s.finishDecode();
          s.frame(material);
          for (int i = 0; i < 3; ++i) {
            s.frame(material);
            childVisible(s, device, target, pipeline, pipelineLayout);
          }
          require(s.h.failures == 1 && s.h.parentRestoreFailed.contains({0, "parent"}) && s.decoder->calls == 1 &&
                      !s.h.familyPending.valid(),
                  "Failed request repeated from stale candidates");
          report["cases"].push_back(mode == 0   ? "decode_failure_keeps_cut_no_same_frame_retry"
                                    : mode == 1 ? "pixel_identity_failure_keeps_cut"
                                                : "source_layout_failure_keeps_cut");
        }
        {
          Scenario s(device, material);
          s.frame(material);
          s.decoder->waitEntered();
          s.h.desired.erase(0);
          s.finishDecode();
          s.frame(material);
          childVisible(s, device, target, pipeline, pipelineLayout);
          require(s.h.parentRestoreCancellations == 1 && s.h.partUploads == 0, "Undesired restore committed");
          report["cases"].push_back("desired_root_removed_discards_decode");
        }
        {
          Scenario s(device, material);
          s.frame(material);
          s.decoder->waitEntered();
          auto& r = s.h.resident.at(0);
          r.sourceCut = std::make_shared<hongtu::renderer::NativeSourceFrontier>(
              r.topology, "parent", std::set<std::string>{"child"}, r.payload, 4 * r.payload);
          s.finishDecode();
          s.frame(material);
          childVisible(s, device, target, pipeline, pipelineLayout);
          require(s.h.parentRestoreCancellations == 1 && s.h.partUploads == 0, "Stale cut identity accepted");
          report["cases"].push_back("cut_identity_change_discards_decode");
        }
        {
          Scenario s(device, material);
          auto before = allocation(device);
          s.frame(material);
          s.decoder->waitEntered();
          s.finishDecode();
          s.frame(material);
          require(s.h.familyNext == 1, "Expected staged first parent page");
          s.frame(material, {0, 0, 1});
          childVisible(s, device, target, pipeline, pipelineLayout);
          auto after = allocation(device);
          require(s.h.parentRestoreCancellations == 1 && s.h.parentPageRestorations == 0 &&
                      after.at("allocationBytes") == before.at("allocationBytes") &&
                      after.at("liveDescriptors") == before.at("liveDescriptors"),
                  "Partial upload cancellation leaked or switched cut");
          report["cases"].push_back("camera_change_cancels_partial_gpu_upload");
        }
        {
          Scenario s(device, material);
          s.h.budget = 3 * s.h.payload - 1;
          s.frame(material);
          s.decoder->waitEntered();
          s.finishDecode();
          s.frame(material);
          for (int i = 0; i < 3; ++i)
            s.frame(material);
          childVisible(s, device, target, pipeline, pipelineLayout);
          require(s.h.parentRestoreCancellations == 1 && s.h.partUploads == 0 && s.decoder->calls == 1,
                  "Concurrent budget rejection retried or uploaded");
          report["cases"].push_back("concurrent_budget_rejection_preserves_child");
        }
        {
          Scenario s(device, material);
          const auto before = allocation(device);
          s.h.failUploadAt = 2;
          s.frame(material);
          s.decoder->waitEntered();
          s.finishDecode();
          s.frame(material);
          childVisible(s, device, target, pipeline, pipelineLayout);
          s.frame(material);
          for (int i = 0; i < 3; ++i)
            s.frame(material);
          childVisible(s, device, target, pipeline, pipelineLayout);
          auto after = allocation(device);
          require(s.h.failures == 1 && s.h.parentPageRestorations == 0 && s.decoder->calls == 1 &&
                      after.at("allocationBytes") == before.at("allocationBytes") &&
                      after.at("liveDescriptors") == before.at("liveDescriptors"),
                  "GPU failure lost child or leaked");
          report["cases"].push_back("second_gpu_part_failure_releases_partial_keeps_child");
        }
        require(report["cases"].size() == 10, "Missing controller scenario");
        report["productionAsyncControllerExercised"] = true;
      }
      device->waitIdle();
      auto final = allocation(device);
      require(final.at("allocationCount") == fixedAllocation.at("allocationCount") &&
                  final.at("allocationBytes") == fixedAllocation.at("allocationBytes") &&
                  final.at("liveDescriptors") == fixedAllocation.at("liveDescriptors"),
              "Scenario resources leaked");
      report["finalAllocation"] = final;
      report["passed"] = true;
      report["oldFailedExecutableOrGISReaderStarted"] = false;
      report["fullLandscapeQualityAccepted"] = false;
    }
    device->waitIdle();
    factory->destroyDevice(device);
    device = nullptr;
    Backend::destroyFactory(factory);
    factory = nullptr;
    std::ofstream out(argv[4]);
    out << report.dump(2) << '\n';
    require(bool(out), "Result write failed");
    std::cout << "ASYNC_CONTROLLER_PASS\n";
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "ASYNC_CONTROLLER_FAIL: " << e.what() << '\n';
    if (device) {
      device->waitIdle();
      factory->destroyDevice(device);
    }
    if (factory)
      Backend::destroyFactory(factory);
    return 1;
  }
}
