import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ui_worker.active_private_beta import ActivePrivateBetaScanner


class ActivePrivateBetaScannerTests(unittest.TestCase):
    def test_first_scan_baselines_without_emitting(self):
        runner = MagicMock()
        runner.read_active_bubbles.return_value = [("a", (500, 200)), ("b", (510, 230))]
        with tempfile.TemporaryDirectory() as directory:
            scanner = ActivePrivateBetaScanner(Path(directory) / "cursor.json", runner)
            self.assertEqual(scanner.scan("195"), [])
        runner.copy_private_bubble.assert_not_called()

    def test_later_new_bubble_is_copied_and_returned(self):
        runner = MagicMock()
        runner.read_active_bubbles.side_effect = [[("a", (500, 200))], [("a", (500, 200)), ("b", (510, 230))]]
        runner.copy_private_bubble.return_value = "hello"
        with tempfile.TemporaryDirectory() as directory:
            scanner = ActivePrivateBetaScanner(Path(directory) / "cursor.json", runner)
            scanner.scan("195")
            events = scanner.scan("195")
        self.assertEqual(events[0]["text"], "hello")
        self.assertEqual(events[0]["sender_id"], "195")
        runner.copy_private_bubble.assert_called_once_with((510, 230))

    def test_copy_failure_is_not_emitted_or_marked_seen(self):
        runner = MagicMock()
        runner.read_active_bubbles.side_effect = [[("a", (500, 200))], [("a", (500, 200)), ("b", (510, 230))], [("a", (500, 200)), ("b", (510, 230))]]
        runner.copy_private_bubble.side_effect = [None, "hello"]
        with tempfile.TemporaryDirectory() as directory:
            scanner = ActivePrivateBetaScanner(Path(directory) / "cursor.json", runner)
            scanner.scan("195")
            self.assertEqual(scanner.scan("195"), [])
            events = scanner.scan("195")
        self.assertEqual(events[0]["text"], "hello")

    def test_restarted_scanner_reuses_persisted_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cursor.json"
            first = MagicMock()
            first.read_active_bubbles.return_value = [("a", (500, 200))]
            ActivePrivateBetaScanner(path, first).scan("195")
            second = MagicMock()
            second.read_active_bubbles.return_value = [("a", (500, 200)), ("b", (510, 230))]
            second.copy_private_bubble.return_value = "hello"
            events = ActivePrivateBetaScanner(path, second).scan("195")
        self.assertEqual(events[0]["text"], "hello")

    def test_changed_scanner_version_rebaselines_without_replaying_visible_bubbles(self):
        runner = MagicMock()
        runner.read_active_bubbles.return_value = [("a", (500, 200)), ("b", (510, 230))]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cursor.json"
            ActivePrivateBetaScanner(path, runner, scanner_version="v1").scan("195")
            events = ActivePrivateBetaScanner(path, runner, scanner_version="v2").scan("195")
        self.assertEqual(events, [])
        runner.copy_private_bubble.assert_not_called()


if __name__ == "__main__":
    unittest.main()
