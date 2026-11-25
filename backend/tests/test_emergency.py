"""
JOURNEX – Phase 8 Test Suite: SOS & Multi-Level Emergency Alert Escalation
Tests emergency event lifecycle, multi-level escalation across trusted contacts,
idempotency, cancellation safeguards, provider abstraction, delivery status tracking,
and access control.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import User
from app.models.journey import Journey
from app.models.trusted_contact import TrustedContact
from app.models.emergency_event import EmergencyEvent
from app.models.emergency_alert_dispatch import EmergencyAlertDispatch
from app.services.alert_provider import MockAlertProvider, set_alert_provider, get_alert_provider
from app.services.emergency_service import EmergencyService

@pytest.fixture
def auth_user(client):
    """Register and login primary test traveler."""
    payload = {
        "full_name": "Emergency Test Traveler",
        "email": "traveler.emergency@journex.internal",
        "phone_number": "+919876500001",
        "password": "StrongPassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    token = res.get_json()["data"]["tokens"]["access_token"]
    user = User.query.filter_by(email=payload["email"]).first()
    return token, user

@pytest.fixture
def other_user(client):
    """Register second user to verify cross-user isolation."""
    payload = {
        "full_name": "Unrelated User",
        "email": "unrelated@journex.internal",
        "phone_number": "+919876500002",
        "password": "StrongPassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    token = res.get_json()["data"]["tokens"]["access_token"]
    user = User.query.filter_by(email=payload["email"]).first()
    return token, user

@pytest.fixture
def user_with_contacts(auth_user):
    """Populate 3 trusted contacts with priorities 1, 2, and 3."""
    token, user = auth_user
    c1 = TrustedContact(
        user_id=user.id,
        contact_name="Primary Guardian (Mom)",
        phone_number="+919876543210",
        relationship="Parent",
        priority=1,
        is_primary=True,
        consent_status="VERIFIED"
    )
    c2 = TrustedContact(
        user_id=user.id,
        contact_name="Secondary Guardian (Dad)",
        phone_number="+919876543211",
        relationship="Parent",
        priority=2,
        is_primary=False,
        consent_status="VERIFIED"
    )
    c3 = TrustedContact(
        user_id=user.id,
        contact_name="Tertiary Guardian (Brother)",
        phone_number="+919876543212",
        relationship="Sibling",
        priority=3,
        is_primary=False,
        consent_status="VERIFIED"
    )
    db.session.add_all([c1, c2, c3])
    db.session.commit()
    return token, user

@pytest.fixture
def active_journey(auth_user):
    """Create active journey for traveler."""
    _, user = auth_user
    now = datetime.now(timezone.utc)
    journey = Journey(
        user_id=user.id,
        journey_title="Late Night Journey to Peelamedu",
        start_location_name="Gandhipuram",
        start_location_address="Gandhipuram, Coimbatore",
        start_latitude=11.0168,
        start_longitude=76.9558,
        destination_name="Peelamedu",
        destination_address="Peelamedu, Coimbatore",
        destination_latitude=11.0280,
        destination_longitude=77.0120,
        planned_start_time=now - timedelta(minutes=10),
        expected_arrival_time=now + timedelta(minutes=30),
        status="ACTIVE"
    )
    db.session.add(journey)
    db.session.commit()
    return journey

# --- 1. Standalone Emergency Creation & Level 1 Dispatch ---

def test_standalone_emergency_creation_and_level_1_dispatch(client, user_with_contacts):
    """Verify manual SOS creation dispatches Level 1 SMS to primary contact."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "trigger_type": "MANUAL_SOS",
        "latitude": 11.0175,
        "longitude": 76.9600,
        "accuracy": 8.0,
        "location_address": "Near Gandhipuram Crosscut Rd"
    }

    res = client.post("/api/v1/emergency-events", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.get_json()["data"]

    assert data["status"] == "ACTIVE"
    assert data["trigger_type"] == "MANUAL_SOS"
    assert data["current_escalation_level"] == 1
    assert data["latitude"] == 11.0175
    assert len(data["dispatches"]) == 1

    d1 = data["dispatches"][0]
    assert d1["escalation_level"] == 1
    assert d1["contact_name"] == "Primary Guardian (Mom)"
    assert d1["status"] == "DELIVERED"
    assert d1["provider_message_id"] is not None

# --- 2. Journey-Scoped Emergency Trigger & Coordinate Inheritance ---

def test_journey_emergency_trigger(client, user_with_contacts, active_journey):
    """Verify journey-scoped SOS inherits journey context."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "trigger_type": "MANUAL_SOS",
        "latitude": 11.0200,
        "longitude": 76.9700
    }

    res = client.post(f"/api/v1/journeys/{active_journey.id}/emergency-events", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.get_json()["data"]

    assert data["journey_id"] == active_journey.id
    assert data["status"] == "ACTIVE"
    assert data["current_escalation_level"] == 1

# --- 3. Idempotency via Client Action ID ---

def test_idempotent_sos_trigger(client, user_with_contacts):
    """Verify repeating request with identical client_action_id returns existing event without re-dispatching."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "trigger_type": "MANUAL_SOS",
        "client_action_id": "test-uuid-sos-action-999",
        "latitude": 11.0180,
        "longitude": 76.9650
    }

    res1 = client.post("/api/v1/emergency-events", headers=headers, json=payload)
    assert res1.status_code == 201
    event_id1 = res1.get_json()["data"]["id"]

    res2 = client.post("/api/v1/emergency-events", headers=headers, json=payload)
    assert res2.status_code == 201
    event_id2 = res2.get_json()["data"]["id"]

    assert event_id1 == event_id2
    # Ensure total dispatches for this event did not double
    event = db.session.get(EmergencyEvent, event_id1)
    assert event.dispatches.count() == 1

