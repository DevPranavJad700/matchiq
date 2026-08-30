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
**Answer:** Time-awareness is strictly enforced using pandas `.shift(1)` across all rolling window operations in `ml/features/feature_engineering.py`. For any match $M$ on date $T$, the rolling 5-match form, Elo ratings, and 10-match goals/xG averages include *only* matches $1 \dots M-1$ played strictly before date $T$. Post-match statistics (e.g., match $M$'s goals/shots) are never in match $M$'s feature vector.

### Q6: Why a Chronological Train/Val/Test Split instead of K-Fold Cross Validation?
**Answer:** Random $K$-Fold cross-validation leaks temporal patterns (training on future matches to predict past matches). Football match prediction is a sequential forecasting problem. We sort matches chronologically:
* **Training (70%):** 3,458 matches (2013–14 through 2022–23 seasons)
* **Validation (15%):** 741 matches (2023–24 and 2024–25 seasons)
* **Untouched Test (15%):** 741 matches (2025–26 season)

### Q7: Why was Random Forest selected over XGBoost on validation data?
**Answer:** While XGBoost achieved marginally higher raw accuracy (57.09% vs. 56.28%), Random Forest was selected because our composite objective prioritizes probability calibration:
$$\text{Score} = 0.6 \times \text{F1}_{\text{weighted}} + 0.4 \times (1 - \text{NormLogLoss})$$
Random Forest achieved superior Log Loss (**0.9515** vs. 0.9572) and a superior Brier Score (**0.5621** vs. 0.5643). In sports analytics, downstream consumers (such as our 10,000-run Monte Carlo simulation) rely on continuous calibrated probability vectors rather than uncalibrated discrete predictions.

### Q8: How does the model handle Draws, and why does the classification report show 0.00 Draw recall under argmax?
**Answer:** Draws occur in ~24.5% of matches and represent high-variance equilibrium outcomes. In a calibrated 3-class model, draw probabilities hover between 22% and 32%. Under standard $\arg\max$ decision rules ($\hat{y} = \arg\max_k P_k$), the predicted mode is almost always either Home Win or Away Win because neither requires an extreme probability to exceed 33%. Rather than distorting calibration by hacking arbitrary discrete decision thresholds, MatchIQ preserves the underlying continuous probability distribution $[P(H), P(D), P(A)]$, which our Monte Carlo simulator samples from directly to reproduce accurate ~24% draw rates across the league.

### Q9: How does SHAP (Explainable AI) work in MatchIQ?
**Answer:** We initialize `shap.TreeExplainer` on the loaded Random Forest model. For a prediction feature vector $X$, SHAP computes Shapley values based on cooperative game theory, determining the marginal contribution of each feature towards the predicted output class probability. We map these factors to natural language explanations (e.g., *"Home team Elo rating advantage: +142 pts"* or *"Visiting club has 6 days of match recovery"*).

### Q10: How does MatchIQ perform against naive baselines on untouched test data?
**Answer:** On the strictly held-out 741-match Test Set:
* **Naive Majority Baseline (Always Home):** **41.70%** accuracy, 0.2454 F1, 1.0848 Log Loss, 0.6574 Brier Score.
* **MatchIQ Random Forest:** **49.66%** accuracy (**+7.96% lift**), **0.4168 weighted F1** (+0.1714 lift), **1.0226 Log Loss** (-0.0622 improvement), and **0.6134 Brier Score** (-0.0440 improvement).

---

## 3. Frontend & Infrastructure Questions

### Q11: How does TanStack Query (React Query) improve UI performance?
**Answer:** TanStack Query handles server-state caching, automatic refetching, deduplication of in-flight requests, and optimistic updates. Team lists and league metadata are cached with a 5-minute `staleTime`, preventing redundant network requests when switching tabs.

### Q12: How does Docker Compose networking work?
**Answer:** Docker Compose creates an isolated bridge network (`matchiq_default`). Containers communicate via service names as DNS hosts (`postgres:5432`, `backend:8000`). Nginx acts as a reverse proxy in the frontend container, proxying `/api/*` traffic to `http://backend:8000/`.

### Q13: How would you scale MatchIQ for high traffic?
**Answer:**
1. **API Scaling:** Run FastAPI inside Docker behind a load balancer (AWS ALB / Nginx) using `gunicorn` with multiple `uvicorn.workers.UvicornWorker` workers.
2. **Prediction Caching:** Cache team feature vectors and prediction results in Redis with a 1-hour TTL.
3. **Database Read Replicas:** Route read requests (`GET /teams`, `/matches`) to PostgreSQL read replicas.
4. **Model Serving:** Offload heavy ML inference to Triton Inference Server or TorchServe if scaling to real-time live match micro-updates.

### Q14: What are the main limitations and next steps?
**Answer:**
1. **Lineup & Injury Feed:** Integrate real-time starting lineups and key player injury reports.
2. **Market Odds Benchmarking:** Incorporate closing betting market odds (Pinnacle/Betfair) to benchmark against market consensus efficiency.
3. **Reliability Diagrams:** Add interactive calibration curve visualizations to the analytics dashboard.
