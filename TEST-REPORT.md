# Test report

`python -m pytest -q`: **164 passed, 4 skipped** on the development Windows host.
Downloader tests mock yt-dlp, ffprobe and file failures; no third-party videos
or AI models were downloaded on this machine. A missing setuptools build backend
was installed only to check application packaging.

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
All four Linux-only media/voice setup tests passed separately under Linux with
mocked system commands, including explicit failure for missing media tools,
Piper installation fallback and failure when no speech engine verifies.
FFprobe is not installed on this development host, so synthetic fixture metadata
was supplied for the browser check. Actual FFmpeg merging, Deno/yt-dlp installation,
YouTube downloads, target Lubuntu/kiosk playback and iPhone Safari were not
exercised. The installer performs media-tool checks on the target laptop.

Quiz checks cover settings, authenticated parent controls, child mode restrictions,
loading-gated timing, minimum answer duration, speech completion, pause/resume,
stale tokens, catalog integrity and mocked speech caching/fallback failures.
Real Edge TV/phone pages loaded all seven category icons, then exercised mouse
selection, five-second automatic reveal, WAV playback, pause/resume, four-second
answer display, next/completion, red X and Food time interruption. Image/answer
containment, close-button hit testing, 1366x768 tiles and phone width were checked.
Browser speech used a local test WAV, not a downloaded model.
The application wheel was checked for all 73 quiz SVGs and bundled license notices.
Real Piper/eSpeak quality and target-laptop model installation remain unverified.

Matching tests cover exact duplicate pairs, all five board sizes, mismatch
delay, disappearing matches, completion, stale/double/invalid flips and display
interruption. Real Edge mouse play completed every round, checked all 80 sparkle
oscillator notes, reload recovery, replay and red X. The 12-card board fit within
1366x768 without scrolling; flipped images stayed inside the cards. Computed
cursor styles confirmed the large pointer on home/quiz/card buttons and no
pointer or visible buttons during Food time and video.