# --- 4. Multi-Level Escalation Progression ---

def test_multi_level_escalation_progression(client, user_with_contacts):
    """Verify escalating Level 1 -> Level 2 -> Level 3 notifies respective priority contacts."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Trigger SOS (Level 1)
    res = client.post("/api/v1/emergency-events", headers=headers, json={"trigger_type": "MANUAL_SOS"})
    event_id = res.get_json()["data"]["id"]

    # Step 2: Escalate to Level 2
    res_esc2 = client.post(f"/api/v1/emergency-events/{event_id}/escalate", headers=headers, json={})
    assert res_esc2.status_code == 200
    data2 = res_esc2.get_json()["data"]
    assert data2["current_escalation_level"] == 2
    assert len(data2["dispatches"]) == 2
    assert data2["dispatches"][1]["contact_name"] == "Secondary Guardian (Dad)"
    assert data2["dispatches"][1]["escalation_level"] == 2

    # Step 3: Escalate to Level 3
    res_esc3 = client.post(f"/api/v1/emergency-events/{event_id}/escalate", headers=headers, json={})
    assert res_esc3.status_code == 200
    data3 = res_esc3.get_json()["data"]
    assert data3["current_escalation_level"] == 3
    assert len(data3["dispatches"]) == 3
    assert data3["dispatches"][2]["contact_name"] == "Tertiary Guardian (Brother)"
    assert data3["dispatches"][2]["escalation_level"] == 3

    # Step 4: Attempting to escalate past Level 3 remains at Level 3 idempotently
    res_esc4 = client.post(f"/api/v1/emergency-events/{event_id}/escalate", headers=headers, json={})
    assert res_esc4.status_code == 200
    assert res_esc4.get_json()["data"]["current_escalation_level"] == 3

# --- 5. Emergency Cancellation Lifecycle ---

def test_emergency_cancellation_lifecycle(client, user_with_contacts):
    """Verify cancelling an active emergency updates status and broadcasts safe notification."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/emergency-events", headers=headers, json={"trigger_type": "MANUAL_SOS"})
    event_id = res.get_json()["data"]["id"]

    cancel_res = client.post(
        f"/api/v1/emergency-events/{event_id}/cancel",
        headers=headers,
        json={"cancellation_reason": "Accidental tap, I am safe."}
    )
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.get_json()["data"]

    assert cancel_data["status"] == "CANCELLED"
    assert cancel_data["cancellation_timestamp"] is not None
    assert "Accidental tap" in cancel_data["cancellation_reason"]

    # Escalating a cancelled event is rejected with 409 Conflict
    esc_res = client.post(f"/api/v1/emergency-events/{event_id}/escalate", headers=headers, json={})
    assert esc_res.status_code == 409

