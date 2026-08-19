import tempfile
import unittest
from pathlib import Path

from ui_worker.private_cursor import PrivateCursor


class PrivateCursorTests(unittest.TestCase):
    def test_startup_baseline_marks_existing_messages_historical(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor = PrivateCursor(Path(directory) / "cursor.json")
            self.assertEqual(cursor.baseline("195", ["old", "old2"]), 2)
            self.assertEqual(cursor.new_messages("195", ["old", "old2"]), [])

    def test_returns_only_new_suffix_after_overlap_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor = PrivateCursor(Path(directory) / "cursor.json")
            cursor.baseline("195", ["old"])
            self.assertEqual(cursor.new_messages("195", ["old", "new"]), ["new"])

    def test_same_text_can_be_emitted_again_with_different_bubble_key(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor = PrivateCursor(Path(directory) / "cursor.json")
            cursor.baseline("195", [])
            self.assertEqual(cursor.accept("195", "ok", "bubble-1"), True)
            self.assertEqual(cursor.accept("195", "ok", "bubble-1"), False)
            self.assertEqual(cursor.accept("195", "ok", "bubble-2"), True)


if __name__ == "__main__":
    unittest.main()
