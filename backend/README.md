# JOURNEX Backend REST API

> **Python Flask Microservice with SQLAlchemy ORM**  
> *Python 3.10+ | SQLite (Development) | MySQL (Production Ready)*

---

## 🌐 Module Overview

The `backend/` directory houses the RESTful web API microservice for JOURNEX. It provides stateless endpoints serving the native Android client, persists user and journey state, and acts as the bridge to the Scikit-learn Machine Learning risk assessment engine.

---

## 🏛️ Planned Directory Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask Application Factory (create_app)
│   ├── config.py            # Development (SQLite) and Production (MySQL) configs
│   ├── models/              # SQLAlchemy database models
│   │   ├── user.py          # User & SafetyProfile models
│   │   ├── contact.py       # EmergencyContact model
│   │   ├── journey.py       # Journey, Waypoint & CheckIn models
│   │   └── incident.py      # IncidentJournal model
│   ├── routes/              # Modular Flask Blueprints
│   │   ├── auth.py          # /api/v1/auth
│   │   ├── contacts.py      # /api/v1/contacts
│   │   ├── journey.py       # /api/v1/journey
│   │   ├── risk.py          # /api/v1/risk (ML integration)
│   │   └── alert.py         # /api/v1/alert
│   └── services/            # Business logic & ML inference bridge
│       └── ml_bridge.py     # Random Forest model inference handler
├── tests/                   # Pytest API integration tests
│   ├── test_auth.py
│   ├── test_journey.py
│   └── test_risk.py
├── .env.example             # Template for environment variables
├── requirements.txt         # Production and development dependencies
└── run.py                   # Development server entry point
```

---

## 📦 Planned Key Dependencies

- `Flask`: Micro web framework.
- `SQLAlchemy` & `Flask-SQLAlchemy`: Database ORM.
- `Flask-Migrate`: Alembic database migration management.
- `PyJWT`: JSON Web Token generation and validation.
- `bcrypt`: Password hashing.
- `scikit-learn` & `joblib`: Machine learning model loading and feature scoring.
- `PyMySQL`: MySQL connector driver (for production database connection).

---

## 🛠️ Readiness Status

This directory is prepared for backend implementation in Phase 1. Dependencies are listed in `requirements.txt` for reference and will be installed in a dedicated Python virtual environment during Phase 1 setup.
