# Kid Learning TV

Current version: **blank black TV screen and parent PIN login only**.
Games, voice, AI, media controls and other feature code have been removed.
Existing PIN and stored files are preserved; no models are downloaded.

Update on the Lubuntu laptop:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

Refresh the TV page at `http://127.0.0.1:8765/`.
Open `http://<laptop-IP>:8765/parent` on your phone and use the existing PIN.
After sign-in, the page has no feature controls.

Use a trusted home network only; do not expose port 8765 to the internet.
See [INSTALLATION.md](INSTALLATION.md) for a fresh installation.
