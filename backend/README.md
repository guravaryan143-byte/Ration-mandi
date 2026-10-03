# Live Availability & Queue Dashboard — Backend

REST + WebSocket API that lets local shops, ration shops, EV charging stations, pharmacies and small
museums/monuments publish **live status and queue levels**, so citizens can check before they travel.
Frontend not included; every endpoint returns JSON ready for a React/HTML/JS client.

**Stack:** Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2, Alembic, Pydantic v2, JWT (PyJWT) + bcrypt, Uvicorn.

---

## Quick start (Docker — recommended for demos)

```bash
cp .env.example .env
# put a real secret in .env:
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste as SECRET_KEY=
docker compose up --build            # starts PostgreSQL, runs migrations, serves on :8000
docker compose exec api python -m app.utils.seed      # load demo data (add --reset to wipe first)
```

Open **http://localhost:8000/docs** (Swagger) or `/redoc`.

## Local setup (without Docker)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # set SECRET_KEY and DATABASE_URL
createdb livedash                    # or any empty PostgreSQL database matching DATABASE_URL
alembic upgrade head                 # create tables
python -m app.utils.seed             # optional demo data
uvicorn app.main:app --reload
```

`DATABASE_URL` uses the psycopg 3 driver, e.g. `postgresql+psycopg://user:pass@localhost:5432/livedash`.
The app refuses to start without `SECRET_KEY` (≥ 32 chars); no secret is hard-coded anywhere.

### Migrations
```bash
alembic upgrade head                                   # apply
alembic revision --autogenerate -m "describe change"   # after editing app/models
alembic downgrade -1                                   # roll back one step
```

### Tests
```bash
pytest -q        # 34 tests; they use an in-memory SQLite DB, no PostgreSQL needed
```
(Constraint behaviour — CHECKs and composite FKs — is exercised on SQLite with foreign keys enabled; the
same DDL is generated for PostgreSQL by the migration.)

---

## Demo accounts (after seeding)
Password for all: `Demo@12345` (override with `SEED_PASSWORD`). **Demo only — never seed production.**

| Email | Role |
|---|---|
| admin@example.com | ADMIN |
| owner1@example.com | OWNER — ration shops + museums |
| owner2@example.com | OWNER — EV stations |
| owner3@example.com | OWNER — pharmacies |
| citizen@example.com | CITIZEN |

Seed data (Mumbai): 3 ration shops, 2 museums/monuments, 3 EV stations, 4 pharmacies, queue/status variety,
and a few audit-history entries. Sample coordinates for searches: `latitude=19.0760&longitude=72.8777`.

## The four hackathon scenarios (no login needed)

```bash
B=http://localhost:8000
# 1. Ration shop: stock, queue, last updated
curl "$B/api/ration-shops"
# 2. Museum: open/closed, crowd level, history, guide
curl "$B/api/museums";  curl "$B/api/museums/4/guide"
# 3. EV charging: total / occupied / available plugs, wait time, status (nearest first)
curl "$B/api/ev-stations?latitude=19.0760&longitude=72.8777&radius=10"
# 4. Rare medicine: pharmacies, availability, quantity, distance, address, last updated
curl "$B/api/pharmacies/search-medicine?medicine=riluzole&latitude=19.0760&longitude=72.8777"
```

Live update demo: log in as an owner, open a WebSocket to `/ws/locations/{id}`, then change data:

```bash
TOKEN=$(curl -s -X POST $B/api/auth/login -H 'content-type: application/json' \
  -d '{"email":"owner1@example.com","password":"Demo@12345"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")
# one request: stock + queue
curl -X PUT $B/api/ration-shops/1/stock -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"rice":"LOW_STOCK","dal":"OUT_OF_STOCK","queue_level":"HIGH"}'
```
Browser console: `new WebSocket("ws://localhost:8000/ws/locations/1").onmessage = e => console.log(JSON.parse(e.data))`

---

## API overview

Success: `{"success": true, "data": ..., "meta": {"total","limit","offset"}}` (`meta` only on lists).
Error: `{"success": false, "error": {"code": "LOCATION_NOT_FOUND", "message": "..."}}` (validation errors add `details`).
Authenticated calls send `Authorization: Bearer <access_token>`. Lists accept `limit` (1-100) and `offset`.

**Auth** — `POST /api/auth/register` (roles `CITIZEN`/`OWNER`; admins cannot self-register), `POST /api/auth/login` (JSON body), `GET /api/auth/me`

**Public** (rate limited) — `GET /api/locations` · `/nearby` · `/search` · `/{id}`
Filters: `category, status, queue_level, keyword, latitude, longitude, radius` (km; default 5 for nearby).
Every location includes `status`, `queue_level`, `last_updated`, `distance_km` (when coordinates given) and its category data
(`ration_stock`, `museum`, `ev_station` with computed `available_plugs`, `medicines`).

