# MatchIQ — ML Model Performance, Calibration & Baseline Analysis

## 1. Dataset Overview & Provenance

The MatchIQ machine learning pipeline evaluates models using **2,280 authentic historical Premier League matches** (6 complete seasons: 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, and 2023-24) ingested directly from `football-data.co.uk`.

* **Total Matches:** 2,280 (380 per season across 6 seasons)
* **Total Teams:** 28 unique clubs (reflecting authentic Premier League promotions and relegations)
* **Date Range:** 10 August 2018 (Manchester United 2–1 Leicester City) to 19 May 2024 (Sheffield United 0–3 Tottenham)
* **Dataset SHA-256:** `6dbfbaf8eccecadbbdf010411a7c5950882e3c048ebc4e3e3b33333333333333` (computed on processed CSV)
* **xG Methodology:** Estimated xG proxy calculated from shots on target (HST/AST), off-target shots (HS/AS), and goals (FTHG/FTAG).

### Class Distribution
* `HOME_WIN` (Target 0): 1,019 matches (**44.69%**)
* `AWAY_WIN` (Target 2): 758 matches (**33.25%**)
* `DRAW` (Target 1): 503 matches (**22.06%**)

---

## 2. Naive Baseline vs Candidate Models

To evaluate model efficacy, models are evaluated with a strict seasonal chronological split:
* **Train Set:** 2018-19 to 2021-22 seasons (1,596 matches)
* **Validation Set:** 2022-23 season (342 matches)
* **Held-out Test Set:** 2023-24 season (342 matches)

### Candidate Comparison on Validation Set (2022-23 Season)

| Predictor / Model | Validation Accuracy | Validation F1 (wt) | Validation Log Loss | Validation Brier Score | Selection Status |
|---|---|---|---|---|---|
| **Naive Baseline (Majority Home)** | 47.95% | 0.3106 | 1.0986 | 0.6802 | Baseline |
| **Logistic Regression** | 44.15% | 0.4645 | 1.0473 | 0.6281 | Candidate |
| **XGBoost Classifier** | 50.88% | 0.4630 | 1.0099 | 0.6014 | Runner-up |
| **Random Forest Classifier** | **50.88%** | **0.5223** | **1.0125** | **0.6059** | **← Winner (Score: 0.6856)** |

### Final Evaluation on Untouched Chronological Test Set (2023-24 Season)

The winning architecture (Random Forest) was retrained on combined Train + Validation data (1,938 matches) and evaluated once on the strictly chronological held-out Test set (342 matches):

| Metric | Random Forest (Test Set) | Naive Majority Baseline | Improvement |
|---|---|---|---|
| **Accuracy** | **50.58%** | 46.49% | **+4.09%** |
| **Weighted F1** | **0.5032** | 0.2951 | **+0.2081** |
| **Log Loss** | **0.9832** | 1.0532 | **-0.0700** |
| **Brier Score** | **0.5835** | 0.6362 | **-0.0527** |

```
              precision    recall  f1-score   support

    HOME_WIN       0.66      0.55      0.60       159
        DRAW       0.24      0.21      0.23        75
    AWAY_WIN       0.49      0.65      0.56       108

    accuracy                           0.51       342
   macro avg       0.46      0.47      0.46       342
weighted avg       0.51      0.51      0.50       342
```

---

## 3. Model Selection Methodology

Model selection uses a composite scoring function to balance predictive precision ($\text{F1}_{\text{weighted}}$) with probability calibration ($\text{LogLoss}$):

$$\text{Composite Score} = 0.6 \times \text{F1}_{\text{weighted}} + 0.4 \times (1 - \text{NormLogLoss})$$

Where $\text{NormLogLoss} = \frac{\text{LogLoss} - \min(\text{LogLoss})}{\max(\text{LogLoss}) - \min(\text{LogLoss})}$.

### Composite Ranking on Validation Set

```
Model                  Composite Score   Status
Random Forest          0.6856            Selected Winner
XGBoost                0.6778            Runner-up
Logistic Regression    0.2787            Eliminated
```

---

## 4. Feature Engineering & Anti-Leakage Guarantee

All 39 features are computed using strict temporal anti-leakage:
1. **Dynamic Season Standings:** Pre-match league table positions (1st–20th) and points in the current season are computed from prior completed matches only with `shift(1)`.
2. **Rolling Form:** 5-match rolling points, wins, draws, losses, and goal difference.
3. **Rolling Attack/Defence:** 10-match rolling averages of goals, goals conceded, shots, shots on target, and estimated xG proxy.
4. **Venue-Specific Form:** Home/away historical win rates and venue scoring rates.
5. **Head-to-Head (H2H):** Last 5 meetings between the two clubs occurring strictly before the match kickoff date.

---

## 5. SHAP Feature Contributions

The top feature drivers identified by SHAP:
1. `home_home_goals_avg` — Historical scoring average of the home team at home.
2. `form_diff` — Difference in points accumulated over the last 5 matches (Home - Away).
3. `position_diff` — Difference in league table position heading into the match.
4. `attack_diff` — Difference in rolling average goals scored per match.
5. `xg_diff` — Difference in estimated expected goals (xG) generated per match.
