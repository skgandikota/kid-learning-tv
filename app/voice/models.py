"""Fixed local model locations; model downloads occur only during setup."""
from pathlib import Path

MODELS = Path(__file__).resolve().parents[2] / "models"
WHISPER_NAME = "whisper-base.en"
WHISPER_REPO = "Systran/faster-whisper-base.en"
WHISPER_REVISION = "3d3d5dee26484f91867d81cb899cfcf72b96be6c"
WHISPER_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt", "README.md")
PIPER_NAME = "piper-cori-medium"
PIPER_REPO = "rhasspy/piper-voices"
PIPER_REVISION = "5041a7a49ae5b3a0f30e6837769eb03fdbb231bd"
PIPER_PREFIX = "en/en_GB/cori/medium"
PIPER_FILE = "en_GB-cori-medium.onnx"
PIPER_FILES = (PIPER_FILE, PIPER_FILE + ".json", "MODEL_CARD")


def present(directory: Path, files) -> bool:
    return all((directory / name).is_file() and (directory / name).stat().st_size > 0 for name in files)
