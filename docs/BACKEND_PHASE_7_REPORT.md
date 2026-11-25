# JOURNEX – Phase 7: Explainable ML Risk Analysis Backend Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Python Flask REST API Risk Analysis Subsystem (`backend/`)  
**Date:** November 22, 2026  
**Status:** **PASSED & OPERATIONAL (100% Tests Passing – 96/96 Tests)**  
**Lead Role:** Senior Python Backend Architect  

---

## 1. Executive Summary

Phase 7 delivers an explainable Machine Learning risk analysis engine integrated into the JOURNEX backend. The subsystem processes real-time GPS telemetry, compliance check-ins, route deviations, and journey delays using a Scikit-learn Random Forest Classifier to quantify situational travel risk.

All implementations strictly adhere to:
- [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md)
- [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md)
- [`docs/ML_RISK_ANALYSIS_DESIGN.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ML_RISK_ANALYSIS_DESIGN.md)
- [`docs/ML_MODEL_EVALUATION.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ML_MODEL_EVALUATION.md)

### Key Achievements:
- **96 Automated Pytest Tests Passing** (100% test suite pass rate, 0 failures, 0 regressions).
- **Alembic Database Migration (`dcbc4049160d`):** Created `risk_analyses` table with composite and single-column indexes for fast historical lookups and user isolation.
- **Scikit-learn Random Forest Model:** Serialized 100-tree model (`risk_model.joblib`) with versioned feature schema and model metadata.
- **Privacy Enforcement:** Zero PII (identities, contact numbers, names) in model features. All 11 features represent objective travel telemetry and spatial compliance.
- **Explainability & Natural-Language Attributions:** Automatically computes key contributing factors with impact ratings (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`, `POSITIVE`).
- **Non-Redundant Inference Engine:** Caches recent inferences and bypasses model execution when telemetry has not changed, optimizing server throughput.
- **Ethical Safeguards:** Explicitly disclaims assault prediction; never initiates autonomous phone calls, SMS broadcasts, or trip cancellations.

---

## 2. Database Schema & Migration

### 2.1 RiskAnalysis Table Definition (`backend/app/models/risk_analysis.py`)

```python
class RiskAnalysis(db.Model):
    __tablename__ = "risk_analyses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journey_id = db.Column(db.Integer, db.ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    risk_category = db.Column(db.String(20), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    contributing_factors = db.Column(db.JSON, nullable=False)
    feature_snapshot = db.Column(db.JSON, nullable=True)
    model_version = db.Column(db.String(30), nullable=False, default="1.0.0-rf")
    analyzed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
```

**Indexes:**
- `ix_risk_analyses_journey_id`: Fast lookups by journey.
- `ix_risk_analyses_user_id`: Scoped user queries.
- `ix_risk_analyses_risk_category`: Categorical filtering.
- `ix_risk_analyses_journey_analyzed`: Composite index `(journey_id, analyzed_at)` for latest analysis queries.
- `ix_risk_analyses_user_category`: Composite index `(user_id, risk_category)` for traveler analytics.

### 2.2 Alembic Migration ID: `dcbc4049160d`
- Generated file: [`backend/migrations/versions/dcbc4049160d_create_risk_analyses_table.py`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/backend/migrations/versions/dcbc4049160d_create_risk_analyses_table.py)
- Applied cleanly via `flask db upgrade` in SQLite and verified for MySQL 8.0 DDL compatibility.

---

## 3. Machine Learning Architecture (`backend/app/ml/`)

```
backend/app/ml/
├── __init__.py               # Exports feature names and label constants
├── dataset_generator.py      # Reproducible synthetic dataset generator (4,000 samples)
├── train.py                  # Random Forest trainer, evaluator, artifact exporter
├── predictor.py              # Singleton inference engine, feature extractor, explainability generator
└── models/
    ├── risk_model.joblib     # Serialized Scikit-learn model artifact
    ├── feature_names.json    # Feature schema array (11 features)
    └── model_meta.json       # Version, training metrics, and disclaimer metadata
```

### 3.1 Feature Extraction Pipeline
1. `missed_checkins_count` (int): Number of check-ins in `MISSED` state.
2. `pending_checkins_count` (int): Active unconfirmed check-ins in `SCHEDULED` or `REMINDED` state.
3. `is_delayed` (binary 0/1): Journey delay status flag.
4. `delay_minutes` (float): Elapsed minutes past expected arrival time.
5. `route_deviation_count` (int): Active corridor deviation incidents.
6. `max_deviation_distance` (float): Maximum perpendicular deviation in meters.
7. `unexpected_stop_count` (int): Active stationary stop incidents.
8. `max_stop_duration_seconds` (float): Duration in seconds of vehicle immobility.
9. `avg_gps_accuracy` (float): Average horizontal GPS error over recent fixes.
10. `journey_progress_pct` (float): Percentage of route distance covered towards destination.
11. `is_night_journey` (binary 0/1): Indicator for travel between 10:00 PM and 6:00 AM.

---

## 4. REST API Endpoints Summary

| HTTP Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/journeys/<id>/risk-analysis` | Execute on-demand or periodic ML risk evaluation | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/risk-analysis/latest` | Retrieve latest analysis (or compute baseline if none) | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/risk-analysis/history` | Retrieve chronological evaluation history | Bearer JWT |

---

## 5. Verification Results

### 5.1 Complete Pytest Execution (96 Tests Passing)

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend
configfile: pytest.ini
collected 96 items

tests\test_app_init.py ..                                                [  2%]
tests\test_auth.py ..............                                        [ 16%]
tests\test_checkins.py .............                                     [ 30%]
tests\test_config.py ...                                                 [ 33%]
tests\test_deviation.py ..........                                       [ 43%]
tests\test_errors.py ..                                                  [ 45%]
tests\test_health.py .                                                   [ 46%]
tests\test_journey_locations.py .......                                  [ 54%]
tests\test_journeys.py ..................                                [ 72%]
tests\test_profile_and_contacts.py ..................                    [ 91%]
tests\test_risk_ml.py ........                                           [100%]

============================= 96 passed in 17.21s =============================
```

### 5.2 Live Backend Integration Script (`backend/verify_phase7_live.py`)
- **Step 1:** Registered test user and acquired JWT token -> **PASS**
- **Step 2:** Created and started active journey (Peelamedu) -> **PASS**
- **Step 3:** Baseline risk evaluation on empty journey; confirmed `LOW` category (`score=0.05`) with insufficient telemetry banner -> **PASS**
- **Step 4:** Ingested in-corridor GPS fixes and confirmed safe check-in; confirmed normal travel `LOW` risk -> **PASS**
- **Step 5:** Ingested 3 consecutive deviated fixes (907m divergence); confirmed risk elevated to `HIGH` (`score=0.6862`) with route deviation factor -> **PASS**
- **Step 6:** Verified `GET /risk-analysis/latest` returned matching active analysis -> **PASS**
- **Step 7:** Verified `GET /risk-analysis/history` returned all historical evaluation records -> **PASS**

---

## 6. Conclusion

Phase 7 backend implementation is complete, mathematically sound, fully covered by automated regression tests, and operational against the live Flask API server.
