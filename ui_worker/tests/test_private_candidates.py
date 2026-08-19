import unittest

from ui_worker.private_candidates import PrivateCandidate, find_private_candidates


class PrivateCandidateTests(unittest.TestCase):
    def test_returns_registered_unpinned_unfolded_unread_changed_rows(self):
        previous = {"fp-a": {"preview": "old", "timestamp": "10:00"}}
        rows = [
            {"fingerprint": "fp-a", "preview": "new", "timestamp": "10:01", "unread": True, "pinned": False, "folded": False},
            {"fingerprint": "unknown", "preview": "x", "timestamp": "10:02", "unread": True, "pinned": False, "folded": False},
        ]
        registry = {"fp-a": {"user_id": "195", "search_key": "Test"}}
        result = find_private_candidates(rows, registry, previous)
        self.assertEqual(result, [PrivateCandidate("195", "fp-a", 0)])

    def test_rejects_pinned_folded_or_not_unread_rows(self):
        rows = [
            {"fingerprint": "a", "preview": "new", "timestamp": "1", "unread": True, "pinned": True, "folded": False},
            {"fingerprint": "b", "preview": "new", "timestamp": "1", "unread": True, "pinned": False, "folded": True},
            {"fingerprint": "c", "preview": "new", "timestamp": "1", "unread": False, "pinned": False, "folded": False},
        ]
        registry = {key: {"user_id": key, "search_key": key} for key in ("a", "b", "c")}
        self.assertEqual(find_private_candidates(rows, registry, {}), [])

    def test_does_not_treat_same_preview_and_timestamp_as_new(self):
        row = {"fingerprint": "a", "preview": "same", "timestamp": "1", "unread": True, "pinned": False, "folded": False}
        self.assertEqual(find_private_candidates([row], {"a": {"user_id": "1"}}, {"a": {"preview": "same", "timestamp": "1"}}), [])


if __name__ == "__main__":
    unittest.main()
