# Lubuntu installation

This version has only a blank TV display and parent PIN login. No AI, microphone,
games or media features are installed or downloaded.

For an existing installation:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

The update preserves the existing PIN and stored files and backs up the previous
application. Previously downloaded models remain on disk but are not used.
If it fails, fix the reported error and rerun the command; the service stays stopped.

For a fresh installation, install Python 3.10+ and `python3-venv`, then run
`sudo bash scripts/install.sh` from the checkout. Set the parent PIN at the hidden
terminal prompts. Python package installation requires internet.

On the laptop, refresh `http://127.0.0.1:8765/`: the screen should be black and empty.
On your phone, open `http://<laptop-IP>:8765/parent` and sign in. There are no
feature controls after login. Use a trusted private LAN only.

For a forgotten PIN, run
`sudo bash /opt/kid-learning-tv/scripts/reset-parent-pin.sh`.
For service status, run `sudo systemctl status kid-learning-tv --no-pager`.
