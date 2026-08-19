import unittest
from unittest.mock import MagicMock

from ui_worker.wechat_x11_driver import WeChatX11Driver


class DriverPrivateCopyTests(unittest.TestCase):
    def test_delegates_private_bubble_copy_to_runner(self):
        runner = MagicMock()
        runner.copy_bubble_text.return_value = "hello"
        driver = WeChatX11Driver(runner)
        self.assertEqual(driver.copy_private_bubble((571, 570)), "hello")
        runner.copy_bubble_text.assert_called_once_with((571, 570), menu_origin=(500, 480))


if __name__ == "__main__":
    unittest.main()
