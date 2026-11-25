# JOURNEX – Trusted Emergency Contacts API Specification

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Trusted Emergency Contacts Subsystem (`/api/v1/contacts`)  
**Specification Version:** 1.0.0  
**Target Clients:** JOURNEX Native Android Application (Kotlin / Jetpack Compose)  

---

## 1. Overview & Business Rules

The Trusted Contacts Subsystem manages the user's circle of safety. In the event of missed check-ins, route deviations, or SOS triggers, the JOURNEX multi-level escalation system dispatches progressive alerts to these contacts.

### Core Business Rules:
1. **Ownership Derived from JWT:** The API never trusts a client-supplied `user_id`. Every action is scoped to the user ID inside the authenticated token.
2. **Quota Limit:** Maximum of **5 trusted contacts** per user account.
3. **Unique Phone Numbers:** A user cannot add the same phone number more than once (`UniqueConstraint(user_id, phone_number)`).
4. **Single Primary Contact:** Only **one contact can be marked as primary (`is_primary: true`)** at any given time. Promoting a contact automatically demotes all other contacts of that user.
5. **Priority Order:** Contacts have an integer priority (`1, 2, 3...`) used by the emergency escalation engine to contact individuals sequentially.
6. **Consent Lifecycle:** `consent_status` defaults to `PENDING`. No contact is marked `CONFIRMED` without an explicit verification flow (SMS/OTP planned for future phase).
7. **Resource Protection:** Attempting to query, update, or delete another user's contact returns `404 Not Found` (never `403`), preventing ID enumeration.

---

## 2. Database Schema (`trusted_contacts`)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal contact ID |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), INDEXED, NOT NULL | Foreign key to user account (on delete cascade) |
| `contact_name` | VARCHAR(100) | NOT NULL | Contact full name |
| `phone_number` | VARCHAR(20) | NOT NULL | Phone number (E.164 format) |
| `relationship` | VARCHAR(50) | NOT NULL | Relationship (Parent, Sibling, Friend, etc.) |
| `priority` | INTEGER | NOT NULL, DEFAULT 1 | Priority ordering (1 is highest) |
| `is_primary` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether this contact is the primary contact |
| `consent_status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | Status: `PENDING`, `CONFIRMED`, `DECLINED` |
| `verified_at` | DATETIME | NULLABLE | Verification timestamp |
| `created_at` | DATETIME | NOT NULL, UTC | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL, UTC | Last modification timestamp |

---

## 3. Endpoints

### 3.1 List Trusted Contacts
- **Endpoint:** `GET /api/v1/contacts`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)
- **Ordering:** Sorted ascending by `priority`, then by `id`.

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Trusted contacts retrieved successfully.",
  "data": [
    {
      "id": 1,
      "contact_name": "Mom",
      "phone_number": "+919876543311",
      "relationship": "Parent",
      "priority": 1,
      "is_primary": true,
      "consent_status": "PENDING",
      "verified_at": null,
      "created_at": "2026-11-22T07:11:25.053449",
      "updated_at": "2026-11-22T07:11:25.053449"
    }
  ],
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.095446+00:00"
}
```

---

### 3.2 Add Trusted Contact
- **Endpoint:** `POST /api/v1/contacts`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Request Body:
```json
{
  "contact_name": "Mom",
  "phone_number": "+919876543311",
  "relationship": "Parent",
  "priority": 1,
  "is_primary": true
}
```

#### Validation Rules:
- `contact_name`: Required, 2 to 100 characters.
- `phone_number`: Required, 10 to 15 digits (optional leading `+`).
- `relationship`: Required, 2 to 50 characters.
- `priority`: Positive integer >= 1 (defaults to 1).
- `is_primary`: Optional boolean (defaults to `false`, or `true` if first contact).

