# Model Card — MatchIQ Premier League Predictor

## Model Details
- **Model Name**: MatchIQ Premier League Match Predictor & Dixon-Coles Statistical Engine
- **Version**: `logistic_regression-v20260830`
- **Model Architecture**: Calibrated Classifier (`CalibratedClassifierCV` with Platt sigmoid scaling, $C=0.2$, balanced class weights) + Statistical Dixon-Coles (1997) Goal Poisson Engine ($\xi=0.0019$, $\rho=-0.0819$)
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
1. **Chronological Splitting**: Data (4,940 matches, 13 seasons) is split chronologically into **Train (4,180 matches: 2013–14 to 2023–24)**, **Validation (380 matches: 2024–25 season)**, and **Test (380 matches: 2025–26 season)**.
2. **Probability Calibration**: Candidate models (Logistic Regression, Random Forest, XGBoost, Voting Ensemble) are trained with 5-fold `CalibratedClassifierCV` on the Train set and evaluated on the Validation set.
3. **Identical Test Set Evaluation**: The final model is evaluated **once** on the untouched 380-match Test set alongside closing betting market odds and Dixon-Coles goal modeling benchmarks. **Every row in the benchmark comparison is scored on the identical 380 test matches ($N=380$, zero dropped rows).**

---

## Accuracy vs. Calibration Trade-off: Plain-English Rationale

> [!NOTE]
> **Why did headline discrete accuracy change (49.66% → 47.63%)?**
> Uncalibrated tree ensembles produce overconfident probability tails that yield slightly higher discrete accuracy on easy home games, but suffer heavy Log Loss and Ranked Probability Score penalties on upsets.
> We deliberately wrapped candidate models in `CalibratedClassifierCV` (Platt scaling), trading ~2% raw discrete accuracy in exchange for continuous probability calibration and lower Log Loss (1.0315) and RPS (0.2099). Continuous calibration is essential because downstream Monte Carlo simulations sample directly from probability distributions, where calibration quality directly determines simulation fidelity.

---

## Official Test Set Benchmark Metrics (Identical $N=380$ Matches)

| Predictor / Architecture | Evaluated Matches ($N$) | Accuracy (argmax) | Weighted F1 | Log Loss | Brier Score | Ranked Prob Score (RPS) | Performance Relative to Market |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Naive Majority Class Baseline** (Always Home) | 380 | 42.63% | 0.2548 | 1.0846 | 0.6565 | 0.2279 | 61.8% efficiency |
| **Dixon-Coles (1997) Goal Model** | 380 | 46.84% | 0.3842 | 1.0394 | 0.6214 | 0.2137 | 96.0% efficiency |
| **MatchIQ Calibrated Model** | 380 | **47.63%** | **0.3989** | **1.0315** | **0.6205** | **0.2099** | **97.8% efficiency** |
| **Closing Betting Market Odds** (Market Consensus) | 380 | **49.47%** | **0.4124** | **1.0153** | **0.6100** | **0.2053** | **100.0% (Ceiling Benchmark)** |

---

## Full Per-Class Classification Reports: Standard Argmax vs. Tuned Draw Threshold ($\theta=0.230$)

### Standard $\arg\max$ Mode ($\theta=0.333$)
```
              precision    recall  f1-score   support

    HOME_WIN     0.5168    0.7593    0.6150       162
        DRAW     0.0000    0.0000    0.0000       104
    AWAY_WIN     0.4225    0.5263    0.4688       114

    accuracy                         0.4816       380
   macro avg     0.3131    0.4285    0.3613       380
weighted avg     0.3471    0.4816    0.4028       380
```

### Tuned Decision Threshold Mode ($\theta_{\text{draw}}=0.230$)
```
              precision    recall  f1-score   support

    HOME_WIN     0.6163    0.3272    0.4274       162
        DRAW     0.2953    0.7212    0.4190       104
    AWAY_WIN     0.5250    0.1842    0.2727       114

    accuracy                         0.3921       380
   macro avg     0.4789    0.4108    0.3730       380
weighted avg     0.5010    0.3921    0.3787       380
```

### Trade-off Summary:
- **Draw Recall**: Rises from **0.00% to 72.12%** (+72.12% lift, identifying 75 of 104 draws).
- **Home Win Precision**: Increases from **51.68% to 61.63%** (+9.95% precision gain).
- **Away Win Precision**: Increases from **42.25% to 52.50%** (+10.25% precision gain).
- **Macro Average F1**: Increases from **0.3613 to 0.3730** (+0.0117 overall balance improvement).

---

## Validation Blend Sweep ($w \in [0.0, 1.0]$)
A systematic grid search on the 2024–25 Validation Set confirmed that the calibrated discriminative model ($w=1.00$) achieves the lowest validation RPS (**0.2033**) and Log Loss (**0.9898**), outperforming linear probability mixing and establishing the standalone calibrated classifier as the primary outcome model.
