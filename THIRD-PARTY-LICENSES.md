# Third-party software and licensing

This project directly declares Flask 3.1.2 and jsonschema 4.25.1 in `pyproject.toml`; `requirements.lock` is also part of the deployment. The deployment installer additionally requests waitress as a production WSGI server because it is not currently declared in the project manifest. Exact transitive dependency versions are determined by the lock/install environment.

| Component | Use | License reference |
|---|---|---|
| Flask | Local web framework | BSD-3-Clause; see the installed package metadata |
| jsonschema | Content/schema validation | MIT; see the installed package metadata |
| waitress | Optional production WSGI server installed by deployment script | ZPL-2.1; see the installed package metadata |
| qrcode | Optional QR generation for the parent connection page; not installed by deployment script | Consult installed package metadata for the selected release |
| eSpeak NG / eSpeak | Optional system-provided local TTS | Consult the distribution's package copyright/license notices |
| faster-whisper 1.2.1 / CTranslate2 | Optional CPU INT8 speech recognition | MIT; installed package notices |
| Whisper base.en (Systran conversion) | Downloaded English model, not bundled in Git | MIT; pinned repository README retained alongside model; https://huggingface.co/Systran/faster-whisper-base.en |
| Piper 1.8.0 | Optional natural local speech synthesis | GPL-3.0; installed package notices; https://github.com/OHF-Voice/piper1-gpl |
| Piper en_GB-cori-medium | Downloaded British voice, not bundled in Git | Model card identifies LibriVox public-domain recordings; MODEL_CARD and pinned source revision retained; https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/cori/medium |
| Silero VAD / ONNX Runtime / PyAV | Voice detection and neural/audio runtime dependencies | MIT / MIT / BSD-3-Clause respectively; retain installed notices, including bundled FFmpeg notices |
| Python, SQLite, Lubuntu, Chromium/Chrome | Runtime/platform/browser, not bundled here | Consult each distribution/vendor's notices |

This page is an inventory, not a reproduction of third-party license texts or a complete SBOM. Before redistribution, generate and review an inventory for the exact installed versions, preserve their copyright/license notices, and inspect licenses for transitive dependencies and any media/assets included in the release.

The learning library contains original browser implementations of common counting,
colour/shape matching and matching-pairs games. GCompris is an inspiration, not a
bundled dependency: none of its source code, artwork, audio or activities is included.
