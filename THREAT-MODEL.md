# Threat model

## Assets

Parent PIN hash and sessions; local preferences and optional activity history; uploaded video files and metadata; integrity/availability of local content and application files; the child's safe use of the device.

## Trust boundaries and actors

The browser and service communicate over local HTTP. Parent controls cross an authentication/CSRF boundary; child-facing actions are intentionally available to anyone able to reach the appliance. The OS administrator controls installation and backups. The home LAN, connected clients, uploaded files, and physical access are not assumed to be trustworthy by default.

## Main risks and mitigations

| Risk | Existing mitigation | Residual concern |
|---|---|---|
| Unauthorized parent changes | PIN hash, session checks, CSRF tokens, login-attempt tracking | HTTP exposes traffic to LAN observers; child page remains open |
| Malformed content/path input | JSON/schema validation and constrained content paths | OS/user with content write access can alter behavior |
| Untrusted media upload | Parent authentication, MP4/WebM allowlist, signature check, size limit, generated storage names | Media parsing/browser vulnerabilities remain possible |
| Data loss during update | Release snapshot, explicit backup/restore, preserved data on rollback | Backups require secure off-device storage; scripts need Linux validation |
| Internet/cloud collection | Runtime features are local; no STT recording | LAN traffic still exists; OS/browser telemetry is outside app control |
| Kiosk escape or physical access | Optional full-screen browser | Kiosk is not a security boundary; use separate accounts and supervision |

## Out of scope / assumptions

This design does not defend against a compromised OS, physical attacker, malicious administrator, public Wi-Fi, browser/OS vulnerabilities, or unsafe content intentionally supplied by a parent. Do not publish the listener or use it as an internet-facing service. No live Alexa integration or microphone capture is present.
