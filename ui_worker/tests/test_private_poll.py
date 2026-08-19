import unittest
from unittest.mock import MagicMock

from ui_worker.private_poll import build_private_event


class PrivatePollTests(unittest.TestCase):
    def test_builds_private_event_only_after_admitted_copy(self):
        event = build_private_event(user_id="195", text="hello", bubble_key="bubble-1")
        self.assertEqual(event["conversation_id"], "195")
        self.assertEqual(event["sender_id"], "195")
        self.assertEqual(event["sender_name"], "private")
        self.assertEqual(event["text"], "hello")
        self.assertTrue(event["event_id"])

    def test_rejects_blank_copy(self):
        self.assertIsNone(build_private_event(user_id="195", text="", bubble_key="bubble-1"))


if __name__ == "__main__":
    unittest.main()
