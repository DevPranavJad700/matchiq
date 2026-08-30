"""Generate publication-ready Reliability (Calibration) Curves for MatchIQ.

Computes and plots binned predicted probability vs. empirical observed frequency
for Uncalibrated vs. Calibrated models on the untouched 2025–26 Premier League test set (380 matches)
using the canonical, sample-weighted Expected Calibration Error (ECE) definition (Naeini et al. 2015, Guo et al. 2017).
"""

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import joblib
import matplotlib.pyplot as plt
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

# Output directories
ASSETS_DIR = Path("docs/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = Path("C:/Users/ASUS/.gemini/antigravity-ide/brain/7a17e3f4-bf69-4ea7-b980-183572337898")

# Load and prepare data
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

# 1. Train Uncalibrated Base Model Pipeline
uncal_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(C=0.2, max_iter=2000, class_weight="balanced", random_state=42)),
])
uncal_pipe.fit(X_train_val, y_train_val)
p_uncal = uncal_pipe.predict_proba(X_test)

# 2. Train Calibrated Model Pipeline (Platt Sigmoid 5-fold CV)
base_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(C=0.2, max_iter=2000, class_weight="balanced", random_state=42)),
])
cal_model = CalibratedClassifierCV(estimator=base_pipe, method="sigmoid", cv=5)
cal_model.fit(X_train_val, y_train_val)
p_cal = cal_model.predict_proba(X_test)


def compute_standard_calibration(y_true_binary, probs, n_bins=5):
    """Compute standard sample-weighted ECE and bin points."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    N = len(y_true_binary)
    prob_pred = []
    prob_true = []
    weighted_ece = 0.0
    max_cal_error = 0.0
    bin_details = []

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
            if diff > max_cal_error:
                max_cal_error = diff
            prob_pred.append(p_mean)
            prob_true.append(y_mean)
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

    return np.array(prob_true), np.array(prob_pred), round(weighted_ece, 4), round(max_cal_error, 4), bin_details


# Class mappings
classes = [("HOME_WIN", 0, "#10B981"), ("DRAW", 1, "#F59E0B"), ("AWAY_WIN", 2, "#EF4444")]
calibration_results = {}

plt.style.use("dark_background")
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), dpi=300)
fig.patch.set_facecolor("#0F1318")

for idx, (cname, ctarget, color) in enumerate(classes):
    ax = axes[idx]
    ax.set_facecolor("#151A21")
    y_binary = (y_test == ctarget).astype(int)

    # Standard Calibration curves and weighted ECE
    prob_true_uncal, prob_pred_uncal, ece_uncal, mce_uncal, bins_uncal = compute_standard_calibration(
        y_binary, p_uncal[:, ctarget], n_bins=5
    )
    prob_true_cal, prob_pred_cal, ece_cal, mce_cal, bins_cal = compute_standard_calibration(
        y_binary, p_cal[:, ctarget], n_bins=5
    )

    # Brier scores
    brier_uncal = float(brier_score_loss(y_binary, p_uncal[:, ctarget]))
    brier_cal = float(brier_score_loss(y_binary, p_cal[:, ctarget]))

    # Perfect calibration reference diagonal
    ax.plot([0, 1], [0, 1], linestyle="--", color="#6B7280", linewidth=1.5, label="Perfect Calibration", alpha=0.8)

    # Uncalibrated curve
    ax.plot(
        prob_pred_uncal,
        prob_true_uncal,
        marker="s",
        markersize=6,
        linestyle=":",
        color="#94A3B8",
        linewidth=1.8,
        label=f"Uncalibrated (Brier={brier_uncal:.4f}, ECE={ece_uncal:.4f})",
    )

    # Calibrated curve
    ax.plot(
        prob_pred_cal,
        prob_true_cal,
        marker="o",
        markersize=7,
        linestyle="-",
        color=color,
        linewidth=2.4,
        label=f"Platt Calibrated (Brier={brier_cal:.4f}, ECE={ece_cal:.4f})",
    )

    ax.set_title(f"{cname.replace('_', ' ')} Calibration (N=380)", fontsize=13, fontweight="bold", color="#F3F4F6", pad=12)
    ax.set_xlabel("Mean Predicted Probability", fontsize=11, color="#9CA3AF")
    ax.set_ylabel("Empirical True Frequency", fontsize=11, color="#9CA3AF")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.0])
    ax.grid(True, linestyle="--", alpha=0.25, color="#374151")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.8, facecolor="#1E242D", edgecolor="#374151")

    # Store numbers
    calibration_results[cname] = {
        "brier_uncalibrated": round(brier_uncal, 4),
        "brier_calibrated": round(brier_cal, 4),
        "standard_weighted_ece_uncalibrated": ece_uncal,
        "standard_weighted_ece_calibrated": ece_cal,
        "mce_uncalibrated": mce_uncal,
        "mce_calibrated": mce_cal,
        "calibrated_bins": bins_cal,
    }

plt.suptitle("MatchIQ Reliability Diagrams — Predicted Probability vs. Empirical Match Frequency (Standard Sample-Weighted ECE, 2025–26 Test Season)", fontsize=13, fontweight="bold", color="#FFFFFF", y=1.02)
plt.tight_layout()

# Save plots
out_plot_path = ASSETS_DIR / "calibration_curve.png"
plt.savefig(out_plot_path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=300)
if ARTIFACTS_DIR.exists():
    plt.savefig(ARTIFACTS_DIR / "calibration_curve.png", bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=300)
plt.close()

# Save JSON data
with open("ml/models/calibration_data.json", "w") as f:
    json.dump(calibration_results, f, indent=2)

print("Calibration curves regenerated successfully with canonical sample-weighted ECE!")
print(f"Saved plot to: {out_plot_path}")
print(f"Saved calibration data to: ml/models/calibration_data.json")
print(json.dumps(calibration_results, indent=2))
