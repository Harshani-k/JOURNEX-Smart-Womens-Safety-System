# JOURNEX REST API Specification: Route Deviation & Safety Events

**Version:** 1.0.0  
**Phase:** 6  
**Base URL:** `/api/v1`  
**Authentication:** Bearer JWT required for all endpoints  

---

## 1. Overview

The JOURNEX Safety Events Subsystem manages detection and lifecycle resolution for route deviations and unexpected stops during active journeys.

### Event Lifecycle States

```
                 +-------------+
                 |   ACTIVE    |
                 +------+------+
                        |
        +---------------+---------------+
        |                               |
        v                               v
+-----------------+             +-----------------+
|  ACKNOWLEDGED   |             |    RESOLVED     |
+--------+--------+             +-----------------+
         |                               ^
         +-------------------------------+
            (User provides reason notes)
```

- **`ACTIVE`**: Anomaly newly triggered or ongoing. Prompts alert in Android UI.
- **`ACKNOWLEDGED`**: Traveler tapped acknowledge; alarm silenced.
- **`RESOLVED`**: Traveler confirmed route change/stop was intentional or normal.
- **`DISMISSED`**: Dismissed by system or journey completion.

---

## 2. API Endpoints

### 2.1 List All Safety Events for Journey

**Endpoint:** `GET /api/v1/journeys/<journey_id>/safety-events`

Retrieves paginated history of all safety events recorded for the specified active journey.

#### Headers
```http
Authorization: Bearer <jwt_access_token>
```

#### Response Envelope (HTTP 200 OK)
```json
{
  "success": true,
  "message": "Safety events retrieved successfully.",
  "data": {
    "safety_events": [
      {
        "id": 1,
        "journey_id": 3,
        "user_id": 1,
        "event_type": "ROUTE_DEVIATION",
        "status": "ACTIVE",
        "trigger_reason": "Route deviation detected: 420m from planned corridor (3 consecutive observations).",
        "severity": "MEDIUM",
        "latitude": 11.0060,
        "longitude": 77.0050,
        "accuracy": 11.0,
        "deviation_distance": 420.0,
        "duration_seconds": null,
        "consecutive_count": 3,
        "detected_at": "2026-11-22T12:20:00Z",
        "acknowledged_at": null,
        "resolved_at": null,
        "resolution_notes": null,
        "client_action_id": null,
        "created_at": "2026-11-22T12:20:00Z",
        "updated_at": "2026-11-22T12:20:00Z"
      }
    ]
  },
  "errors": null,
  "timestamp": "2026-11-22T12:20:01Z"
}
```

---

### 2.2 Get Active Safety Events

**Endpoint:** `GET /api/v1/journeys/<journey_id>/safety-events/active`

Retrieves only currently unresolved/active safety events requiring attention.

#### Headers
```http
Authorization: Bearer <jwt_access_token>
```

#### Response Envelope (HTTP 200 OK)
```json
{
  "success": true,
  "message": "Active safety events retrieved successfully.",
  "data": {
    "active_events": [
      {
        "id": 2,
        "journey_id": 3,
        "user_id": 1,
        "event_type": "UNEXPECTED_STOP",
        "status": "ACTIVE",
        "trigger_reason": "Vehicle stationary for 12 minutes (displacement 4.2m).",
        "severity": "MEDIUM",
        "latitude": 11.0050,
        "longitude": 77.0000,
        "accuracy": 8.0,
        "deviation_distance": null,
        "duration_seconds": 720,
        "consecutive_count": 5,
        "detected_at": "2026-11-22T12:15:00Z",
        "acknowledged_at": null,
        "resolved_at": null,
        "resolution_notes": null,
        "client_action_id": null,
        "created_at": "2026-11-22T12:15:00Z",
        "updated_at": "2026-11-22T12:15:00Z"
      }
    ]
  },
  "errors": null,
  "timestamp": "2026-11-22T12:15:01Z"
}
```

---

### 2.3 Acknowledge Safety Event

**Endpoint:** `POST /api/v1/journeys/<journey_id>/safety-events/<event_id>/acknowledge`

User marks an active incident as seen/acknowledged. Silences alarms while preserving incident record.

#### Headers
```http
Authorization: Bearer <jwt_access_token>
```

#### Response Envelope (HTTP 200 OK)
```json
{
  "success": true,
  "message": "Safety event acknowledged.",
  "data": {
    "id": 1,
    "journey_id": 3,
    "user_id": 1,
    "event_type": "ROUTE_DEVIATION",
    "status": "ACKNOWLEDGED",
    "acknowledged_at": "2026-11-22T12:21:00Z",
    "updated_at": "2026-11-22T12:21:00Z"
  },
  "errors": null,
  "timestamp": "2026-11-22T12:21:00Z"
}
```

---

### 2.4 Resolve Safety Event

**Endpoint:** `POST /api/v1/journeys/<journey_id>/safety-events/<event_id>/resolve`

User resolves the incident, marking the route change or stop as intentional/normal.

#### Headers
```http
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "resolution_notes": "Taking verified alternate detour around construction",
  "client_action_id": "c1f7b920-8e12-4c61-9cbb-92ef210081bb"
}
```

#### Response Envelope (HTTP 200 OK)
```json
{
  "success": true,
  "message": "Safety event resolved successfully.",
  "data": {
    "id": 1,
    "journey_id": 3,
    "user_id": 1,
    "event_type": "ROUTE_DEVIATION",
    "status": "RESOLVED",
    "resolved_at": "2026-11-22T12:22:00Z",
    "resolution_notes": "Taking verified alternate detour around construction",
    "client_action_id": "c1f7b920-8e12-4c61-9cbb-92ef210081bb",
    "updated_at": "2026-11-22T12:22:00Z"
  },
  "errors": null,
  "timestamp": "2026-11-22T12:22:00Z"
}
```
