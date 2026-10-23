# Current build

Food time remains image-only. The parent Video panel adds a fixed local library,
background YouTube downloads, selection-ordered playlists and remote-only
pause/resume, seek, skip, stop and volume controls. The TV shows video, total
remaining time and playlist progress, then the parent-supplied end photo.

Picture quizzes add a child-operated home tile, seven illustrated categories,
large red X, timed reveals and local spoken answers. The curated catalog has
73 locally bundled licensed SVGs; brand marks remain subject to trademark rights.

The updater installs FFmpeg/ffprobe, yt-dlp, Deno and eSpeak on the target laptop.
It attempts optional Piper/model setup there, never on the development host.
Natural setup failures explicitly fall back to verified eSpeak.
Existing parent PIN and data are retained.

Browser playback was exercised with original synthetic H.264/AAC clips, not
third-party downloads. YouTube availability and the target Lubuntu installation
remain on-device checks. See `TEST-REPORT.md`.
