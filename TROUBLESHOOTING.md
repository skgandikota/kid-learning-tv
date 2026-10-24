# Troubleshooting and recovery

## Service does not start

Run `sudo bash /opt/kid-learning-tv/scripts/diagnose.sh`, then inspect:

```bash
sudo systemctl status kid-learning-tv --no-pager
sudo journalctl -u kid-learning-tv -n 100 --no-pager
```

Confirm Python 3.10+, the virtual environment, `/etc/kid-learning-tv/kid-learning-tv.env`, and read/write access to `/var/lib/kid-learning-tv`. If a port conflict is suspected, inspect local listeners and change `KLT_PORT` in the environment file; restart the service afterward.

## Page not reachable

On the appliance itself, test `http://127.0.0.1:8765/api/health`. From another device, use the appliance's current LAN IP, ensure both devices are on the same trusted network, and check local firewall rules. Do not solve connectivity by opening the port to the public internet.

## Content validation fails

Run `sudo bash /opt/kid-learning-tv/scripts/validate-content.sh`. Correct the JSON or schema issue reported, retain a copy of the original file, then restart the service. Content files are under `/opt/kid-learning-tv/content`.

## Kiosk browser is stuck

Switch to a separate administrator account or a local text console, then run the disable script as the kiosk desktop account:

```bash
bash /opt/kid-learning-tv/scripts/disable-kiosk.sh
```

The script removes the desktop-login trigger and stops the old kiosk user service
if present. Current kiosk startup launches directly in the desktop session.
Press Alt+F4 to close that browser; it does not automatically reopen until your
next login. The app itself runs independently as a system service. No shell or
remote-login access is enabled by kiosk setup.

## Parent PIN recovery

Use `sudo bash /opt/kid-learning-tv/scripts/reset-parent-pin.sh` from a local terminal. It invokes `tools/set_parent_pin.py` as the restricted service account, prompts for the replacement twice with hidden input, and stores only the PBKDF2 hash; the PIN is not passed in arguments or printed.

## Update/regression recovery

Updates retain a dated application snapshot under `/var/backups/kid-learning-tv/releases`. Use `sudo bash /opt/kid-learning-tv/scripts/rollback.sh` to restore the newest snapshot. User data is intentionally preserved. For a data restore, use `restore.sh` only with a trusted backup; it saves a pre-restore copy first.

Never delete `/var/lib/kid-learning-tv` as a troubleshooting shortcut. It contains the database and uploaded family media.
