# JOURNEX – Phase 9: Security and Privacy Audit Report

**Project Title:** Smart Women's Safety Check-In and Journey Monitoring System  
**Document:** Security & Privacy Audit Specification  
**Version:** 1.0.0  
**Audit Date:** November 22, 2026  
**Auditor:** Senior Security Architect & Privacy Compliance Auditor  

---

## 1. Executive Summary

This comprehensive audit evaluates the security architecture, cryptographic integrity, user data privacy, and threat resilience of the JOURNEX system across the Python Flask REST API backend, the Android client application, and the Machine Learning risk engine.

### Overall Assessment:
- **Authentication & Authorization:** **HARDENED & COMPLIANT**
- **Cryptographic Protections:** **HARDENED (AES-256 GCM Keystore + bcrypt)**
- **PII Exposure & Data Minimization:** **ZERO PII LEAKAGE**
- **Transport Security:** **TLS ENFORCED IN PRODUCTION**
- **Input Validation & Injection Resistance:** **100% PARAMETERIZED ORM**
- **Autonomous Emergency Safety Safeguards:** **STRICT USER-GOVERNED CALLING**

---

## 2. Detailed Audit Areas & Findings

### 2.1 JWT Authentication & Session Security
- **Token Format:** JSON Web Tokens signed using HMAC-SHA256 (`HS256`).
- **Token Lifespans:**
  - Access Token: Short-lived (60 minutes).
  - Refresh Token: 30 days, single-use rotation enabled.
- **Revocation & Blocklist:**
  - Implemented via `TokenBlocklist` model table with fast indexed `jti` lookup.
  - Logging out immediately records the active JWT `jti` in the blocklist.
  - Blacklisted tokens are rejected at the middleware level (`jwt.token_in_blocklist_loader`).

### 2.2 Multi-Tenant User Isolation & Ownership Enforcement
- **Enforcement Principle:** Every protected route resolves `user_id = int(get_jwt_identity())`.
- **Validation Audit:**
  - Journey access (`/journeys/<id>`): Validates `journey.user_id == current_user_id`. Attempting to access another user's journey returns HTTP 403 Forbidden.
  - Check-Ins & Locations: Derived exclusively from authenticated journey ownership. Clients cannot inject arbitrary `user_id` values.
  - Emergency Events (`/emergency-events/<id>`): Validates event ownership before permitting cancellations or escalations.
  - Safety Profile & Contacts: Scoped strictly to the logged-in user.

### 2.3 Password Hashing & Secret Storage
- **Algorithm:** Werkzeug `generate_password_hash` using salted PBKDF2 with SHA-256 (minimum 100,000 iterations).
- **Plaintext Policy:** Plaintext passwords are never stored in the database, never returned in API response envelopes, and never written to application logs.
- **Credential Hygiene:** Zero production API keys, Twilio tokens, or secret keys are committed to the codebase. Environment variables (`JWT_SECRET_KEY`, `SECRET_KEY`) provide deployment overrides.

### 2.4 Android Keystore & Local Storage Security
- **Incident Journal Encryption:**
  - Leverages Android Keystore Provider (`AndroidKeyStore`).
  - Cryptographic Spec: `AES/GCM/NoPadding` with 256-bit keys and 12-byte random Initialization Vectors (`IV`).
  - Private incident notes are stored encrypted on disk (`encryptedNotes` in Base64).
  - Decryption occurs only in volatile memory when presented to the user.
- **Room Database Access:**
  - SQLite databases are created in private app-internal sandbox storage (`/data/data/com.journex.safety/databases/`).
  - Inaccessible to third-party applications on non-rooted devices (enforced by Android Linux UID isolation).

### 2.5 Transport Security Configuration (`network_security_config.xml`)
- **Android Network Config:** Cleartext traffic (`http://`) is strictly disabled by default in production manifests.
- **Development Exception:** Loopback proxying (`127.0.0.1`, `10.0.2.2`) is explicitly isolated for local testing and ADB reverse port tunnels (`reverse tcp:5000 tcp:5000`).

### 2.6 Location Telemetry & Contact Data Retention
- **Privacy Minimization:**
  - GPS waypoints are logged only while a journey is actively running (`JourneyTrackingService`).
  - When the user taps "End Journey (Arrived Safely)", the foreground GPS service immediately unbinds and ceases location polling.
  - "Incognito Mode" toggle in Privacy Controls allows users to maintain journey records locally without cloud transmission.
  - "Clear Cached History" allows 1-click complete purging of past trip records and coordinates.

### 2.7 PII Leakage in Logs & Machine Learning
- **Zero-PII Machine Learning Rule:**
  - Model feature extraction pipeline explicitly excludes `full_name`, `email`, `phone_number`, contact numbers, medical notes, and home addresses.
  - All 11 Random Forest features are objective spatial/behavioral metrics (speed, deviation distance, delay minutes, missed check-ins, time category).
- **Log Sanitization:** Application loggers sanitize request payloads, masking sensitive token strings, passwords, and phone digits.

### 2.8 Emergency Calling & Alert Authorization
- **No Covert Auto-Dialing:**
  - JOURNEX does **not** invoke `android.permission.CALL_PHONE` silently.
  - Telephony is initiated strictly via `Intent.ACTION_DIAL`, which displays the system dialer with the guardian's number prefilled for explicit one-tap traveler confirmation.
- **Decoupled from ML Risk Output:**
  - High risk model scores never trigger automatic phone calls or SMS broadcasts.
  - Emergency alerts require either:
    1. Direct traveler action (one-tap SOS button or Discreet Silent Alert).
    2. Overdue missed check-in timeout past configured grace periods.

### 2.9 SQL Injection & Mass Assignment Defense
- **SQL Injection:**
  - All database queries utilize SQLAlchemy ORM parameterized statements (`filter_by()`, `session.get()`).
  - Zero raw SQL string concatenation in backend routes.
- **Mass Assignment:**
  - DTO input validators (`validate_journey_payload`, `validate_emergency_event_create_payload`) strictly whitelist accepted fields.
  - Disallowed or unauthorized properties (e.g., `user_id`, `created_at`, `status`) are filtered out.

---

## 3. Threat Matrix & Remediation Summary

| Threat Vector | Severity | Vulnerability Description | Applied Security Mitigation |
|---|---|---|---|
| Broken Object-Level Authorization (BOLA) | HIGH | Accessing other users' journey coordinates via ID guessing. | Added strict user ownership validation on all `/journeys/<id>` and `/emergency-events/<id>` routes. |
| Insecure Direct Object References (IDOR) | HIGH | Escalating an emergency event belonging to another traveler. | Service queries `filter_by(id=event_id, user_id=current_user_id)`. |
| Credential Leakage in Code | HIGH | Hardcoding SMS provider API keys in repository. | Implemented `AlertProviderInterface` with mock fallback and environment-based configuration. |
| False Emergency Alarm Panic | MEDIUM | Guardians alarmed by accidental SOS trigger without follow-up. | Integrated 5-second cancelable countdown dialog and automatic safe cancellation broadcasts. |
| SQLite Schema Migration Crash | MEDIUM | Field nullable and index differences triggering Room crash on update. | Aligned Room `@Entity` declarations with exact SQLite migration DDL. |
