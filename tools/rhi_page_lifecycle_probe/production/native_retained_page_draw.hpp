#pragma once
#include <hongtu/asset/indexed_mesh_compaction.hpp>
// Determine visibility before touching RHI objects. A fully hidden retired page has no draw work.
template<class Part>
std::vector<hongtu::asset::MeshIndexRange> nativeRetainedPageDrawRanges(const Part& part,const std::vector<hongtu::asset::MeshIndexRange>& hidden){
 auto ranges=hongtu::asset::retainedMeshIndexRanges(part.indexCount,hidden);
 if(!ranges.empty() && (!part.descriptor || !part.vertices || !part.indices))throw std::logic_error("Visible source references a retired GPU page");
 return ranges;
}
