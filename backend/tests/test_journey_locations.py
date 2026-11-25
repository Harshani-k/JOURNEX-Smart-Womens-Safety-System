import pytest
from datetime import datetime, timedelta, timezone

@pytest.fixture
def auth_user1(client):
    """Register and return auth token and active journey ID for User 1."""
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Kiran Bedi",
        "email": "kiran.bedi@example.com",
        "phone_number": "+919876543501",
        "password": "Password123"
    })
    token = resp.get_json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create & start active journey
    now = datetime.now(timezone.utc)
    j_resp = client.post("/api/v1/journeys", json={
        "journey_title": "Field Inspection",
        "start_location_name": "Police HQ",
        "start_location_address": "Infantry Road, Bengaluru",
        "destination_name": "City Center",
        "destination_address": "MG Road, Bengaluru",
        "planned_start_time": now.isoformat(),
        "expected_arrival_time": (now + timedelta(hours=1)).isoformat()
    }, headers=headers)
    j_id = j_resp.get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)

    return {"token": token, "journey_id": j_id}

@pytest.fixture
def auth_user2(client):
    """Register User 2."""
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Sunita Rao",
        "email": "sunita.rao@example.com",
        "phone_number": "+919876543502",
        "password": "Password456"
    })
    token = resp.get_json()["data"]["tokens"]["access_token"]
    return {"token": token}

def test_unauthenticated_locations_access(client):
    """Reject unauthenticated requests to location endpoints."""
    assert client.post("/api/v1/journeys/1/locations", json={}).status_code == 401
    assert client.get("/api/v1/journeys/1/locations").status_code == 401
    assert client.get("/api/v1/journeys/1/locations/latest").status_code == 401

def test_successful_single_location_upload(client, auth_user1):
    """Upload a single location object to active journey."""
    token = auth_user1["token"]
    j_id = auth_user1["journey_id"]
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    loc_payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "accuracy": 8.5,
        "altitude": 920.0,
        "speed": 12.5,
        "bearing": 180.0,
        "recorded_at": now.isoformat()
    }

    resp = client.post(f"/api/v1/journeys/{j_id}/locations", json=loc_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["accepted_count"] == 1
    assert data["rejected_count"] == 0
    assert data["total_received"] == 1

def test_batch_location_upload_and_deduplication(client, auth_user1):
    """Upload batch of locations and verify duplicate timestamps are safely rejected."""
    token = auth_user1["token"]
    j_id = auth_user1["journey_id"]
    headers = {"Authorization": f"Bearer {token}"}

    base_time = datetime.now(timezone.utc)
    batch = {
        "locations": [
            {
                "latitude": 12.9716 + (i * 0.001),
                "longitude": 77.5946 + (i * 0.001),
                "accuracy": 5.0,
                "speed": 10.0,
                "recorded_at": (base_time + timedelta(seconds=i * 5)).isoformat()
            }
            for i in range(5)
        ]
    }

    # First upload: all 5 accepted
    resp1 = client.post(f"/api/v1/journeys/{j_id}/locations", json=batch, headers=headers)
    assert resp1.status_code == 201
    assert resp1.get_json()["data"]["accepted_count"] == 5

    # Second upload with identical timestamps: 5 duplicates rejected
    resp2 = client.post(f"/api/v1/journeys/{j_id}/locations", json=batch, headers=headers)
    assert resp2.status_code == 201
    assert resp2.get_json()["data"]["accepted_count"] == 0
    assert resp2.get_json()["data"]["rejected_count"] == 5

def test_reject_invalid_location_fields(client, auth_user1):
    """Reject out-of-bounds coordinates and invalid numeric fields."""
    token = auth_user1["token"]
    j_id = auth_user1["journey_id"]
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc).isoformat()

    # Invalid latitude > 90
    bad_lat = {"latitude": 95.0, "longitude": 77.0, "accuracy": 10.0, "recorded_at": now}
    assert client.post(f"/api/v1/journeys/{j_id}/locations", json=bad_lat, headers=headers).status_code == 400

    # Invalid longitude < -180
    bad_lng = {"latitude": 12.0, "longitude": -185.0, "accuracy": 10.0, "recorded_at": now}
    assert client.post(f"/api/v1/journeys/{j_id}/locations", json=bad_lng, headers=headers).status_code == 400

    # Negative accuracy
    bad_acc = {"latitude": 12.0, "longitude": 77.0, "accuracy": -5.0, "recorded_at": now}
    assert client.post(f"/api/v1/journeys/{j_id}/locations", json=bad_acc, headers=headers).status_code == 400

    # Negative speed
    bad_spd = {"latitude": 12.0, "longitude": 77.0, "accuracy": 10.0, "speed": -2.0, "recorded_at": now}
    assert client.post(f"/api/v1/journeys/{j_id}/locations", json=bad_spd, headers=headers).status_code == 400

