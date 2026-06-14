# FPredict: Quantitative Sports-Trading Platform

## Project Overview
Autonomous, self-adjusting predictive engine for the English Premier League (EPL). Uses a Two-Tower ensemble (XGBoost + PyTorch) to calculate true mathematical probabilities and identify Value Bets.

## Architecture
- **Ingestion Layer:** Python `asyncio` + `Playwright` (Stealth) / `curl_cffi` (Impersonation).
- **Storage:** Dual-Persistence (Local PostgreSQL + Remote Supabase JSONB).
- **Feature Store:** Computes "Dynamic State Vectors" including Squad Degradation Index (SDI) and Tactical Blueprint.
- **NLP Tower:** Sentiment analysis of news headlines via Gemini Flash-Lite.
- **Predictive Towers:**
    - **Tower A (XGBoost):** Tabular expert (Elo, Form, Odds). Saved as `src/models/tower_a.json`.
    - **Tower B (PyTorch DNN):** Contextual expert (SDI, Sentiment). Saved as `src/models/tower_b.pth`.

## Tech Stack
- **Database:** PostgreSQL (v16+), Supabase CLI (v2.67+).
- **Scraping:** `playwright`, `playwright-stealth`, `curl_cffi`.
- **Processing:** `pandas`, `psycopg2`.
- **NLP:** `google-generativeai` (Gemini SDK).
- **ML Frameworks:** `xgboost`, `pytorch`, `scikit-learn`.

## Repository Structure
- `src/ingestion/`: Scrapers, downloaders, and pipeline orchestrator.
- `src/parsing/`: FBref and Understat specific parsing logic.
- `src/nlp/`: Sentiment analysis and NLP management.
- `src/feature_store/`: Feature computation and batch generation.
- `src/models/`: Predictive model definitions, saved weights, and ensemble fusion.
- `data/`: Raw HTML and historical CSV storage.

## Operational Workflow
- **Weekdays:** Low-cognition monitoring and regex adjustments.
- **Weekends:** Deep work on algorithmic engineering and modeling.
- **Security:** Credentials stored strictly in `.env` (git-ignored).
- **Offline-First:** Local PostgreSQL (`fpredict_db`) as primary fallback.
