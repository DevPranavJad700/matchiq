# Model Card — MatchIQ Premier League Predictor

## Model Details
- **Model Name**: MatchIQ Premier League Match Predictor
- **Version**: `random_forest-v20260829_090156`
- **Model Architecture**: Random Forest Classifier (`n_estimators=300`, `max_depth=12`, `min_samples_split=8`, `random_state=42`)
- **Framework**: `scikit-learn` v1.8.0
- **Training Timestamp**: 2026-08-29T09:01:56 UTC
- **Input Features**: 45 engineered features (Dynamic Elo with $K=28$ and Home Advantage $+65$, rest days differential, rolling form with `.shift(1)` offsets, xG differentials, venue win rates, and pre-match standings).
- **Dataset Checksum (SHA-256)**: `ed8a946781ea36b04229e48f27f66426d436f77bafb21bfd7810f44471a5f546`
- **Model Artifact Checksum (SHA-256)**: `c40c945aaaa31a5901e0e166241a1ee8fe2ec280a08926dadabed80ff169be41`

---

## Intended Use
- **Primary Use Case**: Predicting 3-way match outcome probabilities (`HOME_WIN`, `DRAW`, `AWAY_WIN`) for Premier League fixtures based on strictly historical performance metrics available prior to kick-off.
- **Secondary Use Case**: Providing feature-level reasoning via SHAP TreeExplainer and powering 10,000-run Monte Carlo seasonal simulations.
- **Out-of-Scope Use Cases**: In-play micro-betting, financial trading, or deterministic outcome guarantees.

---

## Evaluation & Validation Protocol
To eliminate data contamination and temporal leakage:
1. **Chronological Splitting**: Data (4,940 matches, 13 seasons) is split chronologically into **Train (70%, 3,458 matches)**, **Validation (15%, 741 matches)**, and **Test (15%, 741 matches)**.
2. **Validation Candidate Selection**: Candidate models (Logistic Regression, Random Forest, XGBoost, Voting Ensemble) are trained on the Train set and evaluated on the Validation set using a composite score balancing weighted F1 and Log Loss calibration.
3. **Combined Retraining**: The winning Random Forest candidate is retrained on combined `Train + Validation` data (4,199 matches).
4. **Untouched Test Evaluation**: The retrained model is evaluated **once** on the held-out Test set (741 matches).

---

## Official Test Set Metrics (Source-of-Truth)

| Metric | Score | Baseline (Naive Majority) | Description |
|---|:---:|:---:|---|
| **Accuracy** | **49.66%** | 41.70% | Overall top-1 classification accuracy (+7.96% lift) |
| **Weighted F1 Score** | **0.4168** | 0.2454 | F1 score weighted across all 3 classes (+0.1714 lift) |
| **Log Loss** | **1.0226** | 1.0848 | Multi-class cross-entropy loss (-0.0622 improvement) |
| **Brier Score** | **0.6134** | 0.6574 | Mean squared probability error (-0.0440 improvement) |

### Per-Class Performance (Test Set: 741 Matches)

| Class | Precision | Recall | F1-Score | Support |
|---|:---:|:---:|:---:|:---:|
| **HOME_WIN** | 0.50 | 0.80 | 0.62 | 309 |
| **DRAW** | 0.00 | 0.00 | 0.00 | 194 |
| **AWAY_WIN** | 0.48 | 0.51 | 0.50 | 238 |
| **Macro Average** | 0.33 | 0.44 | 0.37 | 741 |
| **Weighted Average** | 0.37 | 0.50 | 0.42 | 741 |

---

## Modeling Insights & Trade-offs

### 1. The Draw Prediction Dilemma
Draws are the most high-variance outcome in football (~24.5% occurrence rate in the 13-season dataset). In a calibrated 3-class model, draw probabilities typically range between 22% and 32%. Because home and away win probabilities routinely exceed 35%, a standard $\arg\max$ decision rule will almost never choose DRAW as the discrete top class.

Rather than forcing draw predictions with arbitrary probability threshold hacks (which increases false positives and degrades calibration), MatchIQ outputs continuous, calibrated probability vectors $[P(\text{Home}), P(\text{Draw}), P(\text{Away})]$. Downstream simulation tools sample from this distribution directly, preserving accurate league-wide draw rates (~24%).

### 2. Model Selection: Random Forest vs. XGBoost
XGBoost achieved marginally higher discrete accuracy on validation (57.09% vs. 56.28%), but Random Forest achieved lower Log Loss (**0.9515** vs. 0.9572) and a superior Brier Score (**0.5621** vs. 0.5643). Random Forest was selected because ensemble bagging produces smoother probability estimates on noisy sports fixtures, avoiding the overconfident extreme predictions that penalize boosted gradient methods.
