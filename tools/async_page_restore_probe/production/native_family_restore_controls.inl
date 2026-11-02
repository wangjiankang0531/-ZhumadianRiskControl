static const ZhumadianNativeSource* sourceRecord(const Resident& ready, const std::string& name) {
  if (auto it = ready.sources.find(name); it != ready.sources.end())
    return &it->second;
  for (const auto& [parent, family] : ready.families)
    if (auto it = family.sources.find(name); it != family.sources.end())
      return &it->second;
  return nullptr;
}
void cancelFamily() {
  if (familyTicket && familyCut)
    familyCut->cancel(*familyTicket);
  familyStaged.reset();
  familyGpu = {};
  familyTicket.reset();
  familyCut.reset();
  familyNext = 0;
  familyRestoreSource.clear();familyRestoreOwner.clear();familyRestoreParts.clear();
}
void resetFamilies(Resident& ready) {
  if (!ready.sourceCut || ready.families.empty())
    return;
  if(std::any_of(ready.sources.begin(),ready.sources.end(),[&](const auto& entry){return !sourcePagesAvailable(ready,entry.first);}))return;
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
  if(!sourcePagesAvailable(ready,parent))throw std::logic_error("Cannot reveal retired parent pages");
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
