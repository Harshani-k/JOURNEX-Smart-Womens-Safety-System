"""
JOURNEX – Synthetic Journey Risk Dataset Generator
Phase 7: Explainable ML Risk Analysis

Generates reproducible, realistic synthetic travel telemetry scenarios for training
the Random Forest risk classifier.

IMPORTANT LIMITATION & DISCLAIMER:
This dataset is purely synthetic and rule-generated to model simulated travel anomalies
(missed check-ins, route divergence, vehicle stops, GPS degradation, delays).
It does NOT reflect real-world crime incidence, assault prediction, or production safety guarantees.
"""

import os
import json
import numpy as np

FEATURE_NAMES = [
    "missed_checkins_count",
    "pending_checkins_count",
    "is_delayed",
    "delay_minutes",
    "route_deviation_count",
    "max_deviation_distance",
    "unexpected_stop_count",
    "max_stop_duration_seconds",
    "avg_gps_accuracy",
    "journey_progress_pct",
    "is_night_journey"
]

RISK_LABELS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
LABEL_MAP = {name: idx for idx, name in enumerate(RISK_LABELS)}
REV_LABEL_MAP = {idx: name for idx, name in enumerate(RISK_LABELS)}

def generate_synthetic_data(n_samples: int = 4000, random_seed: int = 42):
    """
    Generate synthetic journey feature matrix X and risk target vector y.
    Scenarios simulated:
    1. Normal safe journey (40%) -> LOW
    2. Minor friction: traffic delay, single unconfirmed check-in, noisy GPS (25%) -> MODERATE
    3. Elevated concern: route deviation or unexpected stop (20%) -> HIGH
    4. Severe compounding risk: missed check-in + off-route or prolonged stop (15%) -> CRITICAL
    """
    rng = np.random.RandomState(random_seed)

    n_low = int(n_samples * 0.40)
    n_mod = int(n_samples * 0.25)
    n_high = int(n_samples * 0.20)
    n_crit = n_samples - (n_low + n_mod + n_high)

    X_list = []
    y_list = []

    # 1. LOW Risk Scenarios
    for _ in range(n_low):
        missed = 0
        pending = rng.choice([0, 1], p=[0.85, 0.15])
        is_delayed = 0
        delay_min = 0.0
        route_dev = 0
        max_dev = rng.uniform(0.0, 120.0)  # Normal corridor jitter well below 300m
        unexp_stop = 0
        stop_dur = rng.uniform(0.0, 180.0)  # Brief traffic light / intersection
        gps_acc = rng.uniform(4.0, 22.0)    # Good GPS fix
        prog_pct = rng.uniform(10.0, 95.0)
        is_night = rng.choice([0, 1], p=[0.75, 0.25])

        X_list.append([
            missed, pending, is_delayed, delay_min, route_dev,
            max_dev, unexp_stop, stop_dur, gps_acc, prog_pct, is_night
        ])
        y_list.append(LABEL_MAP["LOW"])

    # 2. MODERATE Risk Scenarios
    for _ in range(n_mod):
        missed = 0
        pending = rng.choice([0, 1, 2], p=[0.4, 0.45, 0.15])
        is_delayed = rng.choice([0, 1], p=[0.3, 0.7])
        delay_min = float(rng.uniform(5.0, 35.0)) if is_delayed else 0.0
        route_dev = 0
        max_dev = rng.uniform(50.0, 280.0)   # Close to boundary but not breaching 300m threshold
        unexp_stop = 0
        stop_dur = rng.uniform(120.0, 480.0) # Up to 8 min stop (not breaching 10m threshold)
        gps_acc = rng.uniform(15.0, 65.0)    # Moderate / noisy GPS
        prog_pct = rng.uniform(5.0, 90.0)
        is_night = rng.choice([0, 1], p=[0.6, 0.4])

        X_list.append([
            missed, pending, is_delayed, delay_min, route_dev,
            max_dev, unexp_stop, stop_dur, gps_acc, prog_pct, is_night
        ])
        y_list.append(LABEL_MAP["MODERATE"])

    # 3. HIGH Risk Scenarios
    for _ in range(n_high):
        # Either route deviation, unexpected stop, or missed check-in alone
        anomaly_type = rng.choice(["dev", "stop", "missed_delay"])
        
        if anomaly_type == "dev":
            missed = rng.choice([0, 1], p=[0.8, 0.2])
            pending = rng.choice([0, 1], p=[0.5, 0.5])
            is_delayed = rng.choice([0, 1], p=[0.5, 0.5])
            delay_min = float(rng.uniform(5.0, 45.0)) if is_delayed else 0.0
            route_dev = rng.randint(1, 4)
            max_dev = rng.uniform(350.0, 1200.0)  # Clearly off route corridor
            unexp_stop = 0
            stop_dur = rng.uniform(0.0, 300.0)
        elif anomaly_type == "stop":
            missed = rng.choice([0, 1], p=[0.8, 0.2])
            pending = rng.choice([0, 1], p=[0.5, 0.5])
            is_delayed = 1
            delay_min = float(rng.uniform(15.0, 50.0))
            route_dev = 0
            max_dev = rng.uniform(20.0, 200.0)
            unexp_stop = rng.randint(1, 3)
            stop_dur = rng.uniform(600.0, 1800.0) # 10 to 30 mins stopped
        else: # missed checkin with delay
            missed = 1
            pending = 0
            is_delayed = 1
            delay_min = float(rng.uniform(20.0, 60.0))
            route_dev = 0
            max_dev = rng.uniform(20.0, 200.0)
            unexp_stop = 0
            stop_dur = rng.uniform(60.0, 400.0)

        gps_acc = rng.uniform(10.0, 55.0)
        prog_pct = rng.uniform(15.0, 85.0)
        is_night = rng.choice([0, 1], p=[0.5, 0.5])

        X_list.append([
            missed, pending, is_delayed, delay_min, route_dev,
            max_dev, unexp_stop, stop_dur, gps_acc, prog_pct, is_night
        ])
        y_list.append(LABEL_MAP["HIGH"])

    # 4. CRITICAL Risk Scenarios
    for _ in range(n_crit):
        # Multiple compounding failures: missed checkin + off route + prolonged stop
        missed = rng.randint(1, 4)
        pending = rng.choice([0, 1, 2], p=[0.3, 0.4, 0.3])
        is_delayed = 1
        delay_min = float(rng.uniform(30.0, 150.0))
        route_dev = rng.randint(1, 5)
        max_dev = rng.uniform(450.0, 2500.0)
        unexp_stop = rng.randint(1, 4)
        stop_dur = rng.uniform(700.0, 3600.0)
        gps_acc = rng.uniform(15.0, 90.0)
        prog_pct = rng.uniform(10.0, 80.0)
        is_night = rng.choice([0, 1], p=[0.3, 0.7])  # Frequently late at night

        X_list.append([
            missed, pending, is_delayed, delay_min, route_dev,
            max_dev, unexp_stop, stop_dur, gps_acc, prog_pct, is_night
        ])
        y_list.append(LABEL_MAP["CRITICAL"])

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int64)

    # Shuffle
    indices = rng.permutation(len(y))
    X = X[indices]
    y = y[indices]

    return X, y

if __name__ == "__main__":
    X, y = generate_synthetic_data()
    print(f"Generated synthetic dataset: X={X.shape}, y={y.shape}")
    for cat in RISK_LABELS:
        count = np.sum(y == LABEL_MAP[cat])
        print(f"  {cat}: {count} ({count/len(y)*100:.1f}%)")
