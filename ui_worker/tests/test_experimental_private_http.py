import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ui_worker.http_api import handle_experimental_private_request


class ExperimentalPrivateHttpTests(unittest.TestCase):
    def test_requires_explicit_private_evidence_payload(self):
        runner = MagicMock()
        runner.copy_private_bubble.return_value = "hello"
        payload = {"user_id": "195", "x": 571, "y": 570, "bubble_key": "bubble-1"}
        with tempfile.TemporaryDirectory() as directory:
            beta = Path(directory) / "beta.json"
            beta.write_text('{"enabled": true}')
            status, body = handle_experimental_private_request(payload, runner, beta)
        self.assertEqual(status, 200)
        self.assertEqual(body["text"], "hello")

    def test_rejects_missing_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            beta = Path(directory) / "beta.json"
            beta.write_text('{"enabled": true}')
            status, body = handle_experimental_private_request({"user_id": "195"}, MagicMock(), beta)
        self.assertEqual(status, 400)
        self.assertIn("missing", body["error"])


if __name__ == "__main__":
    unittest.main()
