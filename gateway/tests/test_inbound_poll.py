import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from gateway.app import GatewayService


class InboundPollTests(unittest.IsolatedAsyncioTestCase):
    async def test_polls_worker_and_publishes_onebot_message(self):
        worker = MagicMock()
        worker.poll_inbound.return_value = [{"event_id": "evt-1", "conversation_id": "42", "sender_name": "Test", "text": "hello"}]
        with tempfile.TemporaryDirectory() as directory:
            gateway = GatewayService(Path(directory) / "gateway.sqlite3", worker_client=worker)
            events = []
            async def collect(event): events.append(event)
            gateway._publish = collect
            try:
                count = await gateway.poll_worker_once()
            finally:
                await gateway.close()

        self.assertEqual(count, 1)
        self.assertEqual(events[0]["post_type"], "message")
        self.assertEqual(events[0]["raw_message"], "hello")

    async def test_logs_only_count_after_worker_publish(self):
        worker = MagicMock()
        worker.poll_inbound.return_value = [{"event_id": "evt-1", "conversation_id": "42", "sender_name": "Test", "text": "secret text"}]
        with tempfile.TemporaryDirectory() as directory:
            gateway = GatewayService(Path(directory) / "gateway.sqlite3", worker_client=worker)
            async def discard(event):
                return None
            gateway._publish = discard
            with self.assertLogs("gateway.app", level="INFO") as captured:
                try:
                    await gateway.poll_worker_once()
                finally:
                    await gateway.close()
        joined = "\n".join(captured.output)
        self.assertIn("UI worker poll published=1", joined)
        self.assertNotIn("secret text", joined)


if __name__ == "__main__":
    unittest.main()
