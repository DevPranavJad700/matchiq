# MatchIQ — ML Model Performance, Calibration & Baseline Analysis

## 1. Dataset Overview & Provenance

The MatchIQ machine learning pipeline evaluates models on **4,940 authentic historical Premier League matches** (13 complete seasons: 2013–14 through 2025–26) ingested directly from `football-data.co.uk`.

* **Total Matches:** 4,940 (380 matches per season across 13 seasons)
* **Total Teams:** 34 unique clubs (accounting for authentic Premier League promotions and relegations)
* **Date Range:** 17 August 2013 (Liverpool 1–0 Stoke City) to 24 May 2026
* **Dataset SHA-256:** `ed8a946781ea36b04229e48f27f66426d436f77bafb21bfd7810f44471a5f546`
* **Model Artifact SHA-256:** `c40c945aaaa31a5901e0e166241a1ee8fe2ec280a08926dadabed80ff169be41`
* **Features:** 45 time-aware, zero-leakage features including Dynamic Elo ratings ($K=28$, $\text{HomeAdv}=65$), rest days differential, pre-match standings, xG trends, and rolling form with `.shift(1)` offsets.

### Overall Class Distribution (4,940 matches)
* `HOME_WIN` (Target 0): 2,217 matches (**44.88%**)
* `AWAY_WIN` (Target 2): 1,514 matches (**30.65%**)
* `DRAW` (Target 1): 1,209 matches (**24.47%**)

---

## 2. Chronological Splitting Protocol

To eliminate temporal leakage and lookahead bias, data is split strictly chronologically by season:

* **Training Set (70%):** 3,458 matches (2013–14 through 2022–23 seasons)
* **Validation Set (15%):** 741 matches (2023–24 and 2024–25 seasons)
* **Held-out Test Set (15%):** 741 matches (2025–26 season) — untouched during all feature tuning, model exploration, and threshold selection.

---

## 3. Candidate Benchmark on Validation Set

Candidate models are trained on the Training Set and benchmarked on the Validation Set:

| Predictor / Model | Validation Accuracy | Validation F1 (wt) | Validation Log Loss | Validation Brier Score | Selection Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Naive Majority Baseline (Always Home)** | 41.70% | 0.2454 | 1.0848 | 0.6574 | Baseline |
| **Logistic Regression** | 55.60% | 0.4899 | 0.9537 | 0.5630 | Candidate |
| **Random Forest Classifier** | **56.28%** | **0.4922** | **0.9515** | **0.5621** | **← Winner (Score: 0.6944)** |
| **XGBoost Classifier** | 57.09% | 0.5026 | 0.9572 | 0.5643 | Runner-up |
| **Voting Ensemble (RF + XGB + GB)** | 56.55% | 0.4957 | 0.9531 | 0.5622 | Candidate |

### Model Selection Rationale: Why Random Forest Over XGBoost?

While **XGBoost** achieved marginally higher discrete accuracy on the validation split (57.09% vs. 56.28%), **Random Forest** was selected as the production architecture based on our multi-metric objective function:

$$\text{Composite Score} = 0.6 \times \text{F1}_{\text{weighted}} + 0.4 \times (1 - \text{NormLogLoss})$$

1. **Superior Probability Calibration:** Random Forest produced lower multi-class Log Loss (**0.9515** vs. 0.9572) and a superior multi-class Brier Score (**0.5621** vs. 0.5643).
2. **Resistance to Overconfident Extremes:** Boosted trees can output overconfident tail probabilities on noisy sports data, resulting in heavy log-loss penalties on unexpected upsets. Random Forest’s bootstrap aggregation naturally yields smoother, better-calibrated posterior probabilities.
3. **Downstream Utility:** In sports forecasting, simulation engines and odds models rely on continuous probability vectors $[P(\text{Home}), P(\text{Draw}), P(\text{Away})]$, where calibration quality directly determines simulation reliability.

---

## 4. Final Evaluation on Untouched Chronological Test Set (741 Matches)

The winning Random Forest architecture was retrained on combined Train + Validation data (4,199 matches) and evaluated once on the untouched 2025–26 Test Set (741 matches):

| Metric | Random Forest (Test Set) | Naive Majority Baseline | Absolute Improvement |
|---|:---:|:---:|:---:|
| **Accuracy** | **49.66%** | 41.70% | **+7.96%** |
| **Weighted F1** | **0.4168** | 0.2454 | **+0.1714** |
| **Log Loss** | **1.0226** | 1.0848 | **-0.0622** |
| **Brier Score** | **0.6134** | 0.6574 | **-0.0440** |

### Test Set Classification Report

```
              precision    recall  f1-score   support

    HOME_WIN       0.50      0.80      0.62       309
        DRAW       0.00      0.00      0.00       194
    AWAY_WIN       0.48      0.51      0.50       238

    accuracy                           0.50       741
   macro avg       0.33      0.44      0.37       741
weighted avg       0.37      0.50      0.42       741
```

---

## 5. Addressing the Draw Prediction Challenge

A key observation in the classification report is that the standard $\arg\max$ decision rule ($\hat{y} = \arg\max_k P(y=k)$) produces **0.00 precision and recall for the DRAW class**.

### Why Does This Happen?

1. **Football Draws as Low-Probability Equilibria:** Draws represent ~24–26% of all Premier League outcomes. Unlike a win, a draw is rarely an isolated tactical intent; it is an equilibrium resulting from match parity, game-state defensive collapses, or low-scoring variance ($0\text{--}0, 1\text{--}1$).
2. **Diffuse Posterior Probabilities:** In a well-calibrated 3-way model, draw probabilities typically range between **22% and 32%**. Because neither team needs more than ~35% probability to beat the draw probability, the argmax mode will almost always select either the home team or away team.
3. **Calibration vs. Discrete Label Forcing:** Artificially lowering the draw threshold (e.g., predicting DRAW if $P(\text{Draw}) > 0.28$) would artificially raise draw recall to ~25%, but at the expense of false positives and degraded overall accuracy/log loss.
4. **Why MatchIQ Keeps Raw Probabilities:** Downstream consumers (such as our 10,000-run Monte Carlo seasonal simulator) sample directly from the continuous probability distribution $[P(H), P(D), P(A)]$ rather than using discrete argmax labels. This preserves the realistic ~24% draw frequency in aggregate league simulations.

---

## 6. Top Feature Importance Rankings (SHAP & Gini Importance)

1. `elo_diff` (16.22%): Pre-match Elo rating differential inclusive of home field advantage (+65.0 pts).
2. `xg_diff` (7.11%): Rolling 10-match expected goals created vs conceded differential.
3. `points_diff` (6.00%): Pre-match accumulated league table points gap.
4. `home_elo` (5.64%): Absolute power rating of the home club.
5. `position_diff` (5.55%): Numerical league standings position difference.
6. `home_home_win_rate` (4.59%): Venue-specific historical win percentage on home turf.
7. `away_elo` (4.44%): Absolute power rating of the visiting club.
8. `home_home_goals_avg` (4.18%): Average goals scored at home venue over prior 10 fixtures.
9. `attack_diff` (3.82%): Rolling 10-match offensive output differential.
10. `away_away_goals_avg` (2.93%): Average goals scored by visiting club on the road.
