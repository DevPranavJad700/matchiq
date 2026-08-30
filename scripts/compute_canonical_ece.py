"""Compute canonical standard Expected Calibration Error (ECE) for MatchIQ.

Academic Definition (Naeini et al. 2015, Guo et al. 2017):
  ECE = sum_{b=1}^B (n_b / N) * | acc_b - conf_b |
  MCE = max_{b=1..B} | acc_b - conf_b |
"""

from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.features.feature_engineering import FEATURE_NAMES, compute_features
from ml.training.train import seasonal_chronological_split

df = pd.read_csv("data/processed/matches_processed.csv")
features_df = compute_features(df).dropna(subset=["target"])
features_df = features_df[
    (features_df["home_form_pts_last5"].notna()) & (features_df["away_form_pts_last5"].notna())
].reset_index(drop=True)

train_df, val_df, test_df = seasonal_chronological_split(features_df)
train_val_df = pd.concat([train_df, val_df]).reset_index(drop=True)

X_train_val = train_val_df[FEATURE_NAMES].values
y_train_val = train_val_df["target"].values.astype(int)
X_test = test_df[FEATURE_NAMES].values
y_test = test_df["target"].values.astype(int)

# 1. Uncalibrated Model Pipeline
uncal_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(C=0.2, max_iter=2000, class_weight="balanced", random_state=42)),
])
uncal_pipe.fit(X_train_val, y_train_val)
p_uncal = uncal_pipe.predict_proba(X_test)

# 2. Calibrated Model Pipeline (Platt Sigmoid 5-fold CV)
base_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(C=0.2, max_iter=2000, class_weight="balanced", random_state=42)),
])
cal_model = CalibratedClassifierCV(estimator=base_pipe, method="sigmoid", cv=5)
cal_model.fit(X_train_val, y_train_val)
p_cal = cal_model.predict_proba(X_test)


def compute_standard_ece(y_true_binary, probs, n_bins=5):
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    N = len(y_true_binary)
    bin_details = []
    weighted_ece = 0.0
    unweighted_macro_ece = []
    max_cal_error = 0.0

    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        if i == n_bins - 1:
            mask = (probs >= low) & (probs <= high)
        else:
            mask = (probs >= low) & (probs < high)
        n_b = int(np.sum(mask))
        if n_b > 0:
            p_mean = float(np.mean(probs[mask]))
            y_mean = float(np.mean(y_true_binary[mask]))
            diff = float(abs(y_mean - p_mean))
            contrib = float((n_b / N) * diff)
            weighted_ece += contrib
            unweighted_macro_ece.append(diff)
            if diff > max_cal_error:
                max_cal_error = diff
            bin_details.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "n": n_b,
                "weight": round(n_b / N, 4),
                "p_mean": round(p_mean, 4),
                "y_mean": round(y_mean, 4),
                "diff": round(diff, 4),
                "weighted_contrib": round(contrib, 4),
            })
        else:
            bin_details.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "n": 0,
                "weight": 0.0,
                "p_mean": None,
                "y_mean": None,
                "diff": 0.0,
                "weighted_contrib": 0.0,
            })
    macro_ece = float(np.mean(unweighted_macro_ece)) if unweighted_macro_ece else 0.0
    return round(weighted_ece, 4), round(macro_ece, 4), round(max_cal_error, 4), bin_details


classes = [("HOME_WIN", 0), ("DRAW", 1), ("AWAY_WIN", 2)]
results = {}

print("=== CANONICAL ECE (STANDARD SAMPLE-WEIGHTED DEFINITION, 5 BINS) ===")

for name, target in classes:
    y_bin = (y_test == target).astype(int)

    # Uncalibrated
    brier_uncal = float(brier_score_loss(y_bin, p_uncal[:, target]))
    ece_uncal, macro_uncal, mce_uncal, bins_uncal = compute_standard_ece(y_bin, p_uncal[:, target], n_bins=5)

    # Calibrated
    brier_cal = float(brier_score_loss(y_bin, p_cal[:, target]))
    ece_cal, macro_cal, mce_cal, bins_cal = compute_standard_ece(y_bin, p_cal[:, target], n_bins=5)

    results[name] = {
        "uncalibrated": {
            "brier": round(brier_uncal, 4),
            "standard_weighted_ece": ece_uncal,
            "unweighted_macro_ece": macro_uncal,
            "mce": mce_uncal,
            "bins": bins_uncal,
        },
        "calibrated": {
            "brier": round(brier_cal, 4),
            "standard_weighted_ece": ece_cal,
            "unweighted_macro_ece": macro_cal,
            "mce": mce_cal,
            "bins": bins_cal,
        },
    }

    print(f"\n{'=' * 65}")
    print(f"CLASS: {name}")
    print(f"  Uncalibrated -> Brier: {brier_uncal:.4f} | Standard Weighted ECE: {ece_uncal:.4f} | MCE: {mce_uncal:.4f}")
    print(f"  Calibrated   -> Brier: {brier_cal:.4f} | Standard Weighted ECE: {ece_cal:.4f} | MCE: {mce_cal:.4f}")
    pct_change = ((ece_cal - ece_uncal) / ece_uncal) * 100
    print(f"  ECE Change:   {ece_cal - ece_uncal:+.4f} ({pct_change:+.1f}%)")

    print("  Calibrated Bins:")
    for b in bins_cal:
        if b["n"] > 0:
            print(f"    Bin {b['bin']}: n={b['n']:>3} (wt: {b['weight']:.3f}) | Pred: {b['p_mean']:.4f} | True: {b['y_mean']:.4f} | Diff: {b['diff']:.4f} | Contrib: {b['weighted_contrib']:.4f}")
        else:
            print(f"    Bin {b['bin']}: n=  0 (empty)")

with open("ml/models/standard_ece_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to ml/models/standard_ece_results.json")
