# ⚽ MatchIQ — Football Match Outcome Prediction & Analytics

> An end-to-end, production-quality ML platform for predicting Premier League match outcomes using authentic historical match statistics (12 complete seasons: 2013–2025 from football-data.co.uk), time-aware feature engineering with anti-leakage dynamic standings and Elo ratings, candidate model selection (Voting Ensemble, Random Forest, XGBoost, Logistic Regression), SHAP explainability, and a modern React dashboard.

[![CI](https://github.com/DevPranavJad700/matchiq/actions/workflows/ci.yml/badge.svg)](https://github.com/DevPranavJad700/matchiq/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6.svg)](https://www.typescriptlang.org/)
[![Vitest](https://img.shields.io/badge/Vitest-4-yellow.svg)](https://vitest.dev/)

---

## 🎯 What is MatchIQ?

MatchIQ is a **full-stack, production-ready** platform demonstrating:

| Skill Area | Technologies & Architecture |
|---|---|
| **Machine Learning** | Random Forest, XGBoost, Logistic Regression, scikit-learn |
| **Explainability (XAI)** | SHAP (TreeExplainer/LinearExplainer) — feature-level prediction reasoning |
| **Data Engineering** | Authentic historical Premier League ingestion (football-data.co.uk), dynamic pre-match standings, anti-leakage rolling windows |
| **Dataset Provenance** | Cryptographic SHA-256 checksums, URL source tracking, training manifests |
| **Backend API** | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PostgreSQL / SQLite, Repository Pattern |
| **Frontend** | React 19, TypeScript, Vitest, TanStack Query, Recharts, Tailwind CSS |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions CI/CD |
| **Testing** | 33 Pytest backend tests (API, feature parity, real fixture regression), 7 Vitest frontend component tests |
| **Documentation** | [Interview Guide](docs/interview-guide.md), [ML Analysis](docs/ml-model-analysis.md), [Deployment Guide](docs/deployment-guide.md) |

---

## 🏗️ Architecture

```
matchiq/
├── backend/                   # FastAPI REST API
│   ├── app/
│   │   ├── api/               # Route handlers (teams, matches, leagues, predictions, health/provenance)
│   │   ├── core/              # Config (DATA_MODE=real|demo), logging
│   │   ├── db/                # SQLAlchemy session, base
│   │   ├── ml/                # Model loader (singleton), SHAP explainer
│   │   ├── models/            # ORM models (SQLAlchemy 2.0)
│   │   ├── schemas/           # Pydantic v2 response schemas
│   │   └── services/          # Business logic (PredictionService, FeatureBuilder)
│   └── tests/                 # pytest suite (33 tests: API, feature parity, real fixtures)
│
├── ml/                        # ML pipeline (standalone, runnable without API)
│   ├── features/              # Feature engineering (dynamic pre-match standings, anti-leakage rolling windows)
│   ├── models/                # Trained artifacts: best_model.joblib, training_manifest.json, metrics.json
│   └── training/              # train.py — Candidate model comparison + chronological evaluation
│
├── frontend/                  # React + TypeScript SPA
│   ├── src/
│   │   ├── components/        # Layout, TeamSelector, PredictionCard, UI primitives
│   │   ├── pages/             # Dashboard, Predict, Teams, TeamDetail, Matches, Analytics
│   │   ├── test/              # Vitest + React Testing Library suite
│   │   ├── services/          # api.ts — typed HTTP client with provenance support
│   │   └── types/             # TypeScript interfaces matching API schemas
│   │
├── scripts/
│   ├── fetch_real_data.py     # Authentic historical PL data fetcher (football-data.co.uk) + SHA-256 provenance
│   ├── seed_demo_data.py      # Offline synthetic demo data generator (clearly marked as simulated)
│   ├── bootstrap.py           # Auto-boot initialization respecting DATA_MODE
│   └── e2e_functional_test.py # End-to-end integration benchmark
│
├── pytest.ini                 # Root pytest configuration
└── data/
    ├── raw/                   # Cached authentic CSV archives
    └── processed/             # matches_processed.csv (2,280 rows) & provenance.json
```

---

## 🚀 Quick Start

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/DevPranavJad700/matchiq.git
cd matchiq
cp .env.example .env

# 2. Start all services (PostgreSQL + Backend + Frontend)
docker compose up --build

# 3. Open http://localhost (frontend) or http://localhost:8000/docs (API)
```

### Option B — Local Development (Without Docker)

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL 14+ (or SQLite)

```bash
git clone https://github.com/DevPranavJad700/matchiq.git
cd matchiq
cp .env.example .env
```

**1. Database Migration & Data Ingestion:**
```bash
pip install -r backend/requirements.txt
python -m alembic -c backend/alembic.ini upgrade head
python scripts/fetch_real_data.py --to-db     # Ingest 4,560 authentic Premier League matches (2013-2025)
```

**2. Model Training & Backend API:**
```bash
python -m ml.training.train                   # Train ML models and generate manifest
python scripts/bootstrap.py                   # Verify data & register active model
python -m uvicorn app.main:app --reload --app-dir backend --port 8000
```

**3. Frontend React SPA:**
```bash
cd frontend
npm install
npm run dev                                   # Starts at http://localhost:5173
```

---

## 🤖 ML Pipeline & Baseline Analysis

### Feature Engineering (Anti-Leakage Design)

All 45 features use strict temporal anti-leakage with `.shift(1)`:
- **Dynamic Elo Power Ratings:** Sequential Elo ratings updated after each match ($K=28.0$, Home Field Advantage $+65.0$) with zero future leakage (`home_elo`, `away_elo`, `elo_diff`).
- **Schedule Rest Days:** Recovery duration and schedule congestion differentials (`home_rest_days`, `away_rest_days`, `rest_diff`).
- **Dynamic Pre-Match Season Standings:** Pre-match league positions (1st–20th) and points in the current season are calculated dynamically from matches played strictly before the kickoff date.
- **Form Metrics:** Rolling 5-match points, wins, draws, losses, and goal difference.
- **Attack/Defence Strength:** Rolling 10-match goals scored, goals conceded, shots, shots on target, and estimated xG proxy.
- **Venue & H2H:** Historical home/away win rates and last 5 head-to-head encounters.

### Model Training & Selection (Verified Source-of-Truth Metrics)

Models are evaluated on 4,560 authentic Premier League matches (12 seasons: 2013–2025) with a strict seasonal chronological split:
- **Train Set:** 2013–14 to 2022–23 seasons (3,192 matches)
- **Validation Set:** 2023–24 season (684 matches)
- **Held-out Test Set:** 2024–25 season (684 matches)

```
Model                  Validation Acc  Validation F1  Validation LogLoss  Validation Brier  Status
Naive Majority Class   47.95%          0.3106         1.0986              0.6802            Baseline
Logistic Regression    55.85%          0.5027         0.9676              0.5722            Candidate
Random Forest          55.85%          0.4886         0.9602              0.5685            Runner-up
XGBoost Classifier     55.41%          0.4885         0.9605              0.5683            Candidate
Voting Ensemble        55.56%          0.4887         0.9597              0.5679            ← Selected Winner (Score: 0.6932)
```

**Final Evaluation on Untouched Chronological Test Set (Voting Ensemble with Dynamic Elo):**
* **Test Accuracy:** **54.24%** (vs Baseline 43.57% -> **+10.67% over naive baseline**)
* **Test Weighted F1:** **0.4698** (vs Baseline 0.2644)
* **Test Log Loss:** **0.9815** (vs Baseline 1.0695)
* **Test Brier Score:** **0.5831** (vs Baseline 0.6476)

---

## 🧪 Testing

```bash
# Backend — 33 Pytest cases (run directly from root via pytest.ini)
python -m pytest -q

# Functional E2E & Latency Benchmark
python scripts/e2e_functional_test.py

# Audit Verification
python audit_script.py

# Frontend — 7 Vitest + React Testing Library cases
cd frontend
npm run test
```

---

## ⚠️ Disclaimer

MatchIQ is an open-source machine learning portfolio and data engineering project created exclusively for analytical, educational, and demonstration purposes. **Predictions generated by MatchIQ are NOT financial or sports betting advice.**

---

## 🛠️ Tech Stack Summary

**Backend:** FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · PostgreSQL / SQLite · psycopg2

**ML & XAI:** scikit-learn · XGBoost · SHAP · pandas · numpy · joblib

**Frontend:** React 19 · TypeScript · Vite · Vitest · TanStack Query · Recharts · Tailwind CSS · Lucide Icons

**DevOps:** Docker · Docker Compose · GitHub Actions · Nginx · uvicorn
