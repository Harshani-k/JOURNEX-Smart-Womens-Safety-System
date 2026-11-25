# JOURNEX – Phase 6: Route Deviation & Unexpected Stop Backend Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Python Flask REST API Deviation & Anomaly Monitoring Subsystem (`backend/`)  
**Date:** November 22, 2026  
**Status:** **PASSED & OPERATIONAL (100% Tests Passing – 88/88 Tests)**  
**Lead Role:** Senior Python Backend Architect  

---

## 1. Executive Summary

Phase 6 extends the JOURNEX backend architecture with mathematical route corridor tracking, multi-observation noise filtering, intelligent unexpected stop detection, and RESTful safety event lifecycle management.

All implementations strictly adhere to:
- [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md)
- [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md)
- [`docs/ROUTE_DEVIATION_DESIGN.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ROUTE_DEVIATION_DESIGN.md)
- [`docs/ROUTE_DEVIATION_API.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ROUTE_DEVIATION_API.md)

### Key Achievements:
- **88 Automated Pytest Tests Passing** (100% test suite pass rate, 0 failures, 0 regressions).
- **Alembic Database Migration (`6ca6163d43d7`):** Created `safety_events` table with comprehensive compound indexes for fast lookups by journey, status, and event type.
- **Spherical Geometry Cross-Track Distance Algorithm:** Implemented Great-Circle cross-track distance ($d_{xt}$) with along-track segment clamping to model a geodesic corridor between origin and destination.
- **Multi-Observation Noise Filtering:** Enforces strict accuracy rejection ($\le 50.0$m) and requires $\ge 3$ consecutive deviated observations to eliminate false alarms from urban GPS multipath reflections.
- **Traffic-Aware Stationary Stop Detection:** Distinguishes stop-and-go progression in heavy traffic ($> 30$m displacement) from sustained vehicle immobility ($< 25$m displacement, $< 0.8$ m/s speed, $\ge 10$ minutes away from destination).
- **Idempotency & Deduplication:** Prevents duplicate active events for the same journey and anomaly type.
- **User Agency & Non-Intrusive Safety Rules:** Safety events do not trigger automatic emergency phone calls or cancel ongoing journeys in Phase 6.

---

## 2. Database Schema & Migration

### 2.1 SafetyEvent Table Definition (`backend/app/models/safety_event.py`)

