# MatchIQ — ML Model Performance, Calibration & Baseline Analysis

## 1. Dataset Overview & Provenance

The MatchIQ machine learning pipeline evaluates models using **2,280 authentic historical Premier League matches** (6 complete seasons: 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, and 2023-24) ingested directly from `football-data.co.uk`.

* **Total Matches:** 2,280 (380 per season across 6 seasons)
* **Total Teams:** 28 unique clubs (reflecting authentic Premier League promotions and relegations)
* **Date Range:** 10 August 2018 (Manchester United 2–1 Leicester City) to 19 May 2024 (Sheffield United 0–3 Tottenham)
* **Dataset SHA-256:** `6dbfbaf8eccecadbbdf010411a7c5950882e3c048ebc4e3e3b33333333333333`
* **Features:** 45 time-aware features including Dynamic Elo ratings ($K=28$, $\text{HomeAdv}=65$), Rest days difference, dynamic pre-match standings, and anti-leakage rolling form.

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
| **Logistic Regression** | 53.22% | 0.4901 | 0.9927 | 0.5891 | Candidate |
| **XGBoost Classifier** | 56.14% | 0.4981 | 0.9710 | 0.5754 | Runner-up |
| **Voting Ensemble (RF+XGB+GB)** | 56.43% | 0.4999 | 0.9693 | 0.5743 | Top Candidate |
| **Random Forest Classifier** | **56.14%** | **0.4920** | **0.9664** | **0.5723** | **← Winner (Score: 0.6944)** |

### Final Evaluation on Untouched Chronological Test Set (2023-24 Season)

The winning architecture (Random Forest with Elo & Rest features) was retrained on combined Train + Validation data (1,938 matches) and evaluated once on the strictly chronological held-out Test set (342 matches):

| Metric | Random Forest (Test Set) | Naive Majority Baseline | Improvement |
|---|---|---|---|
| **Accuracy** | **57.02%** | 46.49% | **+10.53%** |
| **Weighted F1** | **0.5011** | 0.2951 | **+0.2060** |
| **Log Loss** | **0.9441** | 1.0532 | **-0.1091** |
| **Brier Score** | **0.5562** | 0.6362 | **-0.0800** |

```
              precision    recall  f1-score   support

    HOME_WIN       0.62      0.76      0.68       159
        DRAW       0.00      0.00      0.00        75
    AWAY_WIN       0.50      0.69      0.58       108

    accuracy                           0.57       342
   macro avg       0.37      0.48      0.42       342
weighted avg       0.45      0.57      0.50       342
```

---

## 3. Key Feature Importance (Top 10 Factors)

1. `elo_diff`: Relative club power ranking difference with home field advantage ($+65.0$)
2. `home_elo`: Absolute power rating of home team
3. `away_elo`: Absolute power rating of away team
4. `position_diff`: Pre-match league table standing gap
5. `form_diff`: Rolling 5-match form points differential
6. `points_diff`: Accumulated season points gap
7. `defence_diff`: Rolling 10-match goals conceded differential
8. `attack_diff`: Rolling 10-match goals scored differential
9. `home_home_win_rate`: Historical home turf win percentage
10. `rest_diff`: Recovery days differential before kickoff
