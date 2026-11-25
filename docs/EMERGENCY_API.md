# JOURNEX – Phase 8: Emergency & SOS Alert REST API Reference

**Project:** JOURNEX – Smart Women's Safety Check-In and Journey Monitoring System  
**Base URL:** `/api/v1/emergency-events`  
**Authentication:** Required (`Authorization: Bearer <access_token>`)  
**Envelope:** All responses follow standard JOURNEX envelope `{ "status": "success"|"error", "data": ..., "message": ... }`  

---

## Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/emergency-events` | Trigger standalone SOS or silent emergency event |
| `POST` | `/api/v1/journeys/<journey_id>/emergency-events` | Trigger journey-associated emergency event |
| `GET` | `/api/v1/emergency-events/<event_id>` | Get details and dispatches of an emergency event |
| `GET` | `/api/v1/emergency-events` | List user's emergency event history (paginated) |
| `POST` | `/api/v1/emergency-events/<event_id>/cancel` | Cancel active emergency (traveler confirms safe) |
| `POST` | `/api/v1/emergency-events/<event_id>/escalate` | Manually escalate alert to next guardian level |
| `GET` | `/api/v1/emergency-events/<event_id>/delivery-status` | Get delivery status summary across contacts |

---

## 1. Trigger Standalone Emergency Event

Creates a new emergency event and dispatches Level 1 alerts (primary contact).

- **URL:** `POST /api/v1/emergency-events`
- **Headers:** `Authorization: Bearer <jwt>`, `Content-Type: application/json`
- **Request Body:**
```json
{
  "trigger_type": "MANUAL_SOS",
  "journey_id": null,
  "latitude": 12.9716,
  "longitude": 80.2435,
  "accuracy": 12.5,
  "location_address": "OMR IT Corridor, Chennai",
  "client_action_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

- **Parameters:**
  - `trigger_type` (string, required): `MANUAL_SOS`, `MISSED_CHECKIN_ESCALATION`, or `SILENT_ALERT`.
  - `journey_id` (integer, optional): Associated journey ID.
  - `latitude` (float, optional): Latitude $[-90.0, 90.0]$.
  - `longitude` (float, optional): Longitude $[-180.0, 180.0]$.
  - `accuracy` (float, optional): GPS horizontal accuracy error in meters $\ge 0$.
  - `location_address` (string, optional): Resolved geographic address string.
  - `client_action_id` (string, optional): UUID for client-side idempotent deduplication.

- **Response (201 Created):**
```json
{
  "status": "success",
  "message": "Emergency event triggered successfully. Level 1 alert dispatched.",
  "data": {
    "id": 1,
    "user_id": 1,
    "journey_id": null,
    "trigger_type": "MANUAL_SOS",
    "status": "ACTIVE",
    "current_escalation_level": 1,
    "max_escalation_level": 3,
    "latitude": 12.9716,
    "longitude": 80.2435,
    "accuracy": 12.5,
    "location_address": "OMR IT Corridor, Chennai",
    "trigger_timestamp": "2026-11-22T14:10:00Z",
    "cancelled_at": null,
    "cancellation_reason": null,
    "dispatches": [
      {
        "id": 1,
        "emergency_event_id": 1,
        "contact_id": 1,
        "contact_name": "Lakshmi (Mother)",
        "contact_phone": "+919876543210",
        "escalation_level": 1,
        "channel": "SMS",
        "status": "DELIVERED",
        "provider_message_id": "MOCK-SMS-9921",
        "error_message": null,
        "created_at": "2026-11-22T14:10:01Z"
      }
    ]
  }
}
```

---

## 2. Trigger Journey Emergency Event

Convenience route associating the emergency event directly with an active journey.

- **URL:** `POST /api/v1/journeys/<journey_id>/emergency-events`
- **Headers:** `Authorization: Bearer <jwt>`, `Content-Type: application/json`
- **Request Body:** Same as standalone trigger (`journey_id` taken from route).
- **Response:** HTTP 201 Created with emergency event payload.

---

## 3. Get Emergency Event Details

Retrieve status and dispatches for a specific emergency event.

- **URL:** `GET /api/v1/emergency-events/<event_id>`
- **Headers:** `Authorization: Bearer <jwt>`
- **Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "journey_id": 10,
    "trigger_type": "MANUAL_SOS",
    "status": "ACTIVE",
    "current_escalation_level": 1,
    "max_escalation_level": 3,
    "latitude": 12.9716,
    "longitude": 80.2435,
    "accuracy": 12.5,
    "location_address": "OMR IT Corridor, Chennai",
    "trigger_timestamp": "2026-11-22T14:10:00Z",
    "dispatches": [ ... ]
  }
}
```

---

## 4. Escalate Emergency Event

Manually escalates the alert to the next guardian level (Level 1 $\rightarrow$ Level 2 $\rightarrow$ Level 3).

- **URL:** `POST /api/v1/emergency-events/<event_id>/escalate`
- **Headers:** `Authorization: Bearer <jwt>`, `Content-Type: application/json`
- **Request Body (optional):**
```json
{
  "reason": "Traveler requested immediate secondary guardian notification"
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Emergency escalated to level 2.",
  "data": {
    "id": 1,
    "current_escalation_level": 2,
    "status": "ESCALATED",
    "dispatches": [
      {
        "id": 1,
        "contact_name": "Lakshmi (Mother)",
        "escalation_level": 1,
        "status": "DELIVERED"
      },
      {
        "id": 2,
        "contact_name": "Suresh (Father)",
        "escalation_level": 2,
        "status": "DELIVERED"
      }
    ]
  }
}
```

---

## 5. Cancel Emergency Event (Traveler Confirmed Safe)

Cancels an active or escalated emergency. Dispatches safe confirmation notices to all contacted guardians.

- **URL:** `POST /api/v1/emergency-events/<event_id>/cancel`
- **Headers:** `Authorization: Bearer <jwt>`, `Content-Type: application/json`
- **Request Body:**
```json
{
  "cancellation_reason": "Traveler confirmed safe via app"
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Emergency event cancelled. Safe confirmation sent to notified contacts.",
  "data": {
    "id": 1,
    "status": "CANCELLED",
    "cancelled_at": "2026-11-22T14:15:30Z",
    "cancellation_reason": "Traveler confirmed safe via app"
  }
}
```

---

## 6. Get Delivery Status Summary

Summarizes delivery health across all dispatches for an emergency event.

- **URL:** `GET /api/v1/emergency-events/<event_id>/delivery-status`
- **Headers:** `Authorization: Bearer <jwt>`
- **Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "emergency_event_id": 1,
    "status": "ACTIVE",
    "current_escalation_level": 2,
    "total_dispatches": 2,
    "delivered_count": 2,
    "pending_count": 0,
    "failed_count": 0,
    "dispatches": [
      {
        "id": 1,
        "contact_name": "Lakshmi (Mother)",
        "contact_phone": "+919876543210",
        "channel": "SMS",
        "status": "DELIVERED",
        "provider_message_id": "MOCK-SMS-9921",
        "error_message": null
      },
      {
        "id": 2,
        "contact_name": "Suresh (Father)",
        "contact_phone": "+919876543211",
        "channel": "SMS",
        "status": "DELIVERED",
        "provider_message_id": "MOCK-SMS-9922",
        "error_message": null
      }
    ]
  }
}
```
