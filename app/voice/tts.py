"""Small offline TTS adapter; it never contacts a network service."""
from __future__ import annotations

import queue
import logging
import shutil
import subprocess
import threading
import importlib.util
import io
import wave

from app.voice.models import MODELS, PIPER_NAME, PIPER_FILE, PIPER_FILES, present


class SpeechOutput:
    def wave(self, text: str, voice: str, rate: int, volume: int) -> bytes:
        if not self.neural_available():
            raise ValueError("Natural speech is not installed. Run scripts/setup-voice.sh.")
        from piper import PiperVoice, SynthesisConfig
        with self._neural_lock:
            if self._neural_voice is None:
                self._neural_voice = PiperVoice.load(str(self.model_path / PIPER_FILE), use_cuda=False)
            output = io.BytesIO()
            with wave.open(output, "wb") as wav_file:
                self._neural_voice.synthesize_wav(
                    str(text)[:500], wav_file,
                    syn_config=SynthesisConfig(
                        volume=max(0, min(volume, 100)) / 100,
                        length_scale=145 / max(100, min(rate, 200)),
                    ),
                )
            return output.getvalue()

    def __init__(self, model_path=None):
        self.model_path = model_path or MODELS / PIPER_NAME
        self._neural_lock = threading.Lock()
        self._neural_voice = None
        self._queue = queue.Queue(maxsize=3)
        self._lock = threading.Lock()
        self._generation = 0
        self._process = None
        self._worker = threading.Thread(target=self._run, daemon=True, name="local-tts")
        self._worker.start()

    @staticmethod
    def available() -> bool:
        return bool(shutil.which("espeak-ng") or shutil.which("espeak"))

    def neural_available(self):
        return importlib.util.find_spec("piper") is not None and present(self.model_path, PIPER_FILES)

    def say(self, text: str, voice: str = "en-gb", rate: int = 145, volume: int = 70):
        safe_text = str(text)[:240]
        if not safe_text:
            return
        try:
            with self._lock:
                generation = self._generation
            self._queue.put_nowait((safe_text, voice, int(rate), int(volume), generation))
        except queue.Full:
            logging.warning("Offline speech queue is full; a prompt was skipped.")

    def stop(self):
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        with self._lock:
            self._generation += 1
            process = self._process
            if process and process.poll() is None:
                process.terminate()
        if process and process.poll() is None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)

    def _run(self):
        while True:
            text, voice, rate, volume, generation = self._queue.get()
            executable = shutil.which("espeak-ng") or shutil.which("espeak")
            if not executable:
                continue
            voice = voice if voice in {"en-gb", "en-us", "en"} else "en-gb"
            with self._lock:
                if generation != self._generation:
                    continue
                try:
                    process = subprocess.Popen(
                        [executable, "-v", voice, "-s", str(max(100, min(rate, 200))),
                         "-a", str(max(0, min(volume, 100))), text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except OSError:
                    logging.exception("Could not start the offline speech process.")
                    continue
                self._process = process
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
                logging.warning("Offline speech prompt exceeded its time limit.")
            except OSError:
                logging.exception("Offline speech process failed.")
            finally:
                with self._lock:
                    if self._process is process:
                        self._process = None
