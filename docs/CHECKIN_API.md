# JOURNEX REST API Specification: Safety Check-Ins & Missed Check-In Detection

**Version:** 1.0.0  
**Phase:** 5  
**Base URL:** `/api/v1`  
**Authentication:** Bearer JWT required for all endpoints  

---

## 1. Overview

The JOURNEX Safety Check-In Subsystem provides deterministic, rule-based check-in scheduling, verification, and missed check-in detection for women traveling on active journeys.

### Check-In Lifecycle States

```
                +-------------+
                |  SCHEDULED  |
                +------+------+
                       |
        +--------------+--------------+
        |                             |
        v                             v
+---------------+             +---------------+
| CONFIRMED_SAFE|             |    MISSED     |
+---------------+             +---------------+
        ^                             ^
        | (cancel action)             |
        v                             |
+---------------+                     |
|   CANCELLED   |---------------------+ (If journey completes)
+---------------+
```

- **`SCHEDULED`**: Check-in is queued for a future window (`scheduled_at` to `deadline_at`).
- **`REMINDED`**: Check-in notification prompt has been broadcast to user.
- **`CONFIRMED_SAFE`**: User actively verified safety before deadline. Terminal state.
- **`MISSED`**: Deadline expired without on-time verification. Triggers risk escalation.
- **`CANCELLED`**: Journey completed early or check-in dismissed by user.

---

## 2. API Endpoints

### 2.1 Schedule Safety Check-In

**Endpoint:** `POST /api/v1/journeys/<journey_id>/checkins`

Schedules a safety check-in for an `ACTIVE` journey. If `scheduled_at` and `deadline_at` are omitted, the backend's deterministic adaptive scheduling engine automatically derives optimal timestamps based on remaining duration and delay status.

#### Headers
```http
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```

#### Request Body (Optional Manual Schedule)
```json
{
  "scheduled_at": "2026-11-22T15:30:00Z",
  "deadline_at": "2026-11-22T15:33:00Z",
  "client_action_id": "c7a840e6-59f0-46d2-9720-c2f82638e121"
}
```

#### Response (201 Created)
```json
{
  "status": "success",
  "message": "Check-in scheduled successfully.",
  "data": {
    "id": 14,
    "journey_id": 1,
    "user_id": 4,
    "scheduled_at": "2026-11-22T15:30:00Z",
    "deadline_at": "2026-11-22T15:33:00Z",
    "responded_at": null,
    "status": "SCHEDULED",
    "response_type": null,
    "reminder_sent_at": null,
    "client_action_id": "c7a840e6-59f0-46d2-9720-c2f82638e121",
    "created_at": "2026-11-22T15:15:00Z",
    "updated_at": "2026-11-22T15:15:00Z"
  }
}
```

#### Error Codes
- `400 Bad Request`: Journey is not `ACTIVE` or invalid ISO timestamps.
- `403 / 404`: Journey not found or belongs to another user.
- `409 Conflict`: An active check-in is already scheduled for this journey.

---

### 2.2 List Journey Check-In History

**Endpoint:** `GET /api/v1/journeys/<journey_id>/checkins?page=1&per_page=10`

Retrieves paginated check-in records for a journey sorted chronologically.

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Check-in history retrieved successfully.",
  "data": {
    "checkins": [
      {
        "id": 14,
        "journey_id": 1,
        "status": "CONFIRMED_SAFE",
        "scheduled_at": "2026-11-22T15:15:00Z",
        "deadline_at": "2026-11-22T15:18:00Z",
        "responded_at": "2026-11-22T15:16:12Z",
        "response_type": "MANUAL_TAP",
        "client_action_id": "c7a840e6-59f0-46d2-9720-c2f82638e121"
      }
    ],
    "pagination": {
      "total_items": 1,
      "total_pages": 1,
      "current_page": 1,
      "per_page": 10,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 2.3 Get Current Pending Check-In

**Endpoint:** `GET /api/v1/journeys/<journey_id>/checkins/pending`

Returns the currently pending (`SCHEDULED` or `REMINDED`) check-in for active countdown rendering.

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Pending check-in retrieved successfully.",
  "data": {
    "id": 15,
    "journey_id": 1,
    "status": "SCHEDULED",
    "scheduled_at": "2026-11-22T15:45:00Z",
    "deadline_at": "2026-11-22T15:48:00Z"
  }
}
```

---

### 2.4 Confirm Safety ("I Am Safe")

**Endpoint:** `POST /api/v1/checkins/<checkin_id>/confirm`

Confirms user safety for an active check-in.

#### Request Body
```json
{
  "responded_at": "2026-11-22T15:46:10Z",
  "response_type": "MANUAL_TAP",
  "client_action_id": "c7a840e6-59f0-46d2-9720-c2f82638e121"
}
```

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Check-in confirmed safe successfully.",
  "data": {
    "id": 15,
    "status": "CONFIRMED_SAFE",
    "responded_at": "2026-11-22T15:46:10Z",
    "response_type": "MANUAL_TAP"
  }
}
```

#### Error Codes
- `400 Bad Request`: Cannot confirm cancelled check-in.
- `409 Conflict`: 
  - Check-in already confirmed (idempotent if same `client_action_id`).
  - Deadline expired: Check-in was marked `MISSED` and cannot be converted to on-time.

---

### 2.5 Cancel Scheduled Check-In

**Endpoint:** `POST /api/v1/checkins/<checkin_id>/cancel`

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Check-in cancelled successfully.",
  "data": {
    "id": 15,
    "status": "CANCELLED"
  }
}
```

---

### 2.6 Background Missed Check-In Detection

**Endpoint:** `POST /api/v1/checkins/detect-missed`

Automated maintenance endpoint for cron/worker daemons.

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Missed check-in detection sweep complete. 2 overdue check-in(s) marked MISSED.",
  "data": {
    "missed_count": 2
  }
}
```

---

### 2.7 Journey Delay Status & Detection

**Endpoint:** `GET /api/v1/journeys/<journey_id>/delay`  
**Endpoint:** `POST /api/v1/journeys/detect-delayed`

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Journey delay status retrieved successfully.",
  "data": {
    "journey_id": 1,
    "status": "ACTIVE",
    "is_delayed": true,
    "delayed_at": "2026-11-22T15:40:00Z",
    "expected_arrival_time": "2026-11-22T15:30:00Z",
    "minutes_delayed": 10
  }
}
```
