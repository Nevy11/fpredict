# FPredict: Quantitative Sports-Trading Platform

## Project Overview
Autonomous, self-adjusting predictive engine for the English Premier League (EPL). Uses a Two-Tower ensemble (XGBoost + PyTorch) to calculate true mathematical probabilities and identify Value Bets.

## Architecture
- **Ingestion Layer:** Python `asyncio` + `Playwright` (Stealth) / `curl_cffi` (Impersonation).
- **Storage:** Dual-Persistence (Local PostgreSQL + Remote Supabase JSONB).
- **Feature Store:** Computes "Dynamic State Vectors" including Squad Degradation Index (SDI) and Tactical Blueprint.
- **NLP Tower:** Sentiment analysis of news headlines via Gemini Flash-Lite.
- **Predictive Towers:** Quantitative (XGBoost) + Contextual (PyTorch).

## Tech Stack
- **Database:** PostgreSQL (v16+), Supabase CLI (v2.67+).
- **Scraping:** `playwright`, `playwright-stealth`, `curl_cffi`.
- **Processing:** `pandas`, `psycopg2`.
- **NLP:** `google-generativeai` (Gemini SDK).

## Repository Structure
- `src/ingestion/`: Scrapers, downloaders, and pipeline orchestrator.
- `src/parsing/`: FBref and Understat specific parsing logic.
- `src/nlp/`: Sentiment analysis and NLP management.
- `src/feature_store/`: Feature computation and batch generation.
- `data/`: Raw HTML and historical CSV storage.

## Operational Workflow
- **Weekdays:** Low-cognition monitoring and regex adjustments.
- **Weekends:** Deep work on algorithmic engineering and modeling.
- **Security:** Credentials stored strictly in `.env` (git-ignored).
- **Offline-First:** Local PostgreSQL (`fpredict_db`) as primary fallback.
