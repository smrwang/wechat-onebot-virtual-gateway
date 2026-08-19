import threading
import unittest
from unittest.mock import MagicMock

from ui_worker.scan_lock import scan_once_or_empty


class ScanLockTests(unittest.TestCase):
    def test_returns_work_result_when_lock_is_available(self):
        lock = threading.Lock()
        self.assertEqual(scan_once_or_empty(lock, lambda: [{"text": "hello"}]), [{"text": "hello"}])

    def test_returns_empty_when_another_scan_holds_lock(self):
        lock = threading.Lock()
        lock.acquire()
        try:
            self.assertEqual(scan_once_or_empty(lock, lambda: [{"text": "should-not-run"}]), [])
        finally:
            lock.release()


if __name__ == "__main__":
    unittest.main()
