# JOURNEX Backend Phase 4 Report: Real GPS Tracking & Location Ingestion

**Project:** JOURNEX – Smart Women's Safety Check-In and Journey Monitoring System  
**Phase:** 4 – Real GPS Tracking & Background Journey Monitoring (Backend Subsystem)  
**Status:** Complete  
**Date:** 2026-11-22  
**Test Suite:** 65/65 Pytest Tests Passing (100%)  

---

## 1. Executive Summary

In Phase 4, the backend subsystem was augmented to support high-throughput, resilient GPS telemetry ingestion for active journeys. In accordance with strict safety-critical guidelines, all telemetry ingestion is strictly bounded, deduplicated, isolated by authenticated user ownership, and validated against physical geodesic limits.

---

## 2. Database Schema & Migration

### Location Model (`backend/app/models/journey_location.py`)
- **Table Name:** `journey_locations`
- **Fields:**
  - `id` (Integer, Primary Key, Auto-increment)
  - `journey_id` (Integer, Foreign Key to `journeys.id`, Indexed)
  - `latitude` (Float, Not Null) – Validated within $[-90.0, 90.0]$
  - `longitude` (Float, Not Null) – Validated within $[-180.0, 180.0]$
  - `accuracy` (Float, Nullable) – Horizontal accuracy radius in meters ($\ge 0$)
  - `altitude` (Float, Nullable) – Elevation above sea level in meters
  - `speed` (Float, Nullable) – Velocity in meters per second ($\ge 0$)
  - `bearing` (Float, Nullable) – Direction of travel in degrees $[0.0, 360.0]$
  - `recorded_at` (DateTime, Not Null, Indexed) – Client hardware fix timestamp (UTC)
  - `received_at` (DateTime, Not Null, Default UTC) – Server ingestion timestamp (UTC)
- **Composite Index:** `ix_journey_locations_journey_recorded` on `(journey_id, recorded_at)` for millisecond telemetry lookups and fast deduplication.

### Alembic Database Migration
- Generated migration `e750bce88341_create_journey_locations_table.py`.
- Successfully applied to SQLite development instance and verified compatible with MySQL schema definitions.

---

## 3. Endpoints Implemented

All endpoints adhere to the standard JOURNEX response envelope `{"status": "success"|"error", "data": ..., "message": ...}` and require a valid Bearer JWT.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/journeys/<journey_id>/locations` | Ingests a single fix or batch of fixes (up to 100) with deduplication |
| `GET` | `/api/v1/journeys/<journey_id>/locations` | Paginated chronological GPS trace with timestamp filters |
| `GET` | `/api/v1/journeys/<journey_id>/locations/latest` | Retrieves the most recent recorded GPS location fix |

---

## 4. Safety & Ingestion Controls

1. **Active Journey Validation:** Telemetry uploads are strictly forbidden for completed, cancelled, or planned journeys (`400 Bad Request`).
2. **User Data Isolation:** Telemetry can only be queried or uploaded by the authenticated journey owner (`403 Forbidden` / `404 Not Found`).
3. **Geodesic Range Validation:** Coordinates outside physical Earth bounds are rejected with descriptive validation errors.
4. **Hardware Deduplication:** Fixes sharing the identical UTC epoch (`recorded_at`) for a journey are discarded without throwing errors, returning an accurate count of newly inserted points.
5. **Batch Processing:** Supports array payloads up to 100 points per network transmission to accommodate intermittent cellular connectivity.

---

## 5. Automated Verification Results

Full automated test suite executed via `pytest`:
- **Total Backend Tests:** 65
- **Tests Passed:** 65
- **Tests Failed:** 0
- **Execution Duration:** 11.06 seconds
- **Key Location Test Coverage (`tests/test_journey_locations.py`):**
  - Single location ingestion with full telemetry fields.
  - Batch location upload and deduplication verification.
  - Rejection of uploads for non-active journeys (`CANCELLED`, `COMPLETED`).
  - Validation failures on coordinates outside Earth bounds.
  - Strict user isolation preventing unauthorized access.
  - Paginated history retrieval with limit and offset boundaries.
  - Latest location resolution for active journeys.
