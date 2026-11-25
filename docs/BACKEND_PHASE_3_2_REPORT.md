# JOURNEX – Phase 3.2: User Authentication and Management Report

**Official Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Component:** Python Flask REST API User Authentication & Management Subsystem  
**Date:** November 22, 2026  
**Status:** **PASSED & VERIFIED**  
**Lead Role:** Senior Python Flask Backend Architect  

---

## 1. Executive Summary

Phase 3.2 of the **JOURNEX** project implements secure user registration, credential authentication, JWT token lifecycle management, token revocation, rate limiting, and data isolation. 

All implementations adhere strictly to [`docs/PROJECT_SPEC.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/PROJECT_SPEC.md), [`docs/ARCHITECTURE.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/ARCHITECTURE.md), and [`docs/AUTHENTICATION_API.md`](file:///c:/Users/ELCOT/.gemini/antigravity-ide/scratch/JOURNEX/docs/AUTHENTICATION_API.md).

### Key Accomplishments
1. **User Database Model:** SQLAlchemy `User` entity featuring cryptographically salted password hashes (`werkzeug.security`) and strict credential suppression in serialization (`to_dict()`).
2. **Token Revocation Model:** `TokenBlocklist` entity storing revoked JWT IDs (`jti`) upon logout to prevent replay attacks.
3. **Database Migrations:** Configured Flask-Migrate / Alembic migrations in `backend/migrations/`, successfully creating and updating SQLite database `backend/instance/journex.db`.
4. **Complete Authentication Suite:**
   - `POST /api/v1/auth/register`: Input-validated user creation with duplicate email conflict prevention (`409 Conflict`).
   - `POST /api/v1/auth/login`: Credential validation with rate-limiting defense against brute-force attacks (`10 per minute`).
   - `POST /api/v1/auth/refresh`: Refresh token exchange for renewed access tokens.
   - `GET /api/v1/auth/me`: Identity-protected user profile extraction.
   - `POST /api/v1/auth/logout`: Active session revocation.
5. **Security Hardening:**
   - Password strength validation: minimum 8 characters, at least 1 digit, at least 1 letter.
   - Strict input sanitization for email addresses and phone numbers.
   - Rate limiting on sensitive endpoints via `Flask-Limiter` (`429 Too Many Requests`).
   - User data isolation ensuring tokens cannot view or tamper with other users' profiles.
6. **Integration Verification:** 22 automated tests passing with 100% success rate, verified via live HTTP dev server tests.

---

## 2. Directory Structure & New Modules

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py            # Export User and TokenBlocklist
│   │   ├── user.py                # User model with salted password hashing
│   │   └── token_blocklist.py     # Revoked JWT token tracking
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py              # Health check blueprint (/api/v1/health)
│   │   └── auth.py                # Authentication endpoints (/api/v1/auth/*)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── health_service.py      # Health diagnostics probe
│   │   └── auth_service.py        # Registration, login, tokens & revocation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── errors.py              # Error handlers (400, 401, 404, 405, 429, 500)
│   │   ├── exceptions.py          # Custom domain exceptions
│   │   ├── response.py            # Standard JSON envelope
│   │   └── validators.py          # Input validation for email, phone & password
│   ├── __init__.py                # App factory + JWT callbacks & Rate limiter
│   ├── config.py                  # JWT & Rate limit configuration
│   └── extensions.py              # db, migrate, cors, jwt, limiter
├── instance/
│   └── journex.db                 # SQLite development database (migrated)
├── migrations/                    # Alembic database migrations
│   ├── versions/
│   │   └── 9a17e1c634bf_create_users_and_token_blocklist_tables.py
│   ├── alembic.ini
│   └── env.py
└── tests/
    ├── conftest.py                # Fixtures with table auto-creation
    ├── test_app_init.py           # Factory initialization tests
    ├── test_auth.py               # 14 comprehensive authentication test cases
    ├── test_config.py             # Environment configuration tests
    ├── test_errors.py             # Error envelope tests
    └── test_health.py             # Health check test
```

---

## 3. Database Migration Details

The database schema was generated using Flask-Migrate / Alembic.

### Migration Generation:
```powershell
flask db migrate -m "Create users and token_blocklist tables"
flask db upgrade
```

### Generated Schema:
```sql
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
CREATE INDEX ix_users_email ON users (email);

CREATE TABLE token_blocklist (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    jti VARCHAR(36) NOT NULL UNIQUE,
    token_type VARCHAR(10) NOT NULL,
    user_id INTEGER,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_token_blocklist_jti ON token_blocklist (jti);
```

---

## 4. Test Suite Execution (`pytest`)

The complete backend test suite contains **22 tests** covering app initialization, configuration, error handling, health diagnostics, and authentication flows.

### Command:
```powershell
cd backend
.\.venv\Scripts\pytest.exe tests/ -v
```

### Pytest Execution Output:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ELCOT\.gemini\antigravity-ide\scratch\JOURNEX\backend
configfile: pytest.ini
collecting ... collected 22 items

tests/test_app_init.py::test_app_creation_default PASSED                 [  4%]
tests/test_app_init.py::test_app_creation_testing PASSED                 [  9%]
tests/test_auth.py::test_successful_registration PASSED                  [ 13%]
tests/test_auth.py::test_duplicate_email_rejection PASSED                [ 18%]
tests/test_auth.py::test_invalid_email_rejection PASSED                  [ 22%]
tests/test_auth.py::test_weak_password_rejection PASSED                  [ 27%]
tests/test_auth.py::test_successful_login PASSED                         [ 31%]
tests/test_auth.py::test_incorrect_password PASSED                       [ 36%]
tests/test_auth.py::test_unknown_user_login PASSED                       [ 40%]
tests/test_auth.py::test_access_without_token PASSED                     [ 45%]
tests/test_auth.py::test_access_with_valid_token PASSED                  [ 50%]
tests/test_auth.py::test_expired_token PASSED                            [ 54%]
tests/test_auth.py::test_logout_and_token_revocation PASSED              [ 59%]
tests/test_auth.py::test_refresh_token_lifecycle PASSED                  [ 63%]
tests/test_auth.py::test_user_data_isolation PASSED                      [ 68%]
tests/test_auth.py::test_rate_limiting_on_login PASSED                   [ 72%]
tests/test_config.py::test_development_config PASSED                     [ 77%]
tests/test_config.py::test_testing_config PASSED                         [ 81%]
tests/test_config.py::test_production_config PASSED                      [ 86%]
tests/test_errors.py::test_404_not_found PASSED                          [ 90%]
tests/test_errors.py::test_405_method_not_allowed PASSED                 [ 95%]
tests/test_health.py::test_health_check_endpoint PASSED                  [100%]

============================= 22 passed in 2.19s ==============================
```

---

## 5. Live Server Verification

The backend dev server was launched (`run.py` on `0.0.0.0:5000`) and the complete authentication workflow was executed through real HTTP requests:

1. **`POST /api/v1/auth/register`** -> `201 Created`
   - Generated new user `Aishwarya Rai` (`id=1`) with access and refresh tokens.
2. **`POST /api/v1/auth/login`** -> `200 OK`
   - Successfully authenticated with credentials and received fresh JWT tokens.
3. **`GET /api/v1/auth/me`** -> `200 OK`
   - Verified profile data retrieval using Bearer access token.
4. **`POST /api/v1/auth/refresh`** -> `200 OK`
   - Successfully issued renewed access token using Bearer refresh token.
5. **`POST /api/v1/auth/logout`** -> `200 OK`
   - Revoked the JWT session token in `token_blocklist`.

---

## 6. Android Integration Roadmap (Phase 3.3)

1. **Encrypted Token Storage:**
   - Implement `EncryptedTokenStorage` in `com.journex.safety.data.security` using Android Keystore-backed `EncryptedSharedPreferences`.
2. **Retrofit Network Stack:**
   - Add Retrofit, OkHttp, and Moshi/Gson dependencies in `android/app/build.gradle.kts`.
   - Implement `AuthInterceptor` to automatically inject `Authorization: Bearer <token>` on protected requests.
   - Implement `Authenticator` to trigger token refresh automatically when receiving HTTP 401.
3. **UI Integration:**
   - Wire `LoginScreen` and `RegisterScreen` ViewModels to invoke the Retrofit API endpoints.
