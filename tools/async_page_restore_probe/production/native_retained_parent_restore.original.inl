bool retainedRestoreDiagnosticStarted=false,retainedRestoreDiagnosticDone=false,retainedRestoreDiagnosticFailed=false;
int retainedRestoreDiagnosticId=-1;std::string retainedRestoreDiagnosticParent;
bool retainedRestoreDiagnosticEnabled() const {const char* flag=std::getenv("HT_NATIVE_RETAINED_PARENT_DIAGNOSTIC");return retainedPageLifecycleEnabled() && flag && std::string(flag)=="1";}
std::string familyRestoreSource, familyRestoreOwner;
std::vector<size_t> familyRestoreParts;
std::set<std::pair<int, std::string>> parentRestoreFailed;
std::map<std::pair<int, std::string>, uint64_t> parentRestoreCosts;
uint64_t parentPageRestorations = 0, parentRestoreCancellations = 0;
Resident *restoreOwner(Resident &ready) {
  return familyRestoreOwner.empty() ? &ready :
      ready.families.contains(familyRestoreOwner) ? &ready.families.at(familyRestoreOwner) : nullptr;
}



bool serviceRetainedParentPages(RHIDevice* device,const ShowcaseMaterialTextureBinding& material,glm::vec3 camera,float fov,int height) {
  std::vector<std::pair<int, std::string>> restoreCandidates;
  std::vector<int> completeRootFallbacks;
  for (auto& [id, ready] : resident) {
    if (!ready.sourceCut) continue;
    if (!visibilityScheduling() && id != focusId && ready.payload > rootBudget(id)) {
      if (std::all_of(ready.sources.begin(), ready.sources.end(),
          [&](const auto &entry) { return sourcePagesAvailable(ready, entry.first); })) resetFamilies(ready);
      continue;
    }
    std::vector<std::string> rollback;
    for (const auto& [parent, family] : ready.families) {
      const auto* node = sourceRecord(ready, parent);
      if (!node || !node->hasBounds) continue;
      const float distance = glm::length(glm::max(glm::max(node->low-camera, camera-node->high), glm::vec3(0)));
      if (hongtu::renderer::projectedNativeEdge(std::max(node->edge,node->texel*4),distance,fov,height)<2)
        rollback.push_back(parent);
    }
    for (const auto &parent : rollback) {
      if (!ready.families.contains(parent)) continue;
      if (!sourcePagesAvailable(ready,parent)) {
        if (parentRestoreFailed.contains({id,parent})) completeRootFallbacks.push_back(id);
        else restoreCandidates.emplace_back(id,parent);
      } else if (!(familyStaged && familyRequest.id==id) && !(familyPending.valid() && familyRequest.id==id))
        coarsenFamily(ready,parent);
    }
  }
  if(retainedRestoreDiagnosticEnabled() && !retainedRestoreDiagnosticStarted && familyCommits>0 && !familyPending.valid() && !familyStaged && !pending.valid() && !staged) {
    for(const auto& [id,ready]:resident) {
      for(const auto& [parent,family]:ready.families)if(!sourcePagesAvailable(ready,parent)) {retainedRestoreDiagnosticStarted=true;retainedRestoreDiagnosticId=id;retainedRestoreDiagnosticParent=parent;restoreCandidates={{id,parent}};break;}
      if(retainedRestoreDiagnosticStarted)break;
    }
    if(!retainedRestoreDiagnosticStarted)retainedRestoreDiagnosticFailed=true;
  }
  std::sort(completeRootFallbacks.begin(), completeRootFallbacks.end());
  completeRootFallbacks.erase(std::unique(completeRootFallbacks.begin(),completeRootFallbacks.end()),completeRootFallbacks.end());
  for (int id : completeRootFallbacks) {
    if (familyRequest.id==id && familyStaged) { cancelFamily(); ++familyCancellations; }
    payload-=resident.at(id).payload; resident.erase(id); desired.erase(id); failed.erase(id);
    familyFailed.clear(); ++evictions; ++missingBasePageFallbacks;
  }
  const auto restorationCurrent = [&] {
    if (familyRestoreSource.empty() || !resident.contains(familyRequest.id) || !desired.contains(familyRequest.id)) return false;
    auto &ready=resident.at(familyRequest.id);
    if (ready.sourceCut!=familyCut || !ready.families.contains(familyRestoreSource) || !restoreOwner(ready)) return false;
    const auto *node=sourceRecord(ready,familyRestoreSource);
    if (!node || !node->hasBounds) return false;
    const float distance=glm::length(glm::max(glm::max(node->low-camera,camera-node->high),glm::vec3(0)));
    if(retainedRestoreDiagnosticEnabled() && retainedRestoreDiagnosticId==familyRequest.id && retainedRestoreDiagnosticParent==familyRestoreSource && !retainedRestoreDiagnosticDone)return true;
    return hongtu::renderer::projectedNativeEdge(std::max(node->edge,node->texel*4),distance,fov,height)<2;
  };
  if (!familyRestoreSource.empty()) {
    if (familyPending.valid() && familyPending.wait_for(std::chrono::seconds(0))==std::future_status::ready) {
      auto cpu=familyPending.get();
      if (!restorationCurrent()) { if(retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone)retainedRestoreDiagnosticFailed=true;cancelFamily(); ++parentRestoreCancellations; }
      else {
        try {
          if (!cpu.valid) throw std::runtime_error(cpu.error);
          auto &ready=resident.at(familyRequest.id); auto *owner=restoreOwner(ready);
          const auto plan=nativePageRestorePlan(*owner,cpu,familyRestoreSource);
          parentRestoreCosts[{familyRequest.id,familyRestoreSource}]=plan.bytes;
          // No speculative subtraction of child pages: both generations fit.
          if (plan.bytes>budget || payload>budget-plan.bytes || plan.bytes>rootBudget(familyRequest.id) ||
              ready.payload>rootBudget(familyRequest.id)-plan.bytes) {
            if(retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone)retainedRestoreDiagnosticFailed=true;cancelFamily(); ++parentRestoreCancellations;
          } else {
            std::vector<ZhumadianNativeCpu> selected;
            for (size_t part : plan.parts) selected.push_back(std::move(cpu.parts.at(part)));
            cpu.parts=std::move(selected); cpu.payload=plan.bytes;
            familyRestoreParts=plan.parts; familyNext=0; familyGpu={}; familyStaged=std::move(cpu);
          }
        } catch (const std::exception &error) {
          if(retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone)retainedRestoreDiagnosticFailed=true;
          parentRestoreFailed.insert({familyRequest.id,familyRestoreSource});
          recordOutcome("parent_restore_decode_or_identity_error",familyRequest.id,familyRequest.depth,error.what(),familyRestoreSource);
          cancelFamily(); ++failures;
        }
      }
    }
    if (familyStaged && !familyRestoreSource.empty()) {
      if (!restorationCurrent()) { if(retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone)retainedRestoreDiagnosticFailed=true;cancelFamily(); ++parentRestoreCancellations; }
      else {
        try {
          auto &ready=resident.at(familyRequest.id); auto *owner=restoreOwner(ready);
          if (familyStaged->payload>budget || payload>budget-familyStaged->payload ||
              familyStaged->payload>rootBudget(familyRequest.id) ||
              ready.payload>rootBudget(familyRequest.id)-familyStaged->payload)
            throw std::runtime_error("Parent restoration lost its concurrent reservation");
          if (familyNext<familyStaged->parts.size()) {
            auto &cpu=familyStaged->parts.at(familyNext);
            auto part=uploadFamilyPart(device,material,cpu);
            familyGpu.payload+=part.payload; familyGpu.parts.push_back(std::move(part));
            maxUpload=std::max(maxUpload,cpu.payload); ++partUploads;
            peakPayload=std::max(peakPayload,payload+familyGpu.payload); cpu={}; ++familyNext;
          }
          if (familyNext==familyStaged->parts.size()) {
            if (familyGpu.payload!=familyStaged->payload || familyGpu.parts.size()!=familyRestoreParts.size() ||
                familyGpu.payload>owner->retiredBasePayload) throw std::logic_error("Incomplete restored parent pages");
            for (size_t i=0;i<familyRestoreParts.size();++i) {
              const auto &old=owner->parts.at(familyRestoreParts[i]); const auto &fresh=familyGpu.parts[i];
              if (old.payload || old.pageIdentity!=fresh.pageIdentity || old.originalPageBytes!=fresh.payload)
                throw std::logic_error("Parent page identity changed during upload");
            }
            const uint64_t added=familyGpu.payload;
            // This is still the complete child cut. Publish every missing page
            // together before coarsenFamily is allowed to reveal the parent.
            const auto cut=ready.sourceCut->visible(); ready.sourceCut->reset(cut,ready.payload+added);
            for (size_t i=0;i<familyRestoreParts.size();++i)
              owner->parts.at(familyRestoreParts[i])=std::move(familyGpu.parts[i]);
            owner->retiredBasePayload-=added;
            if (owner!=&ready) owner->payload+=added;
            ready.payload+=added; payload+=added; parentPageRestorations+=familyRestoreParts.size();
            const auto parent=familyRestoreSource;
            familyGpu={}; familyStaged.reset(); cancelFamily();
            coarsenFamily(ready,parent); ++uploads; pageRetirementEpoch=uint64_t(-1);
            if(retainedRestoreDiagnosticStarted && retainedRestoreDiagnosticId==familyRequest.id && retainedRestoreDiagnosticParent==parent)retainedRestoreDiagnosticDone=true;
          }
        } catch (const std::exception &error) {
          if(retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone)retainedRestoreDiagnosticFailed=true;
          parentRestoreFailed.insert({familyRequest.id,familyRestoreSource});
          recordOutcome("parent_restore_gpu_error",familyRequest.id,familyRequest.depth,error.what(),familyRestoreSource);
          cancelFamily(); ++failures;
        }
      }
    }
    // Let an in-flight restoration own the single lane even if no pixels were
    // uploaded this frame. Root admission sees familyPending/familyStaged too.
    if (!familyRestoreSource.empty()) { familyDesired={}; return true; }
  }
  if (!familyPending.valid() && !familyStaged && !pending.valid() && !staged) {
    std::erase_if(restoreCandidates,[&](const auto &entry) {
      return !resident.contains(entry.first) || !resident.at(entry.first).families.contains(entry.second) ||
             !sourceRecord(resident.at(entry.first),entry.second);
    });
    std::stable_sort(restoreCandidates.begin(),restoreCandidates.end(),[&](const auto &a,const auto &b) {
      if (!resident.contains(a.first)) return false;
      if (!resident.contains(b.first)) return true;
      return sourceRecord(resident.at(a.first),a.second)->depth < sourceRecord(resident.at(b.first),b.second)->depth;
    });
    for (const auto &[id,parent] : restoreCandidates) {
      if (!resident.contains(id) || !desired.contains(id) || !resident.at(id).families.contains(parent)) continue;
      auto &ready=resident.at(id);
      if (const auto cost=parentRestoreCosts.find({id,parent});cost!=parentRestoreCosts.end() &&
          (cost->second>budget || payload>budget-cost->second || cost->second>rootBudget(id) || ready.payload>rootBudget(id)-cost->second)) continue;
      familyRestoreOwner.clear();
      if (!ready.sources.contains(parent)) {
        bool found=false;
        for (const auto &[key,bundle] : ready.families) if (bundle.sources.contains(parent)) {familyRestoreOwner=key;found=true;break;}
        if (!found) {parentRestoreFailed.insert({id,parent});continue;}
      }
      familyRestoreSource=parent; familyCut=ready.sourceCut;
      const auto *owner=restoreOwner(ready); const int tile=roots[id].tile,depth=owner->depth;
      familyRequest={id,depth,familyRestoreOwner}; const auto originalParent=familyRestoreOwner;
      familyPending=std::async(std::launch::async,[tile,depth,originalParent] {
        return decodeZhumadianNativeChunks(tile,depth,true,originalParent);
      }); ++requests; familyDesired={}; return true;
    }
  }

 if(retainedRestoreDiagnosticEnabled() && retainedRestoreDiagnosticStarted && !retainedRestoreDiagnosticDone && familyRestoreSource.empty())retainedRestoreDiagnosticFailed=true;
 return false;
}
