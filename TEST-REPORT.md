# Test report

`python -m pytest -q`: **98 passed, 2 skipped** on the development Windows host.
Downloader tests mock yt-dlp, ffprobe and file failures; no third-party videos
or new packages were downloaded on this machine.

Coverage includes URL/path validation, staging and atomic publication, explicit
download errors, bounded jobs/download size, authentication, CSRF, range streaming,
playlist order, stale TV reports, seek/pause/skip, total remaining time, completion
artwork, Food time interruption and PIN preservation.

Separate real Edge TV and phone-sized pages played two locally generated
H.264/AAC MP4 clips. Verified selection order, no TV controls, pause stability,
remote seek, volume/mute, TV refresh recovery, automatic playlist advance,
completion image, stop and Food time interruption. At a paused position of six
seconds in an eighteen-second playlist, the TV showed **0:12** and one-third
progress without ticking down during the pause. No JavaScript exceptions were
observed. The completion image was changed to the parent-supplied JPEG and loaded
successfully in the browser.

Python/JavaScript compilation and deployment shell syntax checks passed.
The two Linux-only media setup tests passed separately under Linux with mocked
system commands, including explicit failure for missing FFmpeg/FFprobe/JS tools.
FFprobe is not installed on this development host, so synthetic fixture metadata
was supplied for the browser check. Actual FFmpeg merging, Deno/yt-dlp installation,
YouTube downloads, target Lubuntu/kiosk playback and iPhone Safari were not
exercised. The installer performs media-tool checks on the target laptop.
