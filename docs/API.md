# Local API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Quiz home/menu/round, or control-free Food time/video |
| GET | `/parent` | Parent PIN login and remote controls |
| GET | `/api/display` | Current `food_time` boolean, polled by the TV |
| POST | `/api/parent/food-time` | Authenticated parent sets `{"enabled": true}` or `false` |
| GET | `/api/parent/videos` | Parent-only library, download jobs and playback state |
| POST | `/api/parent/videos/download` | Parent submits `url` and `title`; starts one background job |
| POST | `/api/parent/videos/play` | Parent submits ordered `ids` list (1-50 unique entries) |
| POST | `/api/parent/videos/control` | Parent `action`: pause, resume, seek, next, previous, volume, stop |
| GET | `/api/videos/<id>` | Range-capable local stream, laptop or authenticated parent only |
| POST | `/api/tv/playback` | Loopback TV reports progress/ended/error with session and revision |
| GET | `/api/quiz/catalog` | Public category names, counts and local tile images |
| POST | `/api/child/quiz` | `menu`, `start` with `category`, or `close`; blocked during Food time/video/end photo |
| GET | `/api/parent/quiz` | Parent settings, catalog, playback and speech status |
| POST | `/api/parent/quiz` | `settings` with seconds/count/ticking; start/category, menu, pause, resume, reveal, next, close |
| POST | `/api/tv/quiz` | Loopback ready/speech-done/image-error, current token and optional warning; stale token returns 409 |
| GET | `/api/quiz/audio/<category>/<item_id>` | Laptop/parent WAV for catalog labels only; explicit 503 on speech failure |
| POST | `/api/setup` | First PIN setup, localhost only |
| POST | `/api/login` | Parent PIN sign-in; five failed attempts per five minutes |
| POST | `/api/logout` | End authenticated parent session |
| GET | `/api/health` | Basic service/database status |

POST requests require `X-CSRF-Token` from the parent page. Login rotates the token.
PINs contain 6-12 digits. Food time selection is stored locally and survives restart.
Old game/voice endpoints remain removed. Playback is in memory; service restart
does not restart videos. `/api/display` also includes `playback` with queue,
current item, position, total/remaining time, paused, volume, buffering, errors
and connection heartbeat. TV reports with stale session/revision return 409.
Use `position` (seconds) for seek and `volume` (0-1) for volume.
Quiz phases are loading, question, answer and complete. `ready` starts the timer;
answers stay at least four seconds, waiting for speech completion (bounded by a
further twelve seconds). No microphone or scoring API exists.
