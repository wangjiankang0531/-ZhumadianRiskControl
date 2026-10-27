// Retained page identity covers decoded geometry and actual texture pixels.
// It is an in-process corruption guard, not a cryptographic authenticity claim.
template <class Cpu> uint64_t nativePageIdentity(const Cpu &cpu) {
  uint64_t value = 14695981039346656037ull;
  const auto append = [&](const auto &item) {
    const auto *bytes = reinterpret_cast<const unsigned char *>(&item);
    for (size_t i = 0; i < sizeof(item); ++i) { value ^= bytes[i]; value *= 1099511628211ull; }
  };
  append(cpu.image.width); append(cpu.image.height); append(cpu.payload);
  for (const auto &v : cpu.vertices) {
    for (int axis = 0; axis < 3; ++axis) { append(v.position[axis]); append(v.normal[axis]); }
    for (int axis = 0; axis < 2; ++axis) append(v.uv[axis]);
  }
  for (auto index : cpu.indices) append(index);
  for (auto pixel : cpu.image.rgba) append(pixel);
  if constexpr (requires { cpu.bc7Mips; }) {
    append(cpu.bc7Mips.size());
    for (const auto& level:cpu.bc7Mips) { append(level.size());for (auto byte:level) append(byte); }
  }
  return value;
}
struct NativePageRestorePlan { std::vector<size_t> parts; uint64_t bytes = 0; };
template <class Owner, class Cpu>
NativePageRestorePlan nativePageRestorePlan(const Owner &owner, const Cpu &cpu, const std::string &source) {
  if (owner.parts.size() != cpu.parts.size() || owner.sources.size() != cpu.sources.size())
    throw std::logic_error("Restored bundle layout changed");
  for (const auto &[name, saved] : owner.sources) {
    const auto it = cpu.sources.find(name);
    if (it == cpu.sources.end() || saved.depth != it->second.depth || saved.triangles != it->second.triangles ||
        saved.children != it->second.children || saved.spans.size() != it->second.spans.size())
      throw std::logic_error("Restored source ownership changed");
    for (size_t i = 0; i < saved.spans.size(); ++i) {
      const auto &a = saved.spans[i]; const auto &b = it->second.spans[i];
      if (a.part != b.part || a.first != b.first || a.count != b.count)
        throw std::logic_error("Restored source span changed");
    }
  }
  NativePageRestorePlan plan;
  std::set<size_t> missing;
  const auto &record = owner.sources.at(source);
  if (record.spans.empty()) throw std::logic_error("Restored source has no spans");
  for (const auto &span : record.spans) {
    if (!span.count || span.part >= owner.parts.size()) throw std::logic_error("Restored span escapes bundle");
    const auto &saved = owner.parts.at(span.part); const auto &fresh = cpu.parts.at(span.part);
    if (!saved.originalPageBytes || saved.originalPageBytes != fresh.payload ||
        saved.pageIdentity != nativePageIdentity(fresh) || saved.indexCount != fresh.indices.size())
      throw std::logic_error("Restored page geometry or texture differs from original upload");
    if (!saved.payload) missing.insert(span.part);
    else if (saved.payload != saved.originalPageBytes || !saved.descriptor || !saved.view || !saved.texture ||
             !saved.vertices || !saved.indices) throw std::logic_error("Partially live restore page");
  }
  for (size_t index : missing) { plan.parts.push_back(index); plan.bytes += cpu.parts.at(index).payload; }
  if (plan.bytes > owner.retiredBasePayload) throw std::logic_error("Restored bytes exceed retired pages");
  return plan;
}
