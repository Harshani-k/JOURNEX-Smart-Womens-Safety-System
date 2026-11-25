import pytest
from datetime import datetime, timezone, timedelta
from app.models.safety_event import SafetyEvent
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.services.deviation_service import DeviationService, haversine_distance, point_to_segment_distance

def _auth_headers(client, email_suffix="p6"):
    reg_payload = {
        "full_name": "Route Deviation Traveler",
        "email": f"deviation_{email_suffix}_{int(datetime.now().timestamp())}@journex.org",
        "password": "SecurePassword123!",
        "phone_number": "+91 98840 99887"
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_resp.get_json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _create_active_journey(client, headers, title="Route Corridor Test Trip"):
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=5)
    arrival = now + timedelta(minutes=30)
    # Start: (11.0000, 77.0000), Destination: (11.0100, 77.0000) -> due north ~1112m
    payload = {
        "journey_title": title,
        "start_location_name": "Origin Hub",
        "start_location_address": "Point A",
        "start_latitude": 11.0000,
        "start_longitude": 77.0000,
        "destination_name": "Dest Hub",
        "destination_address": "Point B",
        "destination_latitude": 11.0100,
        "destination_longitude": 77.0000,
        "planned_start_time": start.isoformat(),
        "expected_arrival_time": arrival.isoformat()
    }
    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    journey_id = resp.get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{journey_id}/start", headers=headers)
    return journey_id

def test_distance_and_corridor_calculation():
    """Verify geographic math: Haversine distance and point to line segment."""
    # ~1.11 km north along line of longitude
    d = haversine_distance(11.0000, 77.0000, 11.0100, 77.0000)
    assert 1100.0 < d < 1120.0

    # Point directly on the corridor halfway
    dist_on_line = point_to_segment_distance(11.0050, 77.0000, 11.0000, 77.0000, 11.0100, 77.0000)
    assert dist_on_line < 5.0  # essentially 0m

    # Point 0.005 degrees east (~546m away from segment)
    dist_off_line = point_to_segment_distance(11.0050, 77.0050, 11.0000, 77.0000, 11.0100, 77.0000)
    assert 540.0 < dist_off_line < 560.0

