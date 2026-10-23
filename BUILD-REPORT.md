# Current build

Food time remains image-only. The parent Video panel adds a fixed local library,
background YouTube downloads, selection-ordered playlists and remote-only
pause/resume, seek, skip, stop and volume controls. The TV shows video, total
remaining time and playlist progress, then the parent-supplied end photo.

The updater installs FFmpeg/ffprobe, yt-dlp with its default components, and Deno
on the target laptop. No videos or AI models are downloaded during installation.
Existing parent PIN and data are retained.

Browser playback was exercised with original synthetic H.264/AAC clips, not
third-party downloads. YouTube availability and the target Lubuntu installation
remain on-device checks. See `TEST-REPORT.md`.
