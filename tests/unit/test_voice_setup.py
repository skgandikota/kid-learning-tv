import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == "posix", "Deployment scripts require Linux bash.")
class VoiceSetupTests(unittest.TestCase):
    def run_setup(self, *, update=True, active=False, fail=False):
        source = Path(__file__).resolve().parents[2] / "scripts" / "setup-voice.sh"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".venv" / "bin").mkdir(parents=True)
            (root / "setup-voice.sh").write_text(source.read_text())
            (root / "common.sh").write_text("""
set -Eeuo pipefail
umask 077
INSTALL_DIR="$TEST_ROOT"
STATE_DIR="$TEST_ROOT/state"
SERVICE_NAME=kid-learning-tv
require_root() { :; }
die() { printf '%s\\n' "$*" >&2; exit 1; }
info() { :; }
confirm() { printf 'confirm\\n' >> "$TEST_LOG"; }
apt-get() { printf 'apt-get %s\\n' "$*" >> "$TEST_LOG"; }
chmod() { printf 'chmod %s\\n' "$*" >> "$TEST_LOG"; }
systemctl() {
    printf 'systemctl %s\\n' "$*" >> "$TEST_LOG"
    if [[ "$1" == is-active ]]; then [[ "$TEST_ACTIVE" == 1 ]]; fi
}
runuser() {
    printf 'runuser %s\\n' "$*" >> "$TEST_LOG"
    [[ "$TEST_FAIL" == 0 ]]
}
""")
            python = root / ".venv" / "bin" / "python"
            python.write_text('#!/usr/bin/env bash\nprintf "python %s umask=%s\\n" "$*" "$(umask)" >> "$TEST_LOG"\n')
            python.chmod(0o755)
            log = root / "commands.log"
            result = subprocess.run(
                ["bash", str(root / "setup-voice.sh"), *(["--update"] if update else [])],
                env={**os.environ, "TEST_ROOT": str(root), "TEST_LOG": str(log),
                     "TEST_ACTIVE": str(int(active)), "TEST_FAIL": str(int(fail))},
                capture_output=True, text=True, timeout=10,
            )
            return result, log.read_text()

    def test_update_verifies_without_enabling_voice_or_starting_stopped_service(self):
        result, log = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--verify", log)
        self.assertNotIn("--enable", log)
        self.assertNotIn("confirm", log)
        self.assertNotIn("systemctl start", log)
        self.assertIn("umask=0022", log)
        self.assertIn("apt-get install -y libgomp1", log)
        self.assertIn("[voice]", log)

    def test_update_stops_on_model_verification_failure(self):
        result, log = self.run_setup(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification failed", result.stderr)
        self.assertNotIn("systemctl start", log)

    def test_explicit_setup_confirms_and_enables_voice(self):
        result, log = self.run_setup(update=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("confirm", log)
        self.assertIn("--enable", log)
        self.assertIn("systemctl start", log)

    def test_update_restarts_a_previously_running_service(self):
        result, log = self.run_setup(active=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("systemctl stop", log)
        self.assertIn("systemctl start", log)
