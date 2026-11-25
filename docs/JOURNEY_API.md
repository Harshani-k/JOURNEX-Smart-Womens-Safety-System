# JOURNEX – Journey Management API Specification

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Journey Lifecycle Subsystem (`/api/v1/journeys`)  
**Specification Version:** 1.0.0  
**Target Clients:** JOURNEX Native Android Application (Kotlin / Jetpack Compose)  

---

## 1. Overview & Lifecycle State Machine

The Journey Management Subsystem is responsible for planning, tracking the lifecycle of, and archiving women's travel journeys.

### Journey Lifecycle State Machine:
```
                 +-----------------------+
                 |         DRAFT         | <----+ (Initial State)
                 +-----------------------+
                   |                   |
           start() |                   | cancel()
                   v                   v
         +-------------------+   +-----------+
         |      ACTIVE       |   | CANCELLED |
         +-------------------+   +-----------+
           |               |
complete() |               | cancel()
           v               v
     +-----------+   +-----------+
     | COMPLETED |   | CANCELLED |
     +-----------+   +-----------+
```

### Business Rules:
1. **Ownership Derived from JWT:** The API never trusts a client-supplied `user_id`. Every action is scoped to the user ID inside the authenticated token.
2. **Initial State:** All new journeys are created in `DRAFT` status.
3. **Single Active Journey:** A user can only have **at most one active journey** at any point in time. Attempting to start another journey returns `409 Conflict`.
4. **Editable Only in DRAFT:** Journey titles, origins, destinations, and arrival times can only be modified while in `DRAFT` status (`PUT` on `ACTIVE`, `COMPLETED`, or `CANCELLED` journeys returns `400 Bad Request`).
5. **Timestamp Recording:**
   - Transitioning `DRAFT` -> `ACTIVE` records `actual_start_time` in UTC.
   - Transitioning `ACTIVE` -> `COMPLETED` records `actual_arrival_time` in UTC.
6. **Cancellation:** `DRAFT` and `ACTIVE` journeys may be cancelled with an optional `cancellation_reason`. Completed journeys cannot be cancelled.
7. **History Separation:** The history endpoint strictly queries journeys in `COMPLETED` and `CANCELLED` statuses.
8. **Resource Isolation:** Accessing another user's journey returns `404 Not Found` (never `403`), eliminating ID enumeration vulnerabilities.

---

## 2. Database Schema (`journeys`)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal journey ID |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), INDEXED, NOT NULL | Foreign key to user account (on delete cascade) |
| `journey_title` | VARCHAR(150) | NOT NULL | Human-readable title for journey |
| `start_location_name` | VARCHAR(150) | NOT NULL | Origin venue or landmark name |
| `start_location_address` | VARCHAR(255) | NOT NULL | Physical origin street address |
| `start_latitude` | FLOAT | NULLABLE | Origin latitude (-90.0 to 90.0) |
| `start_longitude` | FLOAT | NULLABLE | Origin longitude (-180.0 to 180.0) |
| `destination_name` | VARCHAR(150) | NOT NULL | Destination venue or landmark name |
| `destination_address` | VARCHAR(255) | NOT NULL | Physical destination street address |
| `destination_latitude` | FLOAT | NULLABLE | Destination latitude (-90.0 to 90.0) |
| `destination_longitude` | FLOAT | NULLABLE | Destination longitude (-180.0 to 180.0) |
| `planned_start_time` | DATETIME | NOT NULL, UTC | Scheduled start time |
| `expected_arrival_time` | DATETIME | INDEXED, NOT NULL, UTC | Estimated arrival time |
| `actual_start_time` | DATETIME | NULLABLE, UTC | Actual timestamp journey started |
| `actual_arrival_time` | DATETIME | NULLABLE, UTC | Actual timestamp journey completed |
| `status` | VARCHAR(20) | INDEXED, NOT NULL, DEFAULT 'DRAFT' | Status: `DRAFT`, `ACTIVE`, `COMPLETED`, `CANCELLED` |
| `cancellation_reason` | VARCHAR(255) | NULLABLE | Explanation if journey was cancelled |
| `created_at` | DATETIME | NOT NULL, UTC | Record creation timestamp |
| `updated_at` | DATETIME | NOT NULL, UTC | Last modification timestamp |

---

## 3. Endpoints

### 3.1 Create Journey (DRAFT)
- **Endpoint:** `POST /api/v1/journeys`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Request Body:
```json
{
  "journey_title": "Evening Commute from Office",
  "start_location_name": "MG Road Metro Station",
  "start_location_address": "MG Road, Bengaluru",
  "start_latitude": 12.9756,
  "start_longitude": 77.6066,
  "destination_name": "Home Residency",
  "destination_address": "Indiranagar 100ft Road, Bengaluru",
  "destination_latitude": 12.9784,
  "destination_longitude": 77.6408,
  "planned_start_time": "2026-11-22T14:00:00Z",
  "expected_arrival_time": "2026-11-22T15:00:00Z"
}
```

