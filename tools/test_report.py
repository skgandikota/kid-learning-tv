#!/usr/bin/env python3
"""Run the automated suite and write an evidence-based Markdown report."""
from __future__ import annotations

import datetime
import platform
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    summary = next(
        (line for line in reversed(output.splitlines()) if re.search(r"\b\d+ passed\b|\b\d+ failed\b", line)),
        "Pytest did not produce a summary line.",
    )
    status = "PASS" if result.returncode == 0 else "FAIL"
    report = f"""# Test Report

Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}

## Automated checks

- Command: `python -m pytest -q`
- Result: **{status}**
- Summary: `{summary}`
- Host: `{platform.platform()}`
- Python: `{platform.python_version()}`

```text
{output}
```

## Scope and limitations

Tests run on the development host. No Lubuntu boot, HDMI/audio device, iPhone Safari,
microphone, or target-laptop performance test was performed by this command.
"""
    (ROOT / "TEST-REPORT.md").write_text(report, encoding="utf-8")
    print(f"{status}: {summary}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
