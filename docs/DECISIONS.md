# ARCHITECTURE DECISION RECORDS (ADRs)

# JOURNEX: Smart Women's Safety Check-In and Journey Monitoring System

This document captures the critical architectural and technical decisions made for the JOURNEX project, detailing the context, considered alternatives, decisions made, and their consequences.

---

## ADR-001: Monorepo Architecture for Android, Backend, and ML

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** JOURNEX is a multi-tier final-year college engineering project consisting of a native mobile client, a Python backend REST API, and a machine learning risk assessment engine.
- **Alternatives Considered:**
  1. Multiple separate repositories (e.g., `journex-android`, `journex-backend`, `journex-ml`).
  2. Single unified monorepo.
- **Decision:** Adopt a single monorepo repository structure containing separate top-level directories: `android/`, `backend/`, `ml/`, and `docs/`.
- **Consequences:**
  - *Positive:* Simplifies code sharing, documentation synchronization, academic project evaluation, and versioning across all components.
  - *Trade-off:* Requires a carefully crafted root `.gitignore` to prevent Android and Python build caches from interfering with each other.

---

## ADR-002: Native Android with Kotlin and Jetpack Compose

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** The application requires uninterrupted background location services, direct telephony and SMS hardware invocation, high-priority notifications, and low battery consumption.
- **Alternatives Considered:**
  1. Flutter / React Native (Cross-platform).
  2. Native Android (Java with XML Views).
  3. Native Android (Kotlin with Jetpack Compose).
- **Decision:** Develop purely as a Native Android application using Kotlin and Jetpack Compose.
- **Consequences:**
  - *Positive:* First-class Android Foreground Service support (`FOREGROUND_SERVICE_TYPE_LOCATION`), unrestricted access to Android Telecom and Telephony APIs, modern declarative UI via Compose, complete null-safety with Kotlin.
  - *Trade-off:* Platform target limited to Android devices (standard and appropriate for college project scope).

---

## ADR-003: Python Flask REST API with SQLAlchemy (SQLite transitioning to MySQL)

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** The backend needs to provide stateless RESTful JSON endpoints, manage user accounts and journey logs, and interact seamlessly with Python data science models.
- **Alternatives Considered:**
  1. Node.js / Express (requires IPC or microservice bridging to execute Python ML models).
  2. Django (heavyweight for a mobile REST API; brings unnecessary HTML template baggage).
  3. Flask with SQLAlchemy (lightweight, modular, direct Python ML integration).
- **Decision:** Utilize Flask with the Application Factory pattern and SQLAlchemy ORM. Initial development will run on SQLite; the database connection string can be re-pointed to MySQL for production without code changes.
- **Consequences:**
  - *Positive:* Fast, lightweight, minimal boilerplate; ML model weights can be loaded directly into backend memory without network overhead; SQLite requires zero configuration during local grading and evaluation.
  - *Trade-off:* Requires manual blueprint and route structuring compared to Django's batteries-included approach.

---

## ADR-004: Scikit-Learn Random Forest Classifier for Journey Risk Scoring

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** The system must evaluate multidimensional journey data (time of night, deviation distance, delay duration, missed check-ins, battery level) to predict a risk tier (`LOW`, `MEDIUM`, `HIGH`).
- **Alternatives Considered:**
  1. Hardcoded If-Else rule heuristic (inflexible, cannot model subtle feature interactions, lacks academic ML rigor).
  2. Deep Neural Network (overly complex, high inference overhead, prone to overfitting on small tabular datasets).
  3. Random Forest Classifier (Scikit-learn).
- **Decision:** Implement a Random Forest Classifier trained on journey anomaly feature vectors.
- **Consequences:**
  - *Positive:* Handles non-linear interactions, robust to outliers, offers high interpretability (feature importance metrics can be inspected during project defense), and executes inference in <50 milliseconds.
  - *Trade-off:* Requires a well-designed synthetic feature dataset representing real-world travel safety edge cases.

---

## ADR-005: Foreground Service for Continuous GPS Journey Tracking

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** Android operating system power management (Doze Mode) aggressively kills background tasks and throttles location updates if an application is not actively in the foreground.
- **Alternatives Considered:**
  1. Periodic WorkManager polling (throttled to 15-minute intervals by Android OS; inadequate for travel safety).
  2. Android Foreground Service with continuous notification.
- **Decision:** Implement an Android `ForegroundService` with `FOREGROUND_SERVICE_TYPE_LOCATION` and a persistent notification channel.
- **Consequences:**
  - *Positive:* Guarantees accurate, real-time location stream and uninterrupted safety check-in countdown timers even when the phone screen is locked.
  - *Trade-off:* Requires explicit runtime location permissions (`ACCESS_FINE_LOCATION`, `ACCESS_BACKGROUND_LOCATION`) and notification permission on Android 13+.

---

## ADR-006: Progressive Multi-Tier Alert Escalation Strategy

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** Immediate, binary emergency triggers cause false-alarm fatigue and cause users to abandon safety applications.
- **Decision:** Implement a three-tier escalation sequence:
  - **Tier 1 (Soft Alert):** On-screen audible notification with countdown for the traveler to self-cancel with a PIN.
  - **Tier 2 (Guardian SMS Notification):** Automated dispatch of SMS with live GPS link to primary emergency contact.
  - **Tier 3 (Distress & Calling):** Full alarm, SMS to all contacts, and automatic call dispatch to primary guardian/emergency dispatch.
- **Consequences:**
  - *Positive:* Drastically reduces false alerts while maintaining uncompromising emergency readiness.
  - *Trade-off:* Requires clear countdown state management on the client device.

---

## ADR-007: Built-In Demo Simulation Mode for Viva and Evaluator Testing

- **Status:** Accepted
- **Date:** 2026-11-22
- **Context:** College evaluators and viva examiners evaluate the project indoors in an examination hall, making it impossible to physically travel multiple kilometers or create real danger to demonstrate route deviations and emergency escalation.
- **Decision:** Build a dedicated, non-invasive Demo Simulation Mode within the Android app.
- **Consequences:**
  - *Positive:* Allows examiners to simulate an entire journey, force a route deviation, simulate an unacknowledged check-in, and watch the ML risk classification and alert escalation unfold in real-time in under 3 minutes.
  - *Trade-off:* Must be clearly isolated from production code paths to prevent accidental simulation triggers during genuine journeys.
