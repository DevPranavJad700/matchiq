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

### Q5: Why did headline discrete accuracy change (49.66% → 47.63%) and why is that an intentional trade-off?
**Answer:** In sports analytics, raw discrete classification accuracy ($\arg\max$) treats all probabilities identically (a 34% home pick counts the same as an 85% home pick). Uncalibrated tree ensembles produce overconfident probability tails that yield slightly higher discrete accuracy on easy home games, but suffer heavy Log Loss and Ranked Probability Score penalties on unexpected draws and away upsets.

By wrapping candidate models in `CalibratedClassifierCV` (Platt sigmoid scaling with 5-fold cross-validation), we deliberately traded ~2.0% raw discrete classification accuracy for calibrated posterior probabilities, lowering Log Loss to **1.0315** and Ranked Probability Score to **0.2099** (achieving **97.8% of professional bookmaker market efficiency**). Continuous calibration is essential because downstream Monte Carlo simulations and odds pricing engines sample directly from continuous probability distributions $[P(H), P(D), P(A)]$, not discrete labels.

### Q6: What is the Ranked Probability Score (RPS) and how is the test set structured?
**Answer:** In academic football forecasting (Epstein 1969; Constantinou & Fenton 2012), 3-way match outcomes are ordered ($\text{Home Win} \prec \text{Draw} \prec \text{Away Win}$). RPS measures cumulative squared error across the ordered classes:
$$\text{RPS} = \frac{1}{2} \sum_{r=1}^{2} \left( \sum_{i=1}^r p_i - \sum_{i=1}^r o_i \right)^2$$
On the untouched 2025–26 test set (**identical $N=380$ matches scored across all methods, zero dropped rows**):
* **Naive Constant Baseline:** $\text{RPS} = 0.2279$
* **Dixon-Coles Goal Model:** $\text{RPS} = 0.2137$
* **MatchIQ Calibrated Model:** $\text{RPS} = 0.2099$
* **Closing Betting Market Odds (Benchmark):** $\text{RPS} = 0.2053$
MatchIQ reaches **97.8% of bookmaker market efficiency** purely on pre-match historical statistics.

### Q7: How did you evaluate the ML vs. Dixon-Coles blend?
**Answer:** We ran a systematic grid search over blend weight $w \in [0.0, 1.0]$ in increments of $0.05$ on the 2024–25 Validation Set. Validation RPS monotonically improved from 0.2134 (100% Dixon-Coles) down to 0.2033 (100% Calibrated ML). Rather than using an unjustified heuristic blend weight, we select the calibrated classifier as the primary outcome predictor, with Dixon-Coles serving as the dedicated goal-scoring engine for bivariate scoreline matrices ($P(0\text{--}0), P(1\text{--}0), \dots$) and expected goals ($\lambda, \mu$).

### Q8: How did you evaluate the Draw Prediction Dilemma and why retain Bayes-optimal argmax?
**Answer:** Under standard $\arg\max$ decision mode ($\hat{y} = \arg\max_k P_k$), draw recall is 0.00% because calibrated draw probabilities cluster around 22%–32% and rarely exceed the ~35% needed to beat both home and away win probabilities.
If you force an artificial threshold (e.g. $\theta_{\text{draw}} = 0.230$), the model begins predicting "Draw" for 254 out of 380 matches (66.8% of all fixtures), causing discrete accuracy to collapse by 9 percentage points (48.16% $\to$ 39.21%), Home Recall to collapse to 32.7%, and Away Recall to collapse to 18.4%.

Under Bayesian decision theory with symmetric 0-1 loss (maximizing accuracy), $\hat{y} = \arg\max_k P(y=k \mid x)$ is mathematically optimal. Therefore, we:
1. Retain pure $\arg\max$ for headline predictions, preserving optimal classification accuracy (48.16% on Test / 51.58% on Validation) and avoiding credibility issues (e.g. Manchester City vs. a relegated club is never labeled "Draw").
2. Treat the calibrated continuous probability distribution $[P(H), P(D), P(A)]$ as the primary ML deliverable (evaluated via Ranked Probability Score **0.2099** and Log Loss **1.0315**).
3. Surface an "Elevated Draw Risk" badge in the UI when $P(\text{Draw}) \ge 0.250$ (the $\ge 90\text{th}$ percentile of draw risk across 4,940 matches, which empirically delivers a 1.34x lift in actual draw frequency), communicating uncertainty transparently without corrupting classification labels.

### Q9: How did you prevent data leakage in feature engineering?
**Answer:** Time-awareness is strictly enforced using pandas `.shift(1)` across all rolling window operations in `ml/features/feature_engineering.py`. For any match $M$ on date $T$, the rolling 5-match form, Elo ratings, and 10-match goals/xG averages include *only* matches $1 \dots M-1$ played strictly before date $T$. Post-match statistics (e.g., match $M$'s goals/shots) are never in match $M$'s feature vector.

### Q10: Why a Chronological Train/Val/Test Split instead of K-Fold Cross Validation?
**Answer:** Random $K$-Fold cross-validation leaks temporal patterns (training on future matches to predict past matches). Football match prediction is a sequential forecasting problem. We sort matches chronologically:
* **Training Set:** 4,180 matches (11 seasons: 2013–14 through 2023–24)
* **Validation Set:** 380 matches (1 season: 2024–25)
* **Untouched Test Set:** 380 matches (1 season: 2025–26)

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
