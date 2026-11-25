# JOURNEX – Safety Profile API Specification

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** User Safety Profile Subsystem (`/api/v1/profile`)  
**Specification Version:** 1.0.0  
**Target Clients:** JOURNEX Native Android Application (Kotlin / Jetpack Compose)  

---

## 1. Overview

The Safety Profile Subsystem stores critical emergency and personal safety preferences for a registered JOURNEX user. It enforces a strict **one-to-one relationship** with the user account, protecting privacy through authenticated JWT identity binding and preventing unauthorized access or data exposure.

### Key Capabilities:
- Single profile per authenticated user (`user_id` enforced unique).
- Emergency SOS message template customized by the user.
- Preferred language setting (e.g., `en`, `hi`, `ta`).
- Optional medical or special safety notes (e.g., medical allergies, blood group).
- Complete user isolation: users can only view and update their own profile.

---

## 2. Database Schema (`safety_profiles`)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal profile identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), UNIQUE, INDEXED, NOT NULL | Foreign key to user account (on delete cascade) |
| `display_name` | VARCHAR(100) | NOT NULL | User's preferred safety display name |
| `preferred_language` | VARCHAR(10) | NOT NULL, DEFAULT 'en' | Preferred ISO language code |
| `emergency_message` | VARCHAR(500) | NOT NULL | Default alert message sent to contacts during SOS |
| `additional_safety_notes` | TEXT | NULLABLE | Medical notes, emergency instructions |
| `created_at` | DATETIME | NOT NULL, UTC | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL, UTC | Last modification timestamp |

---

## 3. Endpoints

### 3.1 Get Safety Profile
- **Endpoint:** `GET /api/v1/profile`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Safety profile retrieved successfully.",
  "data": {
    "id": 1,
    "display_name": "Sneha",
    "preferred_language": "en",
    "emergency_message": "SOS! Please check my live location.",
    "additional_safety_notes": "Asthma patient",
    "created_at": "2026-11-22T07:11:24.985221",
    "updated_at": "2026-11-22T07:11:24.985221"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.012301+00:00"
}
```

#### Error Responses:
- `401 Unauthorized`: Token missing, expired, or invalid.
- `404 Not Found`: Profile has not been created yet for this account.

---

### 3.2 Create Safety Profile
- **Endpoint:** `POST /api/v1/profile`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Request Body:
```json
{
  "display_name": "Sneha",
  "preferred_language": "en",
  "emergency_message": "SOS! Please check my live location.",
  "additional_safety_notes": "Asthma patient"
}
```

#### Validation Rules:
- `display_name`: Required, 2 to 100 characters.
- `preferred_language`: Optional, 2 to 10 characters (default: `"en"`).
- `emergency_message`: Required, 5 to 500 characters.
- `additional_safety_notes`: Optional, maximum 1000 characters.
- Modifying `user_id`, `id`, `created_at` is strictly rejected (mass assignment defense).

#### Success Response (`201 Created`):
```json
{
  "success": true,
  "message": "Safety profile created successfully.",
  "data": {
    "id": 1,
    "display_name": "Sneha",
    "preferred_language": "en",
    "emergency_message": "SOS! Please check my live location.",
    "additional_safety_notes": "Asthma patient",
    "created_at": "2026-11-22T07:11:24.985221",
    "updated_at": "2026-11-22T07:11:24.985221"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:24.993221+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Validation failure or mass assignment attempt.
- `401 Unauthorized`: Missing or invalid Bearer token.
- `409 Conflict`: Safety profile already exists for this user.

---

### 3.3 Update Safety Profile
- **Endpoint:** `PUT /api/v1/profile`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Request Body:
```json
{
  "display_name": "Sneha R",
  "preferred_language": "hi",
  "additional_safety_notes": "Asthma patient (inhaler in backpack)"
}
```

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Safety profile updated successfully.",
  "data": {
    "id": 1,
    "display_name": "Sneha R",
    "preferred_language": "hi",
    "emergency_message": "SOS! Please check my live location.",
    "additional_safety_notes": "Asthma patient (inhaler in backpack)",
    "created_at": "2026-11-22T07:11:24.985221",
    "updated_at": "2026-11-22T07:11:25.023394"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.028740+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Invalid fields or empty update payload.
- `401 Unauthorized`: Missing or invalid Bearer token.
- `404 Not Found`: Safety profile does not exist yet.

---

## 4. Android Integration Contracts (Kotlin)

```kotlin
package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class SafetyProfileDto(
    @SerializedName("id") val id: Int,
    @SerializedName("display_name") val displayName: String,
    @SerializedName("preferred_language") val preferredLanguage: String,
    @SerializedName("emergency_message") val emergencyMessage: String,
    @SerializedName("additional_safety_notes") val additionalSafetyNotes: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class CreateProfileRequest(
    @SerializedName("display_name") val displayName: String,
    @SerializedName("preferred_language") val preferredLanguage: String = "en",
    @SerializedName("emergency_message") val emergencyMessage: String,
    @SerializedName("additional_safety_notes") val additionalSafetyNotes: String? = null
)

data class UpdateProfileRequest(
    @SerializedName("display_name") val displayName: String? = null,
    @SerializedName("preferred_language") val preferredLanguage: String? = null,
    @SerializedName("emergency_message") val emergencyMessage: String? = null,
    @SerializedName("additional_safety_notes") val additionalSafetyNotes: String? = null
)
```
