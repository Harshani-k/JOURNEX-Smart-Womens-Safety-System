# PROJECT DEVELOPMENT ROADMAP & TESTING MILESTONES

# JOURNEX: Smart Women's Safety Check-In and Journey Monitoring System

This document outlines the phased development roadmap, implementation tasks, and rigorous verification milestones for the complete delivery of the JOURNEX system.

---

## Phase Overview & Progress Tracker

- [x] **Phase 0: Workspace Setup & Architectural Foundation** *(Current)*
- [ ] **Phase 1: Backend Foundation & Database Schema Setup**
- [ ] **Phase 2: Android Project Initialization & Core Navigation**
- [ ] **Phase 3: User Authentication & Personal Safety Profile (Features 1–3)**
- [ ] **Phase 4: Journey Configuration & GPS Foreground Tracking (Features 4–5)**
- [ ] **Phase 5: Adaptive Check-In & Anomaly Detection (Features 6–8)**
- [ ] **Phase 6: Machine Learning Risk Assessment Engine (Feature 9)**
- [ ] **Phase 7: Emergency Alert Escalation & SOS Calling (Features 10–12)**
- [ ] **Phase 8: History, Safe Places, Incident Journal & Utilities (Features 13–16)**
- [ ] **Phase 9: Privacy Controls, Simulation Engine & Comprehensive Verification (Features 17–18)**
- [ ] **Phase 10: Final Documentation, Viva Demonstration & Deployment Preparation**

---

## Detailed Phase Breakdown

### Phase 0: Workspace Setup & Architectural Foundation
- **Goal:** Establish clean monorepo architecture, comprehensive engineering documentation, and directory readiness.
- **Tasks:**
  - Verify workspace cleanliness.
  - Define root configuration and `.gitignore`.
  - Author detailed documentation (`PROJECT_SPEC.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md`).
  - Prepare isolated directories for `android/`, `backend/`, and `ml/`.
- **Milestone Verification:** Project structure inspectable, ready for Android Studio and Python virtual environments without conflicting dependencies.

### Phase 1: Backend Foundation & Database Schema Setup
- **Goal:** Scaffold the Flask REST microservice, SQLAlchemy ORM models, and database migrations.
- **Tasks:**
  - Setup Python virtual environment and dependencies (`flask`, `sqlalchemy`, `bcrypt`, `pyjwt`).
  - Create database schema models: `User`, `SafetyProfile`, `EmergencyContact`, `Journey`, `JourneyWaypoint`, `CheckInEvent`, `IncidentLog`.
  - Configure SQLite initial database setup with abstraction allowing MySQL configuration.
  - Write base API response utilities and test harness.
- **Milestone Verification:** Database tables created; migrations run cleanly; basic ping test passing.

### Phase 2: Android Project Initialization & Core Navigation
- **Goal:** Initialize genuine Native Android Kotlin Jetpack Compose application structure.
- **Tasks:**
  - Create Gradle project configured with Kotlin DSL (`build.gradle.kts`).
  - Setup Jetpack Compose dependencies, Material 3 theme, and color schemes.
  - Implement Compose Navigation graph connecting top-level destinations.
  - Establish Dependency Injection / Service Locator and Retrofit network client setup.
- **Milestone Verification:** Android app builds cleanly in Android Studio, runs in emulator, displays welcoming placeholder navigation.

### Phase 3: User Authentication & Safety Profiles (Features 1–3)
- **Goal:** Deliver end-to-end user onboarding, profile configuration, and emergency contact management.
- **Tasks:**
  - Backend: Implement `/api/v1/auth/register`, `/login`, `/profile`, `/contacts`.
  - Android: Create Login, Registration, Safety Profile, and Contact Management Compose screens.
  - Implement secure token storage in Android EncryptedSharedPreferences.
- **Milestone Verification:** New user registers on Android, receives JWT token, creates safety profile, and saves 3 emergency contacts successfully.

### Phase 4: Journey Configuration & GPS Tracking (Features 4–5)
- **Goal:** Implement journey setup and active background GPS tracking.
- **Tasks:**
  - Android: Create Journey Setup UI (destination selection, transit mode, ETA calculation).
  - Implement `JourneyTrackingService` (Foreground Service with persistent notification).
  - Integrate `FusedLocationProviderClient` to stream GPS waypoints.
  - Backend: Endpoint to ingest and store journey status and waypoints.
- **Milestone Verification:** App starts journey, enters foreground service mode, records live GPS fixes even when the app is minimized or the screen is turned off.

