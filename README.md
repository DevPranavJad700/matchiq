# ⚽ MatchIQ — Football Match Outcome Prediction & Analytics

> An end-to-end, production-quality ML platform for predicting Premier League match outcomes using authentic historical data, time-aware feature engineering, Logistic Regression / Random Forest, SHAP explainability, and a modern React dashboard.

[![CI](https://github.com/DevPranavJad700/matchiq/actions/workflows/ci.yml/badge.svg)](https://github.com/DevPranavJad700/matchiq/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6.svg)](https://www.typescriptlang.org/)
[![Vitest](https://img.shields.io/badge/Vitest-4-yellow.svg)](https://vitest.dev/)

---

## 🎯 What is MatchIQ?

MatchIQ is a **full-stack, production-ready** portfolio platform that demonstrates:

| Skill Area | Technologies & Architecture |
|---|---|
| **Machine Learning** | Logistic Regression, Random Forest, XGBoost, scikit-learn |
| **Explainability (XAI)** | SHAP (TreeExplainer/LinearExplainer) — feature-level prediction reasoning |
| **Data Engineering** | Authentic historical Premier League ingestion (football-data.co.uk), anti-leakage rolling windows |
| **Backend API** | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PostgreSQL, Repository Pattern |
| **Frontend** | React 19, TypeScript, Vitest, TanStack Query, Recharts, Tailwind CSS v4 |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions CI/CD |
| **Testing** | 26 Pytest backend tests, 7 Vitest frontend component tests |
| **Documentation** | [Interview Guide](docs/interview-guide.md), [ML Analysis](docs/ml-model-analysis.md), [Deployment Guide](docs/deployment-guide.md) |

---

## 🖼️ Application Showcase

| **Interactive Analytics Dashboard** | **AI Match Predictor & SHAP Explainability** |
|:---:|:---:|
| ![Dashboard Preview](docs/assets/dashboard.png) | ![Predictor Preview](docs/assets/predictor.png) |
| *Real-time Premier League fixtures, recent scores, standings, and team form* | *Match outcome probabilities with SHAP feature-level explanation bars* |

| **Team Performance Breakdown** | **ML Model Benchmark & Analytics** |
|:---:|:---:|
| ![Team Details Preview](docs/assets/team-details.png) | ![Analytics Preview](docs/assets/analytics.png) |
| *Form trends, goals scored/conceded, attack/defense radar metrics* | *Multi-model evaluation (LR, RF, XGBoost), ROC curves, and log loss* |

---

## 🏗️ Architecture

![MatchIQ System Architecture](docs/assets/architecture-diagram.svg)

```
matchiq/
├── backend/                   # FastAPI REST API
│   ├── app/
│   │   ├── api/               # Route handlers (teams, matches, leagues, predictions, analytics)
│   │   ├── core/              # Config, logging
│   │   ├── db/                # SQLAlchemy session, base
│   │   ├── ml/                # Model loader (singleton), SHAP explainer
│   │   ├── models/            # ORM models (SQLAlchemy 2.0)
│   │   ├── schemas/           # Pydantic v2 response schemas
│   │   └── services/          # Business logic (PredictionService, FeatureBuilder)
│   └── tests/                 # pytest suite (26 tests, SQLite isolation)
│
├── ml/                        # ML pipeline (standalone, runnable without API)
│   ├── features/              # Feature engineering (anti-leakage rolling windows)
│   └── training/              # train.py — LR, RF, XGBoost comparison + selection
│
├── frontend/                  # React + TypeScript SPA
│   ├── src/
│   │   ├── components/        # Layout, TeamSelector, PredictionCard, UI primitives
│   │   ├── pages/             # Dashboard, Predict, Teams, TeamDetail, Matches, Analytics
│   │   ├── test/              # Vitest + React Testing Library suite (7 tests)
│   │   ├── services/          # api.ts — typed HTTP client
│   │   └── types/             # TypeScript interfaces matching API schemas
│
├── scripts/
│   ├── fetch_real_data.py     # Authentic historical PL data fetcher (football-data.co.uk)
│   └── seed_demo_data.py      # Offline synthetic demo data generator
│
└── data/
    └── processed/             # Cleaned historical dataset CSV
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

### Option B — Local Development

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL 14+

```bash
git clone https://github.com/DevPranavJad700/matchiq.git
cd matchiq
cp .env.example .env
```

**Backend & Data & ML:**
```bash
pip install -r backend/requirements.txt
python scripts/fetch_real_data.py     # Fetch 1,140 real Premier League matches (2021-2024)
python -m ml.training.train           # Train the ML model
uvicorn app.main:app --reload --app-dir backend  # Start API at http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run test         # Run Vitest test suite
npm run dev          # Starts at http://localhost:5173
```

---

## 🤖 ML Pipeline & Baseline Analysis

### Feature Engineering (Anti-Leakage Design)

All 39 features use `.shift(1)` — **only information available before the match is used**. This prevents data leakage that would inflate test accuracy.

### Model Training & Selection (Verified Source-of-Truth Metrics)

Models are evaluated on Premier League matches with a strict chronological 70/15/15 split. Candidate selection is performed on the **Validation** set, with final retrained evaluation on the untouched **Test** set (see [Model Card](docs/MODEL_CARD.md)):

```
Model                  Accuracy   Weighted F1   Log Loss   Brier Score  Selection
Naive Majority Class   46.47%     0.2952        1.0986     0.6802       Baseline
XGBoost                45.29%     0.4363        1.2054     0.7468       Candidate
Random Forest          49.41%     0.4769        1.0354     0.6235       Candidate
Logistic Regression    50.00%     0.4780        0.9946     0.5952       ← Selected Winner
```

> **Why Logistic Regression was selected:** Candidate models were selected on the Validation set based on a composite score combining weighted F1 and Log Loss calibration. Retrained on Train + Validation and evaluated on the untouched Test set, Logistic Regression achieved **50.00% Accuracy**, **0.4780 Weighted F1**, **0.9946 Log Loss**, and a **0.5952 Brier Score**, maintaining balanced recall across outcomes (`HOME_WIN` F1: 0.69, `AWAY_WIN` F1: 0.38, `DRAW` F1: 0.23).

---

## 🧪 Testing

```bash
# Backend — 29 Pytest cases (SQLite isolated)
cd backend
python -m pytest tests/ -v

# Frontend — 7 Vitest + React Testing Library cases
cd frontend
npm run test
```

---

## 📚 Interview & Architecture Documentation

* 🎴 [Model Card (docs/MODEL_CARD.md)](docs/MODEL_CARD.md) — Comprehensive model architecture, validation methodology, and per-class calibration metrics.
* 📘 [Interview Guide (docs/interview-guide.md)](docs/interview-guide.md) — 14 technical Q&As covering architecture, Postgres, anti-leakage, SHAP XAI, and scaling.
* 📊 [ML Model & Calibration Analysis (docs/ml-model-analysis.md)](docs/ml-model-analysis.md) — Deep dive into baselines, class distributions, and composite metrics.
* 🚀 [Live Deployment Guide (docs/deployment-guide.md)](docs/deployment-guide.md) — Production setup for Render, Vercel, and Supabase.

---

## ⚠️ Disclaimer

MatchIQ is an open-source machine learning portfolio and data engineering project created exclusively for analytical, educational, and demonstration purposes. **Predictions generated by MatchIQ are NOT financial or sports betting advice.**

---

## 🛠️ Tech Stack Summary

**Backend:** FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · PostgreSQL · psycopg2

**ML & XAI:** scikit-learn · XGBoost · SHAP · pandas · numpy · joblib

**Frontend:** React 19 · TypeScript · Vite · Vitest · TanStack Query · Recharts · Tailwind CSS v4 · Lucide Icons

**DevOps:** Docker · Docker Compose · GitHub Actions · Nginx · uvicorn