def test_reject_upload_for_non_active_journey(client, auth_user1):
    """Reject location upload for DRAFT, COMPLETED, or CANCELLED journeys."""
    token = auth_user1["token"]
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc)

    # Create a DRAFT journey (not started)
    draft_resp = client.post("/api/v1/journeys", json={
        "journey_title": "Draft Journey",
        "start_location_name": "Origin Hub A",
        "start_location_address": "Origin Address A",
        "destination_name": "Destination Hub B",
        "destination_address": "Destination Address B",
        "planned_start_time": now.isoformat(),
        "expected_arrival_time": (now + timedelta(hours=1)).isoformat()
    }, headers=headers)
    assert draft_resp.status_code == 201
    draft_id = draft_resp.get_json()["data"]["id"]

    loc_payload = {"latitude": 12.9, "longitude": 77.5, "accuracy": 5.0, "recorded_at": now.isoformat()}
    resp = client.post(f"/api/v1/journeys/{draft_id}/locations", json=loc_payload, headers=headers)
    assert resp.status_code == 400
    assert "Journey must be ACTIVE" in resp.get_json()["message"]

def test_location_ownership_isolation(client, auth_user1, auth_user2):
    """Verify User 2 cannot upload or view User 1's journey locations."""
    j1_id = auth_user1["journey_id"]
    h2 = {"Authorization": f"Bearer {auth_user2['token']}"}
    now = datetime.now(timezone.utc).isoformat()

    loc_payload = {"latitude": 12.9, "longitude": 77.5, "accuracy": 5.0, "recorded_at": now}
    assert client.post(f"/api/v1/journeys/{j1_id}/locations", json=loc_payload, headers=h2).status_code == 404
    assert client.get(f"/api/v1/journeys/{j1_id}/locations", headers=h2).status_code == 404
    assert client.get(f"/api/v1/journeys/{j1_id}/locations/latest", headers=h2).status_code == 404

def test_retrieve_history_and_latest_location(client, auth_user1):
    """Verify chronological history retrieval and latest location fix."""
    token = auth_user1["token"]
    j_id = auth_user1["journey_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Before upload, latest is null
    assert client.get(f"/api/v1/journeys/{j_id}/locations/latest", headers=headers).get_json()["data"] is None

    base_time = datetime.now(timezone.utc)
    for i in range(3):
        client.post(f"/api/v1/journeys/{j_id}/locations", json={
            "latitude": 12.9 + (i * 0.01),
            "longitude": 77.5 + (i * 0.01),
            "accuracy": 10.0 - i,
            "recorded_at": (base_time + timedelta(minutes=i)).isoformat()
        }, headers=headers)

    # Check history (should have 3 items sorted ascending)
    hist_resp = client.get(f"/api/v1/journeys/{j_id}/locations", headers=headers)
    assert hist_resp.status_code == 200
    data = hist_resp.get_json()["data"]
    assert len(data["locations"]) == 3
    assert data["locations"][0]["accuracy"] == 10.0
    assert data["locations"][2]["accuracy"] == 8.0

    # Check latest location (should be index 2)
    latest_resp = client.get(f"/api/v1/journeys/{j_id}/locations/latest", headers=headers)
    assert latest_resp.status_code == 200
    assert latest_resp.get_json()["data"]["accuracy"] == 8.0
