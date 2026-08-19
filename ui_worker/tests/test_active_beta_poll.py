import unittest
from unittest.mock import MagicMock

from ui_worker.active_beta_poll import poll_active_private_beta


class ActiveBetaPollTests(unittest.TestCase):
    def test_skips_when_beta_is_disabled(self):
        scanner = MagicMock()
        self.assertEqual(poll_active_private_beta(False, {"fp": {"user_id": "195"}}, scanner), [])
        scanner.scan.assert_not_called()

    def test_skips_ambiguous_registry(self):
        scanner = MagicMock()
        registry = {"a": {"user_id": "195"}, "b": {"user_id": "196"}}
        self.assertEqual(poll_active_private_beta(True, registry, scanner), [])
        scanner.scan.assert_not_called()

    def test_scans_unique_registered_private_when_enabled(self):
        scanner = MagicMock()
        scanner.scan.return_value = [{"event_id": "e", "conversation_id": "195", "sender_id": "195", "sender_name": "private", "text": "hello"}]
        result = poll_active_private_beta(True, {"fp": {"user_id": "195"}}, scanner)
        self.assertEqual(result[0]["text"], "hello")
        scanner.scan.assert_called_once_with("195")


if __name__ == "__main__":
    unittest.main()