```python
class SafetyEvent(db.Model):
    __tablename__ = 'safety_events'

    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey('journeys.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = db.Column(db.String(30), nullable=False, index=True)  # 'ROUTE_DEVIATION', 'UNEXPECTED_STOP'
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True)  # 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'
    trigger_reason = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='MEDIUM')  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    deviation_distance = db.Column(db.Float, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    consecutive_count = db.Column(db.Integer, nullable=False, default=1)
    detected_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    acknowledged_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    client_action_id = db.Column(db.String(64), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Indexes:**
- `ix_safety_events_journey_id`: Optimized for querying events by journey.
- `ix_safety_events_user_id`: Scoped user ownership queries.
- `ix_safety_events_event_type`: Filter by anomaly type (`ROUTE_DEVIATION`, `UNEXPECTED_STOP`).
- `ix_safety_events_status`: Filter by lifecycle status.
- `ix_safety_events_journey_status`: Composite index `(journey_id, status)` for instant active incident queries.
- `ix_safety_events_journey_type_status`: Composite index `(journey_id, event_type, status)` for event deduplication.
- `ix_safety_events_client_action_id`: Unique index for idempotent offline reconciliation.

### 2.2 Alembic Migration ID: `6ca6163d43d7`
- Migration script: [`backend/migrations/versions/6ca6163d43d7_create_safety_events_table.py`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/backend/migrations/versions/6ca6163d43d7_create_safety_events_table.py)
- Applied cleanly via `flask db upgrade` in SQLite and verified for MySQL 8.0 DDL compatibility.

---

## 3. Core Algorithms & Service Architecture

### 3.1 Mathematical Distance Service (`backend/app/services/deviation_service.py`)

1. **Haversine Surface Distance:**
   $$d = 2 R \arcsin\left(\sqrt{\sin^2(\Delta\phi/2) + \cos\phi_1\cos\phi_2\sin^2(\Delta\lambda/2)}\right)$$
2. **Spherical Cross-Track Distance:**
   $$d_{xt} = \left|\arcsin\left(\sin\delta_{13} \cdot \sin(\theta_{13} - \theta_{12})\right)\right| \cdot R$$
3. **Along-Track Distance & Segment Clamping:**
   $$d_{at} = \arccos\left(\frac{\cos\delta_{13}}{\cos(d_{xt}/R)}\right) \cdot R$$
   - Projects fixes onto the journey vector $\vec{AB}$. Fixes preceding origin $A$ clamp to $d(A, P)$; fixes extending past destination $B$ clamp to $d(B, P)$.

### 3.2 Multi-Observation Noise Filter
- GPS fixes with reported horizontal accuracy $> 50.0$m are rejected as unviable for corridor analysis.
- Corridors specify a default divergence bound of $300.0$m.
- A deviation event triggers **only** when $\ge 3$ consecutive valid GPS fixes exceed the corridor threshold.

### 3.3 Unexpected Stop Detection Heuristic
- Triggered when:
  1. Fix is farther than $100.0$m from destination.
  2. All fixes over the last $\ge 600$s (10 min) cluster within a maximum pairwise displacement $< 25.0$m.
  3. Average speed over ground remains $< 0.8$ m/s.
- Heavy traffic discrimination: If progressive displacement across the 10-minute window exceeds $30.0$m, the stop detector acknowledges slow movement and suppresses false alarms.

### 3.4 Ingestion Pipeline Integration (`backend/app/services/location_service.py`)
- Location ingestion (`record_journey_location`) automatically invokes `evaluate_safety_anomalies(journey_id, new_location)`.
- Anomalies are committed atomically within the transaction and returned in telemetry response envelopes.

---

## 4. API Endpoints Summary

| HTTP Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/v1/journeys/<id>/safety-events` | Chronological list of all safety events | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/safety-events/active` | Active unresolved anomalies for journey | Bearer JWT |
| `POST` | `/api/v1/journeys/<id>/safety-events/<event_id>/acknowledge` | Acknowledge active warning | Bearer JWT |
| `POST` | `/api/v1/journeys/<id>/safety-events/<event_id>/resolve` | Resolve incident with user notes | Bearer JWT |

---

## 5. Automated Verification Results

### 5.1 Pytest Suite Execution
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend
configfile: pytest.ini
collected 88 items

tests/test_auth.py ............                                          [ 13%]
tests/test_checkin.py .................                                  [ 32%]
tests/test_contacts.py ...........                                       [ 45%]
tests/test_deviation.py ..........                                       [ 56%]
tests/test_gps.py .................                                      [ 76%]
tests/test_journeys.py .....................                             [100%]

============================= 88 passed in 15.90s ==============================
```

### 5.2 Live Integration Script (`backend/verify_phase6_live.py`)
- **Step 1:** Registered test user and acquired JWT token -> **PASS**
- **Step 2:** Created active journey with planned origin and destination -> **PASS**
- **Step 3:** Posted in-corridor GPS fixes; confirmed 0 safety events -> **PASS**
- **Step 4:** Ingested 3 consecutive deviated fixes (480m off corridor); verified `ROUTE_DEVIATION` event created -> **PASS**
- **Step 5:** Verified deduplication; subsequent deviated fixes increment `consecutive_count` without creating duplicate events -> **PASS**
- **Step 6:** Acknowledged active route deviation event -> **PASS**
- **Step 7:** Ingested stationary fixes spanning 14 minutes; verified `UNEXPECTED_STOP` event generated -> **PASS**
- **Step 8:** Resolved unexpected stop event with notes ("Stopped for fuel at Shell") -> **PASS**
- **Step 9:** Verified active safety events endpoint returns 0 active events -> **PASS**

---

## 6. Conclusion

Phase 6 backend implementation is complete, mathematically validated, fully tested with 88 automated tests, and fully operational.
