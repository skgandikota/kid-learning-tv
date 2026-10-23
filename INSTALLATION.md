# Lubuntu installation

This version has parent PIN login, Food time and video playlists. No AI, microphone
or games are installed. Videos download only when requested by a parent.

For an existing installation:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

The update installs FFmpeg/ffprobe, yt-dlp and its Deno JavaScript runtime.
Internet is needed for those packages, but no videos are downloaded during setup.
The update preserves the existing PIN and stored files and backs up the previous
application. Previously downloaded models remain on disk but are not used.
If it fails, fix the reported error and rerun the command; the service stays stopped.

For a fresh installation, install Python 3.10+ and `python3-venv`, then run
`sudo bash scripts/install.sh` from the checkout. Set the parent PIN at the hidden
terminal prompts. Python package installation requires internet.

On the laptop, refresh `http://127.0.0.1:8765/`: the screen should be black and empty.
On your phone, open `http://<laptop-IP>:8765/parent` and sign in. Tap **Food time**
to show the picture, then tap again to return to black. Use a trusted private LAN only.

Open **Video** for background downloads and ordered playback. The fixed folder is
`/var/lib/kid-learning-tv/videos`, owned by the service account. To copy your own
compatible file there, use `sudo install -o kid-learning-tv -g kid-learning-tv -m 0640 "/path/to/video.mp4" /var/lib/kid-learning-tv/videos/`.
Do not place symlinks or unfinished downloads in the library.

Close/reopen the kiosk browser after updating (or log out/in to the desktop) so
the new autoplay flag takes effect. The TV must open `http://127.0.0.1:8765/`;
playback reporting is laptop-only. In a regular Chromium window, launch with
`--autoplay-policy=no-user-gesture-required`, then use F11 for full screen.
Playback errors and autoplay failures are visible on the parent panel.

For a forgotten PIN, run
`sudo bash /opt/kid-learning-tv/scripts/reset-parent-pin.sh`.
For service status, run `sudo systemctl status kid-learning-tv --no-pager`.
