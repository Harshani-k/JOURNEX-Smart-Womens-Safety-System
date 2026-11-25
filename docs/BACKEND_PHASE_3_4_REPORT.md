# JOURNEX – Phase 3.4: Journey Management Subsystem Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Backend Journey Management Subsystem  
**Date:** November 22, 2026  
**Status:** **PASSED & VERIFIED**  
**Lead Role:** Senior Python Flask Backend Architect  

---

## 1. Executive Summary

Phase 3.4 implements the Journey Management Subsystem for the **JOURNEX** women's safety platform. The subsystem governs destination setup, expected arrival time planning, journey lifecycle state transitions (`DRAFT` -> `ACTIVE` -> `COMPLETED` / `CANCELLED`), active journey monitoring, and historical journey archival.

All implementations strictly adhere to [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md), [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md), and [`docs/JOURNEY_API.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/JOURNEY_API.md).

### Key Accomplishments:
1. **Journey Database Model:** SQLAlchemy `Journey` entity with start/destination metadata, geographic coordinate validation (-90 to 90, -180 to 180), planned/expected schedule datetimes, and actual arrival timestamps.
2. **Indexed Performance:** Single and composite database indexes on `user_id`, `status`, `expected_arrival_time`, and `(user_id, status)`.
3. **Strict Single Active Journey Invariant:** Users can only have at most one active journey at any time. Attempting to start another active journey is rejected with `409 Conflict`.
4. **Lifecycle State Machine:**
   - `POST /api/v1/journeys/<id>/start`: Transitions `DRAFT` -> `ACTIVE`, recording UTC start timestamp.
   - `POST /api/v1/journeys/<id>/complete`: Transitions `ACTIVE` -> `COMPLETED`, recording UTC arrival timestamp.
   - `POST /api/v1/journeys/<id>/cancel`: Transitions `DRAFT` or `ACTIVE` -> `CANCELLED`, recording optional cancellation reason.
5. **Active Journey & History Separation:**
   - `GET /api/v1/journeys/active`: Instant retrieval of ongoing journey.
   - `GET /api/v1/journeys/history`: Paginated archive of completed and cancelled journeys.
6. **Security & Mass Assignment Defense:**
   - Every endpoint requires valid JWT authentication.
   - Modification of system-controlled fields (`user_id`, `status`, timestamps) is blocked.
   - Accessing another user's journey returns `404 Not Found`.
7. **Database Migration:** Alembic revision `b251f960ce2f` created the `journeys` table and applied cleanly to SQLite.
8. **Automated Testing:** Pytest suite expanded to **58 tests** passing with 100% success rate, verified via live HTTP dev server tests.

---

## 2. Directory Structure & New Modules

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py            # Export User, TokenBlocklist, SafetyProfile, TrustedContact, Journey
│   │   ├── journey.py             # Journey model with lifecycle status & coordinates
│   │   ├── safety_profile.py
│   │   ├── token_blocklist.py
│   │   ├── trusted_contact.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── contacts.py
│   │   └── journeys.py            # Journey endpoints (/api/v1/journeys/*)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── health_service.py
│   │   ├── auth_service.py
│   │   ├── profile_service.py
│   │   ├── contact_service.py
│   │   └── journey_service.py     # Journey lifecycle & pagination service
│   ├── utils/
│   │   ├── errors.py
│   │   ├── exceptions.py
│   │   ├── response.py
│   │   └── validators.py          # Coordinates, schedule & cancellation validation
│   ├── __init__.py                # App factory + Blueprints
│   ├── config.py
│   └── extensions.py
├── instance/
│   └── journex.db                 # SQLite development database (migrated)
├── migrations/
│   └── versions/
│       ├── 9a17e1c634bf_create_users_and_token_blocklist_tables.py
│       ├── 67dcd911cc90_create_safety_profiles_and_trusted_.py
│       └── b251f960ce2f_create_journeys_table.py
└── tests/
    ├── conftest.py
    ├── test_app_init.py           # Factory initialization tests (2 tests)
    ├── test_auth.py               # Authentication tests (14 tests)
    ├── test_config.py             # Configuration tests (3 tests)
    ├── test_errors.py             # Error envelope tests (2 tests)
    ├── test_health.py             # Health check test (1 test)
    ├── test_profile_and_contacts.py # Profile & Contacts tests (18 tests)
    └── test_journeys.py           # Journey lifecycle tests (18 tests)
```

---

## 3. Database Migration Details

Migration revision: `b251f960ce2f_create_journeys_table.py`

### Generated DDL:
```sql
CREATE TABLE journeys (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    journey_title VARCHAR(150) NOT NULL,
    start_location_name VARCHAR(150) NOT NULL,
    start_location_address VARCHAR(255) NOT NULL,
    start_latitude FLOAT,
    start_longitude FLOAT,
    destination_name VARCHAR(150) NOT NULL,
    destination_address VARCHAR(255) NOT NULL,
    destination_latitude FLOAT,
    destination_longitude FLOAT,
    planned_start_time DATETIME NOT NULL,
    expected_arrival_time DATETIME NOT NULL,
    actual_start_time DATETIME,
    actual_arrival_time DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    cancellation_reason VARCHAR(255),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_journeys_user_id ON journeys (user_id);
CREATE INDEX ix_journeys_status ON journeys (status);
CREATE INDEX ix_journeys_expected_arrival_time ON journeys (expected_arrival_time);
CREATE INDEX ix_journeys_user_status ON journeys (user_id, status);
```

---

## 4. Test Suite Execution (`pytest`)

The complete backend test suite contains **58 tests** with a **100% pass rate**:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend
configfile: pytest.ini
collecting ... collected 58 items

tests/test_app_init.py::test_app_creation_default PASSED                 [  1%]
tests/test_app_init.py::test_app_creation_testing PASSED                 [  3%]
tests/test_auth.py::test_successful_registration PASSED                  [  5%]
tests/test_auth.py::test_duplicate_email_rejection PASSED                [  6%]
tests/test_auth.py::test_invalid_email_rejection PASSED                  [  8%]
tests/test_auth.py::test_weak_password_rejection PASSED                  [ 10%]
tests/test_auth.py::test_successful_login PASSED                         [ 12%]
tests/test_auth.py::test_incorrect_password PASSED                       [ 13%]
tests/test_auth.py::test_unknown_user_login PASSED                       [ 15%]
tests/test_auth.py::test_access_without_token PASSED                     [ 17%]
tests/test_auth.py::test_access_with_valid_token PASSED                  [ 18%]
tests/test_auth.py::test_expired_token PASSED                            [ 20%]
tests/test_auth.py::test_logout_and_token_revocation PASSED              [ 22%]
tests/test_auth.py::test_refresh_token_lifecycle PASSED                  [ 24%]
tests/test_auth.py::test_user_data_isolation PASSED                      [ 25%]
tests/test_auth.py::test_rate_limiting_on_login PASSED                   [ 27%]
tests/test_config.py::test_development_config PASSED                     [ 29%]
tests/test_config.py::test_testing_config PASSED                         [ 31%]
tests/test_config.py::test_production_config PASSED                      [ 32%]
tests/test_errors.py::test_404_not_found PASSED                          [ 34%]
tests/test_errors.py::test_405_method_not_allowed PASSED                 [ 36%]
tests/test_health.py::test_health_check_endpoint PASSED                  [ 37%]
tests/test_journeys.py::test_journeys_unauthenticated_access PASSED      [ 39%]
tests/test_journeys.py::test_create_journey_success PASSED               [ 41%]
tests/test_journeys.py::test_create_journey_missing_required_fields PASSED [ 43%]
tests/test_journeys.py::test_create_journey_invalid_coordinates PASSED   [ 44%]
tests/test_journeys.py::test_create_journey_invalid_datetime PASSED      [ 46%]
tests/test_journeys.py::test_create_journey_arrival_before_start PASSED  [ 48%]
tests/test_journeys.py::test_create_journey_mass_assignment_rejection PASSED [ 50%]
tests/test_journeys.py::test_list_journeys_and_pagination PASSED         [ 51%]
tests/test_journeys.py::test_retrieve_individual_journey PASSED          [ 53%]
tests/test_journeys.py::test_user_ownership_isolation PASSED             [ 55%]
tests/test_journeys.py::test_update_draft_journey PASSED                 [ 56%]
tests/test_journeys.py::test_start_journey_lifecycle PASSED              [ 58%]
tests/test_journeys.py::test_reject_multiple_active_journeys PASSED      [ 60%]
tests/test_journeys.py::test_get_active_journey PASSED                   [ 62%]
tests/test_journeys.py::test_complete_active_journey PASSED              [ 63%]
tests/test_journeys.py::test_cancel_draft_and_active_journey PASSED      [ 65%]
tests/test_journeys.py::test_invalid_lifecycle_transitions PASSED        [ 67%]
tests/test_journeys.py::test_journey_history_endpoint PASSED             [ 68%]
tests/test_profile_and_contacts.py::test_profile_unauthenticated_access PASSED [ 70%]
tests/test_profile_and_contacts.py::test_profile_not_created_yet PASSED  [ 72%]
tests/test_profile_and_contacts.py::test_create_profile_success PASSED   [ 74%]
tests/test_profile_and_contacts.py::test_reject_duplicate_profile PASSED [ 75%]
tests/test_profile_and_contacts.py::test_retrieve_profile PASSED         [ 77%]
tests/test_profile_and_contacts.py::test_update_profile PASSED           [ 79%]
tests/test_profile_and_contacts.py::test_profile_validation_and_mass_assignment PASSED [ 81%]
tests/test_profile_and_contacts.py::test_profile_user_isolation PASSED   [ 82%]
tests/test_profile_and_contacts.py::test_contacts_unauthenticated_access PASSED [ 84%]
tests/test_profile_and_contacts.py::test_add_and_list_contacts PASSED    [ 86%]
tests/test_profile_and_contacts.py::test_get_individual_contact PASSED   [ 87%]
tests/test_profile_and_contacts.py::test_update_contact PASSED           [ 89%]
tests/test_profile_and_contacts.py::test_delete_contact PASSED           [ 91%]
tests/test_profile_and_contacts.py::test_primary_contact_setting_and_uniqueness PASSED [ 93%]
tests/test_profile_and_contacts.py::test_reject_duplicate_phone_for_same_user PASSED [ 94%]
tests/test_profile_and_contacts.py::test_reject_more_than_5_contacts PASSED [ 96%]
tests/test_profile_and_contacts.py::test_contact_validation PASSED       [ 98%]
tests/test_profile_and_contacts.py::test_contacts_user_isolation PASSED  [100%]

============================= 58 passed in 9.26s ==============================
```

---

## 5. Live Server HTTP Verification

The live dev server (`0.0.0.0:5000`) was verified through PowerShell `Invoke-RestMethod`:
1. `POST /api/v1/journeys` -> Created Journey 1 in `DRAFT` status (`201 Created`).
2. `PUT /api/v1/journeys/<id>` -> Updated Journey 1 while in `DRAFT` status (`200 OK`).
3. `POST /api/v1/journeys/<id>/start` -> Started Journey 1, transitioning to `ACTIVE` and recording `actual_start_time` (`200 OK`).
4. `GET /api/v1/journeys/active` -> Verified Journey 1 returned as the ongoing journey (`200 OK`).
5. `POST /api/v1/journeys` -> Created Journey 2 in `DRAFT` status (`201 Created`).
6. `POST /api/v1/journeys/<id2>/start` -> Attempted to start Journey 2 while Journey 1 was active -> Rejected with `409 Conflict`.
7. `POST /api/v1/journeys/<id>/complete` -> Completed Journey 1, recording `actual_arrival_time` (`200 OK`).
8. `POST /api/v1/journeys/<id2>/cancel` -> Cancelled Journey 2 with cancellation reason (`200 OK`).
9. `GET /api/v1/journeys/history` -> Confirmed both completed Journey 1 and cancelled Journey 2 appear in history with pagination (`200 OK`).

---

## 6. Known Limitations & Next Steps (Phase 4)

- **Live GPS Tracking & Deviation Detection:** Deferred to Phase 4 (GPS-based journey monitoring and route deviation detection).
- **Adaptive Check-In Engine:** Check-in prompts based on ETA and journey progress will be implemented in Phase 5.
- **Machine Learning Integration:** Random Forest risk scoring using delay, deviation, and time-of-day features is reserved for Phase 6.
