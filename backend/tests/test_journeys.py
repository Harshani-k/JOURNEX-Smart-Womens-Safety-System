import pytest
from datetime import datetime, timedelta, timezone

@pytest.fixture
def auth_tokens_u1(client):
    """Register and return auth token for User 1."""
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Divya Nair",
        "email": "divya.nair@example.com",
        "phone_number": "+919876543101",
        "password": "Password123"
    })
    return resp.get_json()["data"]["tokens"]["access_token"]

@pytest.fixture
def auth_tokens_u2(client):
    """Register and return auth token for User 2."""
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Pooja Hegde",
        "email": "pooja.hegde@example.com",
        "phone_number": "+919876543102",
        "password": "Password456"
    })
    return resp.get_json()["data"]["tokens"]["access_token"]

def sample_journey_payload():
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=15)
    arrival = start + timedelta(hours=1)
    return {
        "journey_title": "Evening Commute from Office to Home",
        "start_location_name": "Tech Park Office",
        "start_location_address": "123 Technology Corridor, Whitefield, Bengaluru",
        "start_latitude": 12.971598,
        "start_longitude": 77.594566,
        "destination_name": "Home Residency",
        "destination_address": "456 Green Valley Apartments, Indiranagar, Bengaluru",
        "destination_latitude": 12.978369,
        "destination_longitude": 77.640839,
        "planned_start_time": start.isoformat(),
        "expected_arrival_time": arrival.isoformat()
    }


# ==============================================================================
# 1. AUTHENTICATION & SECURITY
# ==============================================================================

def test_journeys_unauthenticated_access(client):
    """Reject unauthenticated access to all journey endpoints."""
    assert client.get("/api/v1/journeys").status_code == 401
    assert client.post("/api/v1/journeys", json={}).status_code == 401
    assert client.get("/api/v1/journeys/active").status_code == 401
    assert client.get("/api/v1/journeys/history").status_code == 401
    assert client.get("/api/v1/journeys/1").status_code == 401
    assert client.put("/api/v1/journeys/1", json={}).status_code == 401
    assert client.post("/api/v1/journeys/1/start").status_code == 401
    assert client.post("/api/v1/journeys/1/complete").status_code == 401
    assert client.post("/api/v1/journeys/1/cancel").status_code == 401


# ==============================================================================
# 2. JOURNEY CREATION & VALIDATION
# ==============================================================================

def test_create_journey_success(client, auth_tokens_u1):
    """Successfully create a journey in DRAFT status."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    payload = sample_journey_payload()

    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["journey_title"] == payload["journey_title"]
    assert data["status"] == "DRAFT"
    assert data["start_location"]["name"] == "Tech Park Office"
    assert data["destination"]["name"] == "Home Residency"
    assert data["actual_start_time"] is None
    assert data["actual_arrival_time"] is None
    assert "id" in data

def test_create_journey_missing_required_fields(client, auth_tokens_u1):
    """Reject journey creation with missing required fields."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    payload = sample_journey_payload()
    del payload["destination_name"]

    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Destination name is required" in resp.get_json()["message"]

def test_create_journey_invalid_coordinates(client, auth_tokens_u1):
    """Reject invalid latitude/longitude coordinate bounds."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}

    # Invalid latitude > 90
    bad_lat = sample_journey_payload()
    bad_lat["start_latitude"] = 95.0
    resp = client.post("/api/v1/journeys", json=bad_lat, headers=headers)
    assert resp.status_code == 400
    assert "latitude must be a valid number between -90.0 and 90.0" in resp.get_json()["message"]

    # Invalid longitude < -180
    bad_lng = sample_journey_payload()
    bad_lng["destination_longitude"] = -195.0
    resp2 = client.post("/api/v1/journeys", json=bad_lng, headers=headers)
    assert resp2.status_code == 400
    assert "longitude must be a valid number between -180.0 and 180.0" in resp2.get_json()["message"]

def test_create_journey_invalid_datetime(client, auth_tokens_u1):
    """Reject invalid datetime formats."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    payload = sample_journey_payload()
    payload["planned_start_time"] = "not-a-date"

    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Invalid datetime format" in resp.get_json()["message"]

