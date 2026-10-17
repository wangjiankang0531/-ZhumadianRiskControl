// Transactional room planning: evaluate every retirement before mutating a cut.
// A two-times benefit margin keeps comparable branches from trading places.
struct VisibilityBudgetAction {
  int id;
  std::string parent;
};
std::map<std::pair<int, int>, uint64_t> visibilityRootCosts;
std::map<std::pair<int, std::string>, uint64_t> visibilityFamilyCosts;
uint64_t visibilityBudgetRetirements = 0;
std::map<std::pair<int, std::string>, double> visibilityRetiredScores;
bool visibilityRequestAllowed(int id, const std::string &parent, double score) const {
  const auto hold = visibilityRetiredScores.find({id, parent});
  return hold == visibilityRetiredScores.end() || score > hold->second * 2;
}

bool visibilityScheduling() const {
  return visibilityEnabled && visibilityCli.zhumadianNativeVisibilitySchedule;
}
std::set<std::string> visibilitySubtree(const Resident &ready, const std::string &parent) const {
  std::map<std::string, const std::vector<std::string> *> children;
  for (const auto &node : ready.topology)
    children.emplace(node.name, &node.children);
  std::set<std::string> subtree;
  std::function<void(const std::string &)> visit = [&](const auto &name) {
    if (!subtree.insert(name).second)
      throw std::logic_error("Repeated source in visibility plan");
    for (const auto &child : *children.at(name))
      visit(child);
  };
  visit(parent);
  return subtree;
}
std::optional<std::vector<VisibilityBudgetAction>> visibilityRoom(int requestId,
                                                                  const std::string &requestParent,
                                                                  uint64_t cost, double score, float fov,
                                                                  int height) const {
  if (!visibilityScheduling() || cost > rootBudget(requestId) || !(score > 0) ||
      !visibilityRequestAllowed(requestId, requestParent, score))
    return {};
  uint64_t used = payload, own = resident.contains(requestId) ? resident.at(requestId).payload : 0;
  size_t rootCount=resident.size()+size_t(requestParent.empty() && !resident.contains(requestId));
  const auto fits = [&] {
    return rootCount<=residentLimit() && cost <= budget && used <= budget - cost &&
           (requestParent.empty() || own <= rootBudget(requestId) - cost);
  };
  std::vector<VisibilityBudgetAction> actions;
  if (fits())
    return actions;
  struct Candidate {
    int id;
    std::string parent;
    double benefit;
    std::set<std::string> subtree;
  };
  std::vector<Candidate> candidates;
  for (const auto &[id, ready] : resident) {
    for (const auto &[parent, family] : ready.families) {
      auto subtree = visibilitySubtree(ready, parent);
      if (id == requestId && (requestParent.empty() || subtree.contains(requestParent)))
        continue;
      const auto *node = sourceRecord(ready, parent);
      if (!node)
        throw std::logic_error("Visibility plan missing parent");
      const double benefit =
          std::max(0.0, visibilityPriority(id, parent, {node->edge, node->texel}, fov, height, &subtree) -
                            visibilityCurrentPriority(id, fov, height, &subtree));
      if (benefit * 2 < score)
        candidates.push_back({id, parent, benefit, std::move(subtree)});
    }
    if (id != requestId) {
      const double benefit =
          std::max(0.0, visibilityRootPriority(id, fov, height) - visibilityCurrentPriority(id, fov, height));
      if (benefit * 2 < score)
        candidates.push_back({id, "", benefit, {}});
    }
  }
  std::stable_sort(candidates.begin(), candidates.end(), [](const auto &a, const auto &b) {
    return std::tie(a.benefit, a.id, a.parent) < std::tie(b.benefit, b.id, b.parent);
  });
  std::map<int, std::set<std::string>> remaining;
  for (const auto &[id, ready] : resident)
    for (const auto &[parent, family] : ready.families)
      remaining[id].insert(parent);
  std::map<int, uint64_t> retired;
  std::set<int> removedRoots;
  for (const auto &candidate : candidates) {
    const int id = candidate.id;
    if (removedRoots.contains(id))
      continue;
    uint64_t freed = 0;
    if (candidate.parent.empty()) {
      freed = resident.at(id).payload - retired[id];
      removedRoots.insert(id);
      --rootCount;
      actions.erase(std::remove_if(actions.begin(), actions.end(), [&](const auto &a) { return a.id == id; }),
                    actions.end());
    } else {
      for (auto it = remaining[id].begin(); it != remaining[id].end();) {
        if (candidate.subtree.contains(*it)) {
          freed += resident.at(id).families.at(*it).payload;
          it = remaining[id].erase(it);
        } else
          ++it;
      }
      if (!freed)
        continue;
      actions.erase(
          std::remove_if(actions.begin(), actions.end(),
                         [&](const auto &a) { return a.id == id && candidate.subtree.contains(a.parent); }),
          actions.end());
    }
    used -= freed;
    if (id == requestId)
      own -= freed;
    retired[id] += freed;
    actions.push_back({id, candidate.parent});
    if (fits())
      return actions;
  }
  return {}; // No live cut or resource changed by an unsuccessful plan.
}
bool applyVisibilityRoom(int id, const std::string &parent, uint64_t cost, double score, float fov,
                         int height) {
  const auto plan = visibilityRoom(id, parent, cost, score, fov, height);
  if (!plan)
    return false;
  for (const auto &action : *plan) {
    visibilityRetiredScores[{action.id, action.parent}] = score;
    if (action.parent.empty()) {
      payload -= resident.at(action.id).payload;
      resident.erase(action.id);
      desired.erase(action.id);
      failed[action.id] = -1;
      ++evictions;
    } else
      coarsenFamily(resident.at(action.id), action.parent);
    ++visibilityBudgetRetirements;
  }
  return true;
}
bool visibilityRootEligible(int id, int depth, float fov, int height) const {
  if (!visibilityRequestAllowed(id, "", visibilityRootPriority(id, fov, height)) ||
      !(visibilityRootPriority(id, fov, height) > 0))
    return false;
  // Unknown bytes still have a known slot requirement; do not decode a root
  // that cannot enter the bounded working set even with zero byte cost.
  if (!resident.contains(id) && resident.size()>=residentLimit() &&
      !visibilityRoom(id,"",0,visibilityRootPriority(id,fov,height),fov,height)) return false;
  if (const auto cost = visibilityRootCosts.find({id, depth}); cost != visibilityRootCosts.end())
    return visibilityRoom(id, "", cost->second, visibilityRootPriority(id, fov, height), fov, height)
        .has_value();
  return !failed.contains(id) || failed.at(id) != depth;
}