# --- 6. Delivery Status & History Endpoints ---

def test_delivery_status_and_history(client, user_with_contacts):
    """Verify delivery status summary and paginated user history."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/emergency-events", headers=headers, json={"trigger_type": "MANUAL_SOS"})
    event_id = res.get_json()["data"]["id"]

    # Delivery status
    deliv_res = client.get(f"/api/v1/emergency-events/{event_id}/delivery-status", headers=headers)
    assert deliv_res.status_code == 200
    deliv_data = deliv_res.get_json()["data"]
    assert deliv_data["emergency_event_id"] == event_id
    assert deliv_data["total_dispatches"] >= 1
    assert deliv_data["dispatches"][0]["status"] == "DELIVERED"

    # User history
    hist_res = client.get("/api/v1/emergency-events", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.get_json()["data"]
    assert hist_data["total"] >= 1
    assert len(hist_data["events"]) >= 1

# --- 7. Security, Ownership & Error Handling ---

def test_emergency_unauthorized_and_forbidden_access(client, user_with_contacts, other_user):
    """Verify unauthenticated requests (401) and cross-user tampering (403) are rejected."""
    token, user = user_with_contacts
    other_token, _ = other_user
    headers = {"Authorization": f"Bearer {token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 401 Unauthenticated
    res_unauth = client.post("/api/v1/emergency-events", json={"trigger_type": "MANUAL_SOS"})
    assert res_unauth.status_code == 401

    # Create event as User A
    res = client.post("/api/v1/emergency-events", headers=headers, json={"trigger_type": "MANUAL_SOS"})
    event_id = res.get_json()["data"]["id"]

    # User B tries to view User A's event -> 403 Forbidden
    res_forbid_view = client.get(f"/api/v1/emergency-events/{event_id}", headers=other_headers)
    assert res_forbid_view.status_code == 403

    # User B tries to cancel User A's event -> 403 Forbidden
    res_forbid_cancel = client.post(f"/api/v1/emergency-events/{event_id}/cancel", headers=other_headers, json={})
    assert res_forbid_cancel.status_code == 403

    # Non-existent event -> 404 Not Found
    res_not_found = client.get("/api/v1/emergency-events/99999", headers=headers)
    assert res_not_found.status_code == 404

# --- 8. Provider Failure Handling ---

def test_provider_failure_handling(client, user_with_contacts):
    """Verify system records FAILED status when provider gateway times out."""
    token, user = user_with_contacts
    headers = {"Authorization": f"Bearer {token}"}

    failing_provider = MockAlertProvider(simulate_failure=True)
    set_alert_provider(failing_provider)

    try:
        res = client.post("/api/v1/emergency-events", headers=headers, json={"trigger_type": "MANUAL_SOS"})
        assert res.status_code == 201
        data = res.get_json()["data"]
        assert len(data["dispatches"]) == 1
        d = data["dispatches"][0]
        assert d["status"] == "FAILED"
        assert "timeout" in d["error_message"].lower()
    finally:
        # Reset provider to healthy mock
        set_alert_provider(MockAlertProvider(simulate_failure=False))