def test_create_journey_arrival_before_start(client, auth_tokens_u1):
    """Reject expected arrival time that is earlier than or equal to planned start."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    now = datetime.now(timezone.utc)
    payload = sample_journey_payload()
    payload["planned_start_time"] = (now + timedelta(hours=2)).isoformat()
    payload["expected_arrival_time"] = (now + timedelta(hours=1)).isoformat()

    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Expected arrival time must be strictly later than planned start time" in resp.get_json()["message"]

def test_create_journey_mass_assignment_rejection(client, auth_tokens_u1):
    """Reject attempts to pass user_id, status, or actual timestamps."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    payload = sample_journey_payload()
    payload["user_id"] = 999
    payload["status"] = "COMPLETED"

    resp = client.post("/api/v1/journeys", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Modifying system-controlled or ownership field" in resp.get_json()["message"]


# ==============================================================================
# 3. JOURNEY RETRIEVAL & PAGINATION
# ==============================================================================

def test_list_journeys_and_pagination(client, auth_tokens_u1):
    """List journeys with pagination and status filtering."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}

    # Create 3 journeys
    for i in range(3):
        p = sample_journey_payload()
        p["journey_title"] = f"Journey #{i+1}"
        client.post("/api/v1/journeys", json=p, headers=headers)

    # Query with per_page=2
    resp = client.get("/api/v1/journeys?page=1&per_page=2", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["journeys"]) == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["total_pages"] == 2
    assert data["pagination"]["has_next"] is True

    # Filter by status=DRAFT
    resp_draft = client.get("/api/v1/journeys?status=DRAFT", headers=headers)
    assert resp_draft.status_code == 200
    assert len(resp_draft.get_json()["data"]["journeys"]) == 3

    # Filter by non-matching status
    resp_active = client.get("/api/v1/journeys?status=ACTIVE", headers=headers)
    assert resp_active.status_code == 200
    assert len(resp_active.get_json()["data"]["journeys"]) == 0

def test_retrieve_individual_journey(client, auth_tokens_u1):
    """Retrieve single journey by ID."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    p = sample_journey_payload()
    j_id = client.post("/api/v1/journeys", json=p, headers=headers).get_json()["data"]["id"]

    resp = client.get(f"/api/v1/journeys/{j_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["id"] == j_id

def test_user_ownership_isolation(client, auth_tokens_u1, auth_tokens_u2):
    """Verify User 2 cannot access, update, start, complete, or cancel User 1's journey."""
    h1 = {"Authorization": f"Bearer {auth_tokens_u1}"}
    h2 = {"Authorization": f"Bearer {auth_tokens_u2}"}

    j1_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=h1).get_json()["data"]["id"]

    # User 2 queries User 1's journey -> 404
    assert client.get(f"/api/v1/journeys/{j1_id}", headers=h2).status_code == 404
    assert client.put(f"/api/v1/journeys/{j1_id}", json={"journey_title": "Hacked"}, headers=h2).status_code == 404
    assert client.post(f"/api/v1/journeys/{j1_id}/start", headers=h2).status_code == 404
    assert client.post(f"/api/v1/journeys/{j1_id}/complete", headers=h2).status_code == 404
    assert client.post(f"/api/v1/journeys/{j1_id}/cancel", headers=h2).status_code == 404

def test_update_draft_journey(client, auth_tokens_u1):
    """Update details of a DRAFT journey."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    j_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]

    update_payload = {"journey_title": "Updated Commute Title"}
    resp = client.put(f"/api/v1/journeys/{j_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["journey_title"] == "Updated Commute Title"


# ==============================================================================
# 4. JOURNEY LIFECYCLE (START, ACTIVE, COMPLETE, CANCEL)
# ==============================================================================

def test_start_journey_lifecycle(client, auth_tokens_u1):
    """Start a DRAFT journey, transitioning to ACTIVE and recording actual_start_time."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    j_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]

    start_resp = client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)
    assert start_resp.status_code == 200
    data = start_resp.get_json()["data"]
    assert data["status"] == "ACTIVE"
    assert data["actual_start_time"] is not None

def test_reject_multiple_active_journeys(client, auth_tokens_u1):
    """Reject starting a second journey when one is already ACTIVE."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    j1_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    j2_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]

    # Start Journey 1
    assert client.post(f"/api/v1/journeys/{j1_id}/start", headers=headers).status_code == 200

    # Attempt to start Journey 2 -> 409 Conflict
    resp = client.post(f"/api/v1/journeys/{j2_id}/start", headers=headers)
    assert resp.status_code == 409
    assert "already have an active journey" in resp.get_json()["message"]

def test_get_active_journey(client, auth_tokens_u1):
    """Get active journey endpoint returns active journey or null."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}

    # When no journey is active
    empty_resp = client.get("/api/v1/journeys/active", headers=headers)
    assert empty_resp.status_code == 200
    assert empty_resp.get_json()["data"] is None

    # Start a journey
    j_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)

    active_resp = client.get("/api/v1/journeys/active", headers=headers)
    assert active_resp.status_code == 200
    assert active_resp.get_json()["data"]["id"] == j_id
    assert active_resp.get_json()["data"]["status"] == "ACTIVE"

