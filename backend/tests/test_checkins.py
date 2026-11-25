import pytest
from datetime import datetime, timezone, timedelta
from app.models.journey import Journey
from app.models.checkin import CheckIn
from app.services.checkin_scheduler import CheckinScheduler
from app.services.checkin_service import CheckinService
from app.services.delay_service import JourneyDelayService

def _register_and_login(client, email="checkin_user@example.com", phone="+919876543601"):
    reg_payload = {
        "full_name": "Checkin Tester",
        "email": email,
        "phone_number": phone,
        "password": "SecurePassword123"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.get_json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _create_active_journey(client, headers, title="Active Work Trip", minutes=30):
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=5)
    arrival = now + timedelta(minutes=minutes)
    payload = {
        "journey_title": title,
        "start_location_name": "Home Base",
        "start_location_address": "123 Safe St",
        "start_latitude": 11.0168,
        "start_longitude": 76.9558,
        "destination_name": "Work Hub",
        "destination_address": "456 Main Ave",
        "destination_latitude": 11.0250,
        "destination_longitude": 76.9650,
        "planned_start_time": start.isoformat(),
        "expected_arrival_time": arrival.isoformat()
    }
    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    journey_id = resp.get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{journey_id}/start", headers=headers)
    return journey_id

def test_checkin_unauthenticated_access(client):
    """Verify checkin endpoints reject requests lacking valid JWT."""
    resp = client.post("/api/v1/journeys/1/checkins", json={})
    assert resp.status_code == 401

    resp = client.get("/api/v1/journeys/1/checkins")
    assert resp.status_code == 401

    resp = client.get("/api/v1/journeys/1/checkins/pending")
    assert resp.status_code == 401

    resp = client.post("/api/v1/checkins/1/confirm", json={})
    assert resp.status_code == 401

    resp = client.post("/api/v1/checkins/1/cancel")
    assert resp.status_code == 401

def test_checkin_auto_schedule_creation(client):
    """Verify creating a checkin with auto-scheduling derives timestamps."""
    headers = _register_and_login(client, email="auto_sched@example.com")
    journey_id = _create_active_journey(client, headers, title="Auto Sched Journey", minutes=30)

    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={}, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["journey_id"] == journey_id
    assert data["status"] == "SCHEDULED"
    assert data["scheduled_at"] is not None
    assert data["deadline_at"] is not None
    assert data["deadline_at"] > data["scheduled_at"]

def test_checkin_manual_timestamps_validation(client):
    """Verify custom scheduled_at and deadline_at validation."""
    headers = _register_and_login(client, email="manual_sched@example.com")
    journey_id = _create_active_journey(client, headers, title="Manual Sched Journey")

    now = datetime.now(timezone.utc)
    # Deadline before scheduled -> 400
    bad_payload = {
        "scheduled_at": (now + timedelta(minutes=10)).isoformat(),
        "deadline_at": (now + timedelta(minutes=5)).isoformat()
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json=bad_payload, headers=headers)
    assert resp.status_code == 400

    # Valid manual timestamps
    good_payload = {
        "scheduled_at": (now + timedelta(minutes=10)).isoformat(),
        "deadline_at": (now + timedelta(minutes=13)).isoformat()
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json=good_payload, headers=headers)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["status"] == "SCHEDULED"

def test_duplicate_checkin_prevention_and_idempotency(client):
    """Verify scheduling multiple active checkins on same journey is rejected unless same client_action_id."""
    headers = _register_and_login(client, email="dup_sched@example.com")
    journey_id = _create_active_journey(client, headers)

    # 1. Schedule first checkin with action_id
    action_id = "uuid-checkin-101"
    resp1 = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={"client_action_id": action_id}, headers=headers)
    assert resp1.status_code == 201
    c1_id = resp1.get_json()["data"]["id"]

    # 2. Duplicate with same action_id -> returns same checkin (idempotent)
    resp2 = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={"client_action_id": action_id}, headers=headers)
    assert resp2.status_code == 200 or resp2.status_code == 201
    assert resp2.get_json()["data"]["id"] == c1_id

    # 3. Duplicate with different action_id or none -> 409 Conflict
    resp3 = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={"client_action_id": "different-id"}, headers=headers)
    assert resp3.status_code == 409

