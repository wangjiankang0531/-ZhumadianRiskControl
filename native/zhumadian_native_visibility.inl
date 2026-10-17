// Included inside ZhumadianNativePager. The caller has waited its draw fence.
// A small, depth-tested source-ID target reuses the exact current draw buffers.
#include "zhumadian_native_visibility_scores.inl"
struct VisibilityPush {
  glm::mat4 mvp;
  glm::vec4 camera, forward, color;
};
static_assert(sizeof(VisibilityPush) == 112);
bool visibilityEnabled = false;
Cli visibilityCli;
RHIBufferPtr visibilityBaseVertices, visibilityBaseIndices;
RHIOffscreenTargetPtr visibilityTarget;
RHIPipelineLayoutPtr visibilityLayout;
RHIPipelinePtr visibilityPipeline;
RHIShaderPtr visibilityVertexShader, visibilityFragmentShader;
uint32_t visibilityIndexCount = 0, visibilityWidth = 96, visibilityHeight = 0;
std::string visibilitySignature, visibilityCameraSignature;
nlohmann::json visibilityProbes = nlohmann::json::array();
uint64_t visibilitySamples = 0;
std::set<int> visibilityDeferred;
double visibilityMilliseconds = 0, visibilityDeficit = 0;
double visibilityTotalWeight = 0;
std::array<uint32_t, 4> visibilityAttention{};

