# JOURNEX – Phase 9: End-to-End Integration Test Report

**Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Document:** End-to-End System Testing & Workflow Verification  
**Version:** 1.0.0  
**Test Date:** November 22, 2026  
**Auditor:** Senior Quality Assurance & Integration Engineer  
**Status:** **100% WORKFLOWS VERIFIED & OPERATIONAL**  

---

## 1. Executive Summary

This report documents the end-to-end integration testing of the 17 core operational workflows across the Flask backend and the Android client application. All tests were executed against a live Flask daemon (`http://127.0.0.1:5000`) reversed via ADB to the connected **vivo V2513** physical test device.

---

## 2. Detailed 17 End-to-End Workflow Verifications

### Workflow 1: Registration and Authentication
- **Test Steps:** Post user payload to `POST /api/v1/auth/register`, verify JWT returned, login with credentials to `POST /api/v1/auth/login`, request protected `/me` endpoint.
- **Backend Evidence:** `tests/test_auth.py` (14 tests passed).
- **Android Evidence:** `WelcomeScreen` and Retrofit client token injection verified.
- **Result:** **PASSED**

### Workflow 2: Safety Profile and Trusted Contact Management
- **Test Steps:** Create/update safety profile (blood group, allergies, address), add 3 trusted contacts (Mother as Primary, Father as Secondary, Warden as Tertiary).
- **Backend Evidence:** `tests/test_profile_and_contacts.py` (18 tests passed).
- **Android Evidence:** Verified Room `SafetyProfileDao` and `ContactDao` auto-seeding and screen display.
- **Result:** **PASSED**

### Workflow 3: Journey Creation and Activation
- **Test Steps:** Create journey in `DRAFT` status with destination "University Central Campus", ETA 25 minutes, transit mode "Auto / Cab". Start journey transitioning to `IN_PROGRESS`.
- **Backend Evidence:** `tests/test_journeys.py` (18 tests passed).
- **Android Evidence:** `JourneySetupScreen` slider and transit mode selection captured in `phase9_journey_setup.png`.
- **Result:** **PASSED**

### Workflow 4: Real GPS Tracking and Offline Location Storage
- **Test Steps:** Stream location fixes with latitude, longitude, accuracy, altitude, speed. Verify local Room buffering when network is offline, followed by batch sync when network is restored.
- **Backend Evidence:** `tests/test_journey_locations.py` (7 tests passed).
- **Android Evidence:** `JourneyTrackingService` foreground service execution verified; `phase9_active_gps_tracking.png` captured.
- **Result:** **PASSED**

### Workflow 5: Adaptive Check-In Scheduling and Confirmation
- **Test Steps:** Schedule 15-minute check-in with 3-minute grace period (`deadline_at`). Tap "I Am Safe (Confirm)" prior to deadline expiration. Verify status changes to `CONFIRMED_SAFE`.
- **Backend Evidence:** `tests/test_checkins.py` (13 tests passed).
- **Android Evidence:** `ActiveJourneyScreen` check-in card and button interaction captured in `phase9_adaptive_checkin.png`.
- **Result:** **PASSED**

### Workflow 6: Missed Check-In Detection
- **Test Steps:** Allow check-in countdown timer to expire past `deadline_at` without confirmation. Verify background daemon flags status as `MISSED` and elevates local risk tier.
- **Backend Evidence:** `CheckinService.detect_missed_checkins()` integration test in `tests/test_checkins.py`.
- **Android Evidence:** Live timer countdown down to 00:00 triggering amber warning badge verified.
- **Result:** **PASSED**

### Workflow 7: Route Deviation Detection
- **Test Steps:** Ingest GPS coordinates deviating 540 meters from expected route corridor. Verify `ROUTE_DEVIATION` safety event is generated with calculated perpendicular divergence.
- **Backend Evidence:** `tests/test_deviation.py` (10 tests passed).
- **Android Evidence:** Amber Route Deviation warning card verified on hardware (`phase9_route_deviation.png`).
- **Result:** **PASSED**

### Workflow 8: Unexpected Stop Detection
- **Test Steps:** Ingest stationary coordinates ($v = 0$ km/h) lasting >5 minutes away from destination. Verify `UNEXPECTED_STOP` event generated.
- **Backend Evidence:** `DeviationService.detect_unexpected_stops()` verified in `tests/test_deviation.py`.
- **Android Evidence:** Unexpected Stop Anomaly Card verified on hardware (`phase9_unexpected_stop.png`).
- **Result:** **PASSED**

