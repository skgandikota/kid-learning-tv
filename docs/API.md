# Local API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Black screen or full-screen Food time picture, without controls |
| GET | `/parent` | Parent PIN login and Food time toggle |
| GET | `/api/display` | Current `food_time` boolean, polled by the TV |
| POST | `/api/parent/food-time` | Authenticated parent sets `{"enabled": true}` or `false` |
| POST | `/api/setup` | First PIN setup, localhost only |
| POST | `/api/login` | Parent PIN sign-in; five failed attempts per five minutes |
| POST | `/api/logout` | End authenticated parent session |
| GET | `/api/health` | Basic service/database status |

POST requests require `X-CSRF-Token` from the parent page. Login rotates the token.
PINs contain 6-12 digits. Food time selection is stored locally and survives restart.
All previous game, voice and media endpoints have been removed.
