struct RetainedPageResourceSnapshot {bool descriptorStatsAvailable=false;uint64_t liveDescriptors=0,allocationBytes=0,allocationCount=0;};
struct RetainedPageResourceEvent {uint64_t modelBytes=0,pages=0;RetainedPageResourceSnapshot before,after;};
std::vector<RetainedPageResourceEvent> retainedPageResourceEvents;
uint64_t retainedPageResourceEventsDropped=0;
bool retainedPageLifecycleEnabled() const {
 const char* flag=std::getenv("HT_NATIVE_RETAINED_PAGE_LIFECYCLE");
 return visibilityScheduling() && visibleRootGuardEnabled() && flag && std::string(flag)=="1";
}
// Source metadata survives GPU-page retirement; a rollback needs every page.
static const Resident *sourcePageOwner(const Resident &ready, const std::string &name) {
  if (ready.sources.contains(name)) return &ready;
  for (const auto &[parent, family] : ready.families)
    if (family.sources.contains(name)) return &family;
  return nullptr;
}
static bool sourcePagesAvailable(const Resident &ready, const std::string &name) {
  const auto *owner = sourcePageOwner(ready, name);
  if (!owner) return false;
  const auto &source = owner->sources.at(name);
  if (source.spans.empty()) return false;
  for (const auto &span : source.spans) {
    if (!span.count || span.part >= owner->parts.size()) return false;
    const auto &part = owner->parts[span.part];
    if (!part.payload || !part.descriptor || !part.view || !part.texture || !part.vertices || !part.indices)
      return false;
  }
  return true;
}
// Use full-cut membership, never one visibility histogram or an occluded frame.
static std::vector<size_t> hiddenPageIndices(const Resident &bundle,
                                            const hongtu::renderer::NativeSourceFrontier::Cut &cut) {
  if (bundle.parts.empty()) return {};
  std::vector<bool> referenced(bundle.parts.size()), visible(bundle.parts.size());
  for (const auto &[name, source] : bundle.sources)
    for (const auto &span : source.spans) {
      if (!span.count || span.part >= bundle.parts.size())
        throw std::logic_error("Invalid source page span");
      referenced[span.part] = true;
      visible[span.part] = visible[span.part] || cut.contains(name);
    }
  std::vector<size_t> result;
  for (size_t i = 0; i < bundle.parts.size(); ++i)
    if (bundle.parts[i].payload && referenced[i] && !visible[i]) result.push_back(i);
  return result;
}
uint64_t hiddenBasePageRetirements = 0, hiddenBaseBytesRetired = 0, missingBasePageFallbacks = 0;
uint64_t hiddenSourcePageRetirements = 0, hiddenSourceBytesRetired = 0;
uint64_t pageRetirementEpoch = uint64_t(-1);
uint64_t hiddenBasePagesBytes(const Resident &ready) const {
  if (!ready.sourceCut) return 0;
  uint64_t bytes = 0;
  for (size_t i : hiddenPageIndices(ready, ready.sourceCut->visible())) bytes += ready.parts[i].payload;
  return bytes;
}
void retireHiddenBasePages() {
  if (!retainedPageLifecycleEnabled() || pageRetirementEpoch == familyCommits) return;
  bool deferred = false;
  for (auto &[id, ready] : resident) {
    if (!ready.sourceCut) continue;
    if ((familyTicket && familyRequest.id == id) || (familyPending.valid() && familyRequest.id == id) ||
        (familyStaged && familyRequest.id == id) ||
        (staged && stagingId == id) || (pending.valid() && pendingId == id)) {
      deferred = true;
      continue;
    }
    struct Plan { Resident *bundle; std::vector<size_t> pages; uint64_t bytes; };
    std::vector<Plan> plans;
    uint64_t total = 0;
    const auto &cut = ready.sourceCut->visible();
    const auto plan = [&](Resident &bundle) {
      auto pages = hiddenPageIndices(bundle, cut);
      uint64_t bytes = 0;
      for (size_t i : pages) bytes += bundle.parts[i].payload;
      if (bytes > bundle.payload) throw std::logic_error("Invalid source bundle page accounting");
      if (bytes) { total += bytes; plans.push_back({&bundle, std::move(pages), bytes}); }
    };
    plan(ready);
    for (auto &[parent, family] : ready.families) plan(family);
    if (!total) continue;
    if (total > ready.payload || total > payload || ready.sourceCut->residentBytes() != ready.payload)
      throw std::logic_error("Invalid hidden source page accounting");
    const auto savedCut = cut;
    const auto resourceBefore=captureRetainedPageResources();
    uint64_t retiredPages=0;for(const auto& action:plans)retiredPages+=action.pages.size();
    // All spans and byte totals were checked before releasing any live resource.
    for (auto &action : plans) {
      for (size_t i : action.pages) {
        auto &part = action.bundle->parts[i];
        part.descriptor.reset(); part.view.reset(); part.texture.reset();
        part.vertices.reset(); part.indices.reset(); part.payload = 0;
      }
      action.bundle->retiredBasePayload += action.bytes;
      if (action.bundle != &ready) action.bundle->payload -= action.bytes;
      else { ++hiddenBasePageRetirements; hiddenBaseBytesRetired += action.bytes; }
      hiddenSourcePageRetirements += action.pages.size();
      hiddenSourceBytesRetired += action.bytes;
    }
    ready.payload -= total; payload -= total;
    ready.sourceCut->reset(savedCut, ready.payload);
    const auto resourceAfter=captureRetainedPageResources();
    if(retainedPageResourceEvents.size()<64)retainedPageResourceEvents.push_back({total,retiredPages,resourceBefore,resourceAfter});else ++retainedPageResourceEventsDropped;
  }
  // Only family commits can newly hide retained pages. Retry skipped active roots.
  if (!deferred) pageRetirementEpoch = familyCommits;
}
