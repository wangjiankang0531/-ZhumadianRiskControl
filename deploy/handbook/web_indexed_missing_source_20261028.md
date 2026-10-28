# Sealed-index missing-source fallback (experimental)

Use --prepared-lod --level-index <sealed index> --osgb-data-root <original Data> --osgb-data-tiles indexed-missing with the optional source-sampler page policy. Default behavior stays opt-in. The existing validated 2346-root catalog and index identify the scene; data decoding remains lazy and unsupported structures fail closed.

A complete.json present in any configured prepared store must use its existing validator, including corrupt markers. Raw RAM preparation is allowed only when all prepared markers are absent. Prepared-owned leases stay with their validator; memory leases require their exact folder/part/file. No native reader or asset payload writes are introduced. Existing bounded explicit lists remain supported and reuse state distinguishes both modes.

The health capability reports sealed_index_missing_prepared_v1, tileCount 2346, both SHA identities and preparedFirst without an oversized explicit tiles list; Web preserves coverage priority only for the validated contract. Bounds/budgets and complete original images are unchanged.

Validation: 166 Python checks in local and independent source copies; 776 Web checks in each. Real root 86 metadata and six GET/HEAD payloads match an independent original-data RAM bundle. Actual fixed 350m navigation at 5/20/40s loaded 14/81/163 roots, zero current failed sets; left upper ID sample base count 1 to 0, right upper still 1. Peak tracked source bytes 2137343053 < 2147483648. Overview releases to 5593429 and the full canonical cut/held ledger restores exactly. Timing is not a controlled OS-cold benchmark and 20-second full-frame quality is not accepted. The 18 other missing families passed offline preparation, not all-family GPU admission.

Public deployment, native executable recovery, other machines and the existing 87-file remote review authorization are outside this checkpoint. Full engine/editor/viewer and strict Tianjin application goals remain active. No database schema changes.
