import unittest

from ui_worker.active_beta_guard import approved_single_private_user


class ActiveBetaGuardTests(unittest.TestCase):
    def test_returns_unique_approved_user_id(self):
        registry = {"fp-a": {"user_id": "195"}, "fp-b": {"user_id": "195"}}
        self.assertEqual(approved_single_private_user(registry), "195")

    def test_rejects_multiple_distinct_users(self):
        registry = {"fp-a": {"user_id": "195"}, "fp-b": {"user_id": "196"}}
        self.assertIsNone(approved_single_private_user(registry))

    def test_rejects_empty_registry(self):
        self.assertIsNone(approved_single_private_user({}))


if __name__ == "__main__":
    unittest.main()
