# JOURNEX – Phase 7: Android Explainable ML Risk Analysis Client Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Native Android Client (`android/`)  
**Date:** November 22, 2026  
**Status:** **PASSED & OPERATIONAL (100% Unit Tests Passing – 31/31 Tests; Installed on vivo V2513)**  
**Lead Role:** Senior Android Architect, Kotlin Developer & QA Engineer  

---

## 1. Executive Summary

Phase 7 implements native Android client integration for the **Explainable AI/ML Risk Analysis Subsystem** in **JOURNEX**.

The implementation preserves the Purple and Lavender design system, Material 3 styling, MVVM architecture, and Room local persistence while adding real-time, explainable risk visualization directly on the active journey screen.

All implementations strictly adhere to:
- [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md)
- [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md)
- [`docs/ML_RISK_ANALYSIS_DESIGN.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ML_RISK_ANALYSIS_DESIGN.md)
- [`docs/ML_MODEL_EVALUATION.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ML_MODEL_EVALUATION.md)

### Key Achievements:
- **Zero UI Redesign:** Seamlessly integrates an AI Risk Assessment Card into the existing `ActiveJourneyScreen` with Material 3 styling and Purple/Lavender palette.
- **Room v5 Database Migration (`MIGRATION_4_5`):** Created `risk_analyses` local table with indexed query support, guaranteeing zero data loss for existing users.
- **Offline Caching & Flow Observation:** Room serves as the local source of truth; when network is offline, the last evaluated risk score and factors remain immediately visible.
- **Explainability Visualization:** Displays category badge, linear score progress bar, and parsed contributing factors list with color-coded impact chips (`[CRITICAL]`, `[HIGH]`, `[MODERATE]`, `[POSITIVE]`, `[NEUTRAL]`).
- **Insufficient-Data State:** Renders an informative guidance banner when journey telemetry is insufficient, preventing spurious alarm.
- **Non-Blocking Architecture:** Risk evaluations run on background coroutines (`Dispatchers.IO`), never blocking foreground GPS tracking, countdown timers, or SOS triggers.
- **31 Unit Tests Passing:** 100% pass rate across 7 test suites via `testDebugUnitTest` (including 6/6 in `RiskAnalysisTest.kt`).
- **Hardware Deployment:** Clean `assembleDebug` APK deployed to physical hardware (**vivo V2513**, Android 16).

---

## 2. Android Source Architecture

```
android/app/src/main/java/com/journex/safety/
├── data/
│   ├── local/
│   │   ├── dao/
│   │   │   └── Daos.kt                 # RiskAnalysisDao (latest flow, insert, clear)
│   │   ├── entity/
│   │   │   └── Entities.kt             # RiskAnalysisEntity (Room v5 schema)
│   │   └── JournexDatabase.kt          # Room v5 with MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5
│   ├── remote/
│   │   ├── api/
│   │   │   └── JournexRiskApi.kt       # Retrofit risk endpoints (analyze, latest, history)
│   │   ├── model/
│   │   │   └── RiskAnalysisModels.kt   # DTOs (RiskAnalysisDto, RiskContributingFactorDto, etc.)
│   │   └── RetrofitClient.kt           # Exposes riskApi singleton
│   └── repository/
│       └── RiskAnalysisRepository.kt   # Offline Room caching, Gson parsing, background fetch
└── ui/
    └── screens/
        └── journey/
            └── ActiveJourneyScreen.kt   # AI Journey Risk Assessment Card & factor list
```

---

## 3. Room Database Schema & Migration

### 3.1 RiskAnalysisEntity Definition (`Entities.kt`)

```kotlin
@Entity(tableName = "risk_analyses")
data class RiskAnalysisEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val serverAnalysisId: Long? = null,
    val journeyId: Long,
    val riskScore: Float, // 0.0 to 1.0
    val riskCategory: String, // "LOW", "MODERATE", "HIGH", "CRITICAL"
    val contributingFactorsJson: String, // JSON array string
    val modelVersion: String = "1.0.0-rf",
    val isInsufficientData: Boolean = false,
    val analyzedAt: Long = System.currentTimeMillis(),
    val createdAt: Long = System.currentTimeMillis()
)
```

### 3.2 Backward-Compatible Migration (`MIGRATION_4_5`)

