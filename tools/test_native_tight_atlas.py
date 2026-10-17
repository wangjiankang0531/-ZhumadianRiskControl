import unittest
from native_tight_atlas import tight_layouts


class TightAtlasTests(unittest.TestCase):
    def test_original_placements_and_all_four_pixel_gutters_survive(self):
        mapping = {'one': (4, 4, 512, 512), 'two': (524, 4, 1024, 512)}
        actual, side = tight_layouts([(mapping, 2048)])[0]
        self.assertIs(actual, mapping)
        self.assertEqual(side, 1552)
        for x, y, w, h in actual.values():
            self.assertLessEqual(max(x + w + 4, y + h + 4), side)

    def test_alignment_rounds_up_without_rescaling_odd_source_dimensions(self):
        mapping = {'odd': (4, 4, 1001, 77)}
        self.assertEqual(tight_layouts([(mapping, 1024)])[0], (mapping, 1016))
        self.assertEqual(tight_layouts([({'tiny': (4, 4, 1, 1)}, 1024)])[0][1], 16)

    def test_existing_pot_layout_can_remain_pot_and_invalid_bounds_are_rejected(self):
        self.assertEqual(tight_layouts([({'fit': (4, 4, 1016, 1016)}, 1024)])[0][1], 1024)
        for layouts in [[({}, 2048)], [({'bad': (4, 4, 2048, 512)}, 2048)], [({'bad': (0, 4, 512, 512)}, 2048)], [({'bad': (4, 4, 512.0, 512)}, 2048)]]:
            with self.assertRaises(ValueError):
                tight_layouts(layouts)


if __name__ == '__main__':
    unittest.main()