#### Success Response (`201 Created`):
```json
{
  "success": true,
  "message": "Trusted contact added successfully.",
  "data": {
    "id": 1,
    "contact_name": "Mom",
    "phone_number": "+919876543311",
    "relationship": "Parent",
    "priority": 1,
    "is_primary": true,
    "consent_status": "PENDING",
    "verified_at": null,
    "created_at": "2026-11-22T07:11:25.053449",
    "updated_at": "2026-11-22T07:11:25.053449"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.062447+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Quota exceeded (5 contacts max) or validation error.
- `401 Unauthorized`: Missing or invalid Bearer token.
- `409 Conflict`: Contact with this phone number already registered for this user.

---

### 3.3 Get Single Contact
- **Endpoint:** `GET /api/v1/contacts/<contact_id>`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Trusted contact retrieved successfully.",
  "data": {
    "id": 1,
    "contact_name": "Mom",
    "phone_number": "+919876543311",
    "relationship": "Parent",
    "priority": 1,
    "is_primary": true,
    "consent_status": "PENDING",
    "verified_at": null,
    "created_at": "2026-11-22T07:11:25.053449",
    "updated_at": "2026-11-22T07:11:25.053449"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.070000+00:00"
}
```

#### Error Responses:
- `401 Unauthorized`: Missing or invalid Bearer token.
- `404 Not Found`: Contact does not exist or belongs to another user.

---

### 3.4 Update Contact
- **Endpoint:** `PUT /api/v1/contacts/<contact_id>`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Request Body:
```json
{
  "contact_name": "Mother (Cell)",
  "priority": 1
}
```

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Trusted contact updated successfully.",
  "data": {
    "id": 1,
    "contact_name": "Mother (Cell)",
    "phone_number": "+919876543311",
    "relationship": "Parent",
    "priority": 1,
    "is_primary": true,
    "consent_status": "PENDING",
    "verified_at": null,
    "created_at": "2026-11-22T07:11:25.053449",
    "updated_at": "2026-11-22T07:11:25.110000"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.112000+00:00"
}
```

---

### 3.5 Set Primary Contact
- **Endpoint:** `PATCH /api/v1/contacts/<contact_id>/primary`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Primary trusted contact updated successfully.",
  "data": {
    "id": 2,
    "contact_name": "Sister",
    "phone_number": "+919876543312",
    "relationship": "Sibling",
    "priority": 2,
    "is_primary": true,
    "consent_status": "PENDING",
    "verified_at": null,
    "created_at": "2026-11-22T07:11:25.077114",
    "updated_at": "2026-11-22T07:11:25.114755"
  },
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.119770+00:00"
}
```

---

### 3.6 Delete Contact
- **Endpoint:** `DELETE /api/v1/contacts/<contact_id>`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "message": "Trusted contact deleted successfully.",
  "data": null,
  "errors": null,
  "timestamp": "2026-11-22T07:11:25.136918+00:00"
}
```

---

## 4. Android Integration Contracts (Kotlin)

```kotlin
package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class TrustedContactDto(
    @SerializedName("id") val id: Int,
    @SerializedName("contact_name") val contactName: String,
    @SerializedName("phone_number") val phoneNumber: String,
    @SerializedName("relationship") val relationship: String,
    @SerializedName("priority") val priority: Int,
    @SerializedName("is_primary") val isPrimary: Boolean,
    @SerializedName("consent_status") val consentStatus: String,
    @SerializedName("verified_at") val verifiedAt: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class CreateContactRequest(
    @SerializedName("contact_name") val contactName: String,
    @SerializedName("phone_number") val phoneNumber: String,
    @SerializedName("relationship") val relationship: String,
    @SerializedName("priority") val priority: Int = 1,
    @SerializedName("is_primary") val isPrimary: Boolean = false
)

data class UpdateContactRequest(
    @SerializedName("contact_name") val contactName: String? = null,
    @SerializedName("phone_number") val phoneNumber: String? = null,
    @SerializedName("relationship") val relationship: String? = null,
    @SerializedName("priority") val priority: Int? = null,
    @SerializedName("is_primary") val isPrimary: Boolean? = null
)
```
