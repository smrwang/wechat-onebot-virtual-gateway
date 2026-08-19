import unittest
from pathlib import Path
from unittest.mock import patch

from ui_worker.linux_runner import LinuxWeChatRunner


class LinuxRunnerActiveBubblesTests(unittest.TestCase):
    def test_reads_active_bubbles_from_current_chat_ocr(self):
        runner = LinuxWeChatRunner(workdir=Path("/tmp/test-active-bubbles"))
        # Coordinates reflect the Runner's 300% PSM 11 screenshot.
        tsv = """level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext
5\t1\t1\t1\t1\t1\t210\t480\t60\t45\t95\thello
"""
        with patch.object(runner, "_run"), patch("subprocess.run") as run:
            run.return_value = type("R", (), {"stdout": tsv})()
            bubbles = runner.read_active_bubbles()
        self.assertEqual(len(bubbles), 1)
        self.assertEqual(bubbles[0][1], (510, 267))


if __name__ == "__main__":
    unittest.main()
