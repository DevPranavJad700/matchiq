# Model Card — MatchIQ Premier League Predictor

## Model Details
- **Model Name**: MatchIQ Premier League Match Predictor & Dixon-Coles Statistical Engine
- **Version**: `logistic_regression-v20260830`
- **Model Architecture**: Calibrated Logistic Classifier (`CalibratedClassifierCV` with sigmoid Platt scaling, $C=0.2$, balanced class weights) + Statistical Dixon-Coles (1997) Goal Poisson Engine ($\xi=0.0019$, $\rho=-0.0819$)
- **Framework**: `scikit-learn` v1.8.0, `scipy` v1.15.0
- **Input Features**: 45 engineered features (Dynamic Elo with $K=28$ and Home Advantage $+65$, rest days differential, rolling form with `.shift(1)` offsets, xG differentials, closing market odds, venue win rates, and pre-match standings).
- **Dataset Checksum (SHA-256)**: `f911e768881723e8bfcff643547e5864f04a38c9bfe6ae6fd091cccc1e1f3839`
- **Model Artifact Checksum (SHA-256)**: `1576b24006c2044b78d2441cc9891ca9653d789261ad2377f7be62e2591cdf00`

---

## Intended Use
- **Primary Use Case**: Predicting calibrated 3-way match outcome probabilities (`HOME_WIN`, `DRAW`, `AWAY_WIN`) and bivariate exact scorelines for Premier League fixtures based on strictly historical performance metrics available prior to kick-off.
- **Secondary Use Case**: Providing feature-level reasoning via SHAP/coefficient attribution and powering 10,000-run Monte Carlo seasonal simulations.
- **Out-of-Scope Use Cases**: In-play micro-betting, financial trading, or deterministic outcome guarantees.

---

## Evaluation & Validation Protocol
To eliminate data contamination and temporal leakage:
1. **Chronological Splitting**: Data (4,940 matches, 13 seasons) is split chronologically into **Train (4,180 matches)**, **Validation (380 matches: 2024–25 season)**, and **Test (380 matches: 2025–26 season)**.
2. **Candidate Selection with Calibration**: Candidate models (Logistic Regression, Random Forest, XGBoost, Voting Ensemble) are trained with 5-fold `CalibratedClassifierCV` on the Train set and evaluated on the Validation set using a multi-metric composite score balancing Weighted F1, Log Loss, and Ranked Probability Score (RPS).
3. **Combined Retraining**: The winning calibrated candidate is retrained on combined `Train + Validation` data (4,560 matches).
4. **Untouched Test Evaluation**: The retrained model is evaluated **once** on the held-out Test set (380 matches) alongside closing betting market odds and Dixon-Coles goal modeling benchmarks.

---

## Official Test Set Benchmark Metrics

| Predictor / Architecture | Accuracy (argmax) | Weighted F1 | Log Loss | Brier Score | Ranked Prob Score (RPS) | Performance Relative to Market |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Naive Majority Class Baseline** (Always Home) | 42.63% | 0.2548 | 1.0846 | 0.6565 | 0.2279 | 61.8% efficiency |
| **Dixon-Coles (1997) Goal Model** | 46.84% | 0.3842 | 1.0394 | 0.6214 | 0.2137 | 96.0% efficiency |
| **MatchIQ Calibrated Model** | **47.63%** | **0.3989** | **1.0315** | **0.6205** | **0.2099** | **97.8% efficiency** |
| **Blended Model (65% ML + 35% Dixon-Coles)** | 46.84% | 0.3912 | 1.0291 | 0.6191 | **0.2097** | **97.9% efficiency** |
| **Closing Betting Market Odds** (Market Consensus) | **49.47%** | **0.4124** | **1.0153** | **0.6100** | **0.2053** | **100.0% (Ceiling Benchmark)** |

---

## Per-Class Performance: Standard Argmax vs. Tuned Draw Threshold ($\theta=0.230$)

| Evaluation Mode | Class | Precision | Recall | F1-Score | Support |
|---|---|:---:|:---:|:---:|:---:|
| **Standard $\arg\max$** | **HOME_WIN** | 0.5149 | 0.7469 | 0.6096 | 162 |
| | **DRAW** | 0.0000 | 0.0000 | 0.0000 | 104 |
| | **AWAY_WIN** | 0.4138 | 0.5263 | 0.4633 | 114 |
| | *Macro Average* | 0.3096 | 0.4244 | 0.3576 | 380 |
| **Tuned Decision Threshold ($\theta=0.230$)** | **HOME_WIN** | 0.5574 | 0.4198 | 0.4789 | 162 |
| | **DRAW** | **0.2585** | **0.5096** | **0.3430** | 104 |
| | **AWAY_WIN** | 0.4340 | 0.2018 | 0.2754 | 114 |
| | *Macro Average* | **0.4166** | **0.3770** | **0.3658** | 380 |

---

## Dixon-Coles Goal Model Parameters
- **Home Advantage Factor $\gamma$:** $+0.176$
- **Low-Score Interaction Parameter $\rho$:** $-0.0819$
- **Time Decay Half-Life $\xi$:** $0.0019$
- **Scoreline Matrix Dimension:** $11 \times 11$
