#!/usr/bin/env python3
"""Report only system facts observable on the current host."""
import json
import importlib.util
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.voice.models import MODELS, WHISPER_NAME, WHISPER_FILES, PIPER_NAME, PIPER_FILES, present


def command_output(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=3, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"


def process_rss(pid: Path):
    try:
        for line in (pid / "status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def process_memory():
    proc = Path("/proc")
    if not proc.is_dir():
        return {"application": "unavailable on this platform", "chromium_total": "unavailable on this platform"}
    chromium = []
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            name = (entry / "comm").read_text().strip().lower()
        except OSError:
            continue
        if "chrom" in name:
            value = process_rss(entry)
            if value:
                chromium.append({"pid": int(entry.name), "rss": value})
    return {
        "application": process_rss(proc / str(os.getpid())) or "unavailable",
        "chromium_processes": chromium,
    }


def cpu_model():
    if Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
            if line.lower().startswith(("model name", "hardware")):
                return line.partition(":")[2].strip() or "unavailable"
    return platform.processor() or "unavailable"


def report():
    mem = {}
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, _, rest = line.partition(":")
            if key in {"MemTotal", "MemAvailable"}:
                mem[key] = rest.strip()
    disk = shutil.disk_usage(Path.cwd())
    return {
        "platform": platform.platform(),
        "cpu": cpu_model(),
        "cores": os.cpu_count(),
        "memory": mem or "unavailable on this platform",
        "disk_free_bytes": disk.free,
        "load": os.getloadavg() if hasattr(os, "getloadavg") else "unavailable",
        "process_memory": process_memory(),
        "hostname": socket.gethostname(),
        "addresses": command_output("hostname", "-I") if os.name != "nt" else "inspect network settings locally",
        "audio_devices": command_output("aplay", "-l") if os.name != "nt" else "unavailable on this platform",
        "microphone_visibility": command_output("arecord", "-l") if os.name != "nt" else "unavailable on this platform",
        "display": command_output("xrandr", "--current") if os.name != "nt" else "unavailable on this platform",
        "stt": {
            "faster_whisper_installed": importlib.util.find_spec("faster_whisper") is not None,
            "english_model_present": present(MODELS / WHISPER_NAME, WHISPER_FILES),
            "engine": "Whisper base.en, CPU INT8, 2 threads",
            "microphone": "browser permission on localhost required; see parent controls for live status",
        },
        "tts": {
            "piper_installed": importlib.util.find_spec("piper") is not None,
            "british_model_present": present(MODELS / PIPER_NAME, PIPER_FILES),
        },
        "service_state": command_output("systemctl", "is-active", "kid-learning-tv") if os.name != "nt" else "systemd unavailable",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
