# ⚽ MatchIQ — Engineering & Machine Learning Interview Guide

This guide prepares you to present **MatchIQ** confidently during technical software engineering, data engineering, and machine learning interviews.

---

## 1. Architecture & Backend Questions

### Q1: Why PostgreSQL and SQLAlchemy 2.0?
**Answer:** PostgreSQL provides ACID compliance, strong relational integrity (foreign keys between matches, teams, standings, and predictions), and index optimization for time-series queries. SQLAlchemy 2.0 provides an asynchronous-capable ORM layer with strict static typing, explicit parameter binding (preventing SQL injection), and Alembic auto-migrations.

### Q2: Why FastAPI over Django or Flask?
**Answer:** FastAPI offers:
1. High-performance asynchronous non-blocking I/O (`asyncio`).
2. Automatic OpenAPI/Swagger documentation generated from Pydantic schemas.
3. Strict request validation using Pydantic v2.
4. Python 3.10+ type hints natively integrated into runtime schema validation.

### Q3: How is the Repository Pattern implemented and why?
**Answer:** Data access is encapsulated in `TeamRepository`, `MatchRepository`, and `LeagueRepository`. Route handlers do not construct direct SQL queries; instead, they consume high-level repository methods (`get_by_id`, `get_recent_matches`). This decouples business logic from database schema details and makes mocking/testing straightforward.

### Q4: How is the ML model loaded in FastAPI?
**Answer:** We use a **Module-Level Singleton Pattern** in `app/ml/model_loader.py`. During the FastAPI `lifespan` startup phase, `load_model()` reads `best_model.joblib` and `feature_metadata.json` into memory once. Requests to `/predict` reuse the cached model instance in $O(1)$ time without per-request disk read overhead.

---

## 2. Machine Learning & Data Pipeline Questions

### Q5: How did you prevent data leakage in feature engineering?
**Answer:** Time-awareness is strictly enforced using pandas `.shift(1)` across all rolling window operations in `ml/features/feature_engineering.py`. For any match $M$ on date $T$, the rolling 5-match form and 10-match goals averages include *only* matches $1 \dots M-1$ played strictly before date $T$. Post-match statistics (e.g., match $M$'s goals/shots) are never in match $M$'s feature vector.

### Q6: Why a Chronological Train/Val/Test Split instead of K-Fold Cross Validation?
**Answer:** Random $K$-Fold cross-validation leaks temporal patterns (training on future matches to predict past matches). Football match prediction is a time-series forecasting problem. We sort matches chronologically and use the first 70% for training (2021–2023), 15% for validation, and the final 15% for testing (2024).

### Q7: Why Logistic Regression over Random Forest or XGBoost on real data?
**Answer:** While XGBoost and Random Forest achieved high training accuracy, they over-indexed on majority classes (`HOME_WIN`) and produced uncalibrated probabilities with poor recall on `DRAW` results. Logistic Regression maintained balanced recall across all 3 outcomes (`HOME_WIN` F1: 0.63, `AWAY_WIN` F1: 0.62, `DRAW` F1: 0.36) and minimized Log Loss (0.9381), leading to the highest composite evaluation score.

### Q8: How does SHAP (Explainable AI) work in MatchIQ?
**Answer:** We initialize `shap.TreeExplainer` or `shap.LinearExplainer` on the loaded model. For a prediction feature vector $X$, SHAP computes Shapley values based on cooperative game theory, determining the marginal contribution of each feature towards the predicted output class probability. We map these factors to human-readable explanations (e.g., "Home form advantage of +3.00 pts pushed prediction towards Home Win").

### Q9: How does MatchIQ perform against naive baselines?
**Answer:** 
* Naive Random Predictor: **33.3%** accuracy.
* **MatchIQ Logistic Regression:** **50.0%** accuracy on untouched test data (with 0.4780 weighted F1, 0.9946 Log Loss, and 0.5952 Brier score).

---

## 3. Frontend & Infrastructure Questions

### Q10: How does TanStack Query (React Query) improve UI performance?
**Answer:** TanStack Query handles server-state caching, automatic refetching, deduplication of in-flight requests, and optimistic updates. Team lists and league metadata are cached with a 5-minute `staleTime`, preventing redundant network requests when switching tabs.

### Q11: How does Docker Compose networking work?
**Answer:** Docker Compose creates an isolated bridge network (`matchiq_default`). Containers communicate via service names as DNS hosts (`postgres:5432`, `backend:8000`). Nginx acts as a reverse proxy in the frontend container, proxying `/api/*` traffic to `http://backend:8000/`.

### Q12: How would you scale MatchIQ for high traffic?
**Answer:**
1. **API Scaling:** Run FastAPI inside Docker behind a load balancer (AWS ALB / Nginx) using `gunicorn` with multiple `uvicorn.workers.UvicornWorker` workers.
2. **Prediction Caching:** Cache team feature vectors and prediction results in Redis with a 1-hour TTL.
3. **Database Read Replicas:** Route read requests (`GET /teams`, `/matches`) to PostgreSQL read replicas.
4. **Model Serving:** Offload heavy ML inference to Triton Inference Server or TorchServe if scaling to real-time live match micro-updates.

### Q13: What are the main limitations of the system?
**Answer:**
1. **Player-level Data:** Currently uses team-level statistics; lacks individual player injury/suspension tracking.
2. **Live In-Play Odds:** Does not incorporate real-time betting market odds (e.g., Pinnacle closing lines).
3. **Weather & Travel:** Weather conditions and travel distance are not included in the feature set.

### Q14: What would you improve next?
**Answer:**
1. Integrate player lineups and injury news via an external sports API.
2. Add Elo rating features alongside rolling averages.
3. Implement model calibration curve visualizations (Reliability Diagrams) on the analytics page.
