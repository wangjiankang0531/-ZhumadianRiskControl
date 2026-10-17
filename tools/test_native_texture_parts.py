import tempfile, unittest
from pathlib import Path
from native_texture_parts import (
    texture_bins,
    atlas_layouts,
    save_atlas,
    slice_obj,
    face_count,
    face_counts,
    GUTTER,
)


class TexturePartTests(unittest.TestCase):
    def test_original_rectangles_keep_pixels_and_never_overlap(self):
        sizes = {str(i): (1024, 512) if i < 5 else (512, 512) for i in range(28)}
        buckets = texture_bins(sizes)
        self.assertEqual(set().union(*(set(b) for b in buckets)), set(sizes))
        self.assertEqual(sum(len(b) for b in buckets), len(sizes))
        for b in buckets:
            for name, (x, y, w, h) in b.items():
                self.assertEqual((w, h), sizes[name])
                self.assertTrue(
                    x >= GUTTER
                    and y >= GUTTER
                    and x + w + GUTTER <= 2048
                    and y + h + GUTTER <= 2048
                )
            values = list(b.values())
            for i, (x, y, w, h) in enumerate(values):
                for a, c, d, e in values[i + 1 :]:
                    self.assertTrue(
                        x + w + GUTTER <= a - GUTTER
                        or a + d + GUTTER <= x - GUTTER
                        or y + h + GUTTER <= c - GUTTER
                        or c + e + GUTTER <= y - GUTTER
                    )

    def test_small_tail_pages_reduce_physical_pixels_without_resizing(self):
        sizes = {str(i): (512, 512) for i in range(3)}
        layouts = atlas_layouts(sizes)
        self.assertEqual(sum(side * side for _, side in layouts), 3 * 1024 * 1024)
        self.assertEqual(set().union(*(set(m) for m, _ in layouts)), set(sizes))
        for mapping, side in layouts:
            for name, (x, y, w, h) in mapping.items():
                self.assertEqual((w, h), sizes[name])
                self.assertLessEqual(max(x + w + GUTTER, y + h + GUTTER), side)
        dense = atlas_layouts({str(i): (512, 512) for i in range(9)})
        self.assertEqual(sum(side * side for _, side in dense), 2048 * 2048)

    def test_oversized_source_is_rejected_instead_of_downsampled(self):
        with self.assertRaises(ValueError):
            texture_bins({"source": (2048, 512)})

    def test_face_slices_keep_original_references_and_partition_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            obj = root / "all.obj"
            (root / "all.mtl").write_text(
                "newmtl a\n    map_Kd a.rgb\nnewmtl b\n    map_Kd b.rgb\n"
            )
            obj.write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\ng Group_Tile_+007_+012_L20_0uuuu0\nusemtl a\nf 1/1 2/2 3/3\nf 3/3 2/2 1/1\nusemtl b\nf 2/2 3/3 1/1\n"
            )
            materials = {"a": root / "a.rgb", "b": root / "b.rgb"}
            self.assertEqual(face_count(obj, materials, {root / "a.rgb"}), 2)
            pieces = []
            for index, (names, first, count) in enumerate(
                [
                    ({root / "a.rgb"}, 0, 1),
                    ({root / "a.rgb"}, 1, 1),
                    ({root / "b.rgb"}, 0, 1),
                ]
            ):
                out = root / f"p{index}.obj"
                slice_obj(obj, out, materials, names, first, count)
                pieces += [
                    line
                    for line in out.read_text().splitlines()
                    if line.startswith("f ")
                ]
                self.assertEqual(sum(face_counts(out).values()), 1)
                self.assertIn(str(root / "a.rgb"), out.with_suffix(".mtl").read_text())
            self.assertEqual(len(pieces), 3)
            self.assertEqual(len(set(pieces)), 3)

    def test_atlas_preserves_source_size_and_color_without_resize(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            Image.new("RGB", (1024, 512), (10, 80, 150)).save(source)
            mapping = texture_bins({source: (1024, 512)})[0]
            save_atlas(mapping, root / "atlas.png")
            x, y, w, h = mapping[source]
            with Image.open(root / "atlas.png") as im:
                self.assertEqual(
                    im.crop((x, y, x + w, y + h)).tobytes(),
                    Image.open(source).tobytes(),
                )


if __name__ == "__main__":
    unittest.main()
