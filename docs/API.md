# Local API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Black screen or full-screen Food time picture, without controls |
| GET | `/parent` | Parent PIN login and Food time toggle |
| GET | `/api/display` | Current `food_time` boolean, polled by the TV |
| POST | `/api/parent/food-time` | Authenticated parent sets `{"enabled": true}` or `false` |
| GET | `/api/parent/videos` | Parent-only library, download jobs and playback state |
| POST | `/api/parent/videos/download` | Parent submits `url` and `title`; starts one background job |
| POST | `/api/parent/videos/play` | Parent submits ordered `ids` list (1-50 unique entries) |
| POST | `/api/parent/videos/control` | Parent `action`: pause, resume, seek, next, previous, volume, stop |
| GET | `/api/videos/<id>` | Range-capable local stream, laptop or authenticated parent only |
| POST | `/api/tv/playback` | Loopback TV reports progress/ended/error with session and revision |
| POST | `/api/setup` | First PIN setup, localhost only |
| POST | `/api/login` | Parent PIN sign-in; five failed attempts per five minutes |
| POST | `/api/logout` | End authenticated parent session |
| GET | `/api/health` | Basic service/database status |

POST requests require `X-CSRF-Token` from the parent page. Login rotates the token.
PINs contain 6-12 digits. Food time selection is stored locally and survives restart.
Game and voice endpoints remain removed. Playback is in memory; service restart
does not restart videos. `/api/display` also includes `playback` with queue,
current item, position, total/remaining time, paused, volume, buffering, errors
and connection heartbeat. TV reports with stale session/revision return 409.
Use `position` (seconds) for seek and `volume` (0-1) for volume.
