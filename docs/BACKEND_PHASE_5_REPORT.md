# JOURNEX – Phase 5: Adaptive Safety Check-In & Missed Check-In Backend Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Python Flask REST API Check-In & Delay Monitoring Subsystem (`backend/`)  
**Date:** November 22, 2026  
**Status:** **PASSED & OPERATIONAL (100% Tests Passing – 78/78 Tests)**  
**Lead Role:** Senior Python Backend Architect  

---

## 1. Executive Summary

Phase 5 extends the JOURNEX backend with an adaptive, deterministic safety check-in engine, automated journey delay detection, and server-authoritative missed check-in escalation.

All implementations strictly adhere to:
- [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md)
- [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md)
- [`docs/CHECKIN_API.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/CHECKIN_API.md)
- [`docs/ADAPTIVE_CHECKIN_DESIGN.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ADAPTIVE_CHECKIN_DESIGN.md)

### Key Achievements:
- **78 Automated Pytest Tests Passing** (100% test suite pass rate, 0 failures, 0 regressions).
- **Alembic Database Migration:** Created `checkins` table with composite indexes and added `is_delayed` and `delayed_at` columns to `journeys`.
- **Deterministic Rule-Based Scheduler:** Automatically reduces check-in intervals from 15–30 minutes down to 5–10 minutes upon detected journey delays.
- **Authoritative Missed Check-In Detection:** Enforces strict response deadlines; transitions unconfirmed check-ins to `MISSED` and returns HTTP 409 Conflict for late client confirmations.
- **RESTful Resource Design:** Fully authenticated, user-scoped endpoints with standardized JSON envelopes and domain exception mapping.

---

## 2. Database Schema & Alembic Migration

### 2.1 CheckIn Table Definition (`backend/app/models/checkin.py`)

```python
class CheckIn(db.Model):
    __tablename__ = 'checkins'

    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey('journeys.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=False)
    deadline_at = db.Column(db.DateTime(timezone=True), nullable=False)
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='SCHEDULED', index=True)
    response_type = db.Column(db.String(30), nullable=True)
    reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    client_action_id = db.Column(db.String(64), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Indexes:**
- `ix_checkins_journey_id`: Optimized for querying check-ins by active journey.
- `ix_checkins_user_id`: Scoped user queries.
- `ix_checkins_status`: Filter by `SCHEDULED`, `REMINDED`, `CONFIRMED_SAFE`, `MISSED`.
- `ix_checkins_journey_status`: Composite index `(journey_id, status)` for fast pending check-in lookups.
- `ix_checkins_status_deadline`: Composite index `(status, deadline_at)` for instant execution of `detect-missed` sweep.
- `ix_checkins_client_action_id`: Unique index for idempotent offline action synchronization.

### 2.2 Journey Delay Columns (`backend/app/models/journey.py`)

Added to `journeys` table:
- `is_delayed`: `Boolean`, default `False` (`server_default='0'`), index `True`.
- `delayed_at`: `DateTime(timezone=True)`, nullable `True`.

### 2.3 Migration ID: `c9e97124996b`
- Applied cleanly via `flask db upgrade` in SQLite and fully compatible with MySQL 8.0 DDL syntax.

---

## 3. Backend Services & Business Logic

### 3.1 Adaptive Scheduler (`backend/app/services/checkin_scheduler.py`)
- Calculates dynamic check-in intervals:
  - Default Active Journey: 15–30 minutes based on journey expected duration.
  - Delayed Journey: 5–10 minutes (shortened frequency).
- Automatically calculates response deadline: `deadline_at = scheduled_at + grace_period` (default: 3 minutes / 180 seconds).

### 3.2 Check-In Lifecycle Service (`backend/app/services/checkin_service.py`)
- `schedule_checkin(journey_id, user_id, scheduled_at, deadline_at, client_action_id)`: Enforces active journey ownership and persists window.
- `get_journey_checkins(journey_id, user_id)`: Chronologically ordered check-in history.
- `get_pending_checkin(journey_id, user_id)`: Returns the currently active `SCHEDULED` or `REMINDED` check-in.
- `confirm_safety(checkin_id, user_id, responded_at, response_type, client_action_id)`:
  - If already `CONFIRMED_SAFE`: Returns 200 OK idempotently.
  - If current time exceeds `deadline_at` or check-in is `MISSED`: Rejects late confirmation with **HTTP 409 Conflict** (`Check-in deadline has expired. Marked as MISSED.`).
  - Otherwise: Transitions to `CONFIRMED_SAFE` and records response metadata.
- `detect_and_mark_missed_checkins()`: Periodic or on-demand sweep that finds all active check-ins where `deadline_at < now` and marks them as `MISSED`.

### 3.3 Delay Monitoring Service (`backend/app/services/delay_service.py`)
- `evaluate_journey_delay(journey)`: Compares `expected_arrival_time` against current UTC time. Flags `is_delayed = True` if exceeded.
- `detect_delayed_journeys()`: System-wide sweep marking all overdue active journeys as delayed.
- `get_journey_delay_summary(journey_id, user_id)`: Returns current delay status and elapsed delay minutes.

---

## 4. API Endpoints Summary

| HTTP Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/journeys/<id>/checkins` | Schedule a routine safety check-in | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/checkins` | Retrieve all check-ins for journey | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/checkins/pending` | Retrieve current pending check-in | Bearer JWT |
| `GET` | `/api/v1/journeys/<id>/delay` | Get real-time delay status & minutes | Bearer JWT |
| `POST` | `/api/v1/journeys/detect-delayed` | Sweep and flag overdue journeys | Bearer JWT |
| `POST` | `/api/v1/checkins/<id>/confirm` | Confirm traveler safety ("I Am Safe") | Bearer JWT |
| `POST` | `/api/v1/checkins/<id>/cancel` | Cancel an unexpired check-in | Bearer JWT |
| `POST` | `/api/v1/checkins/detect-missed` | Sweep and mark expired check-ins as MISSED | Bearer JWT |

