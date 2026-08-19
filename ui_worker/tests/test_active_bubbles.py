import unittest

from ui_worker.active_bubbles import parse_active_bubbles


class ActiveBubblesTests(unittest.TestCase):
    def test_parses_left_text_lines_to_root_coordinate_candidates(self):
        tsv = """level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext
5\t1\t1\t1\t1\t1\t70\t160\t20\t15\t95\thello
5\t1\t1\t1\t1\t2\t92\t160\t25\t15\t95\tworld
5\t1\t2\t1\t1\t1\t420\t220\t30\t15\t95\toutgoing
"""
        bubbles = parse_active_bubbles(tsv, crop_origin=(430, 100), split_x=350)
        self.assertEqual(len(bubbles), 1)
        self.assertEqual(bubbles[0].text, "hello world")
        self.assertEqual(bubbles[0].point, (523, 267))
        self.assertTrue(bubbles[0].key)

    def test_excludes_low_confidence_and_right_side_text(self):
        tsv = """level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext
5\t1\t1\t1\t1\t1\t30\t40\t20\t15\t30\tnoise
5\t1\t2\t1\t1\t1\t400\t50\t20\t15\t95\tright
"""
        self.assertEqual(parse_active_bubbles(tsv, crop_origin=(430, 100), split_x=350), [])

    def test_restores_root_coordinates_from_scaled_psm11_tsv(self):
        tsv = """level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext
5\t1\t1\t1\t1\t1\t210\t480\t60\t45\t95\tnew
"""
        bubbles = parse_active_bubbles(tsv, crop_origin=(430, 100), split_x=350, scale=3)
        self.assertEqual(bubbles[0].point, (510, 267))


if __name__ == "__main__":
    unittest.main()
