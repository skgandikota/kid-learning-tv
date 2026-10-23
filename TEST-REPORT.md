# Test report

`python -m pytest -q`: **186 passed, 5 skipped** on the development Windows host.
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
All five Linux-only media/voice setup tests passed separately under Linux with
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

Matching tests cover exact duplicate pairs, all 20 board sizes (4 through 42), mismatch
delay, disappearing matches, completion, stale/double/invalid flips and display
interruption. Earlier real Edge mouse play completed the initial five rounds,
checked 80 sparkle oscillator notes, reload recovery, replay and red X.
The 12-card board fit within 1366x768 without scrolling; flipped images stayed inside the cards. Computed
cursor styles confirmed the large pointer on home/quiz/card buttons and no
pointer or visible buttons during Food time and video.
The expanded version rendered every round 1-20 in Edge and completed all 230
pairs through the real API using a controlled game clock. Mouse interaction was
checked in rounds 1 and 20. All 42 cards fit 1366x768, with each target at least
120x65 pixels; final completion, replay and stale-turn rejection passed.

Hero Typing tests cover all 34 lessons, phonics group endings, Flash's SH,
correct/wrong/stale keys, automatic spaces, next/completion, audio allowlists,
missing engines, silent/invalid WAV rejection and activity interruption.
An already-installed Linux eSpeak NG generated all 34 spelling introductions,
34 complete names and 239 phoneme/blend WAVs; each had valid, nonzero audio.
This exposed silent B/D/G/J releases, fixed with short vowel-assisted prompts.
No models were downloaded. Sound quality has not been reviewed by a phonics teacher.

Real Edge used those generated WAVs to exercise physical/on-screen keys,
F/FL/FLA then SH/FLASH, no premature S sound, wrong-letter hints, celebration,
Next, close during speech, reload recovery and Food time interruption.
Three home tiles, the standing generic hero, long-name wrapping and the
1366x768 keyboard layout were checked. Target-Lubuntu speakers and voice
quality still need on-device listening.
