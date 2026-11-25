# JOURNEX Machine Learning Risk Engine

> **Predictive Journey Anomaly & Travel Risk Assessment Engine**  
> *Scikit-learn | Random Forest Classifier | Python 3.10+*

---

## 🤖 Module Overview

The `ml/` directory contains the data generation scripts, exploratory notebooks, model training pipelines, and serialized model artifacts for the JOURNEX risk engine.

The risk engine analyzes multi-dimensional journey telemetry and categorizes traveler safety into three distinct tiers:
- **`LOW` (0)**: Normal travel progression within expected spatial and temporal parameters.
- **`MEDIUM` (1)**: Noticeable delay, route deviation (>300m), or single unacknowledged safety check-in.
- **`HIGH` (2)**: Severe deviation (>800m), prolonged unexpected halt in unfamiliar areas, night travel anomaly, multiple missed check-ins, or low battery distress.

---

## 🔬 Feature Vector Specification

| Feature Name | Type | Description |
|---|---|---|
| `hour_of_day` | Integer [0–23] | Current hour of the journey |
| `is_night_travel` | Binary [0/1] | Indicator for transit between 20:00 and 06:00 |
| `deviation_distance_m` | Float | Perpendicular spatial distance from planned corridor (meters) |
| `delay_duration_mins` | Float | Elapsed time minus planned travel duration (minutes) |
| `unexpected_stop_duration_s` | Float | Duration of static halt with velocity near 0 (seconds) |
| `missed_checkins_count` | Integer [0–5] | Number of consecutive safety prompts without response |
| `battery_pct` | Float [0–100] | Current traveler device battery percentage |
| `transit_mode` | Categorical [0–4] | Walk (0), Transit (1), Cab (2), Two-Wheeler (3), Car (4) |

---

## 📂 Directory Layout

```
ml/
├── data/                    # Synthetic and collected journey datasets
│   ├── raw/                 # Raw journey telemetry data (git ignored)
│   └── processed/           # Feature-engineered training and test matrices
├── models/                  # Serialized trained model artifacts (.joblib)
│   └── .gitkeep
├── notebooks/               # Jupyter notebooks for EDA and model tuning
│   └── .gitkeep
├── src/                     # Core training & evaluation source scripts
│   ├── data_generator.py    # Synthetic journey dataset generator
│   ├── train.py             # Random Forest training script & metrics output
│   └── evaluate.py          # Confusion matrix, ROC curve, and feature importance
├── requirements.txt         # ML training dependencies
└── README.md                # ML engine guide (this file)
```

---

## 🛠️ Readiness Status

This directory is structured and ready for model synthesis, dataset training, and evaluation in Phase 6.
