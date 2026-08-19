import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ui_worker.active_private_beta import ActivePrivateBetaScanner
from ui_worker.wechat_x11_driver import WeChatX11Driver


class DriverActivePrivateTests(unittest.TestCase):
    def test_scans_active_private_via_driver_runner(self):
        runner = MagicMock()
        runner.read_active_bubbles.side_effect = [[], [("b", (500, 220))]]
        runner.copy_bubble_text.return_value = "hello"
        with tempfile.TemporaryDirectory() as directory:
            driver = WeChatX11Driver(runner)
            scanner = ActivePrivateBetaScanner(Path(directory) / "cursor.json", driver)
            self.assertEqual(scanner.scan("195"), [])
            events = scanner.scan("195")
        self.assertEqual(events[0]["text"], "hello")


if __name__ == "__main__":
    unittest.main()
