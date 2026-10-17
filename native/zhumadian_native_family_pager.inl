// Included inside ZhumadianNativePager. All mutations occur after the frame fence.
struct FamilyTarget {
  int id = -1, depth = 0;
  std::string parent;
};
std::future<ZhumadianNativeCpu> familyPending;
std::optional<ZhumadianNativeCpu> familyStaged;
Resident familyGpu;
FamilyTarget familyRequest, familyDesired;
std::shared_ptr<hongtu::renderer::NativeSourceFrontier> familyCut;
std::optional<hongtu::renderer::NativeSourceFrontier::Ticket> familyTicket;
size_t familyNext = 0;
std::set<std::pair<int, std::string>> familyFailed;
uint64_t familyCommits = 0, familyCoarsenings = 0, familyCancellations = 0;
std::string familyError;

static const ZhumadianNativeSource* sourceRecord(const Resident& ready, const std::string& name) {
  if (auto it = ready.sources.find(name); it != ready.sources.end())
    return &it->second;
  for (const auto& [parent, family] : ready.families)
    if (auto it = family.sources.find(name); it != family.sources.end())
      return &it->second;
  return nullptr;
}
static uint32_t visibleIndices(const Resident& ready) {
  if (!ready.sourceCut)
    return ready.indexCount;
  uint64_t count = 0;
  for (const auto& name : ready.sourceCut->visible())
    count += uint64_t(sourceRecord(ready, name)->triangles) * 3;
  return static_cast<uint32_t>(count);
}
static int visibleDepth(const Resident& ready) {
  int depth = ready.depth;
  if (ready.sourceCut)
    for (const auto& name : ready.sourceCut->visible())
      depth = std::max(depth, sourceRecord(ready, name)->depth);
  return depth;
}
static void installSources(Resident& ready, ZhumadianNativeCpu& cpu, bool whole) {
  ready.sources = std::move(cpu.sources);
  ready.topology = std::move(cpu.topology);
  ready.sourceRoot = std::move(cpu.sourceRoot);
  if (whole && !ready.sources.empty()) {
    hongtu::renderer::NativeSourceFrontier::Cut cut;
    for (const auto& [name, node] : ready.sources)
      cut.insert(name);
    ready.sourceCut = std::make_shared<hongtu::renderer::NativeSourceFrontier>(
        ready.topology, ready.sourceRoot, cut, ready.payload, 384ull * 1048576);
  }
}
void cancelFamily() {
  if (familyTicket && familyCut)
    familyCut->cancel(*familyTicket);
  familyStaged.reset();
  familyGpu = {};
  familyTicket.reset();
  familyCut.reset();
  familyNext = 0;
}
void resetFamilies(Resident& ready) {
  if (!ready.sourceCut || ready.families.empty())
    return;
  uint64_t retired = 0;
  for (const auto& [parent, family] : ready.families)
    retired += family.payload;
  hongtu::renderer::NativeSourceFrontier::Cut cut;
  for (const auto& [name, node] : ready.sources)
    cut.insert(name);
  ready.sourceCut->reset(cut, ready.payload - retired);
  ready.families.clear();
  ready.payload -= retired;
  payload -= retired;
  familyFailed.clear();
  ++familyCoarsenings;
}
void coarsenFamily(Resident& ready, const std::string& parent) {
  std::map<std::string, std::vector<std::string>> children;
  for (const auto& node : ready.topology)
    children[node.name] = node.children;
  std::set<std::string> subtree;
  std::function<void(const std::string&)> visit = [&](const auto& name) {
    subtree.insert(name);
    for (const auto& child : children.at(name))
      visit(child);
  };
  visit(parent);
  auto cut = ready.sourceCut->visible();
  for (const auto& name : subtree)
    cut.erase(name);
  cut.insert(parent);
  uint64_t retired = 0;
  for (const auto& [name, family] : ready.families)
    if (subtree.contains(name))
      retired += family.payload;
  ready.sourceCut->reset(cut, ready.payload - retired);
  for (auto it = ready.families.begin(); it != ready.families.end();)
    if (subtree.contains(it->first))
      it = ready.families.erase(it);
    else
      ++it;
  ready.payload -= retired;
  payload -= retired;
  familyFailed.clear();
  ++familyCoarsenings;
}
FamilyTarget wantedFamily(glm::vec3 camera, glm::vec3 target, float fov, float aspect, int height) const {
  if (!localEnabled || !chunked || !pickingEnabled)
    return {};
  struct Candidate {
    FamilyTarget target;
    float score;
    bool center;
  };
  std::vector<Candidate> candidates;
  std::vector<ZhumadianTexturePage> boxes;
  const auto forward = glm::normalize(target - camera);
  auto right = glm::cross(forward, glm::vec3(0, 0, 1));
  right = glm::length(right) < .001f ? glm::vec3(1, 0, 0) : glm::normalize(right);
  const auto up = glm::normalize(glm::cross(right, forward));
  const auto surface = pickRay({glm::dvec3(camera), glm::dvec3(forward)});
  const float tangent = std::tan(glm::radians(fov * .5f));
  for (const auto& [id, ready] : resident) {
    if (!ready.sourceCut)
      continue;
    for (const auto& name : ready.sourceCut->visible()) {
      const auto* node = sourceRecord(ready, name);
      if (!node->hasBounds || node->children.empty() ||
          (familyFailed.contains({id,name}) && !(visibilityScheduling() && visibilityFamilyCosts.contains({id,name}))))
        continue;
      const float distance = glm::length(glm::max(glm::max(node->low - camera, camera - node->high), glm::vec3(0)));
      const float quality =
          hongtu::renderer::projectedNativeEdge(std::max(node->edge, node->texel * 4), distance, fov, height);
      const float diameter =
          hongtu::renderer::projectedNativeEdge(glm::length(node->high - node->low), distance, fov, height);
      const auto delta = (node->low + node->high) * .5f - camera;
      const float along = glm::dot(delta, forward);
      const float centered = along > 1 ? glm::length(glm::vec2(glm::dot(delta, right) / (along * tangent * aspect),
                                                               glm::dot(delta, up) / (along * tangent)))
                                       : 2;
      const float score = visibilityScheduling()
                              ? float(visibilityPriority(id,name,{node->edge,node->texel},fov,height))
                              : hongtu::renderer::nativeSourceRefinementScore(quality,diameter,float(height),centered,true);
      if (visibilityScheduling() && !visibilityRequestAllowed(id,name,score)) continue;
      if (visibilityScheduling())
        if (const auto cost=visibilityFamilyCosts.find({id,name});cost!=visibilityFamilyCosts.end() &&
            !visibilityRoom(id,name,cost->second,score,fov,height)) continue;
      if (score <= 0)
        continue;
      ZhumadianTexturePage box{};
      box.boundsMin = node->low;
      box.boundsMax = node->high;
      boxes.push_back(box);
      candidates.push_back({{id, node->depth + 1, name},
                            score,
                            surface && surface->tile == roots[id].tile && surface->sourceNode == name});
    }
  }
  auto visible = rankZhumadianVisibleBounds(boxes, camera, target, true, fov, aspect, false);
  std::stable_sort(visible.begin(), visible.end(), [&](int a, int b) {
    if (!visibilityScheduling() && candidates[a].center != candidates[b].center)
      return candidates[a].center;
    return candidates[a].score > candidates[b].score;
  });
  return visible.empty() ? FamilyTarget{} : candidates[visible.front()].target;
}
Resident uploadFamilyPart(RHIDevice* device,
                          const ShowcaseMaterialTextureBinding& material,
                          const ZhumadianNativeCpu& cpu) {
  Resident part;
  part.vertices = makeHostBuffer(device, cpu.vertices, BufferUsageFlagBits::Vertex);
  part.indices = makeHostBuffer(device, cpu.indices, BufferUsageFlagBits::Index);
  const bool image = createUploadedRgbaTexture(
      device, cpu.image.width, cpu.image.height, cpu.image.rgba, part.texture, part.view, true);
  if (part.vertices && part.indices && image) {
    DescriptorSetDesc descriptors;
    for (uint32_t binding = 0; binding < 13; ++binding) {
      DescriptorBinding d;
      d.binding = binding;
      d.type = DescriptorType::CombinedImageSampler;
      d.textureView = part.view;
      d.sampler = material.sampler;
      descriptors.bindings.push_back(d);
    }
    part.descriptor = device->createDescriptorSet(material.layout, descriptors);
  }
  if (!part.descriptor)
    throw std::runtime_error("Local family GPU allocation failed; complete parent retained");
  part.payload = cpu.payload;
  part.indexCount = static_cast<uint32_t>(cpu.indices.size());
  return part;
}
void serviceFamilies(RHIDevice* device,
                     const ShowcaseMaterialTextureBinding& material,
                     glm::vec3 camera,
                     glm::vec3 target,
                     float fov,
                     float aspect,
                     int height) {
  for (auto& [id, ready] : resident) {
    if (!ready.sourceCut)
      continue;
    if (!visibilityScheduling() && id != focusId && ready.payload > rootBudget(id)) {
      resetFamilies(ready);
      continue;
    }
    std::vector<std::string> rollback;
    for (const auto& [parent, family] : ready.families) {
      const auto* node = sourceRecord(ready, parent);
      if (!node || !node->hasBounds)
        continue;
      const float distance = glm::length(glm::max(glm::max(node->low - camera, camera - node->high), glm::vec3(0)));
      if (hongtu::renderer::projectedNativeEdge(std::max(node->edge, node->texel * 4), distance, fov, height) < 2)
        rollback.push_back(parent);
    }
    for (const auto& parent : rollback)
      if (ready.families.contains(parent))
        coarsenFamily(ready, parent);
  }
  familyDesired = wantedFamily(camera,target,fov,aspect,height);
  if (visibilityScheduling() && !familyPending.valid() && !familyStaged && familyDesired.id>=0) {
    const auto* node=sourceRecord(resident.at(familyDesired.id),familyDesired.parent);
    const double score=visibilityPriority(familyDesired.id,familyDesired.parent,{node->edge,node->texel},fov,height);
    for (const auto& [id,depth] : desired)
      if (!resident.contains(id) && visibilityRootEligible(id,depth,fov,height) &&
          visibilityRootPriority(id,fov,height)>score) {familyDesired={};break;}
  }
  if (visibilityScheduling() && familyDesired.id>=0 &&
      visibilityFamilyCosts.contains({familyDesired.id,familyDesired.parent}))
    familyFailed.erase({familyDesired.id,familyDesired.parent});
  const auto current = [&] {
    if (visibilityScheduling()) {
      // Ranking picks the next transaction; it must not revoke an admitted,
      // still-visible parent just because making room changed another score.
      if (!resident.contains(familyRequest.id) || !desired.contains(familyRequest.id)) return false;
      const auto& ready=resident.at(familyRequest.id);
      if (!ready.sourceCut || !ready.sourceCut->visible().contains(familyRequest.parent)) return false;
      const auto* node=sourceRecord(ready,familyRequest.parent);
      return node && visibilityPriority(familyRequest.id,familyRequest.parent,{node->edge,node->texel},fov,height)>0;
    }
    return familyDesired.id == familyRequest.id && familyDesired.parent == familyRequest.parent &&
           resident.contains(familyRequest.id);
  };
  if (familyPending.valid() && familyPending.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
    auto cpu = familyPending.get();
    if (!current()) {
      ++familyCancellations;
    } else if (!cpu.valid) {
      familyFailed.insert({familyRequest.id, familyRequest.parent});
      familyError = cpu.error;
      ++failures;
      recordOutcome(cpu.error == "complete sibling family exceeds local candidate budget" ||
                            cpu.error == "family source decode budget exceeded"
                        ? "family_conversion_budget" : "family_decode_error",
                    familyRequest.id, familyRequest.depth, cpu.error, familyRequest.parent);
    } else {
      auto& ready = resident.at(familyRequest.id);
      if (visibilityScheduling()) {
        visibilityFamilyCosts[{familyRequest.id,familyRequest.parent}]=cpu.payload;
        const auto* node=sourceRecord(ready,familyRequest.parent);
        applyVisibilityRoom(familyRequest.id,familyRequest.parent,cpu.payload,
                            visibilityPriority(familyRequest.id,familyRequest.parent,{node->edge,node->texel},fov,height),fov,height);
      }
      if (!visibilityScheduling() && ready.payload + cpu.payload <= rootBudget(familyRequest.id)) {
        for (auto it = ranking.rbegin(); payload + cpu.payload > budget && it != ranking.rend(); ++it)
          if (*it != familyRequest.id && *it != focusId && resident.contains(*it) &&
              std::find(ranking.begin(), ranking.end(), *it) >
                  std::find(ranking.begin(), ranking.end(), familyRequest.id)) {
            payload -= resident.at(*it).payload;
            resident.erase(*it);
            desired.erase(*it);
            ++evictions;
          }
      }
      std::vector<std::string> children;
      for (const auto& [name, node] : cpu.sources)
        children.push_back(name);
      if (ready.payload + cpu.payload > rootBudget(familyRequest.id) || payload + cpu.payload > budget) {
        familyFailed.insert({familyRequest.id, familyRequest.parent});
        ++budgetFallbacks;
        recordOutcome("family_runtime_budget", familyRequest.id, familyRequest.depth,
                      "Complete family plus resident pages exceeds root or global budget", familyRequest.parent);
      } else {
        familyCut = ready.sourceCut;
        familyTicket = familyCut->prepare(familyRequest.parent, children, cpu.payload, cpu.parts.size());
        if (!familyTicket) {
          familyFailed.insert({familyRequest.id, familyRequest.parent});
          familyError = "Invalid complete family transaction";
          recordOutcome("family_transaction_rejection", familyRequest.id, familyRequest.depth,
                        familyError, familyRequest.parent);
        } else {
          familyStaged = std::move(cpu);
          familyGpu = {};
          familyNext = 0;
        }
      }
    }
  }
  if (familyStaged) {
    if (!current() || resident.at(familyRequest.id).sourceCut != familyCut) {
      cancelFamily();
      ++familyCancellations;
    } else {
      try {
        auto& cpu = familyStaged->parts.at(familyNext);
        auto part = uploadFamilyPart(device, material, cpu);
        familyGpu.payload += part.payload;
        familyGpu.indexCount += part.indexCount;
        familyGpu.parts.push_back(std::move(part));
        familyCut->markPartReady(*familyTicket, familyNext);
        maxUpload = std::max(maxUpload, cpu.payload);
        peakPayload = std::max(peakPayload, payload + familyGpu.payload);
        ++partUploads;
        cpu = {};
        ++familyNext;
        if (familyNext == familyStaged->parts.size()) {
          if (familyGpu.payload != familyStaged->payload)
            throw std::runtime_error("Incomplete source family upload");
          auto& ready = resident.at(familyRequest.id);
          installSources(familyGpu, *familyStaged, false);
          familyGpu.depth = familyRequest.depth;
          const auto addedBytes = familyGpu.payload;
          if (!ready.families.emplace(familyRequest.parent, std::move(familyGpu)).second)
            throw std::runtime_error("Duplicate source family allocation");
          if (!familyCut->commit(*familyTicket)) {
            ready.families.erase(familyRequest.parent);
            throw std::runtime_error("Source family commit cancelled");
          }
          ready.payload += addedBytes;
          payload += addedBytes;
          familyStaged.reset();
          familyGpu = {};
          familyTicket.reset();
          familyCut.reset();
          ++familyCommits;
          ++uploads;
          familyDesired = wantedFamily(camera, target, fov, aspect, height);
        }
      } catch (const std::exception& error) {
        familyError = error.what();
        familyFailed.insert({familyRequest.id, familyRequest.parent});
        cancelFamily();
        ++failures;
        recordOutcome("family_gpu_or_transaction_error", familyRequest.id, familyRequest.depth,
                      familyError, familyRequest.parent);
      }
    }
  }
  if (!familyPending.valid() && !familyStaged && !pending.valid() && !staged && familyDesired.id >= 0 &&
      !familyFailed.contains({familyDesired.id, familyDesired.parent})) {
    familyRequest = familyDesired;
    const int tile = roots[familyRequest.id].tile, depth = familyRequest.depth;
    const auto parent = familyRequest.parent;
    familyPending = std::async(
        std::launch::async, [tile, depth, parent] { return decodeZhumadianNativeChunks(tile, depth, true, parent); });
    ++requests;
  }
}
