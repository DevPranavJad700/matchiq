# 🚀 MatchIQ — Live Production Deployment Guide

This document provides step-by-step instructions for deploying **MatchIQ** to production cloud platforms.

---

## Architecture for Production

```
 [ User ]
    │
    ├── (Static Frontend SPA) ────► Vercel / Netlify / Render Static
    │
    └── (REST API Calls) ─────────► Render / Railway / Fly.io (FastAPI Backend)
                                           │
                                           └──► Managed PostgreSQL (Supabase / Render PG)
```

---

## 1. Free / Low-Cost Deployment Plan

| Component | Platform | Free Tier Capability |
|---|---|---|
| **Frontend** | Vercel / Netlify | Unlimited static deployments, instant global CDN |
| **Backend API** | Render / Fly.io | 512MB RAM, HTTP/2 support, Docker deployments |
| **PostgreSQL** | Supabase / Render Postgres | 500MB storage, SSL connection, automatic backups |

---

## 2. Deploying Backend & Database (Render / Railway)

### Step 1: PostgreSQL Setup (Supabase or Render)
1. Create a PostgreSQL instance on [Supabase](https://supabase.com) or [Render](https://render.com).
2. Copy the Connection URI:
   `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

### Step 2: Backend API Deployment
1. Connect your GitHub repository to **Render Web Services**.
2. Environment: **Docker** or **Python 3.11**.
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
5. Set Environment Variables:
   * `DATABASE_URL`: `postgresql+psycopg2://postgres:[PASSWORD]@[HOST]:5432/postgres`
   * `CORS_ORIGINS`: `["https://matchiq.vercel.app","http://localhost:5173"]`
   * `MODEL_DIR`: `ml/models`
   * `SECRET_KEY`: Generate a random 32-character hex string.

### Step 3: Run Database Migrations & Seed Data
In the cloud terminal / SSH console of your backend:
```bash
cd backend
python -m alembic upgrade head
cd ..
python scripts/fetch_real_data.py
python -m ml.training.train
```

---

## 3. Deploying Frontend (Vercel)

1. Connect your GitHub repository to **Vercel**.
2. Framework Preset: **Vite**.
3. Root Directory: `frontend`.
4. Build Command: `npm run build`.
5. Output Directory: `dist`.
6. Environment Variables:
   * `VITE_API_URL`: `https://matchiq-api.onrender.com` (Your Render API URL).

---

## 4. Verification

Once deployed, visit your live URL:
1. Open `https://matchiq.vercel.app/health` → Verify `{"status": "ok", "db_connected": true, "model_loaded": true}`.
2. Select Home & Away teams on the live predictor page.
3. Verify probability visualizer & SHAP explanations load cleanly over production HTTPs.
