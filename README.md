# FPredict: Quantitative Sports-Trading Platform

FPredict is an autonomous, self-adjusting predictive engine designed specifically for the English Premier League (EPL). By utilizing a Two-Tower ensemble (XGBoost + PyTorch), FPredict calculates true mathematical probabilities to identify and capitalize on Value Bets.

## 🚀 Architecture

The system is built on a robust, scalable architecture separated into distinct layers:

- **Ingestion Layer:** Powered by Python `asyncio` along with `Playwright` (Stealth) and `curl_cffi` for reliable impersonation and stealth scraping. Includes automated background cron jobs that continually update current EPL managers and track their recent form (last 5 games) to align tactical models.
- **Storage:** Dual-Persistence strategy utilizing a Local PostgreSQL database as the primary offline-first fallback and Remote Supabase for cloud sync (including a dedicated `current_managers` table).
- **Feature Store:** Dynamically computes "Dynamic State Vectors", which include advanced metrics such as the Squad Degradation Index (SDI) and Tactical Blueprints.
- **NLP Tower:** Integrates Gemini Flash-Lite via the `google-generativeai` SDK to perform sentiment analysis on recent news headlines.
- **Predictive Towers (Two-Tower Ensemble):**
  - **Tower A (XGBoost):** The tabular expert focusing on standard metrics (Elo, Form, Odds).
  - **Tower B (PyTorch DNN):** The contextual expert handling advanced and dynamic features (SDI, Sentiment analysis).

## 🛠 Tech Stack

- **Database:** PostgreSQL (v16+), Supabase CLI (v2.67+), `@supabase/supabase-js`
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
- `fpredict_web/`: The primary Web Application interface. Built with **React 19**, **Vite**, **TailwindCSS**, and **TanStack Router**, it provides a stunning, glassmorphic UI for running live predictions, viewing the match schedule, and interacting with the backend API.
- `fpredict_app/`: Mobile application frontend / interface built with Flutter.
- `supabase/`: Supabase configuration and edge functions.

## 🌐 Web Interface

The frontend (`fpredict_web`) is designed as a modern, high-performance portal to the Quantum predictive engine:
- **Architecture:** Uses a Vite-powered React architecture with TanStack Router for type-safe routing.
- **Aesthetics:** Implements a premium "Glassmorphism" UI with deep purples, sleek translucency, and CSS-driven micro-animations. 
- **Integration:** Directly hooks into the FastAPI backend for complex ensemble blending. Additionally, it queries Supabase directly using `@supabase/supabase-js` to fetch the latest manager profiles, recent form (last 5 games), and tactical styles, bypassing the backend for real-time manager updates.

The project's maintenance and development are structured around the football calendar:
- **Weekdays:** Focus on low-cognition monitoring, scraping validation, and regex adjustments.
- **Weekends:** Dedicated to deep algorithmic engineering, modeling improvements, and analyzing match outcomes.

## ▶️ Running the Project

1. **Environment Setup & Database:**
   - Ensure you have PostgreSQL running locally with the `fpredict_db` database initialized and the `teams` and `feature_store` tables populated.
   - Create a `.env` file at the root of the project with your credentials:
     ```env
     DB_USER=your_db_username
     DB_PASSWORD=your_db_password
     ODDS_API_KEY=your_odds_api_key # Optional, but recommended for live odds ingestion
     ```

2. **Backend API (FastAPI):**
   To serve predictions to the frontend applications, first ensure all backend dependencies are installed:
   ```bash
   pip install fastapi uvicorn pydantic httpx pandas psycopg2-binary xgboost torch scikit-learn python-dotenv
   ```
   Start the FastAPI development server:
   ```bash
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Web Application (React/Vite):**
   To run the web frontend, navigate to the `fpredict_web` directory, install dependencies, and run the development server:
   ```bash
   cd fpredict_web
   yarn install
   yarn run dev
   ```
   **Deploying to Cloudflare:**
   The frontend is configured as a TanStack Start application, meaning it can be easily deployed to Cloudflare Workers using Wrangler.
   
   **Important Note:** The Cloudflare Vite plugin requires **Node.js v22.12.0 or higher**. Ensure your environment is updated (e.g., `nvm use 22`) before building.

   To build and deploy the project, navigate to `fpredict_web` and run:
   ```bash
   yarn run deploy
   ```

4. **Mobile Application (Flutter):**
   To run the mobile app, navigate to the `fpredict_app` directory, get the Flutter dependencies, and run the app:
   ```bash
   cd fpredict_app
   flutter pub get
   flutter run
   ```

5. **Supabase Functions:**
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

## 📈 Profitability Backtesting

To validate the financial viability of the models, the system includes a **Historical Dry-Run Simulator** (`src/models/simulator.py`). 
The backtesting algorithm operates as follows:

1. **Chronological Simulation**: It iterates through historical matches from the database, retrieving the precise point-in-time state of the Feature Store (Elo, SDI, form, sentiment, etc.) exactly as it was on each `match_date` to prevent lookahead bias.
2. **Probability Generation**: It passes these historical features into the Two-Tower Ensemble to calculate the "true" mathematical probabilities of each match.
3. **Value Bet Identification**: It compares the model's true probabilities against actual historical bookmaker odds to find positive expected value (EV) edges.
4. **Fractional Kelly Sizing**: For identified Value Bets, it determines the optimal wager size using the **Kelly Criterion** (`f* = (bp - q) / b`), scaled down to a **10% Fractional Kelly** strategy (`bet_amount = bankroll * kelly * 0.1`) for safer risk management.
5. **Bankroll Compounding**: Starting with a mock initial bankroll (e.g., $1000), it chronologically applies simulated wins and losses based on actual match outcomes to demonstrate the compounded Return on Investment (ROI) over a season.

You can run the backtest simulation via:
```bash
python -m src.models.simulator
```

## 🔒 Security & Deployment

- **Environment Variables:** All credentials and API keys must be strictly stored in a `.env` file (git-ignored).
- **Offline-First:** The local PostgreSQL (`fpredict_db`) acts as the primary fallback, ensuring operations can continue without internet dependence.
- **Supabase Deployment:** Edge functions are deployed via the Supabase CLI. 
  *(Note: Always deploy the Supabase Edge Function with: `supabase functions deploy <function_name> --no-verify-jwt`)*

---

*This project is an advanced algorithmic trading system and is intended for quantitative analysis and research purposes.*
