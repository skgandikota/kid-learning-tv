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

Card match adds shuffled animal/fruit pairs across five boards of 4/6/8/10/12
cards, animated flips and disappearing matches with locally generated sparkle
sounds. The server owns turns and rejects stale or rapid extra flips. Matching
uses existing licensed pictures; no new packages, models or external assets.
The website's TV pointer is large and white during child interaction and hidden
for Food time, videos and the end photo.

Browser playback was exercised with original synthetic H.264/AAC clips, not
third-party downloads. YouTube availability and the target Lubuntu installation
remain on-device checks. See `TEST-REPORT.md`.
