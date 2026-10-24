# Lubuntu installation

This version has parent PIN login, Food time, videos, quizzes, Card match,
Hero Typing and seven Adventure games.
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

On the laptop, refresh `http://127.0.0.1:8765/`: the screen shows Quiz,
Card match, Hero Typing and Adventure games.
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

## Start automatically in kiosk mode

After installing/updating, run these as the Lubuntu desktop user, **without sudo**:

```bash
bash /opt/kid-learning-tv/scripts/enable-kiosk.sh
bash /opt/kid-learning-tv/scripts/start-kiosk.sh
```

The local TV site opens in Chromium kiosk mode now and at future desktop logins.
For power-on straight to the TV, enable automatic login for the dedicated TV
desktop account in Lubuntu's login settings. Kiosk setup does not change login
security or enable automatic login for you. The app service already starts at boot.

The launcher runs directly in the desktop session, inheriting its display and
login environment rather than using a systemd user service. Rerunning
`enable-kiosk.sh` stops/removes the old kiosk user service and replaces its
autostart entry.

To close kiosk temporarily, press **Alt+F4**. It stays closed until you start it
again or log in next time. Browser errors are not hidden or automatically retried.
To disable future kiosk startup, run
`bash /opt/kid-learning-tv/scripts/disable-kiosk.sh`.

## Keep running with the lid closed

Run as the **Lubuntu desktop user**, without sudo in front:

```bash
bash /opt/kid-learning-tv/scripts/configure-lid.sh
```

It asks for sudo and confirmation, then sets both systemd-logind and LXQt lid
actions to do nothing, on charger **and battery**, with or without the TV attached.
Reboot when ready; the script deliberately does not restart logind or your desktop.
Critical-battery protection, idle sleep and screen locking are not changed.
If it later sleeps while idle, open **Preferences > LXQt settings > Power
Management > Idle** and disable idle suspend on both AC and battery.
Keep it ventilated, preferably on charger; never put it in a bag while running.
Closing the lid does not stop battery drain, and an empty battery still shuts it down.

The original existing LXQt file is backed up once beside it as
`~/.config/lxqt/lxqt-powermanagement.conf.before-klt-lid` (or under
`$XDG_CONFIG_HOME` if set). To undo, restore that backup, or choose your desired
lid actions in **Power Management > Lid** if no previous file existed.
Remove only `/etc/systemd/logind.conf.d/90-kid-learning-tv-lid.conf` with sudo,
then reboot. Do not change or remove other logind settings.

## Connect from a Mac using SSH (same private Wi-Fi)

On Lubuntu, enable SSH and note your normal desktop username and LAN address:

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
whoami
hostname -I
```

On your Mac M1 Pro, open **Terminal**; no extra Mac software is needed:

```bash
ssh YOUR-LUBUNTU-USERNAME@LAPTOP-IP
```

Use your **Linux account password**, not the parent PIN. Check the server's host
key fingerprint on the laptop with
`sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` before accepting it on
the Mac. Use a normal desktop/admin account, not root or `kid-learning-tv`.

For key-based login, on the Mac create a passphrase-protected key only if you
do not already have one, then copy its public part:

```bash
test -f ~/.ssh/id_ed25519 || ssh-keygen -t ed25519
cat ~/.ssh/id_ed25519.pub | ssh YOUR-LUBUNTU-USERNAME@LAPTOP-IP 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
ssh YOUR-LUBUNTU-USERNAME@LAPTOP-IP
```

Never copy/share the private key. Keep the existing terminal open until the
second login succeeds. This does not alter SSH password or root-login policy.
Use only trusted private Wi-Fi; do not forward ports 22 or 8765 on your router.
If a firewall is active, allow TCP 22 only from your Mac's LAN IP rather than
opening it to everyone. A router DHCP reservation keeps the laptop address stable.

Once connected, update normally:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

For a restart only: `sudo systemctl restart kid-learning-tv`.
For logs: `sudo journalctl -u kid-learning-tv -n 50 --no-pager`.
Open `http://LAPTOP-IP:8765/parent` on your Mac to use **Refresh TV**.
SSH does not show the desktop or automatically reopen a closed kiosk browser.

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
