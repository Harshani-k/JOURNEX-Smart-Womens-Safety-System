# PROJECT SPECIFICATION

# JOURNEX: Smart Women's Safety Check-In and Journey Monitoring System

- **Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System
- **Short Name:** JOURNEX
- **Target Audience:** Women commuters, college students, solo travelers, working professionals
- **Platform:** Native Android (Kotlin + Jetpack Compose) supported by Python Flask Backend and ML Risk Engine

---

## 1. Problem Statement & Motivation

Women traveling alone—especially during late hours, along secluded routes, or in unfamiliar transit systems—frequently face personal safety risks. Existing safety mobile apps suffer from critical shortcomings:
1. **Manual Panic Dependency:** Most apps rely exclusively on a physical panic button. In sudden, incapacitating, or high-threat situations, victims cannot physically retrieve their phone, unlock it, and trigger an SOS.
2. **Absence of Intelligent Anomaly Detection:** Current applications lack proactive monitoring. They do not automatically recognize whether a vehicle has taken a major detour, halted in an uninhabited location for an extended duration, or missed an expected arrival time.
3. **Binary Alerting (False Alarm Fatigue):** Existing systems immediately send loud sirens or mass emergency messages without progressive escalation, leading users to disable tracking due to accidental triggers.

**JOURNEX** resolves these gaps by integrating continuous GPS monitoring, dynamic adaptive check-ins, and a machine-learning risk assessment model that autonomously identifies safety threats and progressively escalates assistance before a situation becomes critical.

---

## 2. Technology Stack & Technical Rationale

| Layer | Selected Technology | Technical Rationale |
|---|---|---|
| **Mobile OS** | Native Android (Min SDK 26, Target SDK 34) | Direct access to hardware sensors, telephony APIs, background services, and fine-grained GPS hardware. |
| **Language** | Kotlin 1.9+ | Modern, memory-safe, null-safe language officially endorsed by Google for Android development with coroutine support for asynchronous tasks. |
| **UI Framework** | Jetpack Compose | Declarative UI framework providing seamless state handling, rapid UI iteration, clean architecture compatibility, and high responsiveness. |
| **Backend API** | Python 3.10+ / Flask | Lightweight, performant micro-framework that integrates natively with Python's data science ecosystem (Scikit-learn, NumPy, Pandas) without language interop overhead. |
| **ORM** | SQLAlchemy | Robust, production-grade ORM allowing clean database abstraction and seamless switching from SQLite during development to MySQL in production. |
| **Database** | SQLite (Dev) / MySQL (Prod) | SQLite enables zero-configuration, self-contained local testing; MySQL provides enterprise relational persistence for deployment. |
| **Machine Learning**| Scikit-learn (Random Forest Classifier) | Robust ensemble algorithm capable of handling non-linear tabular feature combinations (delay minutes, deviation distance, check-in latency, time of day) with low latency inference and high resistance to overfitting. |

---

## 3. Comprehensive Breakdown of the 18 Mandatory Features

### Feature 1: User Registration & Login
- Secure user registration capturing full name, email, password (hashed using bcrypt), and phone number.
- JWT-based authentication token exchange for stateless API communication.
- Secure local token persistence using Android Jetpack `EncryptedSharedPreferences`.

### Feature 2: Personal Safety Profile
- Structured profile recording medical information (blood type, allergies, primary language), emergency notes, and home base address.
- Offline access caching to ensure personal safety details are accessible even without internet connectivity.

### Feature 3: Trusted Emergency Contact Management
- CRUD interface for up to 5 verified emergency contacts (guardians, family, friends).
- Priority ordering: Primary, Secondary, and Tertiary contacts.
- Quick contact import from phonebook with explicit permission management.
- Test ping verification to ensure guardian contact details are active and reachable.

### Feature 4: Destination & Expected Arrival Time Setup
- Journey initialization flow where the user defines:
  - Starting location (auto-detected via GPS).
  - Destination point (searchable with geocoding).
  - Selected transit mode (Walking, Bus, Train, Auto/Cab, Personal Vehicle).
  - Estimated travel duration and computed Expected Time of Arrival (ETA).
  - Buffer time threshold before delay detection flags an alert.

### Feature 5: GPS-Based Journey Monitoring
- Android Foreground Service maintaining persistent GPS tracking using `FusedLocationProviderClient`.
- High-accuracy location updates throttled intelligently to conserve battery while maintaining safety granularity.
- Real-time corridor calculation: checking whether current coordinates remain within an acceptable geofence buffer of the route.

### Feature 6: Adaptive Safety Check-In
- Dynamic check-in prompts presented at variable intervals (e.g., every 15, 30, or 45 minutes, or upon entering high-risk transit zones).
- Prompts offer a quick one-tap "I am Safe" confirmation with haptic feedback.
- Configurable countdown timer (e.g., 60 seconds) with audio/vibration reminders before marking a check-in as missed.

### Feature 7: Missed Check-In & Delay Detection
- Automatic detection when a user fails to acknowledge an adaptive check-in within the designated grace period.
- Real-time comparison between current time and calculated ETA: flags journeys running significantly behind schedule without user explanation.

### Feature 8: Route Deviation & Unexpected Stop Detection
- Algorithmic route adherence verification: calculates perpendicular distance from the current GPS fix to the planned route polyline.
- Detects route deviations exceeding predetermined tolerance thresholds (e.g., >500 meters away from expected corridor).
- Detects unexpected static stops (velocity ~ 0 km/h) in non-designated or high-risk zones lasting longer than allowed thresholds (e.g., >5 minutes).

