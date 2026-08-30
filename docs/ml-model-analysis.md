# MatchIQ — ML Model Performance, Calibration & Baseline Analysis

## 1. Dataset Overview & Provenance

The MatchIQ machine learning pipeline evaluates models on **4,940 authentic historical Premier League matches** (13 complete seasons: 2013–14 through 2025–26) ingested directly from `football-data.co.uk`.

* **Total Matches:** 4,940 (380 matches per season across 13 seasons)
* **Total Teams:** 35 unique clubs (accounting for authentic Premier League promotions and relegations)
* **Date Range:** 17 August 2013 (Liverpool 1–0 Stoke City) to 24 May 2026
* **Dataset SHA-256:** `f911e768881723e8bfcff643547e5864f04a38c9bfe6ae6fd091cccc1e1f3839`
* **Model Artifact SHA-256:** `1576b24006c2044b78d2441cc9891ca9653d789261ad2377f7be62e2591cdf00`
* **Features:** 45 time-aware, zero-leakage features including Dynamic Elo ratings ($K=28$, $\text{HomeAdv}=65$), rest days differential, pre-match standings, xG trends, closing betting odds, and rolling form with `.shift(1)` offsets.

### Overall Class Distribution (4,940 matches)
* `HOME_WIN` (Target 0): 2,217 matches (**44.88%**)
* `AWAY_WIN` (Target 2): 1,514 matches (**30.65%**)
* `DRAW` (Target 1): 1,209 matches (**24.47%**)

---

## 2. Chronological Splitting Protocol

To eliminate temporal leakage and lookahead bias, data is split strictly chronologically by season:

* **Training Set:** 4,180 matches (2013–14 through 2023–24 seasons)
* **Validation Set:** 380 matches (2024–25 season) — used for candidate model comparison, probability calibration tuning, and threshold selection.
* **Held-out Test Set:** 380 matches (2025–26 season) — untouched during all feature tuning and model exploration.

---

## 3. Ranked Probability Score (RPS) & Scientific Framing

In academic sports analytics (Epstein 1969; Constantinou & Fenton 2012), discrete accuracy is insufficient because football matches are inherently non-deterministic and ordered ($\text{Home Win} \prec \text{Draw} \prec \text{Away Win}$).

MatchIQ evaluates probability forecasts using the **Ranked Probability Score (RPS)**:

$$\text{RPS} = \frac{1}{2} \sum_{r=1}^{2} \left( \sum_{i=1}^r p_i - \sum_{i=1}^r o_i \right)^2$$

Where $p_i$ is the predicted probability for outcome $i$, and $o_i \in \{0, 1\}$ is the actual outcome indicator.

* **Lower is better**: 0.0 indicates a perfect deterministic forecast; 0.228 indicates a naive constant predictor.
* **Bookmaker Ceiling**: Professional closing betting markets (with injury reports, starting lineups, and multi-million-pound market liquidity) achieve **RPS ≈ 0.205** and **~50–54% accuracy** on Premier League fixtures due to irreducible aleatoric match variance.

---

## 4. Benchmark Comparison on Untouched Test Set (2025–26 Season)

| Model / Predictor | Accuracy (argmax) | Weighted F1 | Log Loss | Brier Score | Ranked Prob Score (RPS) | Performance Relative to Market |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Naive Majority Class Baseline** (Always Home) | 42.63% | 0.2548 | 1.0846 | 0.6565 | 0.2279 | 61.8% efficiency |
| **Dixon-Coles (1997) Goal Model** | 46.84% | 0.3842 | 1.0394 | 0.6214 | 0.2137 | 96.0% efficiency |
| **MatchIQ Calibrated Model** | **47.63%** | **0.3989** | **1.0315** | **0.6205** | **0.2099** | **97.8% efficiency** |
| **Blended Model (65% ML + 35% Dixon-Coles)** | 46.84% | 0.3912 | 1.0291 | 0.6191 | **0.2097** | **97.9% efficiency** |
| **Closing Betting Market Odds** (Bet365 / Market Consensus) | **49.47%** | **0.4124** | **1.0153** | **0.6100** | **0.2053** | **100.0% (Ceiling Benchmark)** |

---

## 5. Candidate Validation Benchmarks (2024–25 Season)

