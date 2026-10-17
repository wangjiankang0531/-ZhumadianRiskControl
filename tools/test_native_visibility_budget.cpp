// Exercise the production retirement planner with independent resource fixtures.
#ifdef NDEBUG
#error Budget fixtures require active assertions
#endif
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>
struct BudgetFixture {
  struct Node {
    std::string name;
    std::vector<std::string> children;
  };
  struct Resident {
    uint64_t payload = 0;
    float edge = 1, texel = 0;
    std::vector<Node> topology;
    std::map<std::string, Resident> families;
  };
  struct Metric {
    float edge, texel;
  };
  uint64_t budget = 100, payload = 0, cap = 100, evictions = 0;
  size_t slots=16;
  size_t residentLimit() const {return slots;}
  std::map<int, Resident> resident;
  std::map<int, int> desired, failed;
  std::map<int, double> rootBenefits;
  std::map<int, double> currentBenefits;
  std::map<std::pair<int, std::string>, double> benefits;
  bool visibilityEnabled = true;
  struct {
    bool zhumadianNativeVisibilitySchedule = true;
  } visibilityCli;
  uint64_t rootBudget(int) const { return cap; }
  const Resident *sourceRecord(const Resident &ready, const std::string &name) const {
    static Resident value;
    for (const auto &node : ready.topology)
      if (node.name == name)
        return &value;
    return nullptr;
  }
  double visibilityPriority(int id, const std::string &name, Metric, float, int,
                            const std::set<std::string> * = nullptr) const {
    const auto it = benefits.find({id, name});
    return it == benefits.end() ? 100 : it->second;
  }
  double visibilityCurrentPriority(int id, float, int, const std::set<std::string> * = nullptr) const {
    const auto it = currentBenefits.find(id);
    return it == currentBenefits.end() ? 0 : it->second;
  }
  double visibilityRootPriority(int id, float, int) const {
    const auto it = rootBenefits.find(id);
    return it == rootBenefits.end() ? 100 : it->second;
  }
  void coarsenFamily(Resident &ready, const std::string &parent) {
    const auto subtree = visibilitySubtree(ready, parent);
    for (auto it = ready.families.begin(); it != ready.families.end();) {
      if (subtree.contains(it->first)) {
        payload -= it->second.payload;
        ready.payload -= it->second.payload;
        it = ready.families.erase(it);
      } else
        ++it;
    }
  }
#include "../native/zhumadian_native_visibility_budget.inl"
  void add(int id, uint64_t base, std::initializer_list<std::pair<std::string, uint64_t>> families) {
    auto &ready = resident[id];
    ready.payload = base;
    ready.topology = {
        {"r", {"A", "B", "C"}}, {"A", {"A1"}}, {"A1", {"A2"}}, {"A2", {}}, {"B", {}}, {"C", {}}};
    for (const auto &[name, bytes] : families) {
      ready.families[name].payload = bytes;
      ready.payload += bytes;
    }
    payload += ready.payload;
  }
};
int main() {
  {
    BudgetFixture p;
    p.add(0, 80, {});
    const auto plan = p.visibilityRoom(1, "", 20, 10, 45, 720);
    assert(plan && plan->empty() && p.payload == 80);
  }
  {
    BudgetFixture p;
    p.add(0, 20, {{"A", 30}, {"B", 30}});
    p.benefits[{0, "A"}] = 1;
    p.benefits[{0, "B"}] = 2;
    const auto plan = p.visibilityRoom(0, "C", 60, 10, 45, 720);
    assert(plan && plan->size() == 2 && p.payload == 80 && p.resident.at(0).families.size() == 2);
    assert(p.applyVisibilityRoom(0, "C", 60, 10, 45, 720));
    assert(p.payload == 20 && p.resident.at(0).payload == 20 && p.resident.at(0).families.empty());
    assert(p.payload + 60 <= p.budget && p.visibilityBudgetRetirements == 2);
  }
  {
    BudgetFixture p;
    p.add(0, 10, {{"A", 20}, {"A1", 20}, {"B", 25}});
    p.benefits[{0, "A"}] = .2;
    p.benefits[{0, "A1"}] = .1;
    p.benefits[{0, "B"}] = 100;
    const auto plan = p.visibilityRoom(0, "C", 60, 10, 45, 720);
    assert(plan && plan->size() == 1 && plan->front().parent == "A");
    assert(p.applyVisibilityRoom(0, "C", 60, 10, 45, 720) && p.payload == 35);
    assert(p.resident.at(0).families.size() == 1 && p.resident.at(0).families.contains("B"));
  }
  {
    BudgetFixture p;
    p.add(0, 10, {{"A", 20}, {"A1", 20}, {"B", 25}});
    p.benefits[{0, "A"}] = .1;
    p.benefits[{0, "A1"}] = .1;
    p.benefits[{0, "B"}] = .1;
    assert(!p.applyVisibilityRoom(0, "A2", 60, 10, 45, 720)); // Request's retained ancestors are protected.
    assert(p.payload == 75 && p.resident.at(0).families.size() == 3 && p.visibilityBudgetRetirements == 0);
  }
  {
    BudgetFixture p;
    p.add(0, 40, {});
    p.add(1, 15, {{"A", 30}});
    p.benefits[{1, "A"}] = .1;
    p.rootBenefits[1] = .2;
    const auto plan = p.visibilityRoom(0, "C", 60, 10, 45, 720);
    assert(plan && plan->size() == 1 && plan->front().id == 1 && plan->front().parent.empty());
    assert(p.applyVisibilityRoom(0, "C", 60, 10, 45, 720) && p.payload == 40 && p.resident.size() == 1 &&
           p.evictions == 1);
  }
  {
    BudgetFixture p;
    p.add(0, 70, {{"A", 20}});
    p.benefits[{0, "A"}] = 5;
    assert(!p.applyVisibilityRoom(0, "C", 20, 10, 45, 720)); // Equal two-times boundary does not churn.
    assert(p.payload == 90 && p.visibilityBudgetRetirements == 0);
  }
  {
    BudgetFixture p;
    p.add(0, 10, {{"A", 20}});
    p.cap = 20;
    p.benefits[{0, "A"}] = 0;
    assert(!p.applyVisibilityRoom(0, "C", 21, 10, 45, 720));
    assert(p.payload == 30 && p.visibilityBudgetRetirements == 0);
  }
  {
    BudgetFixture p;
    p.add(0, 50, {{"A", 20}});
    p.benefits[{0, "A"}] = 100;
    p.rootBenefits[0] = 100;
    assert(!p.applyVisibilityRoom(1, "", 50, 1, 45, 720));
    assert(p.payload == 70 && p.resident.size() == 1 && p.visibilityBudgetRetirements == 0);
  }
  {
    BudgetFixture p;
    p.add(0, 40, {});
    p.add(1, 45, {});
    p.rootBenefits[1] = 100;
    p.currentBenefits[1] = 99.9;
    const auto plan = p.visibilityRoom(0, "C", 60, 10, 45, 720);
    assert(plan && plan->size() == 1 && plan->front().id == 1);
    assert(p.applyVisibilityRoom(0, "C", 60, 10, 45, 720) && p.payload == 40);
  }
  {
    BudgetFixture p;
    p.add(0, 20, {{"A", 60}});
    p.benefits[{0, "A"}] = 1;
    assert(p.applyVisibilityRoom(0, "B", 60, 10, 45, 720));
    p.resident.at(0).families["B"].payload = 60;
    p.resident.at(0).payload += 60;
    p.payload += 60;
    p.benefits[{0, "B"}] = 1;
    assert(!p.visibilityRoom(0, "A", 60, 12, 45, 720));
    assert(p.payload == 80 && !p.visibilityRequestAllowed(0, "A", 12));
    p.visibilityRetiredScores.clear(); // A changed view can reconsider the retired family.
    assert(p.applyVisibilityRoom(0, "A", 60, 12, 45, 720));
    assert(p.payload == 20);
  }
  {
    BudgetFixture p;p.slots=1;p.add(0,50,{});p.rootBenefits[0]=100;p.currentBenefits[0]=99.9;
    const auto plan=p.visibilityRoom(1,"",10,10,45,720);
    assert(plan && plan->size()==1 && plan->front().id==0 && plan->front().parent.empty());
    assert(p.applyVisibilityRoom(1,"",10,10,45,720) && p.resident.empty() && p.payload==0);
  }
  {
    BudgetFixture p;p.slots=1;p.add(0,50,{});p.rootBenefits[0]=10;p.currentBenefits[0]=0;
    assert(!p.visibilityRoom(1,"",10,1,45,720));
    assert(!p.visibilityRoom(1,"",0,1,45,720));
    assert(p.resident.size()==1 && p.payload==50 && p.visibilityBudgetRetirements==0);
  }
  std::cout << "12 independent visibility-budget resource fixtures passed\n";
}
