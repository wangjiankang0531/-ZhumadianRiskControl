import array
import json
import tempfile
import unittest
from pathlib import Path
from native_source_frontier import SourceForest, face_spans, source_metadata


def catalog():
    return {
        "root": "root",
        "nodes": [
            {"name": "root", "children": ["a", "b"]},
            {"name": "a", "children": ["a0", "a1"]},
            {"name": "b", "children": []},
            {"name": "a0", "children": []},
            {"name": "a1", "children": []},
        ],
    }


class SourceFrontierTests(unittest.TestCase):
    def test_terminal_leaf_is_retained_in_local_replacement(self):
        forest = SourceForest(catalog())
        old = {"a", "b"}
        self.assertEqual(
            forest.replace_family(old, "a", ["a1", "a0"]), {"a0", "a1", "b"}
        )
        self.assertEqual(old, {"a", "b"})

    def test_missing_duplicate_or_wrong_sibling_preserves_previous_cut(self):
        forest = SourceForest(catalog())
        old = {"a", "b"}
        for ready in [["a0"], ["a0", "a0", "a1"], ["a0", "b"]]:
            with self.assertRaises(ValueError):
                forest.replace_family(old, "a", ready)
            self.assertEqual(old, {"a", "b"})

    def test_frontier_rejects_holes_ancestor_overlap_and_unreachable_node(self):
        forest = SourceForest(catalog())
        for names in [["a"], ["root", "a"], ["a0", "b"], ["a", "b", "unknown"]]:
            with self.assertRaises(ValueError):
                forest.validate_cut(names)

    def test_hierarchy_rejects_cycles_missing_children_and_shared_children(self):
        for doc in [
            {"root": "r", "nodes": [{"name": "r", "children": ["r"]}]},
            {"root": "r", "nodes": [{"name": "r", "children": ["missing"]}]},
            {
                "root": "r",
                "nodes": [
                    {"name": "r", "children": ["a", "b"]},
                    {"name": "a", "children": ["b"]},
                    {"name": "b", "children": []},
                ],
            },
        ]:
            with self.assertRaises(ValueError):
                SourceForest(doc)

    def test_face_order_tracks_material_changes_without_bbox_approximation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "all.obj"
            p.write_text(
                "g Group_Tile_+001_+002_L21_0uuu0\nusemtl a\nf 1/1 2/2 3/3\nusemtl b\nf 3/3 2/2 1/1\ng Group_Tile_+001_+002_L21_0uuu1\nf 2/2 1/1 3/3\n"
            )
            spans = face_spans(p)
            self.assertEqual(
                [(s["first"], s["count"]) for s in spans], [(0, 6), (6, 3)]
            )
            p.write_text("f 1/1 2/2 3/3\n")
            with self.assertRaises(ValueError):
                face_spans(p)

    def test_metadata_uses_actual_node_geometry_and_rejects_index_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            part = folder / "part_000"
            part.mkdir()
            keys = ["Tile_+001_+002_L21_0uuu0", "Tile_+001_+002_L21_0uuu1"]
            sources = [
                {"name": "a.osgb", "sha256": "a", "children": []},
                {"name": "b.osgb", "sha256": "b", "children": []},
            ]
            for source, key in zip(sources, keys):
                (folder / source["name"]).write_bytes(key.encode())
            positions = array.array(
                "f", [0, 0, 0, 1, 0, 0, 0, 1, 0, 10, 0, 2, 12, 0, 2, 10, 2, 2]
            )
            uvs = array.array("f", [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1])
            indices = array.array("I", range(6))
            (part / "geometry.bin").write_bytes(
                positions.tobytes() + uvs.tobytes() + indices.tobytes()
            )
            (part / "geometry.gltf").write_text(
                json.dumps(
                    {
                        "bufferViews": [
                            {"byteOffset": 0},
                            {},
                            {"byteOffset": 72},
                            {"byteOffset": 120},
                        ]
                    }
                )
            )
            records = [
                {
                    "directory": "part_000",
                    "vertices": 6,
                    "indices": 6,
                    "atlas_size": 1024,
                    "source_face_counts": dict.fromkeys(keys, 1),
                    "source_spans": [
                        {"geometry_name": key, "first": i * 3, "count": 3}
                        for i, key in enumerate(keys)
                    ],
                }
            ]
            doc = {
                "root": "r",
                "nodes": [{"name": "r", "children": ["a.osgb", "b.osgb"]}, *sources],
            }
            result = source_metadata(folder, records, sources, doc, folder)
            self.assertEqual(result[0]["bounds_max"], [1, 1, 0])
            self.assertEqual(result[1]["bounds_min"], [10, 0, 2])
            self.assertAlmostEqual(result[1]["texel_world_p90_m"], 2 / 1024)
            self.assertEqual(
                result[0]["spans"], [{"part": "part_000", "first": 0, "count": 3}]
            )
            records[0]["source_spans"][1]["first"] = 0
            with self.assertRaises(ValueError):
                source_metadata(folder, records, sources, doc, folder)


if __name__ == "__main__":
    unittest.main()
