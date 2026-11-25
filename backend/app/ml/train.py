"""
JOURNEX – Random Forest Risk Model Trainer
Phase 7: Explainable ML Risk Analysis

Trains and serializes the Scikit-learn Random Forest risk classifier, reports
complete performance metrics, and exports metadata.

REPRODUCIBILITY:
Run: `python -m app.ml.train` from `backend/`
"""

import os
import json
import joblib
import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from app.ml.dataset_generator import (
    generate_synthetic_data,
    FEATURE_NAMES,
    RISK_LABELS,
    LABEL_MAP,
    REV_LABEL_MAP
)

MODEL_VERSION = "1.0.0-rf"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def train_and_evaluate(n_samples: int = 4000, random_seed: int = 42):
    """
    Train Random Forest model on reproducible synthetic journey data,
    evaluate on held-out test split, and save artifacts.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("Step 1: Generating synthetic journey data...")
    X, y = generate_synthetic_data(n_samples=n_samples, random_seed=random_seed)

    print(f"Total samples: {len(y)}")
    class_dist = {cat: int(np.sum(y == LABEL_MAP[cat])) for cat in RISK_LABELS}
    print(f"Class distribution: {class_dist}")

    print("Step 2: Splitting into train (75%) and test (25%) splits (stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_seed, stratify=y
    )
    print(f"Train size: {len(y_train)}, Test size: {len(y_test)}")

    print("Step 3: Fitting Random Forest Classifier...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_seed,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    print("Step 4: Evaluating on test set...")
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    prec_weighted = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    rec_weighted = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()

    report_dict = classification_report(
        y_test, y_pred, target_names=RISK_LABELS, output_dict=True, zero_division=0
    )

    feature_importances = {
        feat: float(imp)
        for feat, imp in zip(FEATURE_NAMES, clf.feature_importances_)
    }
    # Sort descending
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    print(f"\n--- EVALUATION METRICS (Test Set, N={len(y_test)}) ---")
    print(f"Accuracy:          {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision (Macro): {prec_macro:.4f}")
    print(f"Recall (Macro):    {rec_macro:.4f}")
    print(f"F1-Score (Macro):  {f1_macro:.4f}")
    print(f"Confusion Matrix:")
    print(np.array(cm))
    print("\nFeature Importances:")
    for feat, imp in sorted_importances.items():
        print(f"  {feat:26s}: {imp:.4f}")

    print("\nStep 5: Serializing artifacts to disk...")
    model_path = os.path.join(MODELS_DIR, "risk_model.joblib")
    features_path = os.path.join(MODELS_DIR, "feature_names.json")
    meta_path = os.path.join(MODELS_DIR, "model_meta.json")

    joblib.dump(clf, model_path)

    with open(features_path, "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 8,
            "min_samples_split": 4,
            "min_samples_leaf": 2,
            "class_weight": "balanced",
            "random_state": random_seed
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "total_samples": len(y),
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "class_distribution": class_dist,
            "synthetic_disclaimer": (
                "Trained on synthetic rule-simulated travel anomalies. "
                "Does not reflect real-world crime incidence or calibrated probability of violence."
            )
        },
        "metrics": {
            "accuracy": acc,
            "precision_macro": prec_macro,
            "precision_weighted": prec_weighted,
            "recall_macro": rec_macro,
            "recall_weighted": rec_weighted,
            "f1_macro": f1_macro,
            "f1_weighted": f1_weighted,
            "confusion_matrix": cm,
            "classification_report": report_dict
        },
        "feature_importances": sorted_importances
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model to: {model_path}")
    print(f"Saved feature list to: {features_path}")
    print(f"Saved metadata to: {meta_path}")
    return metadata

if __name__ == "__main__":
    train_and_evaluate()
