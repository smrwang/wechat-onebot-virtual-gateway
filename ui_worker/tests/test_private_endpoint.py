import unittest
from unittest.mock import MagicMock

from ui_worker.private_endpoint import experimental_private_event


class PrivateEndpointTests(unittest.TestCase):
    def test_returns_event_from_verified_copy(self):
        runner = MagicMock()
        runner.copy_private_bubble.return_value = "hello"
        event = experimental_private_event(runner, user_id="195", point=(571, 570), bubble_key="bubble-1")
        self.assertEqual(event["text"], "hello")
        self.assertEqual(event["conversation_id"], "195")

    def test_returns_none_when_copy_fails(self):
        runner = MagicMock()
        runner.copy_private_bubble.return_value = None
        self.assertIsNone(experimental_private_event(runner, user_id="195", point=(571, 570), bubble_key="bubble-1"))


if __name__ == "__main__":
    unittest.main()