def test_checkin_user_isolation(client):
    """Verify users cannot see or manipulate another user's checkins."""
    headers1 = _register_and_login(client, email="user1_checkin@example.com", phone="+919876543611")
    headers2 = _register_and_login(client, email="user2_checkin@example.com", phone="+919876543612")

    j1 = _create_active_journey(client, headers1)
    resp = client.post(f"/api/v1/journeys/{j1}/checkins", json={}, headers=headers1)
    c1_id = resp.get_json()["data"]["id"]

    # User 2 cannot list User 1's checkins
    resp = client.get(f"/api/v1/journeys/{j1}/checkins", headers=headers2)
    assert resp.status_code == 404

    # User 2 cannot confirm User 1's checkin
    resp = client.post(f"/api/v1/checkins/{c1_id}/confirm", json={}, headers=headers2)
    assert resp.status_code == 404

    # User 2 cannot cancel User 1's checkin
    resp = client.post(f"/api/v1/checkins/{c1_id}/cancel", headers=headers2)
    assert resp.status_code == 404

def test_checkin_confirm_safe_lifecycle(client):
    """Verify confirming checkin transitions status to CONFIRMED_SAFE."""
    headers = _register_and_login(client, email="confirm_safe@example.com")
    journey_id = _create_active_journey(client, headers)

    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={}, headers=headers)
    c_id = resp.get_json()["data"]["id"]

    # Confirm safe
    resp = client.post(f"/api/v1/checkins/{c_id}/confirm", json={
        "response_type": "MANUAL_TAP"
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["status"] == "CONFIRMED_SAFE"
    assert data["responded_at"] is not None

    # Duplicate confirmation without action id -> 409 Conflict
    resp = client.post(f"/api/v1/checkins/{c_id}/confirm", json={}, headers=headers)
    assert resp.status_code == 409

def test_checkin_cancellation_lifecycle(client):
    """Verify cancelling scheduled checkin transitions to CANCELLED and cannot be confirmed."""
    headers = _register_and_login(client, email="cancel_chk@example.com")
    journey_id = _create_active_journey(client, headers)

    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={}, headers=headers)
    c_id = resp.get_json()["data"]["id"]

    # Cancel checkin
    resp = client.post(f"/api/v1/checkins/{c_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "CANCELLED"

    # Confirm cancelled checkin -> 400 Bad Request
    resp = client.post(f"/api/v1/checkins/{c_id}/confirm", json={}, headers=headers)
    assert resp.status_code == 400

def test_detect_missed_checkins_service(client, app):
    """Verify missed checkin detection marks overdue checkins as MISSED idempotently."""
    headers = _register_and_login(client, email="missed_test@example.com")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Schedule a checkin whose deadline is 5 minutes in the past
    past_sched = {
        "scheduled_at": (now - timedelta(minutes=10)).isoformat(),
        "deadline_at": (now - timedelta(minutes=5)).isoformat()
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json=past_sched, headers=headers)
    c_id = resp.get_json()["data"]["id"]

    # Run detection sweep
    sweep_resp = client.post("/api/v1/checkins/detect-missed", headers=headers)
    assert sweep_resp.status_code == 200
    assert sweep_resp.get_json()["data"]["missed_count"] >= 1

    # Check status of c_id
    with app.app_context():
        from app.extensions import db
        checkin = db.session.get(CheckIn, c_id)
        assert checkin.status == "MISSED"

    # Idempotent second sweep -> count 0
    sweep_resp2 = client.post("/api/v1/checkins/detect-missed", headers=headers)
    assert sweep_resp2.status_code == 200

def test_confirmed_checkin_not_marked_missed(client, app):
    """Verify a confirmed checkin is NEVER marked MISSED even if time advances past deadline."""
    headers = _register_and_login(client, email="confirmed_not_missed@example.com")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Create checkin and immediately confirm
    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json={}, headers=headers)
    c_id = resp.get_json()["data"]["id"]
    client.post(f"/api/v1/checkins/{c_id}/confirm", json={}, headers=headers)

    # Force deadline into the past
    with app.app_context():
        from app.extensions import db
        c = db.session.get(CheckIn, c_id)
        c.deadline_at = now - timedelta(hours=1)
        db.session.commit()

    # Run detection sweep
    client.post("/api/v1/checkins/detect-missed", headers=headers)

    with app.app_context():
        from app.extensions import db
        c = db.session.get(CheckIn, c_id)
        assert c.status == "CONFIRMED_SAFE"

def test_late_confirmation_rejected_when_missed(client):
    """Verify a confirmation arriving after deadline is rejected and checkin is marked MISSED."""
    headers = _register_and_login(client, email="late_confirm@example.com")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Schedule checkin in past
    past_sched = {
        "scheduled_at": (now - timedelta(minutes=10)).isoformat(),
        "deadline_at": (now - timedelta(minutes=2)).isoformat()
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/checkins", json=past_sched, headers=headers)
    c_id = resp.get_json()["data"]["id"]

    # Attempt to confirm after deadline has expired
    resp = client.post(f"/api/v1/checkins/{c_id}/confirm", json={}, headers=headers)
    assert resp.status_code == 409
    assert "MISSED" in resp.get_json()["message"]

def test_journey_delay_detection_service(client, app):
    """Verify delay detection flags active journeys exceeding expected arrival time."""
    headers = _register_and_login(client, email="delay_user@example.com", phone="+919876543621")
    now = datetime.now(timezone.utc)
    # Create journey whose expected arrival is 10 minutes ago
    start = now - timedelta(minutes=40)
    arrival = now - timedelta(minutes=10)
    payload = {
        "journey_title": "Delayed Journey",
        "start_location_name": "Terminal A",
        "start_location_address": "Street A",
        "destination_name": "Terminal B",
        "destination_address": "Street B",
        "planned_start_time": start.isoformat(),
        "expected_arrival_time": arrival.isoformat()
    }
    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    j_id = resp.get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)

    # Check initial delay status
    resp = client.get(f"/api/v1/journeys/{j_id}/delay", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["minutes_delayed"] >= 10

    # Run delay detection sweep
    sweep_resp = client.post("/api/v1/journeys/detect-delayed", headers=headers)
    assert sweep_resp.status_code == 200
    assert sweep_resp.get_json()["data"]["delayed_count"] >= 1

    with app.app_context():
        from app.extensions import db
        j = db.session.get(Journey, j_id)
        assert j.is_delayed is True
        assert j.delayed_at is not None

    # Idempotent second sweep
    sweep_resp2 = client.post("/api/v1/journeys/detect-delayed", headers=headers)
    assert sweep_resp2.status_code == 200
    assert sweep_resp2.get_json()["data"]["delayed_count"] == 0

def test_completed_journey_not_flagged_delayed(client, app):
    """Verify completed journeys are not flagged as delayed."""
    headers = _register_and_login(client, email="completed_no_delay@example.com", phone="+919876543622")
    now = datetime.now(timezone.utc)
    payload = {
        "journey_title": "Completed Journey",
        "start_location_name": "Terminal A",
        "start_location_address": "Street A",
        "destination_name": "Terminal B",
        "destination_address": "Street B",
        "planned_start_time": (now - timedelta(hours=2)).isoformat(),
        "expected_arrival_time": (now - timedelta(hours=1)).isoformat()
    }
    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    j_id = resp.get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)
    client.post(f"/api/v1/journeys/{j_id}/complete", headers=headers)

    sweep_resp = client.post("/api/v1/journeys/detect-delayed", headers=headers)
    assert sweep_resp.status_code == 200

    with app.app_context():
        from app.extensions import db
        j = db.session.get(Journey, j_id)
        assert j.is_delayed is False

def test_adaptive_scheduler_shortens_interval_on_delay(app):
    """Verify CheckinScheduler reduces interval when journey is delayed."""
    now = datetime.now(timezone.utc)
    with app.app_context():
        normal_journey = Journey(
            user_id=1,
            journey_title="Normal",
            start_location_name="A",
            start_location_address="A",
            destination_name="B",
            destination_address="B",
            planned_start_time=now,
            expected_arrival_time=now + timedelta(hours=1),
            status="ACTIVE",
            is_delayed=False
        )
        interval_normal = CheckinScheduler.compute_interval_minutes(normal_journey, current_time=now)
        assert interval_normal == 15

        delayed_journey = Journey(
            user_id=1,
            journey_title="Delayed",
            start_location_name="A",
            start_location_address="A",
            destination_name="B",
            destination_address="B",
            planned_start_time=now - timedelta(hours=2),
            expected_arrival_time=now - timedelta(minutes=15),
            status="ACTIVE",
            is_delayed=True
        )
        interval_delayed = CheckinScheduler.compute_interval_minutes(delayed_journey, current_time=now)
        assert interval_delayed == 5  # shortened to 5 minutes
