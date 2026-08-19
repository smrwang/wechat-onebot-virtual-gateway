import unittest

from ui_worker.bubble_overlap import new_bubble_keys


class BubbleOverlapTests(unittest.TestCase):
    def test_returns_new_tail_after_visible_overlap(self):
        previous = ["a", "b", "c"]
        current = ["b", "c", "d"]
        self.assertEqual(new_bubble_keys(previous, current), ["d"])

    def test_returns_all_when_no_overlap_exists(self):
        self.assertEqual(new_bubble_keys(["a"], ["b", "c"]), ["b", "c"])

    def test_keeps_same_text_when_bubble_evidence_is_different(self):
        previous = ["bubble-old-ok"]
        current = ["bubble-old-ok", "bubble-new-ok"]
        self.assertEqual(new_bubble_keys(previous, current), ["bubble-new-ok"])


if __name__ == "__main__":
    unittest.main()