def test_normal_route_movement_no_deviation(client):
    """Normal fixes along corridor should not trigger deviation event."""
    headers = _auth_headers(client, "normal")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Fix directly on corridor: (11.0050, 77.0000)
    loc_payload = {
        "locations": [
            {
                "latitude": 11.0050,
                "longitude": 77.0000,
                "accuracy": 10.0,
                "speed": 5.0,
                "recorded_at": (now - timedelta(seconds=10)).isoformat()
            }
        ]
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/locations", json=loc_payload, headers=headers)
    assert resp.status_code == 201

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    assert events_resp.status_code == 200
    assert len(events_resp.get_json()["data"]["safety_events"]) == 0

def test_poor_gps_accuracy_ignored(client):
    """Fixes with poor accuracy (>50m) should be ignored and not trigger deviation."""
    headers = _auth_headers(client, "poor_acc")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Way off corridor (550m east), but accuracy is terrible (85m)
    loc_payload = {
        "locations": [
            {
                "latitude": 11.0050,
                "longitude": 77.0050,
                "accuracy": 85.0,  # poor accuracy
                "speed": 5.0,
                "recorded_at": now.isoformat()
            }
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=loc_payload, headers=headers)

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    assert len(events_resp.get_json()["data"]["safety_events"]) == 0

def test_single_deviated_fix_treated_as_noise(client):
    """A single deviated fix should be ignored as temporary GPS noise."""
    headers = _auth_headers(client, "noise")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Only 1 fix deviated 550m
    loc_payload = {
        "locations": [
            {
                "latitude": 11.0050,
                "longitude": 77.0050,
                "accuracy": 15.0,
                "speed": 4.0,
                "recorded_at": now.isoformat()
            }
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=loc_payload, headers=headers)

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    assert len(events_resp.get_json()["data"]["safety_events"]) == 0

def test_multiple_consecutive_deviations_trigger_event(client):
    """3 consecutive deviated fixes should reliably trigger a ROUTE_DEVIATION event."""
    headers = _auth_headers(client, "consec_dev")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # 3 consecutive fixes deviated ~550m east from corridor
    loc_payload = {
        "locations": [
            {
                "latitude": 11.0040,
                "longitude": 77.0050,
                "accuracy": 12.0,
                "speed": 6.0,
                "recorded_at": (now - timedelta(seconds=30)).isoformat()
            },
            {
                "latitude": 11.0050,
                "longitude": 77.0050,
                "accuracy": 10.0,
                "speed": 6.0,
                "recorded_at": (now - timedelta(seconds=15)).isoformat()
            },
            {
                "latitude": 11.0060,
                "longitude": 77.0050,
                "accuracy": 11.0,
                "speed": 6.0,
                "recorded_at": now.isoformat()
            }
        ]
    }
    resp = client.post(f"/api/v1/journeys/{journey_id}/locations", json=loc_payload, headers=headers)
    assert resp.status_code == 201

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    events = events_resp.get_json()["data"]["safety_events"]
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "ROUTE_DEVIATION"
    assert event["status"] == "ACTIVE"
    assert event["deviation_distance"] > 300.0
    assert event["consecutive_count"] >= 3

def test_duplicate_event_prevention(client):
    """Subsequent deviated fixes should update the existing ACTIVE event, not duplicate."""
    headers = _auth_headers(client, "dedup")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # First batch of 3 deviated fixes
    batch1 = {
        "locations": [
            {"latitude": 11.0040, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": (now - timedelta(seconds=40)).isoformat()},
            {"latitude": 11.0050, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": (now - timedelta(seconds=20)).isoformat()},
            {"latitude": 11.0060, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": (now - timedelta(seconds=10)).isoformat()}
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=batch1, headers=headers)

    # Second batch with further deviation
    batch2 = {
        "locations": [
            {"latitude": 11.0070, "longitude": 77.0060, "accuracy": 10.0, "speed": 5.0, "recorded_at": now.isoformat()}
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=batch2, headers=headers)

    active_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events/active", headers=headers)
    active_events = active_resp.get_json()["data"]["active_events"]
    # Still exactly ONE active route deviation event
    assert len(active_events) == 1
    assert active_events[0]["consecutive_count"] >= 3

def test_unexpected_stop_detection(client):
    """Vehicle stationary for >= 10 mins with displacement < 25m triggers UNEXPECTED_STOP."""
    headers = _auth_headers(client, "unexp_stop")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Stationary fixes halfway along journey over 12 minutes (720 seconds)
    stationary_batch = {
        "locations": [
            {"latitude": 11.00500, "longitude": 77.00000, "accuracy": 8.0, "speed": 0.0, "recorded_at": (now - timedelta(minutes=12)).isoformat()},
            {"latitude": 11.00501, "longitude": 77.00001, "accuracy": 8.0, "speed": 0.1, "recorded_at": (now - timedelta(minutes=6)).isoformat()},
            {"latitude": 11.00500, "longitude": 77.00000, "accuracy": 8.0, "speed": 0.0, "recorded_at": now.isoformat()}
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=stationary_batch, headers=headers)

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    events = events_resp.get_json()["data"]["safety_events"]
    stop_event = next((e for e in events if e["event_type"] == "UNEXPECTED_STOP"), None)
    assert stop_event is not None
    assert stop_event["status"] == "ACTIVE"
    assert stop_event["duration_seconds"] >= 600

def test_normal_traffic_delay_not_unexpected_stop(client):
    """Normal traffic with progressive stop-and-go displacement should not trigger unexpected stop."""
    headers = _auth_headers(client, "traffic")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Vehicle moving slowly in traffic: displacement advances ~80m over 12 mins
    traffic_batch = {
        "locations": [
            {"latitude": 11.0020, "longitude": 77.0000, "accuracy": 8.0, "speed": 1.2, "recorded_at": (now - timedelta(minutes=12)).isoformat()},
            {"latitude": 11.0024, "longitude": 77.0000, "accuracy": 8.0, "speed": 0.8, "recorded_at": (now - timedelta(minutes=6)).isoformat()},
            {"latitude": 11.0028, "longitude": 77.0000, "accuracy": 8.0, "speed": 1.5, "recorded_at": now.isoformat()}
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=traffic_batch, headers=headers)

    events_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events", headers=headers)
    events = events_resp.get_json()["data"]["safety_events"]
    stop_event = next((e for e in events if e["event_type"] == "UNEXPECTED_STOP"), None)
    assert stop_event is None

def test_safety_event_acknowledge_and_resolve_lifecycle(client):
    """User acknowledges and resolves safety event with notes and idempotency."""
    headers = _auth_headers(client, "lifecycle")
    journey_id = _create_active_journey(client, headers)

    now = datetime.now(timezone.utc)
    # Trigger deviation
    batch = {
        "locations": [
            {"latitude": 11.0040, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": (now - timedelta(seconds=30)).isoformat()},
            {"latitude": 11.0050, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": (now - timedelta(seconds=15)).isoformat()},
            {"latitude": 11.0060, "longitude": 77.0050, "accuracy": 10.0, "speed": 5.0, "recorded_at": now.isoformat()}
        ]
    }
    client.post(f"/api/v1/journeys/{journey_id}/locations", json=batch, headers=headers)

    active_resp = client.get(f"/api/v1/journeys/{journey_id}/safety-events/active", headers=headers)
    event_id = active_resp.get_json()["data"]["active_events"][0]["id"]

    # 1. Acknowledge
    ack_resp = client.post(f"/api/v1/journeys/{journey_id}/safety-events/{event_id}/acknowledge", headers=headers)
    assert ack_resp.status_code == 200
    assert ack_resp.get_json()["data"]["status"] == "ACKNOWLEDGED"

    # 2. Resolve
    resolve_resp = client.post(
        f"/api/v1/journeys/{journey_id}/safety-events/{event_id}/resolve",
        json={"resolution_notes": "Taking verified detour around road closure", "client_action_id": "act-resolve-001"},
        headers=headers
    )
    assert resolve_resp.status_code == 200
    res_data = resolve_resp.get_json()["data"]
    assert res_data["status"] == "RESOLVED"
    assert "detour" in res_data["resolution_notes"]

    # 3. Idempotent re-resolve
    dup_res = client.post(
        f"/api/v1/journeys/{journey_id}/safety-events/{event_id}/resolve",
        json={"resolution_notes": "Duplicate", "client_action_id": "act-resolve-001"},
        headers=headers
    )
    assert dup_res.status_code == 200
    assert dup_res.get_json()["data"]["status"] == "RESOLVED"

    # Active events list is now empty
    active_now = client.get(f"/api/v1/journeys/{journey_id}/safety-events/active", headers=headers)
    assert len(active_now.get_json()["data"]["active_events"]) == 0

def test_safety_events_user_isolation(client):
    """Users cannot view or modify safety events belonging to other users."""
    headers1 = _auth_headers(client, "user1")
    headers2 = _auth_headers(client, "user2")

    journey1_id = _create_active_journey(client, headers1)

    # User 2 tries to access User 1's safety events
    resp = client.get(f"/api/v1/journeys/{journey1_id}/safety-events", headers=headers2)
    assert resp.status_code == 404

    # User 2 tries to acknowledge
    ack_resp = client.post(f"/api/v1/journeys/{journey1_id}/safety-events/1/acknowledge", headers=headers2)
    assert ack_resp.status_code == 404
