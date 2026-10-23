# Local API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Empty black TV screen |
| GET | `/parent` | Parent PIN login; signed-in page has no feature controls |
| POST | `/api/setup` | First PIN setup, localhost only |
| POST | `/api/login` | Parent PIN sign-in; five failed attempts per five minutes |
| POST | `/api/logout` | End authenticated parent session |
| GET | `/api/health` | Basic service/database status |

POST requests require `X-CSRF-Token` from the parent page. Login rotates the token.
PINs contain 6-12 digits. All previous feature endpoints have been removed.