---

## 5. Automated Test Suite Results

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend
configfile: pytest.ini
collected 78 items

tests\test_app_init.py ....                                              [  5%]
tests\test_auth.py ....................                                  [ 30%]
tests\test_checkins.py .............                                     [ 47%]
tests\test_config.py ...                                                 [ 51%]
tests\test_contacts.py ...........                                       [ 65%]
tests\test_errors.py ..                                                  [ 67%]
tests\test_gps_telemetry.py ............                                 [ 83%]
tests\test_health.py .                                                   [ 84%]
tests\test_journeys.py ............                                      [100%]

============================= 78 passed in 14.85s ==============================
```

All 78 unit and integration tests passed with 100% success rate.

---

## 6. Live API Verification Script Execution

Command:
```powershell
cd backend; .\.venv\Scripts\python.exe verify_phase5_live.py
```

Console Output:
```
=== STARTING LIVE BACKEND CHECK-IN VERIFICATION ===
[OK] Step 1: User registered & logged in: traveler_p5_1795349110@journex.org
[OK] Step 2 & 3: Journey created and started. ID=3, Status=ACTIVE
[OK] Step 4 & 5: Check-in scheduled: ID=1, status=SCHEDULED, scheduled_at=2026-11-22T12:15:10.624896, deadline_at=2026-11-22T12:18:10.624896
[OK] Step 6: Pending check-in retrieved successfully.
[OK] Step 7 & 8: Safety confirmed and recorded: status=CONFIRMED_SAFE, responded_at=2026-11-22T12:05:10.651491
[OK] Step 9: detect-missed executed: detected 1 missed check-in(s)
[OK] Step 9 Verified: Check-in 2 transitioned to MISSED status past its deadline.
[OK] Step 10: Journey remains ACTIVE after missed check-in (requires explicit user action to complete or cancel). Status=ACTIVE

ALL 10 VERIFICATION STEPS PASSED PERFECTLY ON LIVE BACKEND!
```

---

## 7. Known Limitations & Scope Boundaries

1. **Phase Boundary:** Phase 5 covers adaptive rule-based check-ins, missed check-in detection, and journey delay detection. Machine learning risk scoring (Phase 6) and automated emergency dispatch (Phase 7) are explicitly not implemented.
2. **Periodic Detection Execution:** `detect-missed` and `detect-delayed` can be triggered on demand via REST API or via cron/Celery background scheduler.