def test_complete_active_journey(client, auth_tokens_u1):
    """Complete active journey and record actual_arrival_time."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    j_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)

    comp_resp = client.post(f"/api/v1/journeys/{j_id}/complete", headers=headers)
    assert comp_resp.status_code == 200
    data = comp_resp.get_json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["actual_arrival_time"] is not None

def test_cancel_draft_and_active_journey(client, auth_tokens_u1):
    """Cancel DRAFT journey and cancel ACTIVE journey with optional reason."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}

    # Cancel DRAFT
    j1_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    c1_resp = client.post(f"/api/v1/journeys/{j1_id}/cancel", json={"cancellation_reason": "Change of plans"}, headers=headers)
    assert c1_resp.status_code == 200
    assert c1_resp.get_json()["data"]["status"] == "CANCELLED"
    assert c1_resp.get_json()["data"]["cancellation_reason"] == "Change of plans"

    # Cancel ACTIVE
    j2_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j2_id}/start", headers=headers)

    c2_resp = client.post(f"/api/v1/journeys/{j2_id}/cancel", json={"cancellation_reason": "Vehicle breakdown"}, headers=headers)
    assert c2_resp.status_code == 200
    assert c2_resp.get_json()["data"]["status"] == "CANCELLED"
    assert c2_resp.get_json()["data"]["cancellation_reason"] == "Vehicle breakdown"

def test_invalid_lifecycle_transitions(client, auth_tokens_u1):
    """Reject invalid state transitions."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}
    j_id = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]

    # 1. Complete a DRAFT journey directly
    resp1 = client.post(f"/api/v1/journeys/{j_id}/complete", headers=headers)
    assert resp1.status_code == 400
    assert "Cannot complete a draft journey" in resp1.get_json()["message"]

    # 2. Start it
    client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)

    # 3. Edit while ACTIVE
    resp2 = client.put(f"/api/v1/journeys/{j_id}", json={"journey_title": "New Title"}, headers=headers)
    assert resp2.status_code == 400
    assert "Only DRAFT journeys can be modified" in resp2.get_json()["message"]

    # 4. Complete it
    client.post(f"/api/v1/journeys/{j_id}/complete", headers=headers)

    # 5. Start a COMPLETED journey
    resp3 = client.post(f"/api/v1/journeys/{j_id}/start", headers=headers)
    assert resp3.status_code == 400
    assert "Cannot start a journey with status 'COMPLETED'" in resp3.get_json()["message"]

    # 6. Cancel a COMPLETED journey
    resp4 = client.post(f"/api/v1/journeys/{j_id}/cancel", headers=headers)
    assert resp4.status_code == 400
    assert "Cannot cancel an already completed journey" in resp4.get_json()["message"]


# ==============================================================================
# 5. JOURNEY HISTORY
# ==============================================================================

def test_journey_history_endpoint(client, auth_tokens_u1):
    """Verify that only COMPLETED and CANCELLED journeys appear in history."""
    headers = {"Authorization": f"Bearer {auth_tokens_u1}"}

    # 1. DRAFT journey (should NOT appear)
    client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers)

    # 2. COMPLETED journey (SHOULD appear)
    j2 = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j2}/start", headers=headers)
    client.post(f"/api/v1/journeys/{j2}/complete", headers=headers)

    # 3. CANCELLED journey (SHOULD appear)
    j3 = client.post("/api/v1/journeys", json=sample_journey_payload(), headers=headers).get_json()["data"]["id"]
    client.post(f"/api/v1/journeys/{j3}/cancel", headers=headers)

    # 4. Query history
    hist_resp = client.get("/api/v1/journeys/history", headers=headers)
    assert hist_resp.status_code == 200
    history = hist_resp.get_json()["data"]["journeys"]
    assert len(history) == 2
    statuses = {h["status"] for h in history}
    assert statuses == {"COMPLETED", "CANCELLED"}
