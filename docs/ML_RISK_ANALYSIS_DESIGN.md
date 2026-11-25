# JOURNEX – Phase 7: Explainable ML Risk Analysis System Design

**Project:** JOURNEX – Smart Women's Safety Check-In and Journey Monitoring System  
**Document:** System Design & Technical Specification  
**Component:** AI/ML Risk Analysis Subsystem (`backend/app/ml/`, `android/`)  
**Version:** 1.0.0  
**Phase:** 7  

---

## 1. System Overview & Problem Statement

Solo travel entails multifaceted dynamic safety risks that cannot be reliably captured by static thresholds alone. A delayed arrival during daytime rush hour may simply represent congested traffic, whereas the same delay combined with an unacknowledged check-in and an off-corridor stationary stop late at night represents compounding risk requiring elevated attention.

The **JOURNEX Explainable ML Risk Analysis Subsystem** introduces:
1. **Scikit-Learn Random Forest Classifier (`RandomForestClassifier`):** Multi-class decision tree ensemble evaluating the probability distribution across four risk categories (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
2. **Objective Telemetry Feature Engineering:** 11 documented non-PII features derived from GPS tracking, compliance check-ins, journey progress, and spatial anomalies.
3. **Strict Privacy & Anti-Bias Boundaries:** User names, phone numbers, contact lists, biometric details, and personal identity attributes are strictly excluded from the feature space.
4. **Calibrated Continuous Risk Score Formulation:** Converts class probabilities into a continuous scalar risk metric $[0.0, 1.0]$ with defined category boundaries.
5. **Human-Centric Explainability Engine:** Generates natural-language contributing factors detailing the specific telemetry observations driving elevated scores.
6. **Non-Intrusive Safety Guarantee:** ML scores provide situational awareness for the traveler. The system **never** automatically calls emergency contacts, dispatches emergency services, or terminates trips.
7. **Transparent Data Limitations:** Explicitly documents that the model is trained on simulated synthetic anomaly distributions and cannot predict criminal intent, violence, or assault.

---

## 2. Model Architecture & Feature Engineering

### 2.1 Model Specifications
- **Framework:** `scikit-learn` (v1.9.1)
- **Algorithm:** `RandomForestClassifier`
- **Hyperparameters:**
  - `n_estimators`: 100 trees
  - `max_depth`: 8 levels (prevents overfitting and ensures interpretable decision paths)
  - `min_samples_split`: 4
  - `min_samples_leaf`: 2
  - `class_weight`: `"balanced"` (handles class imbalances across risk categories)
  - `random_state`: 42 (guarantees training reproducibility)

### 2.2 Input Feature Matrix (11 Documented Features)

| # | Feature Name | Type | Range | Description / Derivation |
|---|---|---|---|---|
| 1 | `missed_checkins_count` | Integer | $[0, 5+]$ | Count of safety check-ins where deadline expired without confirmation. |
| 2 | `pending_checkins_count` | Integer | $[0, 3+]$ | Count of currently active unacknowledged check-in prompts. |
| 3 | `is_delayed` | Binary (0/1) | $\{0, 1\}$ | Whether journey has exceeded expected arrival time (`expected_arrival_time`). |
| 4 | `delay_minutes` | Float | $[0.0, 180.0+]$ | Elapsed minutes past scheduled arrival time ($0.0$ if on schedule). |
| 5 | `route_deviation_count` | Integer | $[0, 6+]$ | Number of active or logged corridor deviation events. |
| 6 | `max_deviation_distance` | Float | $[0.0, 2500.0+]$ | Maximum perpendicular divergence in meters from the planned route line. |
| 7 | `unexpected_stop_count` | Integer | $[0, 5+]$ | Number of stationary stop anomaly events away from destination. |
| 8 | `max_stop_duration_seconds` | Float | $[0.0, 3600.0+]$ | Maximum duration in seconds of stationary vehicle immobility. |
| 9 | `avg_gps_accuracy` | Float | $[3.0, 150.0]$ | Mean horizontal GPS accuracy error in meters over recent location fixes. |
| 10 | `journey_progress_pct` | Float | $[0.0, 100.0]$ | Ratio of displacement from origin toward destination vs total corridor length. |
| 11 | `is_night_journey` | Binary (0/1) | $\{0, 1\}$ | Whether current UTC/local hour falls between 22:00 (10 PM) and 06:00 (6 AM). |

### 2.3 Strict PII Prevention Rule
The feature extraction pipeline operates exclusively on anonymized trip telemetry. Under no circumstances are the following attributes ingested into the model:
- `user_id`, `full_name`, `email`, `phone_number`
- Emergency contact names, phone numbers, or relationships
- Medical notes, allergies, or blood type from safety profiles

---

## 3. Mathematical Scoring & Categorization

### 3.1 Continuous Risk Score Formulation
The model predicts a probability distribution vector across four classes:
$$\vec{P} = [p_{\text{LOW}}, p_{\text{MODERATE}}, p_{\text{HIGH}}, p_{\text{CRITICAL}}], \quad \sum_{i} p_i = 1.0$$

The scalar risk score $S \in [0.0, 1.0]$ is computed as the expected severity index:
$$S = 0.05 \cdot p_{\text{LOW}} + 0.40 \cdot p_{\text{MODERATE}} + 0.70 \cdot p_{\text{HIGH}} + 0.95 \cdot p_{\text{CRITICAL}}$$

### 3.2 Category Threshold Mapping

$$\text{Category} = \begin{cases}
\text{LOW} & \text{if } S < 0.30 \\
\text{MODERATE} & \text{if } 0.30 \le S < 0.55 \\
\text{HIGH} & \text{if } 0.55 \le S < 0.80 \\
\text{CRITICAL} & \text{if } S \ge 0.80
\end{cases}$$

---

## 4. Explainability & Human-Centric Transparency

The system computes local contributing factors based on feature thresholds and tree importance:
- **Missed Check-In:** Impact `CRITICAL` — *"X safety check-in(s) missed without confirmation."*
- **Route Deviation:** Impact `HIGH` — *"Vehicle diverted X meters from planned corridor."*
- **Prolonged Stop:** Impact `HIGH` — *"Stationary stop for X minutes away from destination."*
- **Schedule Delay:** Impact `MODERATE` — *"Travel delayed by X minutes past estimated arrival time."*
- **Degraded GPS:** Impact `LOW` — *"Average GPS horizontal accuracy degraded (X meters error)."*
- **Nighttime Window:** Impact `LOW` — *"Journey occurring during nighttime hours (10:00 PM – 6:00 AM)."*
- **Normal Adherence:** Impact `POSITIVE` — *"Traveler is within planned corridor with prompt check-ins."*

### Insufficient Data State
When a journey is newly created ($< 2$ GPS fixes, no check-in history), the system returns:
- `risk_score`: `0.05`
- `risk_category`: `LOW`
- `is_insufficient_data`: `True`
- `contributing_factors`: `[{"factor": "Insufficient Telemetry", "impact": "NEUTRAL", "description": "Journey recently initiated; insufficient GPS and check-in history to assess risk."}]`

---

## 5. Database Schema & Migration

### 5.1 `risk_analyses` Table Definition
```sql
CREATE TABLE risk_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    journey_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    risk_category TEXT NOT NULL,
    contributing_factors JSON NOT NULL,
    feature_snapshot JSON,
    model_version TEXT NOT NULL,
    analyzed_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(journey_id) REFERENCES journeys(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Indexes:**
- `ix_risk_analyses_journey_id`
- `ix_risk_analyses_user_id`
- `ix_risk_analyses_risk_category`
- `ix_risk_analyses_journey_analyzed` `(journey_id, analyzed_at)`
- `ix_risk_analyses_user_category` `(user_id, risk_category)`

### 5.2 Migration ID: `dcbc4049160d`
Applied cleanly via `flask db upgrade` in SQLite and compatible with MySQL 8.0 DDL.

---

## 6. Safety Policy & Ethical Guardrails

1. **Non-Predictive Disclaimer:** The model calculates statistical divergence from planned journey parameters. It does not predict criminal intent, violence, or assault.
2. **Traveler Agency:** The traveler remains in complete control. Warnings do not silence countdown timers or force SOS triggers.
3. **Zero Autonomous Calling:** The system does not place phone calls or dispatch emergency services.