Candidate models were trained on 4,180 historical matches and wrapped in `CalibratedClassifierCV` (Platt scaling with 5-fold cross-validation) to eliminate overconfident probability tails:

| Candidate Model | Validation Accuracy | Weighted F1 | Validation Log Loss | Validation Brier | Validation RPS | Composite Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Logistic Regression (Calibrated)** | **51.58%** | **0.4388** | **0.9898** | **0.5920** | **0.2033** | **0.7145 (Winner)** |
| **Random Forest (Calibrated)** | 52.11% | 0.4441 | 1.0005 | 0.5972 | 0.2062 | 0.5450 |
| **Voting Ensemble (Calibrated)** | 51.05% | 0.4332 | 1.0046 | 0.6003 | 0.2072 | 0.4749 |
| **XGBoost (Calibrated)** | 51.32% | 0.4357 | 1.0086 | 0.6032 | 0.2084 | 0.4118 |

---

## 6. Resolving the Draw Blindness Dilemma

In a standard 3-way classifier with continuous probabilities, raw $\arg\max$ decision boundaries ($\hat{y} = \arg\max_k P(y=k)$) often yield 0.00 recall on draws because draw probabilities naturally cluster between **22% and 32%**, rarely exceeding the 34%–45% required to beat both home and away win probabilities.

MatchIQ tunes the decision threshold on validation data:

$$\hat{y} = \begin{cases} \text{DRAW}, & \text{if } P(\text{Draw}) \ge \theta_{\text{draw}} \\ \arg\max_{k \in \{0, 2\}} P(y=k), & \text{otherwise} \end{cases}$$

For $\theta_{\text{draw}} = 0.230$:

### Before vs. After Threshold Tuning (Test Set: 380 matches)

| Metric | Raw $\arg\max$ ($\theta=0.333$) | Tuned Threshold ($\theta=0.230$) | Net Change |
|---|:---:|:---:|:---:|
| **Draw Recall** | **0.00%** | **50.96%** | **+50.96%** (53 / 104 draws identified) |
| **Draw Precision** | 0.00% | 25.85% | +25.85% |
| **Draw F1-Score** | 0.00 | 0.3430 | +0.3430 |
| **Macro Average F1** | 0.3576 | **0.3658** | **+0.0082** |
| **Home Win Recall** | 74.69% | 41.98% | Balanced across outcomes |
| **Away Win Recall** | 52.63% | 20.18% | Balanced across outcomes |

---

## 7. Statistical Dixon-Coles (1997) Goal Model Engine

In addition to discriminative classification, MatchIQ implements the classic statistical model by Mark J. Dixon and Stuart G. Coles:
* *'Modelling Association Football Scores and Inefficiencies in the Football Betting Market'*, *Applied Statistics*, 46(2), 265–280 (1997).

### Mathematical Formulation:
Home and away goals $X \sim \text{Poisson}(\lambda)$, $Y \sim \text{Poisson}(\mu)$ where:
$$\lambda = \exp(\mu_0 + \alpha_h + \beta_a + \gamma)$$
$$\mu = \exp(\mu_0 + \alpha_a + \beta_h)$$
With low-score correlation adjustment $\tau(x, y; \rho)$ on scorelines $(0,0), (0,1), (1,0), (1,1)$, time-decay parameter $\xi = 0.0019$, and zero-sum constraint $\sum \alpha = 0$.

* **Home Advantage Factor $\gamma$:** $+0.176$
* **Low-Score Interaction Parameter $\rho$:** $-0.0819$
* **Output Capabilities:** Generates full $11 \times 11$ score probability matrices, top 3 most likely exact scorelines (e.g., `1-0`, `1-1`, `2-0`), and expected goals $\lambda$ vs. $\mu$.

---

## 8. Feature Importance Rankings

1. `elo_diff` (15.8%): Pre-match Elo differential including home ground factor (+65.0 pts).
2. `points_diff` (8.4%): Pre-match league points accumulation gap.
3. `market_prob_home` / `market_prob_away` (7.6%): Closing betting market implied probabilities.
4. `xg_diff` (6.9%): Rolling 10-match expected goals created vs conceded differential.
5. `home_form_pts_last5` (5.2%): 5-match rolling points form.
