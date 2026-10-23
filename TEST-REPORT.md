# Test Report

## Automated checks

- Command: `python -m pytest -q`
- Result: **PASS**
- Summary: `81 passed, 4 skipped in 27.62s`.
- Host: `Windows-11-10.0.26200-SP0`
- Python: `3.14.5`
- `node --test tests/unit/voice-browser.test.cjs`: **3 passed**.
- Linux `python3 -m unittest tests.unit.test_voice_setup -v`: **4 passed**.
  These script-control-flow checks mock package/service commands; they are the
  four deployment tests skipped on Windows.
- Python compilation, JavaScript/shell syntax, content validation and `pip check`
  passed. Actual bundled Silero VAD returned no speech for half-second silence.

## Scope and limitations

Tests run on the development host. No Lubuntu boot, HDMI/audio device, iPhone Safari,
microphone, or target-laptop performance test was performed by this command.
Neural adapter tests use fake inference/synthesis. The development network blocked
real model downloads (HTTP 403); no successful Piper/Whisper model inference or
latency measurement is claimed. Downloads now run only on the target machine via
`update.sh`, which verifies models before restarting. The isolated wheel build was
stopped; the non-isolated attempt could not import the missing setuptools backend.
