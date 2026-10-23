# Third-party software

| Component | Use | License reference |
|---|---|---|
| Flask | Local HTTP application | BSD-3-Clause; installed package notices |
| Waitress | Production HTTP server | ZPL-2.1; installed package notices |
| yt-dlp | Parent-requested YouTube downloads | Unlicense; https://github.com/yt-dlp/yt-dlp |
| yt-dlp-ejs | YouTube JavaScript support installed by yt-dlp default extras | Review installed package and bundled dependency notices |
| Deno Python distribution | JavaScript runtime for yt-dlp | MIT; https://deno.com and installed notices |
| FFmpeg/ffprobe | Merge downloads and inspect local media | Distribution build may be LGPL/GPL; preserve its exact package notices |
| eSpeak NG | Basic offline quiz speech | GPL-3.0-or-later; preserve distribution package notices |
| Piper TTS (optional) | Natural local quiz speech | GPL-3.0; https://github.com/OHF-Voice/piper1-gpl and installed notices |
| Hugging Face Hub (optional) | Target-laptop model setup | Apache-2.0; installed package notices |
| Cori medium voice (optional) | English Piper model | Review pinned model's downloaded MODEL_CARD; model/data terms are separate from engine terms |
| OpenMoji, Simple Icons, flag-icons, Natural Earth | Quiz illustrations, brand marks, flags and country outlines | Exact pinned sources, licenses and trademark caveats: [quiz asset notices](docs/QUIZ-ASSET-LICENSES.md); bundled `app/static/quiz/ATTRIBUTION.txt` and `licenses/` |
| Python, SQLite, Lubuntu, Chromium/Chrome | Runtime/platform/browser | Consult each vendor/distribution's notices |

Preserve notices for exact installed versions and transitive dependencies when
redistributing. Downloaded media is not licensed by this software: only download
content you own or have permission to download; do not bypass restrictions.
No videos are bundled. The Food time and end-screen images were supplied by the
parent; they are not licensed as part of any third-party software dependency.
