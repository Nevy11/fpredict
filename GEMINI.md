# FPredict — Agent Context

Concise project reference for AI assistants working in this repository. For full setup and usage, see [README.md](README.md).

## Overview

Autonomous EPL predictive engine: match probabilities, value bets, manager-aware blending, FPL fantasy guidance, and backtesting. Offline-first on local PostgreSQL with optional Supabase cloud sync.

## Architecture

```
fpredict_web (React 19 / TanStack Start)
    ├── FastAPI :8000  →  FPredictEngine, ManagerPredictionEngine, FantasyEngine
    └── Supabase (direct)  →  current_managers
         │
    PostgreSQL fpredict_db (primary)
```

### Predictive stack

| Component | Path | Role |
|-----------|------|------|
| Tower A (XGBoost) | `src/models/tower_a.json` | Tabular: Elo, form, odds |
| Tower B (PyTorch DNN) | `src/models/tower_b.pth` | Contextual: SDI, sentiment, squad power |
| Meta-learner | `src/models/meta_learner.joblib` | Logistic regression fusion of A + B |
| Manager Tower | `src/models/manager_tower.json` | Manager H2H/form/tactics; 32% blend in `ManagerPredictionEngine` |
| PlayerPerformanceModel | `src/models/player_performance_model.py` | WIP — per-player stat prediction |
| LineupMatchModel | `src/models/lineup_match_model.py` | WIP — lineup synergy + match outcome |

### Other layers

- **Ingestion:** `playwright` + stealth, `curl_cffi`, FBref/Understat parsers (`src/ingestion/`, `src/parsing/`)
- **Feature store:** Dynamic state vectors — Elo, SDI, form PPG/GD, sentiment, squad power (`src/feature_store/`)
- **NLP:** Local **TinyLlama** via `transformers` — not Gemini (`src/nlp/sentiment.py`, `src/nlp/manager.py`)
- **Fantasy:** FPL bootstrap sync, squad optimizer, transfers, chips (`src/fantasy/`)
- **Managers:** Repository + FBref scraper → Supabase `current_managers` (`src/managers/`)

## Repository layout

```
src/api/main.py          FastAPI entry; lifespan validates managers + FPL availability, starts Understat sync
src/ingestion/           Scrapers and sync jobs
src/parsing/             FBref & Understat parsers
src/nlp/                 News sentiment / knowledge extraction
src/feature_store/       Batch feature generation
src/models/              Towers, ensemble, simulator, player/lineup models
src/fantasy/             FPL guidance engine
src/managers/            Manager data repository
src/alerts/              SMTP email alerts
fpredict_web/            React web app (port 3000)
fpredict_app/            Flutter mobile (early stage)
supabase/migrations/     SQL migrations (also applied locally via scripts/apply_local_migrations.sh)
schema.sql               Canonical local DB schema
requirements.txt         Python dependencies
```

## Key API endpoints (`src/api/main.py`)

| Endpoint | Purpose |
|----------|---------|
| `POST /predict` | Two-tower ensemble + value bets |
| `POST /predict/manager` | Manager-blended prediction |
| `POST /backtest` | Historical dry-run simulation |
| `GET /features/{team}` | Feature store time series |
| `GET /fantasy/guide` | FPL squad, transfers, chips (503 until availability sync completes) |
| `GET /managers/lookup` | Resolve managers for a fixture |
| `WS /ws/odds` | Demo odds drift |

## Environment variables (`.env`)

```
DB_USER, DB_PASSWORD          # PostgreSQL (required)
ODDS_API_KEY                  # Live odds (optional)
SUPABASE_URL, SERVICE_ROLE_KEY  # Cloud sync (optional)
SMTP_*                        # Email alerts (optional)
```

Web (`fpredict_web`): `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

## Common commands

```bash
pip install -r requirements.txt && playwright install chromium
createdb fpredict_db && psql -d fpredict_db -f schema.sql
./scripts/apply_local_migrations.sh
python -m src.ingestion.understat_deep_sync
uvicorn src.api.main:app --reload                    # API :8000
cd fpredict_web && yarn dev                          # Web :3000
yarn dev                                             # Both (from repo root)
python -m src.models.simulator                       # Backtest CLI
python test_prediction.py                            # Ensemble smoke test
```

## Database tables (high level)

`teams`, `players`, `match_records`, `feature_store`, `player_impact_metrics`, `player_performance`, `unstructured_news`, `fantasy_player_status`, `current_managers` (Supabase)

## Conventions

- **Offline-first:** Local `fpredict_db` is primary; Supabase is sync/read layer.
- **Team name mapping:** API maps display names ↔ DB names (e.g. "Manchester City" ↔ "Man City") in `main.py`.
- **Startup gates:** Fantasy endpoints return 503 until `validate_players_on_startup` finishes.
- **Credentials:** Never commit `.env`. Web uses anon key; backend/scripts use service role key.
- **Scope:** Minimize diffs; match existing patterns; no over-engineering.

## Disclaimer

Research/analysis platform only — not financial or gambling advice.
