# JOURNEX – Phase 8: SOS & Multi-Level Emergency Alert Escalation Android Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Android Application Subsystem (`android/`)  
**Date:** November 22, 2026  
**Status:** **PASSED & VERIFIED ON HARDWARE (vivo V2513 – Android 16)**  
**Lead Role:** Lead Android Mobile Architect  

---

## 1. Executive Summary

Phase 8 integrates the SOS Panic and Multi-Level Emergency Alert Escalation system into the JOURNEX Android application. The client interface combines immediate panic button accessibility with a 5-second cancelable countdown dialog, offline-first Room local persistence, real-time escalation status monitoring, discreet silent safety alerts, and user-authorized emergency dialer invocation.

All implementations strictly adhere to:
- [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md)
- [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md)
- [`docs/EMERGENCY_ESCALATION_DESIGN.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/EMERGENCY_ESCALATION_DESIGN.md)
- [`docs/EMERGENCY_API.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/EMERGENCY_API.md)

### Key Achievements:
- **Room Database Upgrade to Version 6:**
  - Added `emergency_events` and `emergency_alert_dispatches` tables.
  - Implemented lossless migration `MIGRATION_5_6` preserving all user profiles, contacts, and check-ins.
- **Offline-First Emergency Repository (`EmergencyRepository.kt`):**
  - Instant optimistic local Room persistence.
  - Non-blocking background network synchronization to Flask backend.
  - Periodic polling of dispatch delivery status when an emergency is active.
- **Emergency UI Integration (`ActiveJourneyScreen.kt`, `SosEmergencyButton.kt`):**
  - **SosEmergencyButton:** Accessible 72dp high-contrast panic bar with 5-second countdown cancellation dialog.
  - **Active Emergency Status & Escalation Monitor Card:** Rendered dynamically when `activeEmergency != null`, displaying current escalation level (1 to 3), location snapshot, dispatched guardians, and delivery badges (`[DELIVERED]`).
  - **I Am Safe (Cancel Emergency):** Confirmation dialog immediately cancelling active alert and triggering backend safe notices.
  - **Escalate Level Button:** Allows manual escalation to secondary or tertiary guardians.
  - **Call Primary Guardian:** Launches `Intent.ACTION_DIAL` with `tel:<phone>`, presenting native dialer with prefilled number for explicit user confirmation.
  - **Discreet Silent Alert:** Triggers `SILENT_ALERT` emergency event without sirens or flashing UI for vulnerable situations.
- **Unit Testing (`EmergencySosTest.kt`):**
  - 8 comprehensive test cases verifying entity initialization, escalation bounds, cancellation transitions, trigger validation, DTO serialization, and safe dialer URI format.
  - Full suite passed cleanly via `gradlew.bat testDebugUnitTest`.
- **Physical Hardware Verification:**
  - Assembled `app-debug.apk` in 23 seconds.
  - Stream-installed and launched on **vivo V2513** (`10BG2E010L007AJ`).
  - Screenshot verified at `phase8_device.png`.

---

## 2. Room Local Architecture & Migration

### 2.1 Database Entities (`Entities.kt`)
- `EmergencyEventEntity` (Table: `emergency_events`):
  - Primary key: `id` (auto-generate).
  - Server ID: `serverEventId` (nullable).
  - Trigger details: `triggerType`, `status`, `triggerTimestamp`, `cancellationTimestamp`, `cancellationReason`.
  - Coordinates: `latitude`, `longitude`, `accuracy`, `locationAddress`.
  - Escalation bounds: `currentEscalationLevel` (1..3), `maxEscalationLevel` (3).
  - Synchronization: `clientActionId`, `syncStatus` (`PENDING`, `SYNCED`).
- `EmergencyAlertDispatchEntity` (Table: `emergency_alert_dispatches`):
  - Primary key: `id` (auto-generate).
  - Foreign key: `emergencyEventId`.
  - Guardian info: `contactName`, `contactPhone`, `escalationLevel`.
  - Provider telemetry: `channel`, `status`, `providerMessageId`, `errorMessage`.

### 2.2 Room Migration: `MIGRATION_5_6` (`JournexDatabase.kt`)
```kotlin
val MIGRATION_5_6 = object : Migration(5, 6) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS emergency_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                serverEventId INTEGER,
                journeyId INTEGER,
                triggerType TEXT NOT NULL,
                status TEXT NOT NULL,
                triggerTimestamp INTEGER NOT NULL,
                cancellationTimestamp INTEGER,
                cancellationReason TEXT,
                latitude REAL,
                longitude REAL,
                accuracy REAL,
                locationAddress TEXT,
                currentEscalationLevel INTEGER NOT NULL,
                maxEscalationLevel INTEGER NOT NULL,
                clientActionId TEXT NOT NULL,
                syncStatus TEXT NOT NULL,
                createdAt INTEGER NOT NULL,
                updatedAt INTEGER NOT NULL
            )
        """)
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS emergency_alert_dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                serverDispatchId INTEGER,
                emergencyEventId INTEGER NOT NULL,
                contactName TEXT NOT NULL,
                contactPhone TEXT NOT NULL,
                escalationLevel INTEGER NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                providerMessageId TEXT,
                errorMessage TEXT,
                sentAt INTEGER,
                deliveredAt INTEGER,
                syncStatus TEXT NOT NULL
            )
        """)
    }
}
```

---

## 3. UI Component Architecture

### 3.1 Active Emergency & Escalation Monitor Card
When an emergency is triggered, `ActiveJourneyScreen` detects `activeEmergency != null` from `EmergencyRepository.getActiveEmergencyFlow()` and renders a high-visibility card:
- **Emergency Red Container** with solid border and pulsing warning icon.
- **Escalation Badge:** Displays `LEVEL 1 OF 3` (or Level 2/3).
- **Dispatched Contacts List:** Real-time delivery badges (`[SENT]`, `[DELIVERED]`).
- **Interactive Action Controls:**
  - `I Am Safe`: Prompts confirmation dialog to cancel emergency.
  - `Escalate Level`: Advances escalation to the next guardian tier.
  - `Call`: Opens native phone dialer with primary contact's phone number.

### 3.2 Safe Calling Architecture
To guarantee security and privacy, JOURNEX adheres to Google Play and Android security policies:
```kotlin
val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$primaryPhone"))
context.startActivity(intent)
```
- Never uses silent `ACTION_CALL` or bypasses user confirmation.
- The phone dialer is presented with the guardian's number prefilled, requiring the user to tap Call.

---

## 4. Hardware Verification & Artifacts

- **Device:** vivo V2513 (Android 16, API 36)
- **Serial:** `10BG2E010L007AJ`
- **Reverse Port Tunnel:** `adb -s 10BG2E010L007AJ reverse tcp:5000 tcp:5000`
- **Install Output:** `Success`
- **Screenshot Artifact:** `phase8_device.png`
