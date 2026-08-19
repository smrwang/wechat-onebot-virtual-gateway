import tempfile
import unittest
from pathlib import Path

from panel.inbound_status import private_inbound_status


class InboundStatusTests(unittest.TestCase):
    def test_reports_experimental_private_only_requirements(self):
        status = private_inbound_status()
        self.assertEqual(status["mode"], "experimental_private_only")
        self.assertTrue(status["requires_unpinned_unfolded_inbox"])
        self.assertFalse(status["group_inbound"])
        self.assertFalse(status["mentions"])

    def test_reports_beta_toggle_state_from_persisted_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beta.json"
            path.write_text('{"enabled": true}')
            self.assertTrue(private_inbound_status(path)["beta_enabled"])


if __name__ == "__main__":
    unittest.main()
