# SYSTEM ARCHITECTURE SPECIFICATION

# JOURNEX: Smart Women's Safety Check-In and Journey Monitoring System

This document outlines the end-to-end technical architecture, component interactions, data flows, and subsystem specifications of the **JOURNEX** platform.

---

## 1. High-Level Architectural Diagram

```
+---------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                    |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       Android Client (Kotlin)                           |   |
|   |                                                                         |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |   |   Jetpack Compose UI   | <----> |  ViewModel / State Management |   |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |                                                    |                    |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |   |  Foreground Service    | <----> |  Journey Tracking Repository  |   |   |
|   |   | (GPS / FusedLocation)  |        +-------------------------------+   |   |
|   |   +------------------------+                       |                    |   |
|   |                                     +-------------------------------+   |   |
|   |                                     |    Retrofit Network Client    |   |   |
|   |                                     +-------------------------------+   |   |
|   +-------------------------------------------------------------------------+   |
+--------------------------------------------------------|------------------------+
                                                         | HTTPS / REST (JSON)
                                                         v
+---------------------------------------------------------------------------------+
|                                BACKEND LAYER                                    |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                          Flask REST API Microservice                    |   |
|   |                                                                         |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |   | Authentication & Auth0 |        |     Journey Management API    |   |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |                |                                    |                   |   |
|   |                v                                    v                   |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   |   | Emergency Alert Engine |        |   ML Inference Bridge Service |   |   |
|   |   +------------------------+        +-------------------------------+   |   |
|   +-------------------------------------------------------------------------+   |
+------------------------------|-----------------------------------|--------------+
                               |                                   |
                               v                                   v
+---------------------------------------------+   +-------------------------------+
|                DATA LAYER                   |   |           ML LAYER            |
|                                             |   |                               |
|   +-------------------------------------+   |   |  Scikit-Learn Random Forest   |
|   |        SQLAlchemy ORM Layer         |   |   |  Classifier Model (.joblib)   |
|   +-------------------------------------+   |   |                               |
|                      |                      |   |  - Feature Vector Extraction  |
|         +------------+------------+         |   |  - Anomaly & Delay Evaluation |
|         v                         v         |   |  - Risk Score Calculation     |
|   SQLite (Local Dev)       MySQL (Prod)     |   |                               |
+---------------------------------------------+   +-------------------------------+
```

---

## 2. Component Breakdown

### 2.1 Android Client Subsystem
- **UI & Presentation**: Built entirely using modern **Jetpack Compose** following Material 3 guidelines. Single-activity architecture hosting Compose Navigation destinations.
- **Architecture Pattern**: **MVVM (Model-View-ViewModel)** with Unidirectional Data Flow (UDF).
  - *Views (Composables)*: Pure UI rendering driven by immutable State objects.
  - *ViewModels*: Manage UI state, expose `StateFlow`, handle coroutine lifecycles.
  - *Repositories*: Abstract data sources (local Room cache/DataStore and remote Retrofit API).
- **Background Tracking**:
  - `JourneyTrackingService`: An Android **Foreground Service** running with `FOREGROUND_SERVICE_TYPE_LOCATION`. Displays a persistent non-dismissible notification to guarantee continuous GPS polling by the operating system.
  - `FusedLocationProviderClient`: Configured for balanced power and high accuracy location tracking.
- **Local Resilience**:
  - Encrypted SharedPreferences / Jetpack DataStore for sensitive authentication tokens.
  - Local Room database fallback for caching route points during periods of cellular connectivity loss.

### 2.2 Backend Subsystem (Flask REST API)
- **Framework**: Python 3.10+ with Flask microframework.
- **API Architecture**: Application Factory pattern with modular Blueprints:
  - `auth_bp`: User registration, password encryption, JWT issuance.
  - `contacts_bp`: CRUD operations for trusted emergency contacts.
  - `journey_bp`: Journey creation, status synchronization, GPS waypoint logging.
  - `risk_bp`: Gateway to the Machine Learning risk evaluation pipeline.
  - `alert_bp`: Multi-tier escalation management and incident logging.
- **ORM & Database Support**:
  - **SQLAlchemy** acts as the persistence abstraction layer.
  - Default connection URL points to a local SQLite database (`journex.db`).
  - Production readiness: Configuration easily switched to MySQL (`mysql+pymysql://user:pass@host/journex`) without rewriting database models.

