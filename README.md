# FPredict: Quantitative Sports-Trading Platform

FPredict is an autonomous predictive engine built for the English Premier League (EPL). It combines tabular and deep-learning models with manager context, live odds ingestion, and a Fantasy Premier League (FPL) advisor to surface match probabilities, value bets, and squad recommendations.

---

## Features

| Area | What it does |
|------|--------------|
| **Match prediction** | Two-tower ensemble (XGBoost + PyTorch DNN) fused by a logistic-regression meta-learner |
| **Manager-aware predictions** | Optional third tower blends tactical/manager signals into base probabilities |
| **Value betting** | Kelly-criterion sizing against live or historical bookmaker odds |
| **Backtesting** | Chronological dry-run simulator with compounding bankroll and equity curve |
| **Feature store** | Point-in-time team vectors: Elo, SDI, form, sentiment, squad power |
| **Fantasy engine** | FPL squad optimizer, transfer suggestions, chip strategy, availability checks |
| **Player intelligence** | Understat/FBref ingestion, impact metrics, PyTorch player/lineup models (in progress) |
| **Manager tracking** | FBref scraper + Supabase `current_managers` table with form and tactical style |
| **Web dashboard** | React 19 / TanStack Start app with glassmorphic UI |
| **Mobile app** | Flutter cockpit connected to Supabase (early stage) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         fpredict_web (React 19)                          │
│  Match Predictor · Fixtures · Fantasy · Managers · Backtest · Features   │
└───────────────┬──────────────────────────────┬──────────────────────────┘
                │ FastAPI (port 8000)           │ Supabase (direct reads)
                ▼                               ▼
┌───────────────────────────┐       ┌───────────────────────────┐
│       src/api/main.py      │       │   current_managers       │
│  FPredictEngine            │       │   (cloud sync)           │
│  ManagerPredictionEngine   │       └───────────────────────────┘
│  FantasyEngine             │
└───────────────┬────────────┘
                │
    ┌───────────┼───────────┬──────────────┬─────────────┐
    ▼           ▼           ▼              ▼             ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐
│Ingestion│ │Feature  │ │  Models  │ │  Fantasy  │ │  Managers  │
│ Layer   │ │ Store   │ │  Towers  │ │  Engine   │ │  Repo      │
└────┬───┘ └────┬────┘ └────┬─────┘ └─────┬─────┘ └──────┬─────┘
     │          │           │             │              │
     └──────────┴───────────┴─────────────┴──────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  PostgreSQL        │
                    │  fpredict_db       │
                    │  (offline-first)   │
                    └───────────────────┘
