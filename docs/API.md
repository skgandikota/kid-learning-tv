# Local HTTP API

The service listens at `http://<host>:8765` by default. All routes are local Flask endpoints; there is no supported public/cloud API contract. JSON is returned for API paths. The child UI and parent UI are served at `/` and `/parent`.

## Main routes

| Method | Path | Access/purpose |
|---|---|---|
| GET | `/api/state` | Current child-visible state |
| POST | `/api/child/action` | Child game/activity action |
| GET | `/api/events` | Local event stream endpoint |
| POST | `/api/setup` | Initial parent setup |
| POST | `/api/login`, `/api/logout` | Parent session |
| GET | `/api/parent/state`, `/api/parent/events` | Parent state/event views; parent session required |
| GET | `/api/parent/qr` | Parent session required; optional QR generation |
| POST | `/api/parent/action` | Parent remote-control actions |
| GET/POST | `/api/parent/categories` | Read/update categories; protected mutations |
| GET | `/api/parent/media` | Parent media library |
| POST | `/api/parent/media/upload` | Parent upload, MP4/WebM, 256 MiB request limit |
| DELETE | `/api/parent/media/<media_id>` | Remove a library item; authenticated and CSRF-checked |
| GET | `/api/media/<media_id>` | Stream a local library item |
| POST | `/api/child/media-progress`, `/api/child/video-ended` | Local player progress/completion |
| GET/POST | `/api/parent/nicknames` | Read/save nicknames |
| GET | `/api/parent/export` | Export settings JSON |
| POST | `/api/parent/import` | Import validated settings JSON |
| POST | `/api/parent/history/delete` | Delete history with explicit `DELETE` confirmation |
| POST | `/api/parent/pin` | Change PIN |
| GET | `/api/parent/backup` | Download SQLite backup |
| GET | `/api/health` | Basic health and feature status |

The parent template supplies the required CSRF token in `X-CSRF-Token` for protected mutations. Parent-only endpoints require a session. QR generation returns 503 unless the optional `qrcode` package is installed; deployment does not install it automatically. Route details can change with the code; inspect `app/main.py` before integrating clients. HTTP is unencrypted by default and the API must not be exposed to an untrusted network.

## Example health response

```json
{"status":"ok","database":true,"stt":"manual-parent-assist","tts_available":false,"uptime_seconds":12}
```

There is no microphone/STT endpoint. `tools/mock_voice_input.py` accepts typed mock text and prints a local demo event; it does not capture sound.

## Learning library

`GET /api/parent/state` includes `learning_catalog`. Parent actions use
`POST /api/parent/action` with the existing authenticated session and CSRF token:

- `{"action":"learning_enabled","activity_id":"matching-pairs","enabled":true}`
- `{"action":"start_learning","activity_id":"matching-pairs"}`
- Existing `home`, `reset`, `pause`, `resume`, `lock` and `unlock` control the session.

Activity IDs are `matching-pairs`, `count-objects`, `match-colours` and
`match-shapes`. All start disabled. Enabled IDs persist under
`enabled_learning_activities`; disabling the current activity stops it.

Child state includes `parent_managed_activity` and `learning_game`. Submit
`learning_answer` through `/api/child/action` with the current game's `session_id`,
`revision`, and `choice` (integer card ID for pairs, string option otherwise).
`learning_settle` uses the same session/revision after a mismatched pair's reveal
delay. Hidden card identities are not sent to clients. Stale turns are rejected.
Children cannot start or exit these activities; automatic session breaks remain
available. Finished boards remain on screen until a parent acts.
