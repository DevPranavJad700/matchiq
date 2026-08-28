"""Audit script: leakage test, ML verification, API probe."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, 'ml')
sys.path.insert(0, 'backend')

print("=" * 60)
print("AUDIT 1: DATA LEAKAGE CHECK")
print("=" * 60)

from features.feature_engineering import _rolling_team_features, compute_features

# 5-match sequence for team 1
df = pd.DataFrame({
    'match_id': range(1, 6),
    'match_date': pd.date_range('2024-01-01', periods=5, freq='7D'),
    'home_team_id': [1, 2, 1, 2, 1],
    'away_team_id': [2, 1, 2, 1, 2],
    'result':       ['H', 'D', 'A', 'H', 'H'],
    'home_goals':   [2, 1, 0, 3, 2],
    'away_goals':   [0, 1, 2, 1, 1],
    'home_shots':   [10, 8, 5, 12, 9],
    'away_shots':   [5, 6, 10, 4, 7],
    'home_sot':     [5, 3, 2, 6, 4],
    'away_sot':     [2, 2, 5, 2, 3],
    'home_xg':      [1.8, 0.9, 0.4, 2.1, 1.5],
    'away_xg':      [0.5, 0.8, 1.6, 0.7, 1.0],
})

tf = _rolling_team_features(df, team_id=1)
print("Team 1 rolling form_pts_last5 (should be NaN/0 for match 1, 3.0 for match 2):")
print(tf[['form_pts_last5', 'avg_goals_scored', 'avg_goals_conceded']].head())

# For match 1, no prior data — first value after shift should be NaN/0
m1_pts = tf.loc[1, 'form_pts_last5'] if 1 in tf.index else None
m2_pts = tf.loc[2, 'form_pts_last5'] if 2 in tf.index else None

print(f"\nMatch 1 form_pts_last5 = {m1_pts} (expected 0 or NaN - no history)")
print(f"Match 2 form_pts_last5 = {m2_pts} (expected 3.0 - only match 1 before it)")

if m2_pts == 3.0:
    print("LEAKAGE CHECK: PASS - shift(1) working correctly")
else:
    print(f"LEAKAGE CHECK: FAIL - expected 3.0 got {m2_pts}")

print()
print("=" * 60)
print("AUDIT 2: FEATURE COUNT MATCHES TRAINING vs INFERENCE")
print("=" * 60)

from app.ml.model_loader import load_model, get_model_metadata, get_feature_names
load_model()
meta = get_model_metadata()
train_features = meta.get('features', [])
print(f"Training features: {len(train_features)}")
print(f"Inference features (feature_builder.py FEATURE_NAMES): check manually")

from app.services.feature_builder import FEATURE_NAMES as inference_features
print(f"Inference FEATURE_NAMES count: {len(inference_features)}")
print(f"Features match: {set(train_features) == set(inference_features)}")
if set(train_features) != set(inference_features):
    missing_in_train = set(inference_features) - set(train_features)
    missing_in_infer = set(train_features) - set(inference_features)
    print(f"  Missing in training: {missing_in_train}")
    print(f"  Missing in inference: {missing_in_infer}")

print()
print("=" * 60)
print("AUDIT 3: ML MODEL METRICS (actual recorded values)")
print("=" * 60)

import json
with open('ml/models/metrics.json') as f:
    metrics = json.load(f)
print(f"Algorithm: {metrics.get('algorithm')}")
print(f"Accuracy:  {metrics.get('accuracy')}")
print(f"F1 Score:  {metrics.get('f1_score')}")
print(f"Log Loss:  {metrics.get('log_loss')}")
print(f"Training Date: {metrics.get('training_date')}")

print()
print("=" * 60)
print("AUDIT 4: PROBABILITY SANITY CHECK")
print("=" * 60)

from app.ml.model_loader import predict_proba
# Use a zero feature vector as a baseline
zero_vector = np.zeros((1, len(train_features)))
proba = predict_proba(zero_vector)[0]
total = sum(proba)
print(f"Probabilities (zero vector): H={proba[0]:.4f} D={proba[1]:.4f} A={proba[2]:.4f}")
print(f"Sum = {total:.6f} (expected ~1.0)")
print(f"Probability sum check: {'PASS' if abs(total - 1.0) < 0.001 else 'FAIL'}")

print()
print("=" * 60)
print("AUDIT 5: SHAP EXPLANATION CHECK")
print("=" * 60)

from app.ml.model_loader import explain_prediction, get_explainer
explainer = get_explainer()
print(f"SHAP explainer loaded: {explainer is not None}")
if explainer is not None:
    explanations = explain_prediction(zero_vector)
    print(f"Number of explanation factors: {len(explanations)}")
    if explanations:
        print(f"Sample factor: {explanations[0]}")
        has_impact = all('impact' in e and 'feature' in e for e in explanations)
        print(f"All factors have impact+feature: {'PASS' if has_impact else 'FAIL'}")