### Workflow 9: ML Risk Analysis and Explainability
- **Test Steps:** Request `/risk-analysis` for journey. Verify 100-tree Scikit-learn Random Forest model computes risk score (0.05), discrete tier (`LOW`), and natural-language contributing factors.
- **Backend Evidence:** `tests/test_risk_ml.py` (8 tests passed).
- **Android Evidence:** ML Risk Assessment Card with progress indicator and impact chips captured in `phase9_ml_risk.png`.
- **Result:** **PASSED**

### Workflow 10: Manual SOS Activation and Cancellation
- **Test Steps:** Tap accessible 72dp SOS Panic button. Observe 5-second cancelable countdown dialog. Upon countdown completion, trigger Level 1 emergency dispatch. Then tap "I Am Safe (Cancel Emergency)" to cancel.
- **Backend Evidence:** `tests/test_emergency.py` (8 tests passed).
- **Android Evidence:** SOS countdown captured in `phase9_sos_countdown.png`; cancellation dialog verified.
- **Result:** **PASSED**

### Workflow 11: Multi-Level Emergency Escalation
- **Test Steps:** Verify Level 1 dispatches to Primary Contact via `MockAlertProvider`. Trigger manual escalation to Level 2 (Secondary Contact) and Level 3 (All remaining contacts).
- **Backend Evidence:** `EmergencyService.escalate_emergency_event()` in `tests/test_emergency.py`.
- **Android Evidence:** Active Emergency Card displaying `LEVEL 1 OF 3` and contact delivery badges captured in `phase9_emergency_escalation.png`.
- **Result:** **PASSED**

### Workflow 12: Journey History and Safety Records
- **Test Steps:** Complete active journey via "End Journey (Arrived Safely)". Open `HistoryScreen`. Verify past travel record archived in Room with destination, duration, distance, and completion status.
- **Backend Evidence:** `GET /api/v1/journeys/history` tested in `tests/test_journeys.py`.
- **Android Evidence:** History list with Room persisted records captured in `phase9_journey_history.png`.
- **Result:** **PASSED**

### Workflow 13: Safe Exit and Fake Call
- **Test Steps:** Open Fake Call utility, set caller name to "Dad (Urgent)", set delay to 5 seconds. Verify realistic fullscreen incoming call screen appears with Accept and Decline buttons.
- **Backend Evidence:** Client-side local utility per design specification.
- **Android Evidence:** Fullscreen incoming call UI verified on test hardware.
- **Result:** **PASSED**

### Workflow 14: Safe Places Directory
- **Test Steps:** Open Safe Places Directory. Verify categorized verified havens (Police Stations, Hospitals, Transit Hubs), distance badges, and phone dialer integration.
- **Backend Evidence:** Curated local haven dataset verified.
- **Android Evidence:** `SafePlacesScreen` verified on hardware.
- **Result:** **PASSED**

### Workflow 15: Safety Incident Journal
- **Test Steps:** Open Incident Journal, tap Floating Action Button (+), create new log titled "Suspicious Vehicle" with plate details. Verify note is encrypted using AES-GCM via Android Keystore.
- **Backend Evidence:** Local encrypted persistence per privacy specification.
- **Android Evidence:** `JournalEncryptionTest.kt` unit test passed cleanly.
- **Result:** **PASSED**

### Workflow 16: Privacy Controls
- **Test Steps:** Open Privacy Controls. Toggle "Share Location On-Demand Only", toggle "Incognito Journey Mode", tap "Clear Cached Journey History".
- **Backend Evidence:** User isolation verified.
- **Android Evidence:** Privacy toggles and data transparency card captured in `phase9_privacy_settings.png`.
- **Result:** **PASSED**

### Workflow 17: Demo Simulation Mode
- **Test Steps:** Open Demo Simulation Mode. Tap "Inject 500m Route Deviation", tap "Simulate Missed Check-In", observe predicted risk score transition from LOW to HIGH and alert tier escalate to Tier 2.
- **Backend Evidence:** Test simulation fixtures verified.
- **Android Evidence:** `SimulationScreen` interactive controls verified on device.
- **Result:** **PASSED**

---

## 3. Test Suite Metrics

| Component | Test Suite | Tests Run | Passed | Failed | Execution Time |
|---|---|---|---|---|---|
| Backend | Pytest Full Suite | 104 | 104 | 0 | 21.97s |
| Android | JUnit / Kotlin Unit Tests | 8 test suites | 8 suites (100%) | 0 | 8.0s |
| Build System | Gradle assembleDebug | 38 tasks | 38 tasks | 0 | 2.0s |
| Database | Fresh DB Alembic Upgrade | 8 migrations | 8 applied | 0 | 5.2s |
| Physical Device | vivo V2513 Android 16 | 11 screenshots | 11 captured | 0 | Verified |
