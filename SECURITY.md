# Security notes

## Deployment

- Keep the appliance on a trusted private LAN. The default listener is `0.0.0.0:8765` over plain HTTP; do not expose it to the internet or forward the port.
- The parent UI uses a PIN, authenticated session, CSRF checks for protected mutations, security response headers, and rate-limited login attempts. PINs are stored as salted PBKDF2-SHA256 hashes.
- Plain HTTP does not encrypt traffic. Anyone able to observe the LAN could potentially see session traffic; use a trusted network and do not reuse the PIN. TLS termination is not configured by these assets.
- Kiosk mode is a convenience, not an OS security boundary. Maintain a separate administrator account and a recovery route.
- The service runs as an unprivileged system user with systemd filesystem restrictions. Review the unit and environment file for local policy before installation.
- Content changes and parent-uploaded media are trusted local inputs, but file uploads remain a risk. Only upload media you trust and have the right to use.

## Operations

Use explicit confirmations for backup restoration, PIN replacement, updates, and kiosk changes. Keep backups access-restricted: they contain the app database and may contain family-uploaded videos and preferences. Updates retain previous files; rollback does not restore the database. Keep the OS and browser patched.

## Reporting

Do not include a real child's information, PIN, database, or media in a bug report. Report reproducible issues with sanitized logs and version/platform details through the project's private maintainer channel.

## Known limitations

No TLS, firewall rules, OS account lockdown, encrypted database, automatic backup, or network authentication for the child UI is configured here. The application has not had a dedicated security audit. Do not treat it as suitable for hostile/public networks.
