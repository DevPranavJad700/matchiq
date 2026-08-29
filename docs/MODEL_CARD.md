# Model Card — MatchIQ Premier League Predictor

## Model Details
- **Model Name**: MatchIQ Premier League Match Predictor
- **Version**: `logistic_regression-v20260829`
- **Model Architecture**: Scaled Logistic Regression (`StandardScaler` + `LogisticRegression(class_weight='balanced')`)
- **Framework**: `scikit-learn`
- **Training Date**: 2026-08-29
- **Input Features**: 39 engineered features (team form, rolling goals/xg/shots, venue win rates, standings, head-to-head metrics, and feature differentials).

---

## Intended Use
- **Primary Use Case**: Predicting 3-way match outcomes (Home Win, Draw, Away Win) for Premier League fixtures based on historical performance metrics prior to kick-off.
- **Out-of-Scope Use Cases**: Live in-game micro-betting, financial trading, or deterministic outcome guarantees.

---

## Evaluation & Validation Protocol
To eliminate data contamination and temporal leakage:
1. **Chronological Splitting**: Data is split chronologically into Train (70%), Validation (15%), and Test (15%).
2. **Validation Candidate Selection**: Candidate algorithms (Logistic Regression, Random Forest, XGBoost) are trained on the Train set and evaluated on the Validation set.
3. **Combined Retraining**: The winning algorithm (`logistic_regression`) is retrained on combined Train + Validation data.
4. **Untouched Test Evaluation**: The retrained model is evaluated ONCE on the completely untouched Test set (170 matches).

---

## Official Test Set Metrics (Source-of-Truth)

| Metric | Score | Description |
|---|---:|---|
| **Accuracy** | **50.00%** | Overall top-1 classification accuracy |
| **Weighted F1 Score** | **0.4780** | F1 score weighted across all 3 classes |
| **Log Loss** | **0.9946** | Multi-class cross-entropy loss |
| **Brier Score** | **0.5952** | Mean squared probability error |

### Per-Class Performance

| Class | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| **HOME_WIN** | 0.63 | 0.75 | 0.69 | 79 |
| **DRAW** | 0.31 | 0.18 | 0.23 | 50 |
| **AWAY_WIN** | 0.35 | 0.41 | 0.38 | 41 |

### Draw Class Explanation
Draws represent the most chaotic and high-variance outcome in association football (~25% base rate). Using `class_weight='balanced'`, draw recall improved to **18.00%** (up from 6.00%), providing realistic probability calibration rather than over-confident predictions.