#### Success Response (`201 Created`):
```json
{
  "success": true,
  "message": "Journey created successfully in DRAFT status.",
  "data": {
    "id": 1,
    "journey_title": "Evening Commute from Office",
    "start_location": {
      "name": "MG Road Metro Station",
      "address": "MG Road, Bengaluru",
      "latitude": 12.9756,
      "longitude": 77.6066
    },
    "destination": {
      "name": "Home Residency",
      "address": "Indiranagar 100ft Road, Bengaluru",
      "latitude": 12.9784,
      "longitude": 77.6408
    },
    "planned_start_time": "2026-11-22T14:00:00+00:00",
    "expected_arrival_time": "2026-11-22T15:00:00+00:00",
    "actual_start_time": null,
    "actual_arrival_time": null,
    "status": "DRAFT",
    "cancellation_reason": null,
    "created_at": "2026-11-22T07:36:26.466782",
    "updated_at": "2026-11-22T07:36:26.466782"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:36:26.473794+00:00"
}
```

---

### 3.2 List Journeys
- **Endpoint:** `GET /api/v1/journeys`
- **Query Parameters:**
  - `page` (optional integer, default `1`)
  - `per_page` (optional integer, default `10`, max `50`)
  - `status` (optional filter: `DRAFT`, `ACTIVE`, `COMPLETED`, `CANCELLED`)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Journeys retrieved successfully.",
  "data": {
    "journeys": [ ... ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 3,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  },
  "errors": null,
  "timestamp": "2026-11-22T07:36:26.500000+00:00"
}
```

---

### 3.3 Get Active Journey
- **Endpoint:** `GET /api/v1/journeys/active`
- **Authentication:** Bearer Access Token

#### Success Response (Active Journey Exists) (`200 OK`):
```json
{
  "success": true,
  "message": "Active journey retrieved successfully.",
  "data": {
    "id": 1,
    "journey_title": "Evening Commute from Office",
    "status": "ACTIVE",
    "actual_start_time": "2026-11-22T07:36:26.521798",
    ...
  },
  "errors": null,
  "timestamp": "2026-11-22T07:36:26.530000+00:00"
}
```

#### Success Response (No Active Journey) (`200 OK`):
```json
{
  "success": true,
  "message": "No active journey found.",
  "data": null,
  "errors": null,
  "timestamp": "2026-11-22T07:36:26.530000+00:00"
}
```

---

### 3.4 Start Journey
- **Endpoint:** `POST /api/v1/journeys/<journey_id>/start`
- **Authentication:** Bearer Access Token

Transitions journey from `DRAFT` to `ACTIVE`. Automatically records `actual_start_time`.

#### Error Responses:
- `400 Bad Request`: Journey is already active, completed, or cancelled.
- `409 Conflict`: User already has another active journey.

---

### 3.5 Complete Journey
- **Endpoint:** `POST /api/v1/journeys/<journey_id>/complete`
- **Authentication:** Bearer Access Token

Transitions journey from `ACTIVE` to `COMPLETED`. Automatically records `actual_arrival_time`.

#### Error Responses:
- `400 Bad Request`: Journey is not currently `ACTIVE`.

---

### 3.6 Cancel Journey
- **Endpoint:** `POST /api/v1/journeys/<journey_id>/cancel`
- **Authentication:** Bearer Access Token

#### Request Body (Optional):
```json
{
  "cancellation_reason": "Change of plans; working from home"
}
```

#### Error Responses:
- `400 Bad Request`: Journey is already `COMPLETED` or `CANCELLED`.

---

### 3.7 Journey History
- **Endpoint:** `GET /api/v1/journeys/history`
- **Query Parameters:** `page`, `per_page`
- Returns only `COMPLETED` and `CANCELLED` journeys, ordered most recent first.

---

## 4. Android Client Integration Contracts (Kotlin)

```kotlin
package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class LocationPointDto(
    @SerializedName("name") val name: String,
    @SerializedName("address") val address: String,
    @SerializedName("latitude") val latitude: Double?,
    @SerializedName("longitude") val longitude: Double?
)

data class JourneyDto(
    @SerializedName("id") val id: Int,
    @SerializedName("journey_title") val journeyTitle: String,
    @SerializedName("start_location") val startLocation: LocationPointDto,
    @SerializedName("destination") val destination: LocationPointDto,
    @SerializedName("planned_start_time") val plannedStartTime: String,
    @SerializedName("expected_arrival_time") val expectedArrivalTime: String,
    @SerializedName("actual_start_time") val actualStartTime: String?,
    @SerializedName("actual_arrival_time") val actualArrivalTime: String?,
    @SerializedName("status") val status: String,
    @SerializedName("cancellation_reason") val cancellationReason: String?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String
)

data class CreateJourneyRequest(
    @SerializedName("journey_title") val journeyTitle: String,
    @SerializedName("start_location_name") val startLocationName: String,
    @SerializedName("start_location_address") val startLocationAddress: String,
    @SerializedName("start_latitude") val startLatitude: Double? = null,
    @SerializedName("start_longitude") val startLongitude: Double? = null,
    @SerializedName("destination_name") val destinationName: String,
    @SerializedName("destination_address") val destinationAddress: String,
    @SerializedName("destination_latitude") val destinationLatitude: Double? = null,
    @SerializedName("destination_longitude") val destinationLongitude: Double? = null,
    @SerializedName("planned_start_time") val plannedStartTime: String,
    @SerializedName("expected_arrival_time") val expectedArrivalTime: String
)

data class CancelJourneyRequest(
    @SerializedName("cancellation_reason") val cancellationReason: String? = null
)
```
