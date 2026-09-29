# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Macroeconomic crisis monitoring dashboard with a Ukrainian-language UI. Aggregates 17+ collectors (FRED, yfinance, SEC EDGAR, CFTC, EIA, Finnhub, CNN, …) into PostgreSQL. FastAPI serves a scored crisis indicator feed, structured AI analysis, and per-domain data. Nuxt 4 frontend. Celery Beat runs 13 scheduled collection tasks. AI responses (Claude or LongCat) are always instructed to reply in Ukrainian via explicit prompt directives.

## Environments

- **Local development:** Docker Compose (see below)
- **Production:** Remote server at `crisismeter.duckdns.org` — services run as **individual systemd units** (no Docker on prod). Managed via `mcp__ssh-mcp` SSH tool. App lives at `/var/www/html/crisis_dashboard/`.

## Commands

### Docker (local)

```bash
TRANSPORT=json docker compose up --build   # REST only; Swagger at :8000/docs
TRANSPORT=grpc docker compose up --build   # REST + gRPC :50051
docker compose logs -f backend
```

### Frontend (standalone)

```bash
cd frontend && npm install
npm run dev      # dev server at :3000
npm run build
```

### Backend (standalone)

```bash
cd backend && pip install -r requirements.txt
python -m app.main                                       # REST :8000 (+ gRPC if TRANSPORT=grpc)
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat   --loglevel=info
```

> Entry point is `python -m app.main`, not `uvicorn app.main:app`.

### Lint / format

```bash
ruff check backend/     # must be 0 errors before committing
ruff format backend/    # line-length 100, Python 3.12
```

### Manual collection triggers

```bash
curl -X POST http://localhost:8000/collect/indicators
curl -X POST http://localhost:8000/collect/news
curl -X POST http://localhost:8000/collect/yahoo
curl -X POST http://localhost:8000/collect/finnhub
curl -X POST http://localhost:8000/collect/buffett
curl -X POST http://localhost:8000/collect/managers_13f
curl -X POST http://localhost:8000/collect/eia
curl -X POST http://localhost:8000/collect/fed_balance
curl -X POST http://localhost:8000/collect/cpi
curl -X POST http://localhost:8000/collect/cot
curl -X POST http://localhost:8000/collect/fear_greed
curl -X POST http://localhost:8000/collect/signals
curl -X POST http://localhost:8000/collect/index_comparison
curl -X POST http://localhost:8000/analysis/generate
```

### Production service management (via SSH)

```bash
sudo systemctl restart crisis-nuxt
sudo systemctl restart crisis-backend
sudo systemctl restart crisis-celery-worker
sudo systemctl restart crisis-celery-beat
journalctl -u crisis-backend --no-pager -n 50
```

## Architecture

```
internet → nginx:80 → nuxt:3000 (frontend)
                         ↓ $fetch /api/* (nginx strips /api/ prefix)
                    backend:8000 (REST, always on)
                    backend:50051 (gRPC, only when TRANSPORT=grpc)
                         ↓
                    postgres:5432 + redis:6379
                    celery-beat → celery-worker (13 scheduled tasks)
```

### Key locations

| What | Where |
|---|---|
| Entry point | `backend/app/main.py` |
| Celery tasks + beat schedule | `backend/app/celery_app.py` |
| FastAPI app factory + router registration | `backend/app/api/rest.py` |
| REST routes (one file per domain) | `backend/app/api/routes/` |
| Raw data fetchers (no DB writes) | `backend/app/collectors/` |
| DB-persisting wrappers | `backend/app/services/collectors/` |
| ORM models + SessionLocal | `backend/app/models/db.py` |
| Pydantic response schemas | `backend/app/schemas/` |
| Score calculation | `backend/app/services/indicators.py` |
| Unified AI client (Anthropic or LongCat) | `backend/app/services/ai_client.py` |
| Indicator definitions (weight, thresholds) | `backend/app/config/indicators.json` |
| AI analyst config (provider, model, cache TTL) | `backend/app/config/analyst_config.json` |

## Wiring a New Collector (end-to-end)

