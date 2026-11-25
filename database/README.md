# JOURNEX Database Architecture & Storage Directory

> **Relational Data Management for JOURNEX**  
> *Development: SQLite | Production: MySQL | ORM: SQLAlchemy & Alembic*

---

## 📂 Directory Structure & Purpose

- **`migrations/`**: Stores database migration scripts (managed via Flask-Migrate / Alembic) to ensure safe schema upgrades and rollbacks without data loss.
- **`schema/`**: Contains raw SQL DDL schemas and entity-relationship definitions documenting tables, indexes, and foreign key constraints for both SQLite and MySQL.
- **`seed/`**: Contains seed data scripts and sample fixtures (such as standard emergency hotlines, verified safe places directory records, and test user personas for evaluation).

---

## 🗄️ Relational Entities

1. **`users`**: Account credentials, contact numbers, and security metadata.
2. **`safety_profiles`**: Personal medical info, blood group, allergies, and emergency notes.
3. **`trusted_contacts`**: Guardian names, relationships, phone numbers, and priority ranks.
4. **`journeys`**: Trip records, start/end locations, scheduled ETAs, transit modes, and completion statuses.
5. **`journey_waypoints`**: Time-stamped GPS coordinate telemetry recorded during active monitoring.
6. **`checkin_events`**: Scheduled and adaptive check-in triggers, response timestamps, and latency status.
7. **`risk_logs`**: ML evaluation results, anomaly vector inputs, and computed risk tiers.
8. **`emergency_alerts`**: Log of triggered escalations (Tier 1/2/3), guardian SMS dispatch records, and emergency calls.
9. **`incident_journal`**: Encrypted traveler incident reports, notes, and vehicle tags.
10. **`safe_places`**: Curated directory of 24/7 safe havens (police stations, hospitals, transit stations).
