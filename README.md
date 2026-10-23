# Kid Learning TV

Current version: **Food time and parent-controlled video playlists**.
Games, voice and AI features remain removed.
Existing PIN and stored files are preserved; no models are downloaded.

Update on the Lubuntu laptop:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

Refresh the TV page at `http://127.0.0.1:8765/`.
Open `http://<laptop-IP>:8765/parent` on your phone and use the existing PIN.
Tap **Food time** at the top of the signed-in parent page to show the supplied
picture on the TV. Tap it again to return to black. The image fits without
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
Food time interrupts playback; Stop returns to black. Playlists do not restart
automatically after a service restart.

For sound without touching the TV, run the laptop browser in kiosk mode:
after updating, close/reopen the kiosk browser (or log out/in to the desktop).
The updated launcher allows video autoplay. For a normal browser window, launch
Chromium with `--autoplay-policy=no-user-gesture-required` and use F11 to hide
browser chrome. The app cannot hide OS/browser chrome from a remote phone.

Use a trusted home network only; do not expose port 8765 to the internet.
See [INSTALLATION.md](INSTALLATION.md) for a fresh installation.