### Phase 5: Adaptive Check-Ins & Anomaly Detection (Features 6–8)
- **Goal:** Implement dynamic safety check-in prompts, delay tracking, and route deviation algorithms.
- **Tasks:**
  - Android: Implement check-in dialog with countdown timer and haptic vibration feedback.
  - Algorithms: Calculate route corridor polyline cross-track distance (deviation detection) and static halt detection.
  - Backend & Local state: Detect missed check-in events when grace period expires.
- **Milestone Verification:** System successfully triggers scheduled check-in; missing the confirmation flags a warning state.

### Phase 6: Machine Learning Risk Assessment Engine (Feature 9)
- **Goal:** Develop, train, and integrate the Scikit-learn Random Forest journey risk classifier.
- **Tasks:**
  - ML: Synthesize representative journey anomaly training dataset covering various times, delays, deviations, and missed check-ins.
  - Train Random Forest Classifier model, evaluate metrics (Accuracy, F1-Score, Confusion Matrix).
  - Serialize model using `joblib`.
  - Backend: Implement `/api/v1/risk/evaluate` endpoint invoking model inference in under 50ms.
- **Milestone Verification:** Backend returns correct risk level (`LOW`, `MEDIUM`, `HIGH`) when presented with varied journey anomaly vectors.

### Phase 7: Emergency Alert Escalation & SOS (Features 10–12)
- **Goal:** Implement the progressive multi-level escalation pipeline and emergency dialing.
- **Tasks:**
  - Escalation logic: Tier 1 Soft Alert -> Tier 2 Guardian SMS notification with live GPS -> Tier 3 Full distress escalation.
  - Android: Implement one-tap red SOS Panic button and silent hardware key trigger.
  - Implement telephony emergency call dispatch intent to primary guardian / emergency service.
- **Milestone Verification:** Simulating a critical event transitions through Tier 1 to Tier 3, dispatches SMS simulation and prompts emergency call.

### Phase 8: History, Safe Places, Incident Journal & Utilities (Features 13–16)
- **Goal:** Implement utility modules supporting traveler safety and post-journey records.
- **Tasks:**
  - Feature 13: Journey history list with map route visualization and safety score summaries.
  - Feature 14: Fake Call simulator with customizable caller name and timed countdown.
  - Feature 15: Safe Places Directory displaying nearby police stations, hospitals, and transit hubs.
  - Feature 16: Safety Incident Journal with encrypted local note-taking and export option.
- **Milestone Verification:** User can trigger a realistic fake call, browse verified safe places on a map, and record an incident in the journal.

### Phase 9: Privacy Controls & Demo Simulation Mode (Features 17–18)
- **Goal:** Implement user privacy controls and the evaluator demonstration simulation engine.
- **Tasks:**
  - Feature 17: Privacy toggle center (location sharing permissions, data wipe option).
  - Feature 18: Demo Simulation Controller allowing evaluators to inject synthetic GPS movement, force a 1-click route deviation, or simulate missed check-in without leaving the room.
- **Milestone Verification:** Evaluator can perform a complete end-to-end journey demonstration in 3 minutes indoors using the simulation controls.

### Phase 10: Final Documentation, Viva Preparation & Release Packaging
- **Goal:** Prepare college project submission deliverables, final architecture slides, and release build.
- **Tasks:**
  - Generate release APK signed for demonstration.
  - Assemble comprehensive final report and viva presentation slides.
  - Final code review, linting, and documentation validation.
- **Milestone Verification:** Ready for college project evaluation and live demonstration.

---

## Testing & Quality Milestones

| Milestone ID | Testing Objective | Criteria for Success |
|---|---|---|
| **TM-01** | API Unit & Integration Tests | 100% passing tests across all Flask authentication, journey, and alert endpoints. |
| **TM-02** | ML Model Precision & Recall | Random Forest model achieves >90% precision on anomaly classification test split. |
| **TM-03** | Android Background Persistence | Foreground service maintains GPS fix for 30 continuous minutes with screen locked. |
| **TM-04** | Anomaly Detection Accuracy | Deviation >500m or delay >15 mins successfully triggers Tier 1 alert within 30 seconds. |
| **TM-05** | Offline Resilience Test | Anomaly detected locally triggers on-screen alarm even with airplane mode enabled. |
| **TM-06** | Viva Simulation Test | Complete 18-feature flow runnable within Demo Simulation Mode in under 5 minutes. |