| Category | Public | Owner/Admin |
|---|---|---|
| Ration | `GET /api/ration-shops[/{id}]` | `PUT .../{id}/status`, `PUT .../{id}/stock` (stock + status + queue in one call) |
| Museum | `GET /api/museums[/{id}]`, `GET .../{id}/guide` | `PUT .../{id}/status` (status, crowd, hours, description, guide URL/content id) |
| EV | `GET /api/ev-stations[/{id}]` | `PUT .../{id}/availability` |
| Pharmacy | `GET /api/pharmacies[/{id}]`, `GET .../search-medicine?medicine=` | `PUT .../{id}/inventory` |

**Owner** — `GET/POST /api/owner/locations`, `PUT/DELETE /api/owner/locations/{id}`, `GET .../{id}/updates` (audit trail),
`POST .../{id}/update-status`

**Admin** — `GET /api/admin/users`, `PUT /api/admin/users/{id}/active`, `GET /api/admin/locations`,
`PUT /api/admin/locations/{id}/approve|reject`, `DELETE /api/admin/locations/{id}`, `GET /api/admin/stats`

**WebSocket** — `WS /ws/locations/{id}`: sends a `snapshot` on connect, then `{"event":"location_update","location_id":..,"data":{...}}`
after every stock / queue / EV / inventory / status change. Send `ping` to receive `{"event":"pong"}`.
Unknown or unapproved locations close with code `4404`.

---

## Behaviour worth knowing

- **Approval workflow:** owner-created locations are `PENDING` and invisible to the public until an admin approves.
  Owners/admins can still see them. Rejected or deleted locations disappear from public results.
- **Authorization:** CITIZEN has read-only public access. OWNER can only modify locations where `owner_id` is theirs
  (403 otherwise). ADMIN can modify anything.
- **Delete = soft delete.** The row is hidden but the audit history is preserved.
- **EV:** `available_plugs = total_plugs - occupied_plugs` (derived, never stored). `occupied_plugs > total_plugs` is rejected
  by the API (`422 INVALID_PLUG_COUNT`) *and* by a database CHECK. If you don't send `status`, an `AVAILABLE`/`BUSY` station
  flips to `BUSY` at 0 free plugs and back to `AVAILABLE` otherwise; manual states (`MAINTENANCE`, `CLOSED`) are never overridden.
- **Ration:** if you don't send overall `status`, it becomes `OUT_OF_STOCK` when rice, wheat and dal are all out and returns to
  `AVAILABLE` when something is restocked.
- **Pharmacy:** inventory only (name, availability, optional quantity, prescription-required flag, last update). No patient or
  prescription data exists in the schema. `quantity: 0` is stored as unavailable. Medicine names are matched case-insensitively,
  by substring.
- **Audit trail:** every changed field writes a `location_updates` row (timestamp, location, user, previous → new value, optional `note`).
  Re-sending identical values still refreshes `last_updated` ("still accurate") but adds no audit row.
- **Database rules:** CHECK constraints for enum values, EV plug counts and lat/lon ranges; composite foreign keys
  `(location_id, category)` make it impossible to attach, e.g., a medicine to a museum.

## Project layout
```
app/main.py            app factory, CORS, routers
app/config.py          env settings (python-dotenv)
app/database.py        engine/session/Base
app/models/            SQLAlchemy models
app/schemas/           Pydantic request/response models
app/routers/           thin HTTP handlers
app/services/          all business logic (auth, locations, ration, museum, EV, pharmacy, audit, admin)
app/auth/              JWT + bcrypt, role dependencies
app/websocket/         connection manager + /ws route
app/utils/             errors, handlers, geo, rate limit, seed
migrations/            Alembic
tests/                 pytest suite
```

## Scaling & security notes
- The rate limiter and WebSocket manager are **in-process**. Run one worker for the demo; for several workers/instances
  swap in Redis (rate limiting + pub/sub for broadcasts). Behind a reverse proxy, forward the real client IP
  (e.g. uvicorn `--proxy-headers`) so limits apply per user.
- Nearby search uses a bounding-box SQL pre-filter (indexed on latitude/longitude) followed by an exact haversine check; for very large
  datasets move to PostGIS. Medicine search is substring-based; add a `pg_trgm` index if the inventory grows large.
- Passwords: bcrypt (max 72 bytes). Tokens: HS256 JWT with expiry. There is no refresh-token or login throttling —
  put the API behind a gateway with login rate limiting for production.
- Create the first real admin by inserting a user with role `ADMIN` (hash with `app.auth.security.hash_password`) or by running the seed
  in a non-production environment.
