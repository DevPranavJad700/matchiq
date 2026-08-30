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
**Answer:** We use a **Module-Level Singleton Pattern** in `app/ml/model_loader.py`. During the FastAPI `lifespan` startup phase, `load_model()` reads `best_model.joblib`, `dixon_coles.joblib`, and `feature_metadata.json` into memory once. Requests to `/predict` reuse the cached model instance in $O(1)$ time without per-request disk read overhead.

---

## 2. Machine Learning, Metrics & Scientific Framing

### Q5: What is the Ranked Probability Score (RPS) and why is it preferred over raw accuracy in sports forecasting?
**Answer:** In academic football forecasting (Epstein 1969; Constantinou & Fenton 2012), 3-way match outcomes are ordered ($\text{Home Win} \prec \text{Draw} \prec \text{Away Win}$). Discrete accuracy treats misclassifying a Home Win as a Draw the same as misclassifying it as an Away Win, which is scientifically flawed. 

RPS measures cumulative squared error across the ordered classes:
$$\text{RPS} = \frac{1}{2} \sum_{r=1}^{2} \left( \sum_{i=1}^r p_i - \sum_{i=1}^r o_i \right)^2$$
On the untouched 2025–26 test set:
* **Naive Constant Baseline:** $\text{RPS} = 0.2279$
* **MatchIQ Calibrated Model:** $\text{RPS} = 0.2099$
* **Professional Closing Betting Market Odds (Benchmark):** $\text{RPS} = 0.2053$
MatchIQ reaches **97.8% of bookmaker market efficiency** purely on public historical match metrics!

### Q6: How did you implement probability calibration (`CalibratedClassifierCV`)?
**Answer:** Raw tree ensembles and logistic classifiers often exhibit overconfident probability tails on noisy sports data. We wrap candidate models in `CalibratedClassifierCV(method='sigmoid', cv=5)` (Platt scaling). This fits a cross-validated logistic transformation on candidate probabilities, aligning predicted probabilities with true empirical long-run frequencies and minimizing Brier score / Log Loss.

### Q7: What is the Dixon-Coles (1997) Goal Model and how does MatchIQ use it?
**Answer:** Dixon & Coles (*Applied Statistics*, 1997) models match scorelines as bivariate Poisson processes where expected goals $\lambda$ (home) and $\mu$ (away) depend on team attack strength $\alpha_i$, defense parameter $\beta_j$, home pitch factor $\gamma$, and exponential time decay $\xi = 0.0019$. It includes a low-score correlation parameter $\tau(x, y; \rho)$ on $(0,0), (0,1), (1,0), (1,1)$. 
MatchIQ fits this via maximum likelihood estimation (`scipy.optimize.minimize`), outputting full $11 \times 11$ score probability matrices, top probable exact scorelines (e.g. `1-0`, `1-1`), and natural draw probabilities.

### Q8: How did you solve the Draw Prediction Dilemma?
**Answer:** In raw $\arg\max$ decision mode ($\hat{y} = \arg\max_k P_k$), draw recall is often 0.00% because calibrated draw probabilities cluster around 22%–32% and rarely exceed the ~35% needed to beat both home and away win probabilities.
We solved this by tuning the decision threshold on validation data:
$$\hat{y} = \begin{cases} \text{DRAW}, & \text{if } P(\text{Draw}) \ge \theta_{\text{draw}} \\ \arg\max_{k \in \{0, 2\}} P(y=k), & \text{otherwise} \end{cases}$$
With $\theta_{\text{draw}} = 0.230$, **Draw Recall increases from 0.00% to 50.96%** (+50.96% lift, identifying 53 of 104 test draws) with a Macro Average F1 of **0.3658**.

### Q9: How did you prevent data leakage in feature engineering?
**Answer:** Time-awareness is strictly enforced using pandas `.shift(1)` across all rolling window operations in `ml/features/feature_engineering.py`. For any match $M$ on date $T$, the rolling 5-match form, Elo ratings, and 10-match goals/xG averages include *only* matches $1 \dots M-1$ played strictly before date $T$. Post-match statistics (e.g., match $M$'s goals/shots) are never in match $M$'s feature vector.

### Q10: Why a Chronological Train/Val/Test Split instead of K-Fold Cross Validation?
**Answer:** Random $K$-Fold cross-validation leaks temporal patterns (training on future matches to predict past matches). Football match prediction is a sequential forecasting problem. We sort matches chronologically:
* **Training Set:** 4,180 matches (2013–14 through 2023–24 seasons)
* **Validation Set:** 380 matches (2024–25 season)
* **Untouched Test Set:** 380 matches (2025–26 season)

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