1. `backend/app/collectors/<name>.py` — fetch data, return `list[dict]`, no DB
2. `backend/app/services/collectors/<name>.py` — call collector, upsert to DB, return summary dict
3. `backend/app/models/db.py` — add ORM model if needed (new table)
4. `backend/app/schemas/<name>.py` — add Pydantic response schema
5. `backend/app/api/routes/<name>.py` — add `GET` route; register in `api/rest.py`
6. `backend/app/api/routes/collect.py` — add `POST /collect/<name>` manual trigger
7. `backend/app/celery_app.py` — add `@celery_app.task` + entry in `beat_schedule`

## Environment Variables

```
FRED_API_KEY=          # FRED API (indicators, CPI, Fed balance)
ANTHROPIC_API_KEY=     # Anthropic Claude API
EIA_API_KEY=           # EIA petroleum API
FINNHUB_API_KEY=       # Finnhub calendar + news
TRANSPORT=json         # json = REST only; grpc = REST + gRPC :50051
AI_PROVIDER=anthropic  # anthropic | longcat — used by services/ai_client.py
LONGCAT_API_KEY=       # required if AI_PROVIDER=longcat
ANTHROPIC_MODEL=claude-sonnet-4-20250514
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/crisisdb
REDIS_URL=redis://redis:6379/0
```

Note: `collectors/ai_analyst.py` has its **own** provider/model config read from `analyst_config.json`, independent of `AI_PROVIDER`.

## Conventions

- **DB sessions:** Use `async with SessionLocal() as session:` in services/collectors, or `Depends(get_session)` in FastAPI routes.
- **Upserts:** `pg_insert(...).on_conflict_do_update(...)` (PostgreSQL dialect, imported as `from sqlalchemy.dialects.postgresql import insert as pg_insert`).
- **Schema auto-created** at startup via `init_db()` → `Base.metadata.create_all`. No Alembic migrations exist.
- **Score formula:** `normalize(value, threshold_low, threshold_high, inverted) × weight` for each indicator, summed and capped at 100.
- **gRPC is optional:** `serve_grpc()` skips gracefully if proto code has not been compiled.
- **Two AI call paths:** `services/ai_client.py` (`AIClient`) is used by YouTube/stock/chat endpoints; `collectors/ai_analyst.py` uses `anthropic` SDK directly with config from `analyst_config.json`.

## Rules

- All code, comments, LLM prompts, and documentation must be in **English**. LLM output language is controlled via explicit instructions in each prompt (e.g., `"Respond in Ukrainian."`).
- Keep `ruff check backend/` at **0 errors** before committing.
- **Do not replace `datetime.utcnow()` / `utcfromtimestamp()`** without also migrating the affected `DateTime` DB columns to timezone-aware types. All `DateTime` columns are naive (no `timezone=True`) and asyncpg expects naive datetimes; mixing the two causes runtime errors.
- Never read or print secret values from `.env`.
- Avoid unnecessary code comments — only comment where logic is non-obvious.

## Known Gotchas

- **`collectors/assets.py`** is dead code — `collect_assets()` and the `Asset` ORM model are defined but not connected to any route, Celery task, or beat schedule.
- **PMI** has a `POST /collect/pmi` route but is **not in the celery beat schedule** — PMI data must be triggered manually.
- **gRPC `GetAnalysis`** is defined in `crisis.proto` but not implemented in `grpc/servicer.py`.
- **Alembic** is in `requirements.txt` but there is no `alembic.ini` or migrations folder.
- **`.env.example`** is incomplete — missing `FINNHUB_API_KEY`, `LONGCAT_API_KEY`, `AI_PROVIDER`, `DATABASE_URL`, `REDIS_URL`.
- **`ai_analyst.py` cache cooldown message** (`"Аналіз оновлено … Спробуйте через …"`) is a user-facing API error string returned as HTTP 429 detail — intentionally left in Ukrainian.

## CI/CD (GitHub Actions)

- **`deploy-backend.yml`** — triggers on push to `main` with `backend/**` changes → SSH → `git pull` → `pip install` → restart `crisis-backend`, `crisis-celery-worker`, `crisis-celery-beat`
- **`deploy-frontend.yml`** — triggers on push to `main` with `frontend/**` changes → `npm install` + `npm run build` → `rsync` `.output/` to server → restart `crisis-nuxt`
- Secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`