### Feature 9: AI/ML-Based Risk Analysis
- Multi-feature tabular risk classifier powered by Scikit-learn Random Forest.
- Input Features:
  - `time_of_day_category` (Day, Twilight, Late Night)
  - `delay_minutes` (Difference between current time and original ETA)
  - `deviation_distance_meters` (Distance away from established route corridor)
  - `unexpected_stop_duration_seconds` (Duration of static halt)
  - `missed_checkin_count` (Number of unacknowledged safety prompts)
  - `battery_level_percentage` (Current device battery state)
  - `transit_mode` (Categorical: Cab, Walk, Transit, etc.)
- Model Output: Discrete Risk Classification (`LOW`, `MEDIUM`, `HIGH`) and continuous anomaly confidence score (0.00 – 1.00).

### Feature 10: Multi-Level Emergency Alert Escalation
- **Level 1 (Soft Alert):** High-priority notification on the traveler's phone asking for immediate PIN confirmation to cancel warning.
- **Level 2 (Guardian Notification):** Automated dispatch of SMS/data notification to Primary Emergency Contact containing live GPS coordinates and nature of the anomaly.
- **Level 3 (Full Emergency Escalation):** Notification dispatch to all trusted contacts, audible alert initiation, and live location broadcasting link.

### Feature 11: SOS & Silent Safety Check
- **Instant SOS:** Prominent one-tap red panic button on the home/journey screen triggering instant Level 3 escalation.
- **Hardware Trigger:** Rapid multi-press of the power/volume button to activate SOS discreetly while the phone remains inside a bag or pocket.
- **Silent Check:** Covert verification screen disguised as a generic utility or calculator to prevent a hostile observer from noticing an alert check.

### Feature 12: Automatic Emergency Calling
- Automated telephony invocation through Android Telecom APIs dialing the designated primary emergency contact or local emergency dispatch (e.g., 112) when Level 3 High Risk status is sustained and unacknowledged.
- Hands-free speakerphone enablement when permitted by system capabilities.

### Feature 13: Journey History & Safety Records
- Historical record keeping of all completed, canceled, and alerted journeys.
- Metrics logged: start/end times, total distance, safety check-in compliance rate, deviation flags, and final journey outcome.
- Ability to review past routes on a map with color-coded safety indices.

### Feature 14: Safe Exit / Fake Call
- Realistic mock incoming phone call simulator.
- Configurable delay (e.g., "Call me in 15 seconds", "Call me in 1 minute").
- Realistic caller screen with custom name (e.g., "Dad", "Hostel Warden", "Office") and pre-recorded voice playback to provide a credible pretext to leave dangerous environments.

### Feature 15: Safe Places Directory
- Curated offline and online directory of verified 24/7 safe havens:
  - Police Stations and Women's Help Desks
  - Government and Private Hospitals / 24-Hour Pharmacies
  - Open Metro Stations, Major Transit Hubs, and Verified Night Shelters
- One-tap turn-by-turn navigation redirecting the traveler to the closest refuge.

### Feature 16: Safety Incident Journal
- Private encrypted journal allowing users to record incidents, harassment experiences, or suspicious vehicle license plates.
- Supports text descriptions, category tags, timestamping, and optional photo attachment references.
- Exportable report format suitable for submission to campus security or law enforcement.

### Feature 17: Privacy Controls
- Strict user-driven consent switches:
  - Toggle GPS broadcasting on/off.
  - Incognito journey option (logs kept locally only, zero cloud synchronization).
  - Clear journey history and cached data on demand.
  - Transparent disclosure of what data guardians receive.

### Feature 18: Demo Simulation Mode
- Comprehensive testing and demonstration harness built directly into the app.
- Allows college project evaluators to simulate:
  - GPS route following without stepping outside.
  - Simulated 2-kilometer route deviation with a single toggle.
  - Simulated missed check-in timeout.
  - Simulated unexpected halt in an unfamiliar area.
  - Direct triggering and visualization of ML risk classification output (`LOW` -> `MEDIUM` -> `HIGH`).

---

## 4. End-to-End Application Flow

The mandatory execution sequence is strictly structured as follows:

```
[1] Login / Registration
       ↓
[2] Add / Verify Trusted Contacts
       ↓
[3] Create Journey
       ↓
[4] Set Destination & Expected Arrival Time (ETA)
       ↓
[5] Start Journey Monitoring
       ↓
[6] Real-Time GPS Tracking & Corridor Geofencing
       ↓
[7] Adaptive Safety Check-In Triggered
       ↓
[8] AI/ML-Based Risk Analysis Engine Evaluates Features
       ↓
[9] Detect Missed Check-In OR Route Deviation OR Halt
       ↓
[10] Real-Time Risk Assessment (Low → Medium → High)
       ↓
[11] Progressive Multi-Level Alert Escalation
       ↓
[12] Automatic Emergency Calling & Live Guardian Alert
       ↓
[13] Journey Conclusion & View Journey History Records
```

---

## 5. Security, Ethics, and College Submission Criteria

1. **Non-Invasive Tracking:** Tracking is active exclusively while a journey session is marked "IN_PROGRESS".
2. **Data Protection:** Passwords and sensitive profile records are hashed/encrypted; location coordinates are transmitted over secure HTTPS payloads.
3. **Resilience to Network Loss:** Critical anomaly triggers and local check-in alarms operate completely on-device without requiring continuous internet connectivity.
