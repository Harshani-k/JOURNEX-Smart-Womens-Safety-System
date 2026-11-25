# JOURNEX – Authentication API & Contract Specification

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** REST API Authentication Subsystem (`/api/v1/auth`)  
**Specification Version:** 1.0.0  
**Target Clients:** JOURNEX Native Android Application (Kotlin / Jetpack Compose)  

---

## 1. Overview & Security Architecture

The JOURNEX Authentication API provides stateless, secure, token-based session management for the mobile client. It combines:
- **JWT (JSON Web Tokens):** Short-lived access tokens (1 hour in production) and long-lived refresh tokens (30 days in production) powered by `Flask-JWT-Extended`.
- **Hardware-Secure Android KeyStore Storage Plan:** Client-side tokens must be stored using Android Keystore-backed AES-256-GCM encryption (`EncryptedSharedPreferences`).
- **Cryptographic Password Hashing:** Industry-standard password hashing via `werkzeug.security` (Scrypt / PBKDF2 with unique cryptographic salt per user).
- **Proactive Token Revocation:** Server-side `token_blocklist` database table tracking revoked JWT IDs (`jti`) upon logout.
- **Brute-Force Protection:** Rate limiting configured on public authentication endpoints (10 requests/minute per IP).
- **Data Isolation:** User resources are scoped strictly to the token's authenticated subject (`sub`), preventing cross-account data leaks.

---

## 2. Database Schema

### 2.1 `users` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user identifier |
| `full_name` | VARCHAR(100) | NOT NULL | User's legal or preferred name |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL, INDEXED | Normalized lowercased email |
| `phone_number` | VARCHAR(20) | NOT NULL | Contact phone number (+E.164 format) |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password (never plaintext) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account operational status |
| `created_at` | DATETIME | NOT NULL, UTC | Timestamp of account registration |
| `updated_at` | DATETIME | NOT NULL, UTC | Timestamp of latest record modification |

### 2.2 `token_blocklist` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Revocation record identifier |
| `jti` | VARCHAR(36) | UNIQUE, NOT NULL, INDEXED | JWT unique identifier |
| `token_type` | VARCHAR(10) | NOT NULL | `access` or `refresh` |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NULLABLE | User associated with token |
| `created_at` | DATETIME | NOT NULL, UTC | Revocation timestamp |
| `expires_at` | DATETIME | NOT NULL, UTC | Token natural expiration time |

---

## 3. Standard Response Envelope

Every endpoint returns a predictable JSON envelope:
```json
{
  "success": true,
  "message": "Human readable status message.",
  "data": { ... },
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.159950+00:00"
}
```

When an error occurs:
```json
{
  "success": false,
  "message": "Descriptive error message.",
  "data": null,
  "errors": {
    "code": "ERROR_CODE",
    "description": "Specific error details"
  },
  "timestamp": "2026-11-22T06:55:38.159950+00:00"
}
```

---

## 4. API Endpoints

### 4.1 Register New User
- **Endpoint:** `POST /api/v1/auth/register`
- **Rate Limit:** 10 requests / minute
- **Authentication:** None (Public)

#### Request Body:
```json
{
  "full_name": "Priya Sharma",
  "email": "priya.sharma@example.com",
  "phone_number": "+919876543210",
  "password": "SecurePassword123"
}
```

#### Validation Rules:
- `full_name`: String, 2 to 100 characters.
- `email`: Valid RFC 5322 email syntax, max 120 characters, automatically lowercased and trimmed.
- `phone_number`: 10 to 15 digits, optional leading `+`.
- `password`: Minimum 8 characters, at least 1 letter, at least 1 numeric digit.

