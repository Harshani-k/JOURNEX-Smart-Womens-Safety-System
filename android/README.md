# JOURNEX Android Client

> **Native Android Application**  
> *Language: Kotlin | UI: Jetpack Compose | Target SDK: 34 (Android 14) | Min SDK: 26 (Android 8.0)*

---

## 📱 Module Overview

The `android/` directory contains the complete source code, Gradle configurations, and UI assets for the native Android application of JOURNEX.

This module provides:
1. **User Experience:** Fully declarative UI using **Jetpack Compose** and Material 3 design principles.
2. **Foreground Location Tracking:** Background-persistent GPS tracking service powered by `FusedLocationProviderClient`.
3. **Safety Engine:** Local anomaly detection algorithms (perpendicular cross-track deviation, unexpected static halt detection, adaptive check-in countdown timers).
4. **Emergency Escalation:** Progressive multi-level alert handlers, automated SMS dispatch, and telephony calling intents.
5. **Evaluator Simulation:** Dedicated Demo Simulation Mode for viva testing.

---

## 🏗️ Planned Architecture & Package Structure

When the Android project is initialized in Phase 2, the source structure under `app/src/main/java/com/journex/app/` will be structured as follows:

```
android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/journex/app/
│   │   │   │   ├── data/            # Repositories, API interfaces, DataStore, Models
│   │   │   │   ├── di/              # Dependency injection / Service locator modules
│   │   │   │   ├── domain/          # Business logic use cases & anomaly algorithms
│   │   │   │   ├── service/         # JourneyTrackingService (Foreground Service)
│   │   │   │   ├── ui/              # Jetpack Compose Screens, ViewModels, Components
│   │   │   │   │   ├── auth/        # Login & Registration screens
│   │   │   │   │   ├── contacts/    # Emergency Contacts CRUD screens
│   │   │   │   │   ├── journey/     # Active Journey, Map & Tracking screens
│   │   │   │   │   ├── profile/     # Safety Profile screen
│   │   │   │   │   ├── history/     # Past Journey Records screen
│   │   │   │   │   ├── safeplaces/  # Safe Places Directory screen
│   │   │   │   │   ├── simulation/  # Demo Simulation Controller screen
│   │   │   │   │   └── theme/       # Color, Type, Shape & Material3 Theme
│   │   │   │   └── JournexApp.kt    # Android Application class
│   │   │   ├── res/                 # Vector drawables, strings, mipmaps
│   │   │   └── AndroidManifest.xml  # Permissions, services & activity declarations
│   └── build.gradle.kts             # App-level build script
├── gradle/                          # Gradle wrapper files
├── build.gradle.kts                 # Project-level build script
└── settings.gradle.kts              # Gradle project settings
```

---

## ⚙️ Hardware Permissions Required

- `ACCESS_FINE_LOCATION` & `ACCESS_COARSE_LOCATION`: High precision real-time GPS coordinates.
- `ACCESS_BACKGROUND_LOCATION`: Continuous journey tracking when app is minimized.
- `FOREGROUND_SERVICE` & `FOREGROUND_SERVICE_LOCATION`: Android 14+ compliant location service.
- `SEND_SMS`: Automatic dispatch of guardian alerts with live location URLs.
- `CALL_PHONE`: Autonomous telephony trigger for emergency escalation.
- `POST_NOTIFICATIONS`: Android 13+ safety check-in and alert notifications.

---

## 🛠️ Readiness Status

This directory is prepared and reserved for genuine Android project initialization using **Android Studio** and Kotlin Gradle DSL. No fake or placeholder source files have been generated.
