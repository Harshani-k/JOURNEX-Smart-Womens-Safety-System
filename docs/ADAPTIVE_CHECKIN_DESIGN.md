# JOURNEX – Adaptive Safety Check-In & Missed Check-In System Design

**Project:** JOURNEX – Smart Women's Safety Check-In and Journey Monitoring System  
**Document:** System Design & Technical Specification  
**Component:** Adaptive Check-In Engine (Android Client & Flask Backend)  
**Version:** 1.0.0  
**Phase:** 5  

---

## 1. System Overview & Problem Statement

In women's travel safety, static check-in timers either cause alarm fatigue (if too frequent) or fail to detect emergencies promptly (if too sparse). Furthermore, network connectivity during travel fluctuates between dead zones and strong 5G/LTE coverage.

The **JOURNEX Adaptive Safety Check-In Subsystem** introduces:
1. **Deterministic Rule-Based Check-In Scheduling:** Proactively schedules verification check-ins scaled according to trip duration and journey status.
2. **Adaptive Interval Reduction on Delay:** When an active journey surpasses its expected arrival time (`expected_arrival_time`), the system automatically flags the journey as **DELAYED** and tightens the check-in frequency (e.g. reducing intervals from 15–30 minutes down to 5–10 minutes).
3. **Robust Missed Check-In Escalation:** If a safety prompt passes its deadline (`deadline_at`) without affirmative confirmation, the system marks the check-in as **MISSED**, raising safety risk levels for emergency alerting (Phase 7).
4. **Offline-First Synchronization:** Room database buffers all check-in actions locally, provides instant optimistic UI feedback to the traveler, and synchronizes with the Flask backend using UUID `client_action_id` idempotency.

---

## 2. Check-In Lifecycle & State Transitions

### 2.1 State Transition Diagram

```
                 +---------------+
                 |   SCHEDULED   |
                 +-------+-------+
                         |
           (Alarm fires /| Notification sent)
                         v
                 +---------------+
                 |   REMINDED    |
                 +-------+-------+
                         |
         +---------------+---------------+---------------+
         |                               |               |
(User confirms before)          (Deadline expires       (Journey cancelled
   deadline_at)                  without confirmation)   or completed)
         v                               v               v
+-----------------+             +-----------------+ +---------------+
| CONFIRMED_SAFE  |             |     MISSED      | |   CANCELLED   |
+-----------------+             +-----------------+ +---------------+
         |                               |
  (Terminal Safe)                 (Risk Escalated)
```

### 2.2 State Definitions

| State | Scope | Description |
|---|---|---|
| `SCHEDULED` | Client & Server | The check-in window is registered with a `scheduled_at` timestamp and an enforced `deadline_at` timestamp. |
| `REMINDED` | Client & Server | The scheduled window has opened. High-priority notification shade prompt and audio/haptic alert have been triggered. |
| `CONFIRMED_SAFE` | Client & Server | The traveler actively tapped "I Am Safe" prior to `deadline_at`. Terminal safe state. Next check-in is scheduled. |
| `MISSED` | Client & Server | The deadline passed without confirmation (`now > deadline_at`). Risk level escalates to MEDIUM/HIGH. |
| `CANCELLED` | Client & Server | The journey ended safely or was cancelled prior to the check-in window. |

---

## 3. Adaptive Scheduling Engine

The adaptive scheduling logic is deterministic and rule-based (`backend/app/services/checkin_scheduler.py`):

### 3.1 Interval Calculation Rules

1. **Default Routine Interval:** For normal active journeys, check-ins are spaced at **15 to 30 minutes** (configurable based on total estimated trip duration).
2. **Grace Period:** Every scheduled check-in includes a **3-minute (180-second)** response window between `scheduled_at` and `deadline_at`.
3. **Journey Delay Shortening:**
   - If the current wall-clock time exceeds `journey.expected_arrival_time`:
     - Journey is flagged `is_delayed = True`, and `delayed_at` is recorded.
     - Check-in interval is automatically shortened to **5 to 10 minutes** (default: 5 minutes) to ensure continuous monitoring during unexpected delays.
   - If delay exceeds 30 minutes, check-in interval remains at the minimum 5 minutes, and traveler receives delay confirmation notifications.

### 3.2 Scheduling Algorithm

```python
def calculate_next_checkin_window(journey, base_interval_minutes=15, grace_period_minutes=3):
    now = datetime.now(timezone.utc)
    
    # Check if journey is delayed
    is_delayed = False
    if journey.expected_arrival_time:
        is_delayed = now > journey.expected_arrival_time
        
    # Adapt interval
    interval = 5 if is_delayed else base_interval_minutes
    
    scheduled_at = now + timedelta(minutes=interval)
    deadline_at = scheduled_at + timedelta(minutes=grace_period_minutes)
    
    return scheduled_at, deadline_at, is_delayed
```

---

## 4. Offline Synchronization & Conflict Resolution

### 4.1 Room Database Buffering

