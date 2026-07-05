# FPredict: Quantitative Sports-Trading Platform

FPredict is an autonomous, self-adjusting predictive engine designed specifically for the English Premier League (EPL). By utilizing a Two-Tower ensemble (XGBoost + PyTorch), FPredict calculates true mathematical probabilities to identify and capitalize on Value Bets.

## 🚀 Architecture

The system is built on a robust, scalable architecture separated into distinct layers:

- **Ingestion Layer:** Powered by Python `asyncio` along with `Playwright` (Stealth) and `curl_cffi` for reliable impersonation and stealth scraping.
- **Storage:** Dual-Persistence strategy utilizing a Local PostgreSQL database as the primary offline-first fallback and Remote Supabase JSONB for cloud sync.
- **Feature Store:** Dynamically computes "Dynamic State Vectors", which include advanced metrics such as the Squad Degradation Index (SDI) and Tactical Blueprints.
- **NLP Tower:** Integrates Gemini Flash-Lite via the `google-generativeai` SDK to perform sentiment analysis on recent news headlines.
- **Predictive Towers (Two-Tower Ensemble):**
  - **Tower A (XGBoost):** The tabular expert focusing on standard metrics (Elo, Form, Odds).
  - **Tower B (PyTorch DNN):** The contextual expert handling advanced and dynamic features (SDI, Sentiment analysis).

## 🛠 Tech Stack

- **Database:** PostgreSQL (v16+), Supabase CLI (v2.67+)
- **Scraping:** `playwright`, `playwright-stealth`, `curl_cffi`
- **Data Processing:** `pandas`, `psycopg2`
- **NLP:** `google-generativeai` (Gemini SDK)
- **Machine Learning:** `xgboost`, `pytorch`, `scikit-learn`
- **Package Management:** `yarn`

## 📂 Repository Structure

- `src/ingestion/`: Web scrapers, downloaders, and the primary pipeline orchestrator.
- `src/parsing/`: Specific parsing logic for platforms like FBref and Understat.
- `src/nlp/`: NLP management and headline sentiment analysis.
- `src/feature_store/`: Batch generation and computation of advanced features.
- `src/models/`: Predictive model definitions, saved weights (`tower_a.json`, `tower_b.pth`), and the ensemble fusion logic.
- `data/`: Local storage for raw HTML files and historical CSV datasets.
- `fpredict_app/`: Application frontend / interface.
- `supabase/`: Supabase configuration and edge functions.

## ⚙️ Operational Workflow

The project's maintenance and development are structured around the football calendar:
- **Weekdays:** Focus on low-cognition monitoring, scraping validation, and regex adjustments.
- **Weekends:** Dedicated to deep algorithmic engineering, modeling improvements, and analyzing match outcomes.

## ▶️ Running the Project

1. **Environment Setup:** Ensure all your credentials and API keys are stored in a `.env` file at the root of the project.
2. **Web Application:**
   To run the frontend/web app, navigate to the `fpredict_app` directory, install dependencies using `yarn`, and start the development server:
   ```bash
   cd fpredict_app
   yarn install
   yarn run dev
   ```
3. **Supabase Functions:**
   To deploy the Supabase Edge Functions:
   ```bash
   supabase functions deploy <function_name> --no-verify-jwt
   ```

## 🧪 Running Tests

To verify that the core predictive engine and email alerting systems are functioning correctly, you can run the test scripts provided in the root directory:

1. **Prediction Engine Test:**
   Tests the Two-Tower ensemble (XGBoost + PyTorch) model predictions by loading local model weights and running a hypothetical match (e.g., Man City vs Arsenal).
   ```bash
   python test_prediction.py
   ```

2. **Email Alert Test:**
   Tests the SMTP configuration and notification system to ensure alerts can be sent properly.
   ```bash
   python test_smtp.py
   ```

## 🔒 Security & Deployment

- **Environment Variables:** All credentials and API keys must be strictly stored in a `.env` file (git-ignored).
- **Offline-First:** The local PostgreSQL (`fpredict_db`) acts as the primary fallback, ensuring operations can continue without internet dependence.
- **Supabase Deployment:** Edge functions are deployed via the Supabase CLI. 
  *(Note: Always deploy the Supabase Edge Function with: `supabase functions deploy <function_name> --no-verify-jwt`)*

---

*This project is an advanced algorithmic trading system and is intended for quantitative analysis and research purposes.*
