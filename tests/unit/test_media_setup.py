import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "posix", "The deployment scripts require Linux.")
class MediaToolSetupTests(unittest.TestCase):
    def verify(self, failed_tool=""):
        common = Path(__file__).resolve().parents[2] / "scripts" / "common.sh"
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "commands"
            script = """
source "$COMMON"
runuser() {
    printf '%s\\n' "$*" >> "$TEST_LOG"
    [[ -z "$FAIL_TOOL" || "$*" != *"$FAIL_TOOL"* ]]
}
verify_video_tools
"""
            result = subprocess.run(
                ["bash", "-c", script],
                env={**os.environ, "COMMON": str(common), "TEST_LOG": str(log), "FAIL_TOOL": failed_tool},
                capture_output=True, text=True, timeout=10,
            )
            return result, log.read_text()

    def test_checks_runtime_as_restricted_service_account(self):
        result, log = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log.count("-u kid-learning-tv --"), 4)
        self.assertIn("ffmpeg -version", log)
        self.assertIn("ffprobe -version", log)
        self.assertIn("import yt_dlp, yt_dlp_ejs", log)
        self.assertIn("/.venv/bin/deno --version", log)

    def test_missing_media_tool_causes_setup_failure(self):
        for name in ("ffmpeg", "ffprobe", "yt_dlp", "deno"):
            with self.subTest(name=name):
                result, _ = self.verify(name)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("verification failed", result.stderr)