Implemented in [`JournexDatabase.kt`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/android/app/src/main/java/com/journex/safety/data/local/JournexDatabase.kt):

```kotlin
val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS risk_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                serverAnalysisId INTEGER,
                journeyId INTEGER NOT NULL,
                riskScore REAL NOT NULL,
                riskCategory TEXT NOT NULL,
                contributingFactorsJson TEXT NOT NULL,
                modelVersion TEXT NOT NULL,
                isInsufficientData INTEGER NOT NULL DEFAULT 0,
                analyzedAt INTEGER NOT NULL,
                createdAt INTEGER NOT NULL
            )
        """.trimIndent())
        db.execSQL("CREATE INDEX IF NOT EXISTS index_risk_analyses_journeyId ON risk_analyses(journeyId)")
        db.execSQL("CREATE INDEX IF NOT EXISTS index_risk_analyses_analyzedAt ON risk_analyses(analyzedAt)")
    }
}
```

Registered via:
```kotlin
.addMigrations(MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5)
```

---

## 4. UI Components & User Experience

### 4.1 Visual Design Hierarchy (`ActiveJourneyScreen.kt`)
The **AI Journey Risk Assessment Card** incorporates:
1. **Header Row:**
   - Icon: `Icons.Default.Analytics` in `PurplePrimary`.
   - Title: **"AI Journey Risk Assessment"** with subtitle indicating model version (`1.0.0-rf (Random Forest)`).
   - Category Badge: High-contrast pill badge with dynamic colors:
     - `LOW RISK`: Guardian Teal container & text.
     - `MODERATE RISK`: Warning Amber container & text.
     - `HIGH RISK`: Deep Orange container (`#FFE0B2`) & text (`#E65100`).
     - `CRITICAL RISK`: Emergency Red container (`#FFCDD2`) & text.
2. **Quantitative Risk Score Bar:**
   - LinearProgressIndicator tracking $S \in [0.0, 1.0]$.
   - Displays percentage and numeric decimal (e.g. `12% (0.12)`).
3. **Insufficient Telemetry State:**
   - When a trip recently starts, renders an info container stating: *"Collecting journey telemetry... Risk analysis updates as GPS fixes and check-in responses arrive."*
4. **Contributing Factors Breakdown:**
   - Each factor is formatted as a bullet item with title, impact tag chip (e.g., `[HIGH]`, `[CRITICAL]`), and natural-language description (e.g., *"Vehicle diverted 546m from planned corridor."*).
5. **Interactive Controls:**
   - "Re-Evaluate Risk" button with progress indicator during inference.
   - Transparent disclaimer: *"Disclaimer: Algorithmic risk evaluation based on journey telemetry. Does not replace personal safety judgment or predict crime."*

---

## 5. Build and Unit Test Verification

### 5.1 Unit Test Execution (`testDebugUnitTest`)

```text
> Task :app:testDebugUnitTest

com.journex.safety.CheckInTrackingTest: tests=6, failures=0, errors=0
com.journex.safety.DashboardViewModelTest: tests=4, failures=0, errors=0
com.journex.safety.GpsTrackingTest: tests=6, failures=0, errors=0
com.journex.safety.JournalEncryptionTest: tests=3, failures=0, errors=0
com.journex.safety.PermissionUtilsTest: tests=1, failures=0, errors=0
com.journex.safety.RiskAnalysisTest: tests=6, failures=0, errors=0
com.journex.safety.RouteDeviationTest: tests=5, failures=0, errors=0

Total Test Suites: 7
Total Tests: 31
Failures: 0
Errors: 0
Result: BUILD SUCCESSFUL in 37s
```

### 5.2 Build Output (`assembleDebug`)

```text
> Task :app:assembleDebug
BUILD SUCCESSFUL in 11s
38 actionable tasks: 4 executed, 34 up-to-date
Output: app-debug.apk
```

### 5.3 Physical Device Deployment
- **Target Hardware:** vivo V2513 (Android 16, API 36)
- **Serial:** `10BG2E010L007AJ`
- **Installation:** `adb install -r android/app/build/outputs/apk/debug/app-debug.apk` -> **Success**
- **Port Forwarding:** `adb reverse tcp:5000 tcp:5000` active.

---

## 6. Conclusion

Phase 7 Android client integration is complete, responsive, fully covered by 31 unit tests, and successfully deployed to physical hardware.