void clearVisibility() {
  visibilityPipeline.reset();
  visibilityLayout.reset();
  visibilityTarget.reset();
  visibilityVertexShader.reset();
  visibilityFragmentShader.reset();
  visibilityBaseVertices.reset();
  visibilityBaseIndices.reset();
  visibilitySignature.clear();
  visibilityCameraSignature.clear();
  visibilityRetiredScores.clear();
  clearVisibilityScores();
  visibilityDeferred.clear();
  visibilityProbes = nlohmann::json::array();
  visibilityEnabled = false;
  visibilitySamples = 0;
  visibilityRootCosts.clear();
  visibilityFamilyCosts.clear();
  visibilityBudgetRetirements = 0;
  visibilityMilliseconds = visibilityDeficit = 0;
  visibilityTotalWeight = 0;
}
void configureVisibility(RHIDevice *device, const RHIBufferPtr &vertices, const RHIBufferPtr &indices,
                         uint32_t indexCount, const Cli &cli) {
  if (!cli.zhumadianNativeVisibility)
    return;
  if (!chunked || !pickingEnabled || !vertices || !indices)
    throw std::runtime_error("Source visibility requires the chunked landscape editor");
  visibilityEnabled = true;
  visibilityCli = cli;
  visibilityBaseVertices = vertices;
  visibilityBaseIndices = indices;
  visibilityIndexCount = indexCount;
  ShaderCompiler compiler;
  const auto vertex = compiler.compileGLSLToSPIRV(R"glsl(
    layout(location=0) in vec3 position;
    layout(location=4) in float kind;
    layout(location=0) out float viewDepth;
    layout(push_constant) uniform Push { mat4 mvp; vec4 camera; vec4 forward; vec4 color; } pc;
    void main() {
      vec3 pos = position;
      if (kind > 3.5) pos += pc.camera.xyz;
      gl_Position = pc.mvp * vec4(pos,1);
      if (kind > 3.5) gl_Position.z = gl_Position.w;
      viewDepth = dot(pos-pc.camera.xyz,pc.forward.xyz);
    }
  )glsl",
                                                  "main", "vertex");
  const auto fragment = compiler.compileGLSLToSPIRV(R"glsl(
    layout(location=0) in float viewDepth;
    layout(location=0) out vec4 outputColor;
    layout(push_constant) uniform Push { mat4 mvp; vec4 camera; vec4 forward; vec4 color; } pc;
    void main() {
      float depth = clamp(log2(max(viewDepth,0.5)/0.5)/log2(120000.0),0.0,1.0);
      outputColor = vec4(pc.color.rgb,depth);
    }
  )glsl",
                                                    "main", "fragment");
  if (!vertex.success || !fragment.success)
    throw std::runtime_error("Source visibility shader: " + vertex.errorMessage + fragment.errorMessage);
  ShaderDesc desc;
  desc.stage = ShaderStageFlagBits::Vertex;
  desc.spirvCode = vertex.spirvCode;
  visibilityVertexShader = device->createShader(desc);
  desc.stage = ShaderStageFlagBits::Fragment;
  desc.spirvCode = fragment.spirvCode;
  visibilityFragmentShader = device->createShader(desc);
  PipelineLayoutDesc layout;
  PushConstantRange range;
  range.stageFlags = ShaderStageFlagBits::Vertex | ShaderStageFlagBits::Fragment;
  range.size = sizeof(VisibilityPush);
  layout.pushConstantRanges.push_back(range);
  visibilityLayout = device->createPipelineLayout(layout);
  if (!visibilityVertexShader || !visibilityFragmentShader || !visibilityLayout)
    throw std::runtime_error("Source visibility resources unavailable");
}
void sampleVisibility(RHIDevice *device, glm::vec3 camera, glm::vec3 target, float fov, float aspect,
                      int height) {
  if (!visibilityEnabled)
    return;
  nlohmann::json state = {{"camera", {camera.x, camera.y, camera.z}},
                          {"target", {target.x, target.y, target.z}},
                          {"fov", fov},
                          {"aspect", aspect},
                          {"height", height},
                          {"uploads", uploads},
                          {"evictions", evictions},
                          {"coarsenings", familyCoarsenings}};
  auto cameraState = state;
  for (const auto *key : {"uploads", "evictions", "coarsenings"})
    cameraState.erase(key);
  const auto cameraSignature = cameraState.dump();
  if (visibilityCameraSignature != cameraSignature) {
    visibilityCameraSignature = cameraSignature;
    visibilityRetiredScores.clear();
  }
  const auto signature = state.dump();
  if (visibilitySignature == signature)
    return;
  const auto started = std::chrono::steady_clock::now();
  const uint32_t rh =
      std::clamp<uint32_t>(static_cast<uint32_t>(std::lround(visibilityWidth / aspect)), 16, 256);
  if (!visibilityTarget || visibilityHeight != rh) {
    visibilityPipeline.reset();
    visibilityTarget = device->createOffscreenTarget(visibilityWidth, rh, Format::R8G8B8A8_UNORM);
    if (!visibilityTarget)
      throw std::runtime_error("Source visibility target unavailable");
    visibilityHeight = rh;
    GraphicsPipelineDesc pipeline;
    pipeline.shaders = {visibilityVertexShader, visibilityFragmentShader};
    pipeline.vertexInput.bindings = {Vertex::binding()};
    pipeline.vertexInput.attributes = {Vertex::attributes()[0], Vertex::attributes()[4]};
    pipeline.primitiveTopology = PrimitiveTopology::TriangleList;
    pipeline.rasterization.cullMode = CullMode::None;
    pipeline.rasterization.fillMode = FillMode::Solid;
    pipeline.depthStencil.depthTestEnable = true;
    pipeline.depthStencil.depthWriteEnable = true;
    pipeline.depthStencil.depthCompareOp = CompareOp::Less;
    pipeline.renderPass = visibilityTarget->getRenderPass();
    pipeline.pipelineLayout = visibilityLayout;
    ColorBlendAttachmentState blend;
    blend.blendEnable = false;
    pipeline.colorBlendAttachments.push_back(blend);
    visibilityPipeline = device->createGraphicsPipeline(pipeline);
    if (!visibilityPipeline)
      throw std::runtime_error("Source visibility pipeline unavailable");
  }
  const auto clip = cameraClipPlanesFor(visibilityCli, camera);
  const auto view = glm::lookAt(camera, target, glm::vec3(0, 0, 1));
  auto projection = glm::perspective(glm::radians(fov), aspect, clip.nearMeters, clip.farMeters);
  projection[1][1] *= -1;
  VisibilityPush push{projection * view, glm::vec4(camera, 0), glm::vec4(glm::normalize(target - camera), 0),
                      glm::vec4(0)};
  auto cmd = device->createCommandBuffer();
  auto fence = device->createFence(false);
  cmd->begin();
  Rect2D area;
  area.extent = {visibilityWidth, rh};
  cmd->beginRenderPass(visibilityTarget->getRenderPass(), visibilityTarget->getFramebuffer(), area,
                       {{0, 0, 0, 0}}, 1, 0);
  Viewport viewport;
  viewport.width = float(visibilityWidth);
  viewport.height = float(rh);
  viewport.maxDepth = 1;
  cmd->setViewport(viewport);
  cmd->setScissor(area);
  cmd->bindPipeline(visibilityPipeline);
  const auto pushColor = [&](uint32_t id) {
    if (id > 0xffffff)
      throw std::runtime_error("Source visibility ID capacity exceeded");
    push.color =
        glm::vec4(float(id & 255) / 255, float((id >> 8) & 255) / 255, float((id >> 16) & 255) / 255, 0);
    cmd->pushConstants(visibilityLayout, ShaderStageFlagBits::Vertex | ShaderStageFlagBits::Fragment, 0,
                       sizeof(push), &push);
  };
  cmd->bindVertexBuffer(0, visibilityBaseVertices);
  cmd->bindIndexBuffer(visibilityBaseIndices);
  pushColor(0);
  if (prefixIndices)
    cmd->drawIndexed(prefixIndices);
  std::vector<VisibilityKey> registry(1);
  std::map<VisibilityKey, VisibilityMetric> metrics;
  const auto registerSource = [&](int id, const std::string &name, VisibilityMetric metric) {
    registry.push_back({id, name});
    metrics[{id, name}] = metric;
    pushColor(static_cast<uint32_t>(registry.size() - 1));
  };
  for (int id : rankZhumadianVisibleBounds(bounds, camera, target, true, fov, aspect, false)) {
    if (resident.contains(id))
      continue;
    registerSource(id, "", {roots[id].baseEdge, roots[id].baseTexel});
    for (const auto &span : roots[id].spans)
      cmd->drawIndexed(span.count, 1, prefixIndices + span.first);
  }
  for (const auto &[id, ready] : resident) {
    if (!ready.sourceCut)
      throw std::runtime_error("Source visibility requires an audited source cut");
    for (const auto &name : ready.sourceCut->visible()) {
      const auto *node = sourceRecord(ready, name);
      if (!node)
        throw std::runtime_error("Source visibility references missing record");
      const Resident *bundle = ready.sources.contains(name) ? &ready : nullptr;
      for (const auto &[parent, family] : ready.families)
        if (family.sources.contains(name))
          bundle = &family;
      if (!bundle)
        throw std::runtime_error("Source visibility references missing GPU bundle");
      registerSource(id, name, {node->edge, node->texel});
      for (const auto &span : node->spans) {
        const auto &part = bundle->parts.at(span.part);
        cmd->bindVertexBuffer(0, part.vertices);
        cmd->bindIndexBuffer(part.indices);
        cmd->drawIndexed(span.count, 1, span.first);
      }
    }
  }
  cmd->endRenderPass();
  cmd->end();
  device->submit({cmd}, {}, {}, fence);
  fence->wait();
  std::vector<uint8_t> pixels;
  uint32_t rw = 0, outHeight = 0;
  if (!visibilityTarget->readbackToBuffer(pixels, rw, outHeight) || rw != visibilityWidth ||
      outHeight != rh || pixels.size() != size_t(rw) * rh * 4)
    throw std::runtime_error("Source visibility readback failed");
  resetVisibilityScoreCache();
  visibilityBins.clear();
  visibilityMetrics = std::move(metrics);
  const auto decode = [&](size_t pixel) {
    const uint32_t id = uint32_t(pixels[pixel * 4]) | uint32_t(pixels[pixel * 4 + 1]) << 8 |
                        uint32_t(pixels[pixel * 4 + 2]) << 16;
    if (id >= registry.size())
      throw std::runtime_error("Source visibility readback contains invalid ID");
    return id;
  };
  // Preserve the inspected center without reserving a fixed root quota.
  // The central 40% by 40% receives four pixel votes; the rest still contributes.
  visibilityAttention = {rw * 3 / 10, rh * 3 / 10, rw * 7 / 10, rh * 7 / 10};
  const auto weightAt = [&](size_t pixel) {
    const auto x = uint32_t(pixel % rw), y = uint32_t(pixel / rw);
    return x >= visibilityAttention[0] && x < visibilityAttention[2] && y >= visibilityAttention[1] &&
                   y < visibilityAttention[3]
               ? 4.0
               : 1.0;
  };
  visibilityTotalWeight = double(rw) * rh + 3.0 * (visibilityAttention[2] - visibilityAttention[0]) *
                                                (visibilityAttention[3] - visibilityAttention[1]);
  for (size_t pixel = 0; pixel < size_t(rw) * rh; ++pixel) {
    const auto id = decode(pixel);
    if (id)
      visibilityBins[registry[id]][pixels[pixel * 4 + 3]] += weightAt(pixel) / visibilityTotalWeight;
  }
  visibilityDeficit = 0;
  for (const auto &[key, bins] : visibilityBins)
    visibilityDeficit += visibilitySourcePriority(key, visibilityMetrics.at(key), bins, fov, height);
  visibilityProbes = nlohmann::json::array();
  const auto inverse = glm::dmat4(glm::inverse(projection * view));
  for (int row = 1; row <= 5; ++row)
    for (int column = 1; column <= 5; ++column) {
      const uint32_t x = rw * column / 6, y = rh * row / 6;
      const size_t pixel = size_t(y) * rw + x;
      const auto id = decode(pixel);
      const float px = (float(x) + .5f) / rw * float(height) * aspect, py = (float(y) + .5f) / rh * height;
      const auto ray =
          hongtu::renderer::screenToWorldRay(px, height - py, float(height) * aspect, height, inverse);
      const auto &key = registry[id];
      visibilityProbes.push_back({{"raster_pixel", {x, y}},
                                  {"pixel", {px, py}},
                                  {"tile", id ? roots[key.root].tile : 0},
                                  {"source_node", id ? key.name : ""},
                                  {"depth_bin", pixels[pixel * 4 + 3]},
                                  {"pixel_weight", weightAt(pixel)},
                                  {"ray_origin", {ray.origin.x, ray.origin.y, ray.origin.z}},
                                  {"ray_direction", {ray.direction.x, ray.direction.y, ray.direction.z}}});
    }
  visibilitySignature = signature;
  ++visibilitySamples;
  visibilityMilliseconds =
      std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - started).count();
}
nlohmann::json visibilityStats() const {
  auto sources = nlohmann::json::array();
  for (const auto &[key, bins] : visibilityBins) {
    double weight = 0;
    auto depths = nlohmann::json::array();
    for (size_t bin = 0; bin < bins.size(); ++bin)
      if (bins[bin] > 0) {
        weight += bins[bin];
        depths.push_back({bin, bins[bin]});
      }
    sources.push_back({{"tile", roots[key.root].tile},
                       {"source_node", key.name},
                       {"weight", weight},
                       {"depth_bins", depths}});
  }
  return {
      {"view", visibilitySignature.empty() ? nlohmann::json() : nlohmann::json::parse(visibilitySignature)},
      {"enabled", visibilityEnabled},
      {"scheduling", visibilityScheduling()},
      {"width", visibilityWidth},
      {"height", visibilityHeight},
      {"samples", visibilitySamples},
      {"retirement_holds", visibilityRetiredScores.size()},
      {"normalization_weight", visibilityTotalWeight},
      {"attention_rectangle", visibilityAttention},
      {"attention_weight", 4},
      {"last_milliseconds", visibilityMilliseconds},
      {"weighted_quality_deficit", visibilityDeficit},
      {"score_cache_generation", visibilityScoreCacheGeneration},
      {"score_evaluations", visibilityScoreEvaluations},
      {"score_cache_hits", visibilityScoreCacheHits},
      {"score_cache_entries", visibilitySourceScores.size() + visibilityRootScores.size()},
      {"sources", sources},
      {"probe_pixels", visibilityProbes},
      {"method", "depth-tested current complete source cut, logarithmic per-pixel view-depth bins"}};
}
