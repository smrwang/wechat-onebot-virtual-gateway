import unittest
from pathlib import Path

import yaml


class ComposeGatewayTests(unittest.TestCase):
    def test_gateway_is_local_only_and_persists_its_database(self):
        compose = yaml.safe_load(Path("compose.yaml").read_text())
        gateway = compose["services"]["gateway"]

        self.assertIn("127.0.0.1:16700:16700", gateway["ports"])
        self.assertIn("./runtime/gateway:/data", gateway["volumes"])
        self.assertEqual(gateway["networks"], ["default", "internal"])

    def test_default_network_is_created_by_compose_for_new_installs(self):
        compose = yaml.safe_load(Path("compose.yaml").read_text())
        self.assertNotIn("default", compose.get("networks", {}))

    def test_gateway_targets_default_worker_port_and_mounts_adapter_directory(self):
        compose = yaml.safe_load(Path("compose.yaml").read_text())
        gateway = compose["services"]["gateway"]
        self.assertEqual(gateway["environment"]["UI_WORKER_URL"], "http://virtual-desktop:9121")
        self.assertIn("./runtime/wechat-profile/adapter:/data/adapter:ro", gateway["volumes"])
        self.assertEqual(gateway["environment"]["CONTACTS_PATH"], "/data/adapter/contacts.json")


if __name__ == "__main__":
    unittest.main()
