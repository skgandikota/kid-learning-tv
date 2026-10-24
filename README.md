# Kid Learning TV

Current version: **Food time, videos, picture quizzes, Card match and Hero Typing**.
Existing PIN and stored files are preserved. Quiz speech runs locally; no microphone.

Update on the Lubuntu laptop:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

Refresh the TV page at `http://127.0.0.1:8765/`.
Open `http://<laptop-IP>:8765/parent` on your phone and use the existing PIN.
Tap **Food time** at the top of the signed-in parent page to show the supplied
picture on the TV. Tap it again to return to the Quiz home tile. The image fits without
cropping or stretching; other screen shapes may have black bars.
Food time has no buttons, clock, text overlays or visible cursor on the TV.
The selection survives refresh and service restart.

Tap **Video** next to Food time to open the video panel. Paste a YouTube URL and
title to download in the background, or copy compatible MP4/WebM/M4V files into
`/var/lib/kid-learning-tv/videos` on the laptop. Only download content you own or
have permission to download. Restricted/unavailable videos may fail; errors and
progress appear on the parent page. Downloads do not start playback.

Select videos in the order you want (1, 2, 3...), then tap **Play selection**.
Each library row also has **Play** for that video alone. Pause/resume, seek, skip,
previous, stop and volume controls are phone-only. The TV shows a small total
remaining-time countdown and playlist progress bar, and "Loading..." only while
buffering. After the last video, your supplied end-of-screen-time photo appears.
Food time interrupts playback; Stop returns to the Quiz home tile. Playlists do not restart
automatically after a service restart.

The TV home has **Quiz**, **Card match** and **Hero Typing** picture buttons. Click Quiz, then choose a
picture tile: car logos, animals, vegetables, fruits, birds, country shapes or
flags. A large red **X** closes the quiz. Food time and videos still have no TV
buttons. Quizzes show a picture, count down gently, then show and speak its name
for at least four seconds. There are no scores or microphone recordings.

Use **Quiz** on the parent page to choose 5/10/15/20 seconds, up to 5/10 pictures,
and optional ticking; save before starting the next round. Five pictures at ten
seconds is a gentle starting point for age three. Country shapes are harder.
The curated catalog contains 73 licensed pictures, including 15 car brands, not
every car logo worldwide. [Asset sources and licenses](docs/QUIZ-ASSET-LICENSES.md).

The update installs eSpeak and attempts to install the optional Piper natural
voice and download its model **on the Lubuntu laptop only**. It checks speech as
the service account and reports whether natural or basic fallback speech works.
To skip natural-voice downloads, run
`sudo env KLT_QUIZ_NATURAL_VOICE=0 bash scripts/update.sh "$PWD"`.
Actual voice quality and speaker volume must be checked on that laptop.

**Card match** uses familiar animal, fruit and bird pictures. Click two cards: matching
pairs vanish with a gentle sparkle sound; different pictures flip back after a
short look. **20 rounds** automatically grow through **4, 6, 8, 10...42 cards**,
adding two cards each round. Larger boards use up to seven columns to fit the TV.
There is no timer or score. The red X returns home; Play again starts fresh.
A large white mouse pointer is used on home, quizzes and Card match, including
over buttons. Food time, videos and the end photo keep the pointer hidden.

**Hero Typing - Level 1** adds 26 favourite character names, including Flash,
Batman, Superman, Wonder Woman, Robin, Aquaman, Avengers, Thanos, Joker, Venom,
Woody and Buzz Lightyear, followed by 25 everyday words: animals, fruit,
Table, Chair, Bed, Cup, Book, Ball and body parts.
Each character has a parent-supplied picture on its choice card and inside the lesson.
These supplied character images remain the property of their respective owners;
they are not covered by this project's code license. Existing image credits are preserved.
The new household and body-part illustrations are original SVGs.
Choose a name, listen to its spelling, then type the highlighted letters using
the keyboard or large on-screen keys. Sounds play after each completed sound
group; Flash builds F, FL, FLA and then SH/FLASH. SH waits for both letters.
Irregular names use sound chunks rather than misleading partial-name blends.
After the complete-name audio finishes, the next lesson starts automatically.
Large bottom-corner arrows go back or forward at any time, even during speech;
the ends return to the choices. Hear again repeats the prompt.
There is no scoring, countdown, microphone capture or typed-text history.
Phonics uses local eSpeak NG; complete names use the existing local voice.

For sound without touching the TV, run the laptop browser in kiosk mode:
after updating, close/reopen the kiosk browser (or log out/in to the desktop).
The updated launcher allows video autoplay. For a normal browser window, launch
Chromium with `--autoplay-policy=no-user-gesture-required` and use F11 to hide
browser chrome. The app cannot hide OS/browser chrome from a remote phone.

Use a trusted home network only; do not expose port 8765 to the internet.
See [INSTALLATION.md](INSTALLATION.md) for a fresh installation.
