import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "posix", "The deployment scripts require Linux.")
class KioskStartupTests(unittest.TestCase):
    def test_launchers_work_without_executable_script_permissions(self):
        project = Path(__file__).resolve().parents[2]
        unit = (project / "systemd" / "kid-learning-kiosk.service").read_text()
        command = shlex.split(next(line.removeprefix("ExecStart=") for line in unit.splitlines() if line.startswith("ExecStart=")))
        self.assertEqual(command[0], "/bin/bash")
        desktop = (project / "kiosk" / "kid-learning-tv.desktop").read_text()
        enable = (project / "scripts" / "enable-kiosk.sh").read_text()
        self.assertIn("Exec=/bin/bash ", desktop)
        self.assertIn("Exec=/bin/bash ", enable)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("common.sh", "kiosk-supervisor.sh"):
                target = root / name
                target.write_text((project / "scripts" / name).read_text())
                target.chmod(0o644)
            binaries = root / "bin"
            binaries.mkdir()
            for name, script in (
                ("chromium", '#!/bin/bash\nprintf "%s\\n" "$@" > "$TEST_LOG"\nprintf "%s" "$DISPLAY" > "$TEST_LOG-display"\n'),
            ):
                target = binaries / name
                target.write_text(script)
                target.chmod(0o755)
            result = subprocess.run(
                [command[0], str(root / Path(command[1]).name)],
                env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}",
                     "TEST_LOG": str(root / "browser-args"),
                     "DISPLAY": ":7",
                     "KLT_KIOSK_URL": "http://127.0.0.1:8765/"},
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "browser-args-display").read_text(), ":7")
            arguments = (root / "browser-args").read_text().splitlines()
            self.assertIn("--kiosk", arguments)
            self.assertIn("--autoplay-policy=no-user-gesture-required", arguments)
            self.assertIn("http://127.0.0.1:8765/", arguments)

    def test_desktop_launcher_uses_inherited_session_not_user_service(self):
        project = Path(__file__).resolve().parents[2]
        launcher = (project / "scripts" / "start-kiosk.sh").read_text()
        self.assertIn("exec /bin/bash ", launcher)
        self.assertIn("/kiosk-supervisor.sh", launcher)
        self.assertNotIn("systemctl", launcher)


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


@unittest.skipUnless(os.name == "posix", "The deployment scripts require Linux.")
class QuizVoiceSetupTests(unittest.TestCase):
    def verify(self, natural="0", verify_failure="0"):
        common = Path(__file__).resolve().parents[2] / "scripts" / "common.sh"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binaries = root / ".venv" / "bin"
            binaries.mkdir(parents=True)
            pip = binaries / "pip"
            pip.write_text("#!/usr/bin/env bash\nexit 1\n")
            pip.chmod(0o755)
            script = """
source "$COMMON"
INSTALL_DIR="$TEST_ROOT"
STATE_DIR="$TEST_ROOT/state"
install() { printf 'install %s\\n' "$*"; }
chmod() { printf 'chmod %s\\n' "$*"; }
chown() { printf 'chown %s\\n' "$*"; }
runuser() {
    printf 'runuser %s\\n' "$*"
    if [[ "$VERIFY_FAILURE" == phonics ]]; then
        [[ "$*" != *PhonicsSpeech* ]]
    else
        [[ "$VERIFY_FAILURE" == 0 ]]
    fi
}
setup_quiz_voice
"""
            return subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True, timeout=10,
                env={**os.environ, "COMMON": str(common), "TEST_ROOT": str(root),
                     "KLT_QUIZ_NATURAL_VOICE": natural, "VERIFY_FAILURE": verify_failure},
            )

    def test_skip_download_and_failed_natural_install_still_verify_as_service(self):
        for natural in ("0", "1"):
            with self.subTest(natural=natural):
                result = self.verify(natural)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("runuser -u kid-learning-tv --", result.stdout)
                self.assertIn("--verify --data-dir", result.stdout)
                if natural == "1":
                    self.assertIn("WARNING: Piper package installation failed", result.stdout)
                else:
                    self.assertIn("Skipping natural-voice downloads", result.stdout)

    def test_no_working_voice_blocks_service_start(self):
        result = self.verify(verify_failure="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Neither natural nor fallback quiz speech works", result.stderr)

    def test_missing_phonics_blocks_service_even_if_name_voice_works(self):
        result = self.verify(verify_failure="phonics")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Hero Typing phonics failed", result.stderr)
