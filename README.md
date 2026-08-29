# ⚽ MatchIQ — Football Match Outcome Prediction & Analytics Platform

> An end-to-end, production-grade Machine Learning platform for Premier League match outcome prediction, probabilistic simulation, and historical intelligence. Trained on **13 authentic seasons (2013–2026, 4,940 matches)** from [football-data.co.uk](https://www.football-data.co.uk/), powered by **45 anti-leakage features** (Dynamic Elo $K=28$, Home Advantage $+65$, rolling form, pre-match standings), **SHAP explainable AI**, and a **10,000-run Monte Carlo 2026–27 season simulator**.

[![CI](https://github.com/DevPranavJad700/matchiq/actions/workflows/ci.yml/badge.svg)](https://github.com/DevPranavJad700/matchiq/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-40%20Passed-brightgreen.svg)](https://github.com/DevPranavJad700/matchiq)

---

## 📑 Table of Contents

- [Key Highlights](#-key-highlights)
- [System Architecture](#-system-architecture)
- [Project Directory Layout](#-project-directory-layout)
- [Quick Start](#-quick-start)
  - [Option A: Docker Compose (Production Setup)](#option-a--docker-compose-production-setup)
  - [Option B: Local Development Setup](#option-b--local-development-setup)
- [Machine Learning & Modeling Pipeline](#-machine-learning--modeling-pipeline)
  - [45 Anti-Leakage Feature System](#45-anti-leakage-feature-system)
  - [Candidate Model Benchmark & Evaluation](#candidate-model-benchmark--evaluation)
  - [Explainable AI (SHAP & Marginal Sensitivity Drivers)](#explainable-ai-shap--marginal-sensitivity-drivers)
- [2026–27 Premier League Season AI Simulation](#-202627-premier-league-season-ai-simulation)
  - [Simulated 2026–27 Standings Table](#simulated-202627-standings-table)
  - [Running the Live Simulation Script](#running-the-live-simulation-script)
- [Analytics & Multi-Season Intelligence Dashboard](#-analytics--multi-season-intelligence-dashboard)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Dataset Provenance & Verification](#-dataset-provenance--verification)
- [Documentation & Resources](#-documentation--resources)
- [Disclaimer](#-disclaimer)

---

## 🌟 Key Highlights

* **100% Authentic Dataset**: Ingests **4,940 matches** across 35 clubs spanning 13 completed Premier League seasons (2013–14 through 2025–26) with cryptographic SHA-256 validation (`ed8a946781ea...`).
* **Zero-Leakage Feature Engineering**: Strict `.shift(1)` temporal windows calculating sequential **Dynamic Elo ratings** ($K=28.0$, Home Field $+65$), schedule congestion/rest days, dynamic pre-match standings positions, and rolling form/xG metrics.
* **Production ML Engine**: Active **RandomForestClassifier** refitted on 100% of authentic data, calibrated to beat naive baselines by **+7.96% accuracy** and minimize multi-class log loss.
* **Feature Importance Drivers (XAI)**: Dynamic SHAP values decomposed per matchup with signed directional contributions (🟢 Boost / 🔴 Drag) and contextual human-readable explanations.
* **2026–27 Full Season Monte Carlo Simulation**: 10,000-iteration stochastic simulation predicting all **380 match fixtures** and final 20-team standings for the new 2026–27 season (including **Hull City**, **Coventry City**, and **Ipswich Town**).
* **Multi-Season Analytics Dashboard**: Seamlessly switch between **14 seasons** (2026–27 AI Projected down to 2013–14) with dynamic league tables, champions, and attacking/defensive analytics.
* **Enterprise Full-Stack Stack**: FastAPI backend, SQLAlchemy 2.0 repository layer, PostgreSQL database, React 19 + TypeScript frontend with glassmorphism dark mode UI.

---

## 🏗️ System Architecture

```
                                  MATCHIQ PLATFORM ARCHITECTURE

  ┌──────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    REACT 19 + VITE SPA                                   │
  │  Match Predictor  │  Analytics & 14-Season Standings  │  Team Detail  │  Live Head-to-Head│
  └─────────────────────────────────────────────┬────────────────────────────────────────────┘
                                                │ REST API (JSON / HTTP)
                                                ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────┐
  │                                 FASTAPI BACKEND SERVICES                                 │
  │  ├── Predictions Router   ───> PredictionService ───> ModelLoader (Singleton)            │
  │  ├── Leagues Router       ───> LeagueRepository  ───> Standings & Multi-Season Analytics │
  │  ├── Matches & Teams      ───> TeamRepository    ───> H2H & Form Extraction              │
  │  └── Health & Provenance  ───> ProvenanceService ───> SHA-256 Checksum Verification     │
  └───────────────────────┬───────────────────────────────────────────┬──────────────────────┘
                          │                                           │
                          ▼                                           ▼
  ┌───────────────────────────────────────────────┐ ┌────────────────────────────────────────┐
  │             POSTGRESQL DATABASE               │ │          MACHINE LEARNING ENGINE       │
  │  • 36 Teams (inc. Promoted 2026-27 Clubs)     │ │  • Model: RandomForest (45 features)   │
  │  • 14 Seasons (2013-14 to 2026-27)            │ │  • Dynamic Elo System (K=28, Home=+65) │
  │  • 4,940 Matches & 9,880 Match Statistics     │ │  • SHAP TreeExplainer & Marginal Drivers│
  │  • 280 Season Standing Records                │ │  • 10,000-run Monte Carlo Simulator    │
  └───────────────────────────────────────────────┘ └────────────────────────────────────────┘
```

---

## 📁 Project Directory Layout

```
matchiq/
├── backend/                       # FastAPI REST API Backend
│   ├── app/
│   │   ├── api/                   # Route handlers (predictions, leagues, teams, matches, health)
│   │   ├── core/                  # Configuration (Pydantic Settings, DATA_MODE)
│   │   ├── db/                    # SQLAlchemy database engine and session
│   │   ├── ml/                    # model_loader.py (Singleton loader, SHAP explainer)
│   │   ├── models/                # ORM models (Team, Season, Match, Standing, Prediction)
│   │   ├── repositories/          # Database abstraction layer (LeagueRepository, TeamRepository)
│   │   ├── schemas/               # Pydantic v2 validation and output schemas
│   │   └── services/              # PredictionService, FeatureBuilderService, ProvenanceService
│   ├── Dockerfile                 # Backend container definition
│   ├── requirements.txt           # Python dependencies
│   └── tests/                     # 33 pytest cases (API, real fixtures, feature parity)
│
├── frontend/                      # React 19 + TypeScript Frontend
│   ├── src/
│   │   ├── components/            # PredictionCard, ShapExplanationChart, TeamSelector, Layout
│   │   ├── pages/                 # PredictPage, AnalyticsPage, Dashboard, MatchesPage, TeamsPage
│   │   ├── services/              # Typed API client with React Query integration
│   │   ├── test/                  # 7 Vitest frontend component tests
│   │   └── types/                 # TypeScript data contracts matching API schemas
│   ├── Dockerfile                 # Multi-stage production Nginx container
│   ├── package.json               # Frontend dependencies & scripts
│   └── vite.config.ts             # Vite build & test configuration
│
├── ml/                            # Machine Learning Pipeline
│   ├── features/                  # feature_engineering.py (45 zero-leakage features, Dynamic Elo)
│   ├── models/                    # best_model.joblib, training_manifest.json, metrics.json
│   └── training/                  # train.py (Candidate model benchmark, CV, 100% production refit)
│
├── reports/                       # Generated Analysis & Simulation Artifacts
│   ├── premier_league_2026_27_predicted_standings.csv  # 2026-27 simulated 20-team final table
│   └── premier_league_2026_27_predictions.csv          # All 380 match fixtures with win/draw/loss %
│
├── scripts/                       # Automation & CLI Utilities
│   ├── fetch_real_data.py         # Ingests 13 authentic seasons (2013-2026) from football-data.co.uk
│   ├── simulate_2026_27_season.py # Live 380-match ML prediction & Monte Carlo simulation script
│   ├── verify_system_health.py    # Health and dataset integrity audit tool
│   ├── bootstrap.py               # Auto-boot initializer respecting database state
│   └── e2e_functional_test.py     # End-to-end integration and latency benchmark
│
├── .github/workflows/ci.yml       # GitHub Actions CI/CD Pipeline (5 automated validation jobs)
├── docker-compose.yml             # Full-stack multi-container composition
└── README.md                      # Platform documentation & user guide
```

---

## 🚀 Quick Start

### Option A — Docker Compose (Production Setup)

```bash
# 1. Clone the repository
git clone https://github.com/DevPranavJad700/matchiq.git
cd matchiq

# 2. Configure environment
cp .env.example .env

# 3. Launch full stack (PostgreSQL + FastAPI Backend + React Frontend)
docker compose up --build

# 4. Access the web applications:
#    Frontend Dashboard: http://localhost
#    Interactive API Docs: http://localhost:8000/docs
```

---

### Option B — Local Development Setup

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL 14+ (or SQLite)

```bash
# 1. Setup Python virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Ingest 13 Authentic Premier League Seasons (2013–2026) into Database
python scripts/fetch_real_data.py --to-db

# 4. Train Candidate ML Models and Refit Active Production Model
python -m ml.training.train

# 5. Start FastAPI Backend Server
python -m uvicorn app.main:app --reload --app-dir backend --port 8000
```

In a separate terminal window:

```bash
# 6. Install & launch Frontend React SPA
cd frontend
npm install
npm run dev

# 7. Open http://localhost:5173
```

---

## 🤖 Machine Learning & Modeling Pipeline

### 45 Anti-Leakage Feature System

Every feature is engineered using strict chronological filtering (`.shift(1)`) so that only data known prior to kickoff is used:

| Feature Category | Features | Description |
|---|---|---|
| **Dynamic Elo System** | `home_elo`, `away_elo`, `elo_diff` | Sequential Elo power ratings updated after every match ($K=28.0$, Home Field Advantage $+65.0$). |
| **Schedule & Fatigue** | `home_rest_days`, `away_rest_days`, `rest_diff` | Days elapsed since previous competitive fixture and recovery advantage. |
| **Dynamic Standings** | `home_league_position`, `away_league_position`, `position_diff`, `home_points`, `away_points`, `points_diff` | Pre-match table positions (1st–20th) calculated dynamically from preceding fixtures. |
| **Form Metrics** | `home_form_pts_last5`, `away_form_pts_last5`, `home_form_wins_last5`, `home_form_gd_last5`, `form_diff` | 5-match rolling points, win/draw/loss counts, and goal differentials. |
| **Attack / Defence Strength** | `home_avg_goals_scored`, `away_avg_goals_scored`, `home_avg_goals_conceded`, `away_avg_goals_conceded`, `attack_diff`, `defence_diff` | 10-match rolling scoring rate and defensive solidity. |
| **Expected Goals & Shots** | `home_avg_shots`, `away_avg_shots`, `home_avg_shots_on_target`, `home_avg_xg`, `away_avg_xg`, `xg_diff` | Underlying shot generation, target accuracy, and xG proxy differential. |
| **Venue & Head-to-Head** | `home_home_win_rate`, `away_away_win_rate`, `home_home_goals_avg`, `away_away_goals_avg`, `h2h_home_wins`, `h2h_away_wins`, `h2h_draws` | Venue-specific performance and last 5 direct encounters. |

---

### Candidate Model Benchmark & Evaluation

Models were benchmarked on **4,940 authentic matches** across 13 seasons using a strict chronological split:
* **Train Set:** 2013–14 to 2023–24 (3,458 matches)
* **Validation Set:** 2024–25 (741 matches)
* **Held-out Test Set:** 2025–26 (741 matches)

```
Model                  Validation Acc  Validation F1  Validation LogLoss  Validation Brier  Status
Naive Majority Class   47.95%          0.3106         1.0986              0.6802            Baseline
Logistic Regression    56.28%          0.5049         0.9632              0.5701            Candidate
XGBoost Classifier     57.09%          0.5026         0.9572              0.5643            Runner-up
Voting Ensemble        56.55%          0.4957         0.9531              0.5622            Candidate
Random Forest          56.41%          0.4920         0.9515              0.5621            ← Selected Winner (Score: 0.6953)
```

**Final Evaluation on Untouched Chronological Test Set (2025–26 Season):**
* **Test Accuracy:** **49.66%** *(vs Baseline 41.70% $\rightarrow$ **+7.96% outperformance**)*
* **Test Weighted F1:** **0.4168** *(vs Baseline 0.2454)*
* **Test Log Loss:** **1.0226** *(vs Baseline 1.0848)*
* **Test Brier Score:** **0.6134** *(vs Baseline 0.6574)*

---

### Explainable AI (SHAP & Marginal Sensitivity Drivers)

For every matchup, MatchIQ computes prediction reasoning:
* **TreeExplainer Integration**: Decomposes multi-class probability outputs into signed per-feature SHAP impact values.
* **Marginal Sensitivity Fallback**: Perturbs each input feature against baseline ($P(y \mid X) - P(y \mid X_{j=0})$) ensuring continuous, non-zero factor visibility.
* **Human-Readable Explanations**: Converts raw features into natural football reasoning (e.g. *"Home team Elo rating: 1694"*, *"Pre-match points differential: -14 pts"*, *"Home squad has 6 days of match recovery"*).

---

## 🔮 2026–27 Premier League Season AI Simulation

MatchIQ simulated all **380 match fixtures** for the 2026–27 season featuring confirmed clubs (**Hull City**, **Coventry City**, and **Ipswich Town**; excluding relegated West Ham, Wolves, and Burnley) using a **10,000-run Monte Carlo simulation**.

### Simulated 2026–27 Standings Table

| Pos | Club | MP | W | D | L | GF | GA | GD | Pts | Status / European Qualification |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **1** | 🏆 **Manchester City** | 38 | **24** | 7 | 7 | 80 | 50 | **+30** | **79** | 🔵 **Champions League Winner** |
| **2** | 🥈 **Arsenal FC** | 38 | **22** | 8 | 8 | 78 | 54 | **+24** | **74** | 🔵 **Champions League** |
| **3** | 🥉 **Manchester United** | 38 | **20** | 9 | 9 | 75 | 57 | **+18** | **69** | 🔵 **Champions League** |
| **4** | **Liverpool FC** | 38 | **19** | 8 | 11 | 74 | 59 | **+15** | **65** | 🔵 **Champions League** |
| **5** | **Aston Villa** | 38 | **17** | 9 | 12 | 70 | 63 | **+7** | **60** | 🟢 **Europa League** |
| **6** | **AFC Bournemouth** | 38 | **16** | 9 | 13 | 70 | 64 | **+6** | **57** | 🟢 **Europa League** |
| **7** | **Brighton & Hove Albion** | 38 | **15** | 9 | 14 | 68 | 66 | **+2** | **54** | 🟡 **Conference League** |
| **8** | **Nottingham Forest** | 38 | **14** | 10 | 14 | 66 | 68 | **-2** | **52** | Mid-table |
| **9** | **Chelsea FC** | 38 | **14** | 9 | 15 | 67 | 67 | **0** | **51** | Mid-table |
| **10** | **Brentford FC** | 38 | **14** | 9 | 15 | 66 | 68 | **-2** | **51** | Mid-table |
| **11** | **Newcastle United** | 38 | **14** | 9 | 15 | 65 | 68 | **-3** | **51** | Mid-table |
| **12** | **Everton FC** | 38 | **13** | 9 | 16 | 65 | 69 | **-4** | **48** | Mid-table |
| **13** | **Fulham FC** | 38 | **13** | 9 | 16 | 65 | 69 | **-4** | **48** | Mid-table |
| **14** | **Leeds United** | 38 | **13** | 9 | 16 | 65 | 69 | **-4** | **48** | Mid-table |
| **15** | **Sunderland AFC** | 38 | **12** | 9 | 17 | 64 | 70 | **-6** | **45** | Lower-table |
| **16** | **Tottenham Hotspur** | 38 | **12** | 9 | 17 | 63 | 70 | **-7** | **45** | Lower-table |
| **17** | **Crystal Palace** | 38 | **12** | 9 | 17 | 63 | 71 | **-8** | **45** | Safe from drop |
| **18** | **Coventry City** | 38 | **9** | 10 | 19 | 58 | 74 | **-16** | **37** | 🔴 **Relegation Zone** |
| **19** | **Ipswich Town** | 38 | **8** | 9 | 21 | 55 | 77 | **-22** | **33** | 🔴 **Relegation Zone** |
| **20** | **Hull City** | 38 | **8** | 9 | 21 | 54 | 77 | **-23** | **33** | 🔴 **Relegation Zone** |

---

### Running the Live Simulation Script

You can re-run the live ML simulation locally anytime:

```powershell
python scripts/simulate_2026_27_season.py
```

Generated reports are exported to:
* [`reports/premier_league_2026_27_predicted_standings.csv`](reports/premier_league_2026_27_predicted_standings.csv)
* [`reports/premier_league_2026_27_predictions.csv`](reports/premier_league_2026_27_predictions.csv)

---

## 📊 Analytics & Multi-Season Intelligence Dashboard

The Analytics Page (**[http://localhost:5173/analytics](http://localhost:5173/analytics)**) offers full multi-season historical exploration:

* **14-Season Dropdown Selector**: Explore the **2026–27 AI Projected Season** and **13 historical authentic seasons** (`2025–26` down to `2013–14`).
* **Visual Highlights**: Champion cards, top scoring attacks (goals/match), and best defensive units (conceded/match).
* **Official & Projected Standings Tables**: Full statistics ($MP, W, D, L, GF, GA, GD, Pts$) with UEFA competition and relegation markers.

---

## 🧪 Testing & Quality Assurance

MatchIQ includes a comprehensive test suite across backend, frontend, feature parity, and data integrity:

```bash
# 1. Run all 33 Backend Pytest Cases (API, Feature Parity, Real Fixtures)
python -m pytest -q

# 2. Run Functional E2E Integration and Latency Benchmark
python scripts/e2e_functional_test.py

# 3. Run System Integrity and Audit Verification
python scripts/verify_system_health.py

# 4. Run Frontend Component Tests (Vitest)
cd frontend
npm run test

# 5. Validate TypeScript and Production Build
npm run build

# 6. Run Code Quality & Lint Checks
python -m ruff check backend/app ml/ --select E,W,F --ignore E501
npx oxlint
```

---

## 🔒 Dataset Provenance & Verification

| Metric | Verified Value |
|---|---|
| **Data Provider** | [football-data.co.uk](https://www.football-data.co.uk/) (Official CSV Feeds) |
| **Historical Period** | 13 Seasons: **2013–14 through 2025–26** |
| **Total Ingested Matches** | **4,940 matches** (380 per season $\times$ 13 seasons) |
| **Total Unique Clubs** | **35 clubs** (Plus 2026–27 promoted clubs) |
| **Dataset File** | `data/processed/matches_processed.csv` |
| **Provenance Manifest** | `data/processed/provenance.json` |
| **SHA-256 Checksum** | `ed8a946781ea36b04229e48f27f66426d436f77bafb21bfd7810f44471a5f546` |

---

## 📚 Documentation & Resources

* 📖 **[Interview & Architecture Guide](docs/interview-guide.md)** — Architectural design decisions, trade-offs, and design patterns.
* 📈 **[ML Model Analysis & Evaluation](docs/ml-model-analysis.md)** — In-depth model benchmarking, calibration curves, and feature importances.
* 🚢 **[Deployment & Production Guide](docs/deployment-guide.md)** — Cloud deployment instructions (AWS, GCP, Railway, Docker).

---

## ⚠️ Disclaimer

MatchIQ is an open-source machine learning research, educational, and portfolio project designed to explore predictive sports modeling and explainable AI. **Predictions generated by MatchIQ are probabilistic estimates and DO NOT constitute financial, gambling, or sports betting advice.**

---

## 👨‍💻 Author & License

Built with ❤️ by **Dev Pranav Jadhav** · Released under the [MIT License](LICENSE).
