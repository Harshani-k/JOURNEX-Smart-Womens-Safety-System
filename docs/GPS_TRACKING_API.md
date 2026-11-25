# JOURNEX – GPS Location Tracking API Specification

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Real-Time GPS Location Tracking Subsystem (`/api/v1/journeys/<journey_id>/locations`)  
**Specification Version:** 1.0.0  
**Target Clients:** JOURNEX Native Android Application (Kotlin / Jetpack Compose)  

---

## 1. Overview & Data Ingestion Flow

The GPS Location Tracking API ingests real-time geographic telemetry from the Android client's foreground location service during active journeys. It supports high-frequency updates, batch uploads to conserve battery and tolerate intermittent cellular connectivity, and automatic duplicate detection.

### Ingestion Flow:
```
+-----------------------------------------------------------------------+
|                         ANDROID DEVICE CLIENT                         |
|                                                                       |
|  [FusedLocationProvider]                                              |
|            |                                                          |
|            v                                                          |
|  [JourneyTrackingService (Foreground Service)]                        |
|            |                                                          |
|            v                                                          |
|  [Room Database: journey_locations (syncStatus: PENDING)]              |
|            |                                                          |
|            v                                                          |
|  [LocationSyncRepository (Network Batch)]                             |
+------------|----------------------------------------------------------+
             | POST /api/v1/journeys/{id}/locations
             | (Bearer JWT Token)
             v
+-----------------------------------------------------------------------+
|                          FLASK REST BACKEND                           |
|                                                                       |
|  [LocationService.record_locations()]                                 |
|            |                                                          |
|            +---> Validate: -90<=lat<=90, -180<=lng<=180, accuracy>=0  |
|            +---> Check: Journey must be in ACTIVE status              |
|            +---> Deduplicate: Check existing (journey_id, recorded_at)|
|            |                                                          |
|            v                                                          |
|  [Database Table: journey_locations]                                  |
+-----------------------------------------------------------------------+
```

---

## 2. Database Schema (`journey_locations`)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Fix identifier |
| `journey_id` | INTEGER | FOREIGN KEY (`journeys.id`), INDEXED, NOT NULL | Journey identifier (cascade delete) |
| `latitude` | FLOAT | NOT NULL | WGS 84 latitude (-90.0 to 90.0) |
| `longitude` | FLOAT | NOT NULL | WGS 84 longitude (-180.0 to 180.0) |
| `accuracy` | FLOAT | NOT NULL | Horizontal 68% confidence radius in meters |
| `altitude` | FLOAT | NULLABLE | Altitude above WGS 84 ellipsoid in meters |
| `speed` | FLOAT | NULLABLE | Speed over ground in meters per second |
| `bearing` | FLOAT | NULLABLE | Direction of travel in degrees (0.0 to 360.0) |
| `recorded_at` | DATETIME | NOT NULL, INDEXED, UTC | GPS satellite/device fix capture timestamp |
| `received_at` | DATETIME | NOT NULL, UTC | Backend server receipt timestamp |

---

## 3. API Endpoints

### 3.1 Upload GPS Locations (Batch or Single)
- **Endpoint:** `POST /api/v1/journeys/<int:journey_id>/locations`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)
- **Condition:** Journey must belong to the authenticated user and have `status = "ACTIVE"`.

#### Request Body (Batch Upload):
```json
{
  "locations": [
    {
      "latitude": 12.971598,
      "longitude": 77.594566,
      "accuracy": 8.5,
      "altitude": 920.0,
      "speed": 12.0,
      "bearing": 180.0,
      "recorded_at": "2026-11-22T08:15:30Z"
    },
    {
      "latitude": 12.972100,
      "longitude": 77.595100,
      "accuracy": 7.2,
      "altitude": 921.5,
      "speed": 11.5,
      "bearing": 178.0,
      "recorded_at": "2026-11-22T08:15:35Z"
    }
  ]
}
```

#### Success Response (`201 Created`):
```json
{
  "success": true,
  "message": "Locations uploaded successfully.",
  "data": {
    "accepted_count": 2,
    "rejected_count": 0,
    "total_received": 2
  },
  "errors": null,
  "timestamp": "2026-11-22T08:15:36.123456+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Invalid coordinates, negative accuracy/speed, batch size > 100, or journey is not in `ACTIVE` status.
- `401 Unauthorized`: Missing or invalid Bearer token.
- `404 Not Found`: Journey not found or belongs to another user.

---

### 3.2 Retrieve Location History
- **Endpoint:** `GET /api/v1/journeys/<int:journey_id>/locations`
- **Authentication:** Bearer Access Token
- **Query Parameters:**
  - `page` (default 1)
  - `per_page` (default 50, max 100)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Location history retrieved successfully.",
  "data": {
    "locations": [
      {
        "id": 1,
        "journey_id": 1,
        "latitude": 12.971598,
        "longitude": 77.594566,
        "accuracy": 8.5,
        "altitude": 920.0,
        "speed": 12.0,
        "bearing": 180.0,
        "recorded_at": "2026-11-22T08:15:30+00:00",
        "received_at": "2026-11-22T08:15:36+00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  },
  "errors": null,
  "timestamp": "2026-11-22T08:15:40+00:00"
}
```

---

### 3.3 Get Latest GPS Location Fix
- **Endpoint:** `GET /api/v1/journeys/<int:journey_id>/locations/latest`
- **Authentication:** Bearer Access Token

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Latest location retrieved successfully.",
  "data": {
    "id": 142,
    "journey_id": 1,
    "latitude": 12.978369,
    "longitude": 77.640839,
    "accuracy": 6.0,
    "altitude": 915.0,
    "speed": 0.0,
    "bearing": 90.0,
    "recorded_at": "2026-11-22T08:45:00+00:00",
    "received_at": "2026-11-22T08:45:02+00:00"
  },
  "errors": null,
  "timestamp": "2026-11-22T08:45:03+00:00"
}
```
