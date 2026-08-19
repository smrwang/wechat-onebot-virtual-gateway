import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ui_worker.http_api import handle_experimental_private_request


class PrivateBetaGuardTests(unittest.TestCase):
    def test_disabled_beta_rejects_without_copy(self):
        runner = MagicMock()
        with tempfile.TemporaryDirectory() as directory:
            status, body = handle_experimental_private_request(
                {"user_id": "195", "x": 571, "y": 570, "bubble_key": "bubble-1"},
                runner,
                Path(directory) / "beta.json",
            )
        self.assertEqual(status, 403)
        runner.copy_private_bubble.assert_not_called()

    def test_enabled_beta_permits_verified_copy(self):
        runner = MagicMock()
        runner.copy_private_bubble.return_value = "hello"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beta.json"
            path.write_text('{"enabled": true}')
            status, body = handle_experimental_private_request(
                {"user_id": "195", "x": 571, "y": 570, "bubble_key": "bubble-1"}, runner, path
            )
        self.assertEqual(status, 200)
        self.assertEqual(body["text"], "hello")


if __name__ == "__main__":
    unittest.main()