```

### Predictive stack

1. **Tower A (XGBoost)** — Tabular expert on Elo, form, odds, and derived diffs. Weights: `src/models/tower_a.json`.
2. **Tower B (PyTorch DNN)** — Contextual expert on SDI, sentiment, squad power. Weights: `src/models/tower_b.pth`.
3. **Meta-learner** — Logistic regression blends Tower A/B outputs. Weights: `src/models/meta_learner.joblib`.
4. **Manager Tower (XGBoost)** — Manager H2H, form, and tactical features. Weights: `src/models/manager_tower.json`. Blended at 32% manager / 68% base in `ManagerPredictionEngine`.

### Ingestion layer

- **`curl_cffi`** and **`playwright`** (with stealth) for reliable scraping.
- Parsers for **FBref** and **Understat** (`src/parsing/`).
- Background jobs: Understat deep sync (player rosters), current managers update (FBref → Supabase).
- **`UnderstatDeepSync`** starts automatically when the FastAPI server boots.

### NLP layer

- Local **TinyLlama** via Hugging Face `transformers` for tactical knowledge extraction from news (`src/nlp/sentiment.py`).
- **`NLPManager`** processes `unstructured_news` rows and writes sentiment scores back to the feature store pipeline.
- No external LLM API key required for sentiment processing.

### Storage

- **Local PostgreSQL (`fpredict_db`)** — Primary offline-first datastore.
- **Supabase** — Cloud sync for managers, optional remote reads from the web app.
- Schema defined in `schema.sql` and `supabase/migrations/`.

---

## Tech stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3, FastAPI, Uvicorn, Pydantic, httpx |
| Database | PostgreSQL 16+, psycopg2, Supabase CLI |
| ML | XGBoost, PyTorch, scikit-learn, joblib |
| Scraping | playwright, playwright-stealth, curl_cffi, BeautifulSoup |
| NLP | transformers (TinyLlama) |
| Web | React 19, Vite 8, TanStack Router/Start, Tailwind CSS v4, Recharts |
| Mobile | Flutter, supabase_flutter |
| Deploy | Cloudflare Workers (Wrangler), TanStack Start SSR |
| Package mgmt | yarn (web), pip (Python) |

---

## Repository structure

```
fpredict/
├── src/
│   ├── api/              # FastAPI server (main.py)
│   ├── ingestion/        # Scrapers, sync jobs, pipeline orchestrator
│   ├── parsing/          # FBref & Understat parsers
│   ├── nlp/              # News sentiment & knowledge extraction
│   ├── feature_store/    # Dynamic state vectors, Elo, batch generation
│   ├── models/           # Towers, ensemble, simulator, player/lineup models
│   ├── fantasy/          # FPL guidance engine & player availability validator
│   ├── managers/         # Manager repository, seed data, validation
│   └── alerts/           # SMTP email alerting
├── fpredict_web/         # React web application (TanStack Start)
├── fpredict_app/         # Flutter mobile app
├── supabase/
│   ├── migrations/       # SQL migrations (local + remote)
│   └── config.toml
├── scripts/              # DB migrations, manager model training
├── data/                 # Raw HTML and historical CSV storage
├── schema.sql            # Canonical local DB schema
├── test_prediction.py    # Ensemble smoke test
├── test_smtp.py          # Email alert test
└── start_terminals.sh    # Launch frontend + backend in separate terminals
```

---

## Database

Initialize the local database:

```bash
createdb fpredict_db
psql -d fpredict_db -f schema.sql
./scripts/apply_local_migrations.sh   # applies supabase/migrations/*.sql
```

### Core tables

| Table | Purpose |
|-------|---------|
| `teams` | EPL team lookup, Elo, active flag |
| `players` | Roster with position, injury/suspension/transfer flags |
| `match_records` | Historical and upcoming fixtures with odds and xG |
| `feature_store` | JSONB snapshots per team/date (Elo, SDI, form, sentiment, squad_power) |
| `player_impact_metrics` | Rolling player impact scores |
| `player_performance` | Per-match player stats |
| `unstructured_news` | Raw headlines pending NLP processing |
| `fantasy_player_status` | FPL bootstrap-synced availability (injuries, bans, transfers) |
| `current_managers` | Live manager names, tactical style, last-5 form (Supabase) |

---

## API reference

Base URL: `http://localhost:8000` (override in web app via `VITE_API_URL`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/teams` | List supported frontend team names |
| `POST` | `/predict` | Run two-tower ensemble prediction + value bets |
| `POST` | `/predict/manager` | Manager-blended prediction |
| `POST` | `/backtest` | Run historical dry-run simulation |
| `GET` | `/features/{team}` | Feature store time series for a team |
| `GET` | `/managers` | List known manager names |
| `GET` | `/managers/lookup?home_team=&away_team=` | Resolve managers for a fixture |
| `GET` | `/managers/{name}/profile?team=` | Manager profile with recent form |
| `GET` | `/fantasy/guide?gameweek=` | Full FPL guidance (squad, transfers, chips) |
| `GET` | `/fantasy/gameweek` | Current gameweek and deadline |
| `WS` | `/ws/odds` | Simulated live odds drift (demo) |

On startup the API validates manager data, syncs FPL player availability, and kicks off background Understat sync.

---

## Web interface (`fpredict_web`)

Built with **TanStack Start** (SSR-capable) and deployable to **Cloudflare Workers**.

| Route | Page |
|-------|------|
| `/` | Match Predictor — live ensemble predictions, value bets, H2H history |
| `/fixtures` | Season fixture calendar grouped by month |
| `/players` | Player Intelligence hub (roster browser + AI training UI) |
| `/fantasy` | Fantasy Engine — optimized squad, transfers, chip strategy |
| `/managers` | Manager profiles, tactical styles, form |
| `/backtest` | Interactive backtest simulator with equity chart |
| `/features` | Feature store visualizations per team |
| `/settings` | Risk parameters and configuration |
| `/about` | Platform overview |