Android stores check-in records locally in Room (`checkin_records` table) with the following structure:
- `id`: Local primary key (Auto-increment Long)
- `serverCheckinId`: Server-assigned ID (Nullable Long, populated on remote sync)
- `journeyId`: Associated active journey ID
- `status`: `SCHEDULED`, `REMINDED`, `CONFIRMED_SAFE`, `MISSED`, or `CANCELLED`
- `scheduledAt`: Epoch millisecond timestamp
- `deadlineAt`: Epoch millisecond timestamp
- `respondedAt`: Timestamp when traveler confirmed safety
- `responseType`: `"MANUAL_TAP"`, `"NOTIFICATION_ACTION"`, etc.
- `clientActionId`: UUID string generated on the device
- `syncStatus`: `"PENDING"` or `"SYNCED"`

### 4.2 Optimistic UI Update

When the traveler taps "I Am Safe":
1. Room database updates immediately (`status = CONFIRMED_SAFE`, `respondedAt = now`, `syncStatus = PENDING`).
2. Compose UI updates reactively via Room `Flow<CheckInRecordEntity?>` within milliseconds.
3. Network request is asynchronously dispatched via Retrofit (`POST /api/v1/checkins/<id>/confirm`).
4. Upon HTTP 200/201 response, `syncStatus` transitions to `"SYNCED"`.

### 4.3 Idempotency & Conflict Resolution

- **`client_action_id` Idempotency:** Every check-in and confirmation action carries a unique UUID. The backend stores this ID and ignores duplicate requests with the same action ID, returning the existing recorded confirmation.
- **Server-Authoritative Expiration:** If the device confirms safety after being offline, but the server has already executed `detect-missed` and flagged the check-in as `MISSED` past its deadline:
  - Backend responds with `409 Conflict` (`Check-in deadline has expired. Marked as MISSED.`).
  - Android client respects the server decision, updates local Room state to `MISSED`, and alerts the user to re-confirm on an active window.

---

## 5. Local Notification Architecture

JOURNEX utilizes Android's system-level notification and alarm managers:

1. **Notification Channel:** `journex_checkin_channel`
   - Name: "JOURNEX Safety Check-In"
   - Importance: `NotificationManager.IMPORTANCE_HIGH`
   - Vibration: Enabled
   - Badge: Enabled
2. **Precise Wakeup Alarm:**
   - `AlarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)`
   - Ensures the device wakes up even in Doze mode when `scheduled_at` arrives.
3. **Interactive Notification Actions:**
   - **Shade Action Button:** `I AM SAFE` triggers `CheckInActionReceiver` without opening the full UI.
   - **Content Tap:** Launches `MainActivity` with deep link directly to `ActiveJourneyScreen`.
4. **Broadcast Receivers:**
   - `CheckInAlarmReceiver`: Fires at `scheduled_at`, builds and posts the urgent check-in notification.
   - `CheckInActionReceiver`: Catches "I AM SAFE" notification shade tap, cancels notification, and invokes `checkInRepository.confirmSafety(journeyId, checkInId)`.

### 5.1 System Timing Constraints & Battery Management

> [!NOTE]
> Exact-time notifications on Android (API 23+) are inherently constrained by Doze mode, app standby buckets, and vendor power optimizations. `AlarmManager.setAndAllowWhileIdle()` provides best-effort wakeups under normal conditions. In high-risk scenarios, backend-driven deadline monitoring (`detect-missed`) serves as the authoritative safety verification mechanism.

### 5.2 Device Reboot Behavior

System alarms registered with `AlarmManager` are cleared by Android OS when a device reboots. Reboot rescheduling is not currently handled via a `RECEIVE_BOOT_COMPLETED` receiver. When JOURNEX is opened or the traveler navigates to an active journey, the client automatically detects missing future alarms and re-registers the next scheduled check-in window.

---

## 6. Architecture Verification Matrix

| Component | Responsibility | Implementation File | Verification Test |
|---|---|---|---|
| CheckIn Model | Database representation & relations | `backend/app/models/checkin.py` | `test_checkins.py::test_checkin_model_creation` |
| Journey Delay Flag | Delay tracking fields | `backend/app/models/journey.py` | `test_checkins.py::test_delay_detection_endpoint` |
| Adaptive Scheduler | Interval calculation & delay shortening | `backend/app/services/checkin_scheduler.py` | `test_checkins.py::test_scheduler_delay_adaptation` |
| CheckIn Routes | REST API endpoints | `backend/app/routes/checkins.py` | `test_checkins.py::test_confirm_checkin_success` |
| Room Entity & DAO | Local persistence & Flow queries | `data/local/entity/Entities.kt`, `Daos.kt` | `CheckInTrackingTest::testCheckInEntityDefaultInitialization` |
| CheckIn Repository | Offline buffer & remote sync | `data/repository/CheckInRepository.kt` | `CheckInTrackingTest::testSafeConfirmationStateTransition` |
| Notification Manager | High-priority alert & AlarmManager | `notification/CheckInNotificationManager.kt` | Device verification & shade action test |
| Active Journey Screen | Live countdown & delay banner | `ui/screens/journey/ActiveJourneyScreen.kt` | Device verification on vivo V2513 |
