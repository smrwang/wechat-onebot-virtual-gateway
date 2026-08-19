import tempfile
import unittest
from pathlib import Path

from ui_worker.private_selector import PrivateBubbleSelector


class PrivateBubbleSelectorTests(unittest.TestCase):
    def test_baseline_returns_no_existing_bubbles(self):
        with tempfile.TemporaryDirectory() as directory:
            selector = PrivateBubbleSelector(Path(directory) / "cursor.json")
            self.assertEqual(selector.baseline("195", ["a", "b"]), [])

    def test_returns_only_unseen_new_bubbles(self):
        with tempfile.TemporaryDirectory() as directory:
            selector = PrivateBubbleSelector(Path(directory) / "cursor.json")
            selector.baseline("195", ["a", "b"])
            self.assertEqual(selector.select("195", ["b", "c"]), ["c"])
            self.assertEqual(selector.select("195", ["b", "c"]), [])


if __name__ == "__main__":
    unittest.main()