The web app reads manager data directly from Supabase when available (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`), falling back to the FastAPI backend.

---

## Environment variables

Create a `.env` file at the project root:

```env
# PostgreSQL (required)
DB_USER=your_db_username
DB_PASSWORD=your_db_password

# Live odds (optional — falls back to DB/historical odds)
ODDS_API_KEY=your_odds_api_key

# Supabase (optional — for cloud sync and web direct reads)
SUPABASE_URL=https://your-project.supabase.co
SERVICE_ROLE_KEY=your_service_role_key

# Email alerts (optional)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your_smtp_password
```

Web app (`fpredict_web/.env` or build-time vars):

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

---

## Getting started

### Prerequisites

- Python 3.10+
- PostgreSQL 16+
- Node.js **v22.12.0+** (required for Cloudflare Vite plugin)
- yarn
- Flutter SDK (mobile app only)

### Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Database setup

```bash
createdb fpredict_db
psql -d fpredict_db -f schema.sql
./scripts/apply_local_migrations.sh
```

### Populate player data

```bash
python -m src.ingestion.understat_deep_sync
```

Optional — sync manager data and train the manager tower:

```bash
python scripts/train_manager_model.py
python -m src.ingestion.current_managers_job
```

### Run everything (recommended)

From the repo root, start frontend and backend together:

```bash
yarn install          # installs concurrently
cd fpredict_web && yarn install && cd ..
yarn dev              # fpredict_web on :3000, API on :8000
```

Or use separate terminals / `start_terminals.sh`:

```bash
# Backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd fpredict_web && yarn dev
```

### Mobile app

```bash
cd fpredict_app
flutter pub get
flutter run
```

### Deploy web to Cloudflare

Requires Node.js v22.12.0+. From `fpredict_web/`:

```bash
yarn run deploy    # builds + wrangler deploy
```

### Supabase migrations (remote)

```bash
supabase db push
# or
python scripts/push_supabase_migrations.py
```

---

## Data pipelines

| Command / module | Purpose |
|------------------|---------|
| `python -m src.ingestion.understat_deep_sync` | Scrape Understat rosters, compute impact scores |
| `python -m src.ingestion.fbref_deep_sync` | FBref squad and match data sync |
| `python -m src.ingestion.current_managers_job` | Update Supabase `current_managers` from FBref |
| `python -m src.ingestion.sync_to_supabase` | Push local data to Supabase |
| `python -m src.pipeline_master` | Weekend workflow: NLP → feature store → signals |
| `python -m src.feature_store.batch_generate` | Regenerate all team feature snapshots |
| `python scripts/train_manager_model.py` | Download manager history + train manager tower |

The API lifespan hook runs manager validation, FPL availability sync, and Understat background sync on every boot.

---

## ML models

| Model | File | Role |
|-------|------|------|
| XGBoost Tower A | `src/models/tower_a.json` | Tabular match outcome probabilities |
| PyTorch Tower B | `src/models/tower_b.pth` | Contextual deep features |
| Meta-learner | `src/models/meta_learner.joblib` | Ensemble fusion |
| Manager Tower | `src/models/manager_tower.json` | Manager-aware probability adjustment |
| PlayerPerformanceModel | `src/models/player_performance_model.py` | Multi-task player stat prediction (WIP) |
| LineupMatchModel | `src/models/lineup_match_model.py` | Full-lineup synergy + match outcome (WIP) |

Train scripts:

```bash
python -m src.models.train_player_model
python -m src.models.train_lineup_model
python scripts/train_manager_model.py
```

---

## Fantasy engine

`src/fantasy/engine.py` powers the `/fantasy/*` API endpoints.

On startup, `src/fantasy/player_validator.py` pulls the official FPL bootstrap API and persists injury, suspension, ban, and transfer status to `fantasy_player_status` before any squad recommendations are served.

The engine provides:

- **Squad optimization** — 15-player squad under £100m budget with FPL position/team constraints
- **Starting XI** — 4-4-2 formation with captain/vice selection
- **Transfer suggestions** — Hold/transfer recommendations with projected point gains
- **Chip strategy** — Wildcard, Free Hit, Bench Boost, Triple Captain timing advice
- **Fixture difficulty** — FDR-weighted projections for upcoming gameweeks

Data source falls back to a curated player pool when the local DB has insufficient roster data.

---

## Backtesting

`src/models/simulator.py` runs a chronological dry-run:

1. Iterates historical matches with point-in-time feature store snapshots (no lookahead).
2. Generates ensemble probabilities for each fixture.
3. Identifies positive-EV bets against historical bookmaker odds.
4. Sizes wagers with fractional Kelly (`bet = bankroll × kelly × fraction`).
5. Compounds wins/losses into an equity curve and ROI report.

```bash
# CLI
python -m src.models.simulator

# API (used by web backtest page)
POST /backtest  { "season": "2023/24", "initial_bankroll": 1000, "kelly_fraction": 0.5 }
```

Supported seasons: `2023/24`, `2024/25`.

---

## Tests

```bash
# Ensemble prediction smoke test (Man City vs Arsenal)
python test_prediction.py

# SMTP alert configuration test
python test_smtp.py

# Web unit tests
cd fpredict_web && yarn test
```

---

## Development workflow

The project follows the football calendar:

- **Weekdays** — Monitoring, scraping validation, regex/parser fixes, data sync checks.
- **Weekends** — Model training, feature engineering, backtest analysis, algorithm work.

---

## Security

- Store all credentials in `.env` (git-ignored). Never commit secrets.
- Local PostgreSQL is the primary fallback — the system operates offline when cloud services are unavailable.
- Supabase service role key is for backend/scripts only; the web app uses the anon key.
- The API currently allows all CORS origins (`*`) — restrict this in production.

---

## Disclaimer

FPredict is an algorithmic analysis and research platform. It is not financial advice. Past backtest performance does not guarantee future results. Use responsibly and in compliance with local gambling regulations.
