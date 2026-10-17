# Native visible-source scheduling experiment

The opt-in `--zhumadian-native-visibility` path is a research candidate. It is not enabled by default and is not included in the published portable 0.9.8 archive. `--zhumadian-native-visibility-measure-only` instruments the prior scheduling policy for paired comparisons.

A 96-pixel-wide, depth-tested ID pass reuses the current complete source cut and real vertex/index buffers. RGBA encodes a source ID and logarithmic view-depth bin. Central 40% by 40% pixels have weight four; all other pixels have weight one, with common normalization. Scheduling compares the weighted source-quality proxy. This is not geometric-deviation SSE or a perceptual quality percentage.

Budget planning evaluates complete branch/root retirements before changing a live cut, including simultaneous old and candidate fine payload under 512 MiB and bounded uploads under 32 MiB. The per-root ceiling is 384 MiB. A two-times margin and same-view retirement holds reduce churn. An admitted family remains valid while its parent is visible and still needs detail; a new best-ranked candidate alone does not revoke it. Camera/projection/viewport changes reset view-specific holds.

Verification uses direct float64 glTF triangle intersections, independently reconstructed complete source cuts, GPU source/depth sample checks, and the production retirement planner with independent resource fixtures. The standalone C++ fixtures require active assertions even in Release builds. Python/NumPy verification is QA-only.

Known release blockers as of 2026-10-17:

- Root slots are now admitted transactionally with byte budgets. The 200 m working-set oscillation case converged and passed 25 source rays plus 25 GPU ID/depth checks. This is one recovered case, not proof for every view.
- The two-cycle traversal retained the original depth gates and was rejected: the second cycle's first close approach reached depth five rather than the required six. Complete cuts, budget bounds, cancellation, and far-end resource return passed separately.
- Histogram scores are now memoized per GPU snapshot with metric/FOV/viewport keys, root-bounded map scans and a constant depth table. 9,267 dense-oracle differential checks and six GPU/source paired-view checks passed. The CPU ranking microbenchmark is not a renderer FPS result. Synchronous ID readback and hidden-parent physical payload still require work. No renderer performance improvement or UE-equivalence claim is made.

Evidence, immutable source snapshots, failed attempts and detailed acceptance records live in `D:/Project/Zhumadian/Document/Deployment/native_visibility_20261017`. Default 0.9.7 / web 0.8.5 and original GIS/DLG/business data remain unchanged.

Latest evidence: `D:/Project/Zhumadian/Document/Deployment/native_scores_20261017`. The strict two-cycle replay still failed at depth five on the second first-close view; the original depth-six gate is retained. Research code may be committed independently of default publishing.
