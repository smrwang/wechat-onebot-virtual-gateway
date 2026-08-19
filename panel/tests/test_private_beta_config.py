import tempfile
import unittest
from pathlib import Path

from panel.config_api import apply_private_inbound_beta, private_inbound_beta_enabled


class PrivateBetaConfigTests(unittest.TestCase):
    def test_defaults_to_disabled_and_persists_enabled_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-inbound-beta.json"
            self.assertFalse(private_inbound_beta_enabled(path))
            self.assertTrue(apply_private_inbound_beta(path, {"enabled": True}))
            self.assertTrue(private_inbound_beta_enabled(path))

    def test_rejects_non_boolean_value(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "boolean"):
                apply_private_inbound_beta(Path(directory) / "beta.json", {"enabled": "yes"})


if __name__ == "__main__":
    unittest.main()
