# Lubuntu installation

This version has parent PIN login, Food time, videos, quizzes, Card match and Hero Typing.
No microphone or speech recognition is installed. Videos download only when requested.

For an existing installation:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

The update installs FFmpeg/ffprobe, yt-dlp, Deno and eSpeak, and attempts optional
Piper installation plus its pinned English Cori model download on this laptop.
Internet is needed for packages/model setup; no videos download during setup.
The update preserves the existing PIN and stored files and backs up the previous
application. Other previously downloaded models remain on disk but are not used.
If it fails, fix the reported error and rerun the command; the service stays stopped.

For a fresh installation, install Python 3.10+ and `python3-venv`, then run
`sudo bash scripts/install.sh` from the checkout. Set the parent PIN at the hidden
terminal prompts. Python package installation requires internet.

On the laptop, refresh `http://127.0.0.1:8765/`: the screen shows Quiz, Card match and Hero Typing.
On your phone, open `http://<laptop-IP>:8765/parent` and sign in. Tap **Food time**
to show the picture, then tap again to return home. Use a trusted private LAN only.

Open **Video** for background downloads and ordered playback. The fixed folder is
`/var/lib/kid-learning-tv/videos`, owned by the service account. To copy your own
compatible file there, use `sudo install -o kid-learning-tv -g kid-learning-tv -m 0640 "/path/to/video.mp4" /var/lib/kid-learning-tv/videos/`.
Do not place symlinks or unfinished downloads in the library.

Close/reopen the kiosk browser after updating (or log out/in to the desktop) so
the new autoplay flag takes effect. The TV must open `http://127.0.0.1:8765/`;
playback reporting is laptop-only. In a regular Chromium window, launch with
`--autoplay-policy=no-user-gesture-required`, then use F11 for full screen.
Playback errors and autoplay failures are visible on the parent panel.

## Quiz voice

Setup tries natural Piper first and explicitly reports basic eSpeak fallback
when natural setup or synthesis fails. It verifies speech as `kid-learning-tv`.
To skip natural packages/model downloads, use
`sudo env KLT_QUIZ_NATURAL_VOICE=0 bash scripts/update.sh "$PWD"`.
This does not remove an already installed working natural voice.

The model is stored at `/opt/kid-learning-tv/models/piper-cori-medium`, outside
the replaced application tree. Generated public answer audio is cached under
`/var/lib/kid-learning-tv/quiz-audio`. There are no runtime model downloads.
Hero Typing additionally caches fixed phoneme and spelling WAVs under
`/var/lib/kid-learning-tv/phonics-audio`. It requires eSpeak NG even when Piper
is available: letter names are not a substitute for phonics sounds.
The update verifies a real phonics sound as the service user before starting.
To check without downloading:

```bash
sudo -u kid-learning-tv /opt/kid-learning-tv/.venv/bin/python \
  /opt/kid-learning-tv/tools/setup_quiz_voice.py \
  --verify --data-dir /var/lib/kid-learning-tv
```

Check actual voice quality on the laptop. Natural inference has no process
timeout; if it stalls, restart the service and use the basic voice by moving the
Piper model directory aside. Never expose this appliance to untrusted users.

For a forgotten PIN, run
`sudo bash /opt/kid-learning-tv/scripts/reset-parent-pin.sh`.
For service status, run `sudo systemctl status kid-learning-tv --no-pager`.
