// Compare production cached scores with an uncached, full-histogram oracle.
#ifdef NDEBUG
#error Score differential checks require active assertions
#endif
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cmath>
#include <compare>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <tuple>
#include <vector>
#include <glm/glm.hpp>
struct ScoreFixture {
  struct Root { float baseEdge = 0, baseTexel = 0; };
  std::vector<Root> roots;
#include "../native/zhumadian_native_visibility_scores.inl"
};
using Metric = ScoreFixture::VisibilityMetric;
using Bins = std::array<double, 256>;
static uint64_t checked = 0;
// Deliberately retain the old dense formula and all-root traversal as the oracle.
static double reference(Metric metric, const Bins &bins, float fov, int height) {
  const double scale = std::max(metric.edge, metric.texel * 4) * double(height) /
                       (2 * std::tan(glm::radians(double(fov) * .5)));
  if (!(scale > 0) || !std::isfinite(scale)) return 0;
  double sum = 0;
  for (size_t i = 0; i < 256; ++i) {
    const double q = scale / (.5 * std::pow(120000.0, double(i) / 255.0));
    if (q > 6) sum += std::log2(1 + q / 6) * bins[i];
  }
  return sum;
}
static double referenceRoot(const ScoreFixture &p, int id, float fov, int height) {
  double sum = 0;
  for (const auto &[key, bins] : p.visibilityBins)
    if (key.root == id) sum += reference({p.roots[id].baseEdge,p.roots[id].baseTexel},bins,fov,height);
  return sum;
}
static void equal(double actual, double expected) {
  ++checked;
  assert(std::isfinite(actual) && std::isfinite(expected));
  assert(std::abs(actual-expected) <= 1e-13 * std::max(1.0,std::abs(expected)));
}
int main() {
  ScoreFixture p; p.roots.resize(129);
  std::mt19937 random(20261017);
  std::uniform_real_distribution<float> metric(.001f,80.0f);
  for (int id=0;id<128;++id) {
    p.roots[id]={metric(random),metric(random)};
    for (int node=0;node<3;++node) {
      const ScoreFixture::VisibilityKey key{id,std::to_string(node)};
      auto &bins=p.visibilityBins[key];
      if (node==0) for (int b=0;b<256;++b) bins[b]=double(random()%100)/10000;
      else if (node==1) for (int b=0;b<6;++b) bins[random()%256]+=.01;
      p.visibilityMetrics[key]={metric(random),metric(random)};
    }
  }
  for (float fov : {25.f,45.f,110.f}) for (int height : {360,720,1440}) {
    for (int id=0;id<129;++id) {
      equal(p.visibilityRootPriority(id,fov,height),referenceRoot(p,id,fov,height));
      double current=0,subtreeCurrent=0,subtreeCoarse=0;
      const std::set<std::string> subtree{"0","2","absent"};
      Metric coarse{3,7};
      for (const auto &[key,bins] : p.visibilityBins) if (key.root==id) {
        const auto m=p.visibilityMetrics.at(key);
        equal(p.visibilityPriority(id,key.name,m,fov,height),reference(m,bins,fov,height));
        current+=reference(m,bins,fov,height);
        if (subtree.contains(key.name)) {
          subtreeCurrent+=reference(m,bins,fov,height);
          subtreeCoarse+=reference(coarse,bins,fov,height);
        }
      }
      equal(p.visibilityCurrentPriority(id,fov,height),current);
      equal(p.visibilityCurrentPriority(id,fov,height,&subtree),subtreeCurrent);
      equal(p.visibilityPriority(id,"unused",coarse,fov,height,&subtree),subtreeCoarse);
      equal(p.visibilityPriority(id,"absent",coarse,fov,height),0);
    }
  }
  // Snapshot replacement, FOV/viewport and metric changes must never reuse stale scores.
  p.resetVisibilityScoreCache();
  const auto before=p.visibilityRootPriority(0,45,720);
  p.roots[0].baseEdge*=3; p.roots[0].baseTexel*=3;
  equal(p.visibilityRootPriority(0,45,720),referenceRoot(p,0,45,720));
  assert(p.visibilityRootPriority(0,45,720)>before);
  const auto afterMetric=p.visibilityRootPriority(0,45,720);
  for (auto &[key,bins] : p.visibilityBins) if (key.root==0) for (auto &v:bins) v*=2;
  p.resetVisibilityScoreCache();
  equal(p.visibilityRootPriority(0,45,720),afterMetric*2);
  // Out-of-domain metrics retain the uncached formula; NaNs never enter ordered keys.
  Bins bins{}; bins[0]=1; bins[255]=.25;
  for (Metric m : {Metric{0,0},Metric{-1,-1},Metric{1,std::numeric_limits<float>::quiet_NaN()},
                   Metric{std::numeric_limits<float>::infinity(),1}})
    equal(p.visibilitySourcePriority({0,"special"},m,bins,45,720),reference(m,bins,45,720));
  std::vector<int> original(128); std::iota(original.begin(),original.end(),0);
  auto baseline=original,cached=original;
  std::stable_sort(baseline.begin(),baseline.end(),[&](int a,int b){return referenceRoot(p,a,45,720)>referenceRoot(p,b,45,720);});
  std::stable_sort(cached.begin(),cached.end(),[&](int a,int b){return p.visibilityRootPriority(a,45,720)>p.visibilityRootPriority(b,45,720);});
  assert(baseline==cached);
  const auto evaluations=p.visibilityScoreEvaluations;
  using Clock=std::chrono::steady_clock;
  auto start=Clock::now();
  for(int i=0;i<20;++i) {
    baseline=original;
    std::stable_sort(baseline.begin(),baseline.end(),[&](int a,int b){return referenceRoot(p,a,45,720)>referenceRoot(p,b,45,720);});
  }
  const auto denseMs=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
  start=Clock::now();
  for(int i=0;i<20;++i) {
    cached=original;
    std::stable_sort(cached.begin(),cached.end(),[&](int a,int b){return p.visibilityRootPriority(a,45,720)>p.visibilityRootPriority(b,45,720);});
  }
  const auto cachedMs=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
  assert(baseline==cached && p.visibilityScoreEvaluations==evaluations && p.visibilityScoreCacheHits>0);
  p.clearVisibilityScores();
  assert(p.visibilityBins.empty() && p.visibilityMetrics.empty() && p.visibilitySourceScores.empty() &&
         p.visibilityRootScores.empty() && p.visibilityScoreEvaluations==0 && p.visibilityScoreCacheGeneration==0);
  std::cout << "{\"passed\":true,\"differentialChecks\":"<<checked<<",\"sorts\":20,\"roots\":128,\"denseMilliseconds\":"<<denseMs
    <<",\"cachedMilliseconds\":"<<cachedMs<<",\"scope\":\"CPU ranking microbenchmark; not renderer FPS or UE performance\"}\n";
}