### 2.3 Machine Learning Subsystem
- **Model Engine**: **Random Forest Classifier** implemented via Scikit-learn.
- **Input Feature Vector**:
  1. `hour_of_day`: Normalized time of day [0 - 23].
  2. `is_night_travel`: Binary indicator (1 if between 20:00 and 06:00, else 0).
  3. `deviation_distance_m`: Perpendicular spatial offset from predefined route polyline.
  4. `delay_duration_mins`: Actual elapsed travel time minus anticipated segment ETA.
  5. `unexpected_stop_duration_s`: Duration of static zero-velocity halts outside designated safe nodes.
  6. `missed_checkins_count`: Consecutive unacknowledged safety check-in prompts.
  7. `battery_pct`: Device battery percentage.
- **Inference Pipeline**:
  - Model weights loaded into memory via `joblib.load()` during backend service startup.
  - Sub-50 millisecond inference latency per request.
  - Returns classification: `0 = LOW`, `1 = MEDIUM`, `2 = HIGH`, alongside probabilistic confidence values.

---

## 3. Communication Protocols & API Contracts

All network communication between the Android client and the Flask backend is serialized using standard JSON payloads over HTTP/HTTPS.

### 3.1 Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Authenticate user & return JWT |
| `GET/POST`| `/api/v1/contacts` | Retrieve or add trusted emergency contacts |
| `POST` | `/api/v1/journey/start` | Initialize a new monitored journey |
| `POST` | `/api/v1/journey/ping` | Send periodic GPS coordinates and check-in status |
| `POST` | `/api/v1/risk/evaluate` | Request ML risk score for current journey state |
| `POST` | `/api/v1/alert/escalate` | Trigger progressive emergency alert notification |
| `POST` | `/api/v1/journey/complete` | Conclude journey and archive travel history |

### 3.2 Sample Request & Response Contract: `/api/v1/risk/evaluate`

**Request Payload:**
```json
{
  "journey_id": "jn_98234a1",
  "timestamp": "2026-11-22T22:30:15Z",
  "metrics": {
    "hour_of_day": 22,
    "is_night": true,
    "deviation_distance_m": 420.5,
    "delay_duration_mins": 18,
    "unexpected_stop_duration_s": 380,
    "missed_checkins_count": 1,
    "battery_pct": 28
  }
}
```

**Response Payload:**
```json
{
  "status": "success",
  "journey_id": "jn_98234a1",
  "risk_assessment": {
    "risk_level": "HIGH",
    "risk_score": 0.84,
    "contributing_factors": [
      "Night travel",
      "Route deviation > 400m",
      "Prolonged unexpected halt",
      "Missed check-in"
    ],
    "recommended_action": "ESCALATE_TIER_2_GUARDIAN_SMS"
  }
}
```

---

## 4. Real-Time Tracking & Alert Escalation Strategy

```
Normal Journey Progress (All Check-Ins Confirmed)
  │
  ├─► Minor Anomaly (Delay < 10 mins, Normal route)
  │     └─► Tier 0: Internal log update, maintain standard check-in frequency.
  │
  ├─► Moderate Anomaly (Missed Check-In OR Deviation > 300m OR Risk = MEDIUM)
  │     └─► Tier 1: Soft Alert (Audible beep + High-priority on-screen prompt).
  │           └─ User Acknowledges: Return to normal monitoring.
  │           └─ No Response within 60s: Auto-escalate to Tier 2.
  │
  └─► Severe Anomaly (Missed Tier 1 OR Route Deviation > 800m OR Risk = HIGH OR Panic SOS)
        └─► Tier 2: Guardian Notification (SMS with real-time GPS coordinates).
        └─► Tier 3: Emergency Escalation (Automatic Call to primary contact, high decibel alarm, live tracking broadcast).
```

---

## 5. Security and Data Protection Architecture

1. **Authentication:** Bearer token (JWT) attached to `Authorization` header.
2. **Password Security:** Salted and hashed using `bcrypt` (work factor 12).
3. **Transport Security:** Transport Layer Security (TLS/HTTPS).
4. **Data Isolation:** User journeys and contact lists are strictly query-filtered by the authenticated user's ID.