#### Response (`201 Created`):
```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "user": {
      "id": 1,
      "full_name": "Priya Sharma",
      "email": "priya.sharma@example.com",
      "phone_number": "+919876543210",
      "is_active": true,
      "created_at": "2026-11-22T06:55:38.153350",
      "updated_at": "2026-11-22T06:55:38.153350"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "Bearer"
    }
  },
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.159950+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Invalid email, weak password, or missing fields.
- `409 Conflict`: An account with this email already exists.
- `429 Too Many Requests`: Registration rate limit exceeded.

---

### 4.2 Authenticate User (Login)
- **Endpoint:** `POST /api/v1/auth/login`
- **Rate Limit:** 10 requests / minute
- **Authentication:** None (Public)

#### Request Body:
```json
{
  "email": "priya.sharma@example.com",
  "password": "SecurePassword123"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Authentication successful.",
  "data": {
    "user": {
      "id": 1,
      "full_name": "Priya Sharma",
      "email": "priya.sharma@example.com",
      "phone_number": "+919876543210",
      "is_active": true,
      "created_at": "2026-11-22T06:55:38.153350",
      "updated_at": "2026-11-22T06:55:38.153350"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "Bearer"
    }
  },
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.362432+00:00"
}
```

#### Error Responses:
- `400 Bad Request`: Missing email or password.
- `401 Unauthorized`: Invalid email or password (generic message to prevent email enumeration).
- `429 Too Many Requests`: Login brute-force rate limit reached.

---

### 4.3 Refresh Access Token
- **Endpoint:** `POST /api/v1/auth/refresh`
- **Authentication:** Bearer Refresh Token (`Authorization: Bearer <refresh_token>`)

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Access token refreshed successfully.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer"
  },
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.408769+00:00"
}
```

#### Error Responses:
- `401 Unauthorized`: Expired, invalid, missing, or revoked refresh token.

---

### 4.4 Get Authenticated User Profile
- **Endpoint:** `GET /api/v1/auth/me`
- **Authentication:** Bearer Access Token (`Authorization: Bearer <access_token>`)

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "User profile retrieved successfully.",
  "data": {
    "id": 1,
    "full_name": "Priya Sharma",
    "email": "priya.sharma@example.com",
    "phone_number": "+919876543210",
    "is_active": true,
    "created_at": "2026-11-22T06:55:38.153350",
    "updated_at": "2026-11-22T06:55:38.153350"
  },
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.400921+00:00"
}
```

#### Error Responses:
- `401 Unauthorized`: Token missing, expired, invalid, or revoked.

---

### 4.5 User Logout (Token Revocation)
- **Endpoint:** `POST /api/v1/auth/logout`
- **Authentication:** Bearer Access or Refresh Token (`Authorization: Bearer <token>`)

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Successfully logged out and revoked session token.",
  "data": null,
  "errors": null,
  "timestamp": "2026-11-22T06:55:38.422644+00:00"
}
```

---

## 5. Android Client Integration Plan

### 5.1 Android Keystore-Backed Secure Storage Architecture
To prevent credential theft on rooted or compromised devices, Android must store the JWT tokens in hardware-backed storage using the Android KeyStore:
```
+--------------------------------------------------------------+
|                     Android Application                      |
|                                                              |
|   +--------------------------+                               |
|   |   JournexAuthRepository  |                               |
|   +--------------------------+                               |
|                |                                             |
|                v                                             |
|   +--------------------------+     AES-256-GCM Master Key    |
|   | EncryptedTokenStorage    | <---------------------------+ |
|   | (EncryptedSharedPrefs)   |     (Android KeyStore HW)   | |
|   +--------------------------+                             | |
|                |                                           | |
|                v                                           | |
|   [Encrypted Token XML File]                               | |
+--------------------------------------------------------------+
```

### 5.2 Kotlin DTO Models (Retrofit / Moshi Ready)
```kotlin
package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class ApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String,
    @SerializedName("data") val data: T?,
    @SerializedName("errors") val errors: Any?,
    @SerializedName("timestamp") val timestamp: String
)

data class UserDto(
    @SerializedName("id") val id: Int,
    @SerializedName("full_name") val fullName: String,
    @SerializedName("email") val email: String,
    @SerializedName("phone_number") val phoneNumber: String,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String
)

data class AuthTokensDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    @SerializedName("token_type") val tokenType: String
)

data class AuthResponseDto(
    @SerializedName("user") val user: UserDto,
    @SerializedName("tokens") val tokens: AuthTokensDto
)

data class RefreshResponseDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String
)
```

### 5.3 Retrofit Auth Service Interface
```kotlin
package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.*
import retrofit2.Response
import retrofit2.http.*

interface JournexAuthApi {

    @POST("api/v1/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<ApiResponse<AuthResponseDto>>

    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<ApiResponse<AuthResponseDto>>

    @POST("api/v1/auth/refresh")
    suspend fun refreshToken(@Header("Authorization") bearerRefreshToken: String): Response<ApiResponse<RefreshResponseDto>>

    @GET("api/v1/auth/me")
    suspend fun getProfile(@Header("Authorization") bearerAccessToken: String): Response<ApiResponse<UserDto>>

    @POST("api/v1/auth/logout")
    suspend fun logout(@Header("Authorization") bearerToken: String): Response<ApiResponse<Unit>>
}
```
