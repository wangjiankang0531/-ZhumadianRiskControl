// Included inside a pager (or the independent score fixture). Only the current
// GPU histogram snapshot is cached; a new readback invalidates all entries.
struct VisibilityKey {
  int root = -1;
  std::string name;
  auto operator<=>(const VisibilityKey &) const = default;
};
struct VisibilityMetric {
  float edge = 0, texel = 0;
};
std::map<VisibilityKey, std::array<double, 256>> visibilityBins;
std::map<VisibilityKey, VisibilityMetric> visibilityMetrics;
using VisibilitySourceScoreKey = std::tuple<VisibilityKey, float, float, float, int>;
using VisibilityRootScoreKey = std::tuple<int, float, float, float, int>;
mutable std::map<VisibilitySourceScoreKey, double> visibilitySourceScores;
mutable std::map<VisibilityRootScoreKey, double> visibilityRootScores;
mutable uint64_t visibilityScoreEvaluations = 0, visibilityScoreCacheHits = 0;
uint64_t visibilityScoreCacheGeneration = 0;

void resetVisibilityScoreCache() {
  visibilitySourceScores.clear();
  visibilityRootScores.clear();
  ++visibilityScoreCacheGeneration;
}
void clearVisibilityScores() {
  resetVisibilityScoreCache();
  visibilityBins.clear();
  visibilityMetrics.clear();
  visibilityScoreEvaluations = visibilityScoreCacheHits = visibilityScoreCacheGeneration = 0;
}
static double visibilityDepth(uint32_t bin) {
  static const std::array<double, 256> depths = [] {
    std::array<double, 256> values{};
    for (size_t i = 0; i < values.size(); ++i)
      values[i] = .5 * std::pow(120000.0, double(i) / 255.0);
    return values;
  }();
  return depths.at(bin);
}
double visibilityPriority(VisibilityMetric metric, const std::array<double, 256> &bins, float fov,
                          int height) const {
  const double scale = std::max(metric.edge, metric.texel * 4) * double(height) /
                       (2 * std::tan(glm::radians(double(fov) * .5)));
  if (!(scale > 0) || !std::isfinite(scale))
    return 0;
  double score = 0;
  for (size_t bin = 0; bin < bins.size(); ++bin) {
    if (!(bins[bin] > 0))
      continue;
    const double quality = scale / visibilityDepth(static_cast<uint32_t>(bin));
    if (quality > 6)
      score += std::log2(1 + quality / 6) * bins[bin];
  }
  return score;
}
double visibilitySourcePriority(const VisibilityKey &key, VisibilityMetric metric,
                                const std::array<double, 256> &bins, float fov, int height) const {
  // Nonfinite inputs have no score and must not enter a floating-point map key.
  if (!std::isfinite(metric.edge) || !std::isfinite(metric.texel) || !std::isfinite(fov))
    return visibilityPriority(metric, bins, fov, height);
  const VisibilitySourceScoreKey cacheKey{key, metric.edge, metric.texel, fov, height};
  if (const auto found = visibilitySourceScores.find(cacheKey); found != visibilitySourceScores.end()) {
    ++visibilityScoreCacheHits;
    return found->second;
  }
  const double score = visibilityPriority(metric, bins, fov, height);
  visibilitySourceScores.emplace(cacheKey, score);
  ++visibilityScoreEvaluations;
  return score;
}
double visibilityPriority(int id, const std::string &name, VisibilityMetric metric, float fov, int height,
                          const std::set<std::string> *subtree = nullptr) const {
  if (!subtree) {
    const auto found = visibilityBins.find({id, name});
    return found == visibilityBins.end() ? 0
        : visibilitySourcePriority(found->first, metric, found->second, fov, height);
  }
  double score = 0;
  for (auto it = visibilityBins.lower_bound({id, ""}); it != visibilityBins.end() && it->first.root == id; ++it)
    if (subtree->contains(it->first.name))
      score += visibilitySourcePriority(it->first, metric, it->second, fov, height);
  return score;
}
double visibilityCurrentPriority(int id, float fov, int height,
                                 const std::set<std::string> *subtree = nullptr) const {
  double score = 0;
  for (auto it = visibilityBins.lower_bound({id, ""}); it != visibilityBins.end() && it->first.root == id; ++it)
    if (!subtree || subtree->contains(it->first.name))
      score += visibilitySourcePriority(it->first, visibilityMetrics.at(it->first), it->second, fov, height);
  return score;
}
double visibilityRootPriority(int id, float fov, int height) const {
  const VisibilityMetric metric{roots.at(id).baseEdge, roots.at(id).baseTexel};
  if (!std::isfinite(metric.edge) || !std::isfinite(metric.texel) || !std::isfinite(fov)) {
    double score = 0;
    for (auto it = visibilityBins.lower_bound({id, ""}); it != visibilityBins.end() && it->first.root == id; ++it)
      score += visibilityPriority(metric, it->second, fov, height);
    return score;
  }
  const VisibilityRootScoreKey cacheKey{id, metric.edge, metric.texel, fov, height};
  if (const auto found = visibilityRootScores.find(cacheKey); found != visibilityRootScores.end()) {
    ++visibilityScoreCacheHits;
    return found->second;
  }
  double score = 0;
  for (auto it = visibilityBins.lower_bound({id, ""}); it != visibilityBins.end() && it->first.root == id; ++it)
    score += visibilitySourcePriority(it->first, metric, it->second, fov, height);
  visibilityRootScores.emplace(cacheKey, score);
  return score;
}
