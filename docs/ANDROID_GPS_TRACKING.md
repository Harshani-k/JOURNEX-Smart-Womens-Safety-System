# JOURNEX – Android Real GPS Tracking Architecture

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Native Android GPS & Background Service Subsystem  
**Specification Version:** 1.0.0  

---

## 1. System Architecture

The JOURNEX Android application implements reliable, battery-conscious, hardware-backed GPS tracking using Android's modern location architecture:
- **`FusedLocationProviderClient`:** Fuses GPS satellites, Wi-Fi networks, and cellular cell towers for fast time-to-first-fix (TTFF) and accurate outdoor telemetry.
- **`JourneyTrackingService`:** An Android Foreground Service declaring `android:foregroundServiceType="location"`, guaranteeing continuous location updates when the app is backgrounded or the screen is locked.
- **Local Persistence (`Room`):** Every location fix is recorded to SQLite via Room (`JourneyLocationEntity`) with status `PENDING`, ensuring zero data loss during cellular dropouts.
- **Asynchronous Sync (`LocationSyncRepository`):** Batch synchronizes local locations to the Flask backend without blocking location callbacks or UI threads.

---

## 2. Permission Requirements & Android Target SDK Alignment

| Permission | Minimum API | Purpose | Runtime Prompt |
| :--- | :--- | :--- | :--- |
| `ACCESS_FINE_LOCATION` | API 1 | High-accuracy GPS fixes | Yes (Prompted before journey start) |
| `ACCESS_COARSE_LOCATION` | API 1 | Approximate network location fallback | Yes (Paired with fine location) |
| `FOREGROUND_SERVICE` | API 28 | Background execution permission | Manifest only |
| `FOREGROUND_SERVICE_LOCATION`| API 34 | Location-specific foreground service type | Manifest only |
| `POST_NOTIFICATIONS` | API 33 | User visibility for ongoing foreground service | Yes (Android 13+) |

---

## 3. Power Consumption & Accuracy Profile

- **Priority:** `Priority.PRIORITY_HIGH_ACCURACY`
- **Interval:** 5,000 milliseconds (5 seconds)
- **Fastest Interval:** 2,000 milliseconds (2 seconds)
- **Smallest Displacement:** 3.0 meters (suppresses noise when stationary)
- **Accuracy Filter:** Discards fixes with horizontal accuracy > 200 meters.
