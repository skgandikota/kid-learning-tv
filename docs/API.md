# Local API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Quiz home/menu/round, or control-free Food time/video |
| GET | `/parent` | Parent PIN login and remote controls |
| GET | `/api/display` | Current `food_time` boolean, polled by the TV |
| POST | `/api/parent/food-time` | Authenticated parent sets `{"enabled": true}` or `false` |
| POST | `/api/parent/display` | Authenticated parent sends action `home`, `clock`, `move-back`, `painting` or `refresh` |
| GET | `/api/parent/videos` | Parent-only library, download jobs and playback state |
| POST | `/api/parent/videos/download` | Parent submits `url` and `title`; starts one background job |
| POST | `/api/parent/videos/play` | Parent submits ordered `ids` list (1-50 unique entries) |
| POST | `/api/parent/videos/control` | Parent `action`: pause, resume, seek, next, previous, volume, stop |
| GET | `/api/videos/<id>` | Range-capable local stream, laptop or authenticated parent only |
| POST | `/api/tv/playback` | Loopback TV reports progress/ended/error with session and revision |
| GET | `/api/quiz/catalog` | Public category names, counts and local tile images |
| POST | `/api/child/quiz` | `menu`, `start` with `category`, or `close`; blocked during Food time/video/end photo |
| POST | `/api/child/matching` | `start`, `close`, or `flip` with board `token` and integer `index`; CSRF required |
| GET | `/api/typing/catalog` | Curated character/word choices and local picture paths |
| POST | `/api/child/typing` | `menu`, `start` with lesson `id`, `key`, `next`, `previous`, `advance`, or `close`; CSRF required. Navigation requires current `token`; `advance` also requires completion |
| GET | `/api/typing/audio/<id>/<position>/<kind>` | Local TV/parent WAV; allowlisted name, spell, sound or blend only |
| GET | `/api/adventures/catalog` | Enabled adventure IDs, names and local pictures |
| POST | `/api/child/adventures` | `menu`, `start` with `id`, `close`, or current-token `pick`/`ready`/`remember`/`next`; CSRF required |
| GET/POST | `/api/parent/adventures` | Parent-only settings/status and remote start/menu/close |
| GET | `/api/adventures/audio/<key>` | Local TV/parent WAV for fixed allowlisted instruction keys only |
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
Home selects `blank` (game choices); Clock selects `clock` (local 24-hour
digital time only). Both clear games, video queues and Food time. Child game
controls cannot leave Clock; a parent selects Home or another activity.
Clock survives a page refresh, not a service restart.
`move-back` and `painting` select control-free reminder screens, clearing all
games, video queues and Food time. Child controls cannot dismiss them.
They persist through page refresh but not service restart.
`refresh` rotates `playback.refresh_token` and increments the revision without
changing the active activity. TV polling compares the token with its page's
initial token and reloads once when different, including after a service
restart. Refresh requests require parent authentication and CSRF protection.
Use `position` (seconds) for seek and `volume` (0-1) for volume.
Quiz phases are loading, question, answer and complete. `ready` starts the timer;
answers stay at least four seconds, waiting for speech completion (bounded by a
further twelve seconds). No microphone or scoring API exists.

`playback.matching` contains the current board token, round 1-20, card states,
and phase (playing, match, mismatch, round-done, complete).
Face-down cards have no image/name in the response. Board sizes are 4, 6, 8...42;
each image appears exactly twice. A match vanishes after 0.8 seconds; a mismatch
flips back after 1.5 seconds. Completing a board advances after a short pause.
Stale, duplicate and out-of-turn flips return 409; invalid indexes return 400.
Child matching controls cannot interrupt quizzes, Food time, video or the end
photo (423). Parents can interrupt through existing Food/video/quiz controls.
The game stays in memory only; a service restart does not resume it.

`playback.typing` holds the lesson, board token, accepted-letter position and
completion flag. A `key` command supplies `token`, integer `position` and a
single ASCII alphabetic `key`; uppercase/lowercase are equivalent.
Wrong letters return `accepted:false` without progress; stale positions/tokens
return 400. The response flags available `sound` and cumulative `blend`.
Sound groups such as SH play only when the entire group is typed.
`next`/`previous` allow skipping at any time with the current token.
`advance` requires completion and follows the full-name audio on the TV.
Spaces are automatic.
Typing controls cannot interrupt another activity (423).
Audio kind `name` and `spell` use position 0; `sound` and `blend` require an
allowlisted group-ending position. Unknown sounds return 400; synthesis
failure returns 503. No arbitrary speech text or raw phonemes are accepted.

`playback.adventure` contains the game ID, turn token, phase, visible picture
choices, collected count, scene parts and fixed prompt/audio key.
Phases are `preview` (bag only), `play`, `success` and `finished`.
`pick` supplies current `token` and picture `choice`; wrong pictures return
gentle feedback without losing progress. Collected cards and old tokens
return 400 if repeated. `ready` hides memory pictures; `remember` shows them
again and clears the current packing attempt. `next` requires success.
Child controls return 423 during other activities. Parent start/menu may
interrupt, but parent close never stops an unrelated activity.
Settings are exactly `enabled` (list of game IDs), `rescue_max` (3/5),
`bag_size` (2/3) and `spoken` (boolean). They apply to the next game;
disabling the current game closes it immediately. Empty `enabled` is valid.
