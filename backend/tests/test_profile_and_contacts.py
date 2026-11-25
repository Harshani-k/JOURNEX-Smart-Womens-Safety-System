import pytest

@pytest.fixture
def auth_tokens(client):
    """Register and return auth tokens for User 1."""
    user_payload = {
        "full_name": "Ananya Sharma",
        "email": "ananya@example.com",
        "phone_number": "+919876543201",
        "password": "Password123"
    }
    resp = client.post("/api/v1/auth/register", json=user_payload)
    return resp.get_json()["data"]["tokens"]["access_token"]

@pytest.fixture
def auth_tokens_user2(client):
    """Register and return auth tokens for User 2."""
    user_payload = {
        "full_name": "Bhavna Patel",
        "email": "bhavna@example.com",
        "phone_number": "+919876543202",
        "password": "Password456"
    }
    resp = client.post("/api/v1/auth/register", json=user_payload)
    return resp.get_json()["data"]["tokens"]["access_token"]


# ==============================================================================
# SAFETY PROFILE TESTS
# ==============================================================================

def test_profile_unauthenticated_access(client):
    """Reject unauthenticated GET/POST/PUT to /api/v1/profile."""
    assert client.get("/api/v1/profile").status_code == 401
    assert client.post("/api/v1/profile", json={}).status_code == 401
    assert client.put("/api/v1/profile", json={}).status_code == 401

def test_profile_not_created_yet(client, auth_tokens):
    """Return 404 when retrieving a profile that hasn't been created yet."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert "not been created" in data["message"]

def test_create_profile_success(client, auth_tokens):
    """Create safety profile successfully with valid input."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    payload = {
        "display_name": "Anu",
        "preferred_language": "en",
        "emergency_message": "Emergency! I feel unsafe, please track my location.",
        "additional_safety_notes": "Type 1 Diabetic. Carrying medication."
    }
    resp = client.post("/api/v1/profile", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["display_name"] == "Anu"
    assert data["data"]["preferred_language"] == "en"
    assert data["data"]["emergency_message"] == payload["emergency_message"]
    assert data["data"]["additional_safety_notes"] == payload["additional_safety_notes"]
    assert "id" in data["data"]

def test_reject_duplicate_profile(client, auth_tokens):
    """Reject creating a second safety profile for the same user with 409 Conflict."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    payload = {
        "display_name": "Anu",
        "emergency_message": "Emergency alert message."
    }
    resp1 = client.post("/api/v1/profile", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/profile", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert resp2.get_json()["success"] is False
    assert "already exists" in resp2.get_json()["message"]

def test_retrieve_profile(client, auth_tokens):
    """Retrieve existing safety profile for authenticated user."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    payload = {
        "display_name": "Anu S",
        "emergency_message": "Please call police immediately."
    }
    client.post("/api/v1/profile", json=payload, headers=headers)

    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["display_name"] == "Anu S"
    assert data["data"]["emergency_message"] == "Please call police immediately."

def test_update_profile(client, auth_tokens):
    """Update safety profile successfully."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    initial = {
        "display_name": "Anu Initial",
        "emergency_message": "Initial alert message."
    }
    client.post("/api/v1/profile", json=initial, headers=headers)

    update_payload = {
        "display_name": "Anu Updated",
        "preferred_language": "hi",
        "additional_safety_notes": "Updated blood group O+"
    }
    resp = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["display_name"] == "Anu Updated"
    assert data["data"]["preferred_language"] == "hi"
    assert data["data"]["additional_safety_notes"] == "Updated blood group O+"
    # Emergency message remains intact
    assert data["data"]["emergency_message"] == "Initial alert message."

def test_profile_validation_and_mass_assignment(client, auth_tokens):
    """Validate invalid fields and mass assignment rejection."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}

    # Too short display_name
    resp = client.post("/api/v1/profile", json={"display_name": "A", "emergency_message": "Safe emergency"}, headers=headers)
    assert resp.status_code == 400

    # Short emergency message
    resp = client.post("/api/v1/profile", json={"display_name": "Valid Name", "emergency_message": "Sos"}, headers=headers)
    assert resp.status_code == 400

    # Attempt mass assignment of user_id
    resp = client.post("/api/v1/profile", json={"user_id": 999, "display_name": "Valid Name", "emergency_message": "Valid emergency message"}, headers=headers)
    assert resp.status_code == 400
    assert "Modifying internal" in resp.get_json()["message"]

def test_profile_user_isolation(client, auth_tokens, auth_tokens_user2):
    """Verify User 1 and User 2 have isolated profiles."""
    h1 = {"Authorization": f"Bearer {auth_tokens}"}
    h2 = {"Authorization": f"Bearer {auth_tokens_user2}"}

    client.post("/api/v1/profile", json={"display_name": "User 1 Profile", "emergency_message": "User 1 message"}, headers=h1)
    client.post("/api/v1/profile", json={"display_name": "User 2 Profile", "emergency_message": "User 2 message"}, headers=h2)

    p1 = client.get("/api/v1/profile", headers=h1).get_json()["data"]
    p2 = client.get("/api/v1/profile", headers=h2).get_json()["data"]

    assert p1["display_name"] == "User 1 Profile"
    assert p2["display_name"] == "User 2 Profile"
    assert p1["id"] != p2["id"]


# ==============================================================================
# TRUSTED CONTACTS TESTS
# ==============================================================================

def test_contacts_unauthenticated_access(client):
    """Reject unauthenticated calls to /api/v1/contacts endpoints."""
    assert client.get("/api/v1/contacts").status_code == 401
    assert client.post("/api/v1/contacts", json={}).status_code == 401
    assert client.get("/api/v1/contacts/1").status_code == 401
    assert client.put("/api/v1/contacts/1", json={}).status_code == 401
    assert client.delete("/api/v1/contacts/1").status_code == 401
    assert client.patch("/api/v1/contacts/1/primary").status_code == 401

def test_add_and_list_contacts(client, auth_tokens):
    """Add contacts and list them sorted by priority."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}

    c1 = {
        "contact_name": "Mother",
        "phone_number": "+919876543210",
        "relationship": "Parent",
        "priority": 1,
        "is_primary": True
    }
    c2 = {
        "contact_name": "Father",
        "phone_number": "+919876543211",
        "relationship": "Parent",
        "priority": 2
    }

    resp1 = client.post("/api/v1/contacts", json=c1, headers=headers)
    assert resp1.status_code == 201
    data1 = resp1.get_json()["data"]
    assert data1["contact_name"] == "Mother"
    assert data1["is_primary"] is True
    assert data1["consent_status"] == "PENDING"
    assert data1["verified_at"] is None

    resp2 = client.post("/api/v1/contacts", json=c2, headers=headers)
    assert resp2.status_code == 201

    list_resp = client.get("/api/v1/contacts", headers=headers)
    assert list_resp.status_code == 200
    contacts = list_resp.get_json()["data"]
    assert len(contacts) == 2
    assert contacts[0]["contact_name"] == "Mother"
    assert contacts[1]["contact_name"] == "Father"

def test_get_individual_contact(client, auth_tokens):
    """Retrieve individual contact by ID."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    c = {
        "contact_name": "Sister",
        "phone_number": "+919876543212",
        "relationship": "Sibling",
        "priority": 1
    }
    created = client.post("/api/v1/contacts", json=c, headers=headers).get_json()["data"]
    contact_id = created["id"]

    resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["id"] == contact_id
    assert data["contact_name"] == "Sister"

def test_update_contact(client, auth_tokens):
    """Update contact attributes."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    c = {
        "contact_name": "Brother Initial",
        "phone_number": "+919876543213",
        "relationship": "Sibling",
        "priority": 3
    }
    created = client.post("/api/v1/contacts", json=c, headers=headers).get_json()["data"]
    contact_id = created["id"]

    update_payload = {
        "contact_name": "Brother Renamed",
        "priority": 1
    }
    resp = client.put(f"/api/v1/contacts/{contact_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["contact_name"] == "Brother Renamed"
    assert data["priority"] == 1
    assert data["phone_number"] == "+919876543213"

def test_delete_contact(client, auth_tokens):
    """Delete contact and verify it no longer exists."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    c = {
        "contact_name": "Temporary Contact",
        "phone_number": "+919876543214",
        "relationship": "Friend",
        "priority": 1
    }
    created = client.post("/api/v1/contacts", json=c, headers=headers).get_json()["data"]
    contact_id = created["id"]

    del_resp = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert del_resp.status_code == 200

    # Querying deleted contact returns 404
    get_resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert get_resp.status_code == 404

def test_primary_contact_setting_and_uniqueness(client, auth_tokens):
    """Ensure only one primary contact exists per user."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    c1 = {"contact_name": "C1", "phone_number": "+919876543221", "relationship": "Friend", "priority": 1, "is_primary": True}
    c2 = {"contact_name": "C2", "phone_number": "+919876543222", "relationship": "Friend", "priority": 2, "is_primary": False}

    id1 = client.post("/api/v1/contacts", json=c1, headers=headers).get_json()["data"]["id"]
    id2 = client.post("/api/v1/contacts", json=c2, headers=headers).get_json()["data"]["id"]

    # Verify id1 is primary, id2 is not
    assert client.get(f"/api/v1/contacts/{id1}", headers=headers).get_json()["data"]["is_primary"] is True
    assert client.get(f"/api/v1/contacts/{id2}", headers=headers).get_json()["data"]["is_primary"] is False

    # Set id2 as primary via PATCH
    patch_resp = client.patch(f"/api/v1/contacts/{id2}/primary", headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["data"]["is_primary"] is True

    # Now verify id1 has been automatically demoted to non-primary
    assert client.get(f"/api/v1/contacts/{id1}", headers=headers).get_json()["data"]["is_primary"] is False
    assert client.get(f"/api/v1/contacts/{id2}", headers=headers).get_json()["data"]["is_primary"] is True

def test_reject_duplicate_phone_for_same_user(client, auth_tokens):
    """Reject duplicate phone number for the same user with 409 Conflict."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    c1 = {"contact_name": "Contact A", "phone_number": "+919876543230", "relationship": "Friend"}
    c2 = {"contact_name": "Contact B", "phone_number": "+919876543230", "relationship": "Colleague"}

    resp1 = client.post("/api/v1/contacts", json=c1, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/contacts", json=c2, headers=headers)
    assert resp2.status_code == 409
    assert "already exists" in resp2.get_json()["message"]

def test_reject_more_than_5_contacts(client, auth_tokens):
    """Reject adding a 6th contact with 400 Bad Request."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}
    for i in range(1, 6):
        c = {
            "contact_name": f"Contact {i}",
            "phone_number": f"+91987654324{i}",
            "relationship": "Friend",
            "priority": i
        }
        resp = client.post("/api/v1/contacts", json=c, headers=headers)
        assert resp.status_code == 201

    # 6th contact should fail
    c6 = {
        "contact_name": "Contact 6",
        "phone_number": "+919876543246",
        "relationship": "Friend",
        "priority": 6
    }
    resp6 = client.post("/api/v1/contacts", json=c6, headers=headers)
    assert resp6.status_code == 400
    assert "Maximum limit of 5" in resp6.get_json()["message"]

def test_contact_validation(client, auth_tokens):
    """Validate invalid contact inputs."""
    headers = {"Authorization": f"Bearer {auth_tokens}"}

    # Invalid phone
    resp = client.post("/api/v1/contacts", json={"contact_name": "Name", "phone_number": "123", "relationship": "Friend"}, headers=headers)
    assert resp.status_code == 400

    # Invalid priority (0 or negative)
    resp = client.post("/api/v1/contacts", json={"contact_name": "Name", "phone_number": "+919876543250", "relationship": "Friend", "priority": 0}, headers=headers)
    assert resp.status_code == 400

    # Short relationship
    resp = client.post("/api/v1/contacts", json={"contact_name": "Name", "phone_number": "+919876543250", "relationship": "F"}, headers=headers)
    assert resp.status_code == 400

    # Mass assignment attempt
    resp = client.post("/api/v1/contacts", json={"contact_name": "Name", "phone_number": "+919876543250", "relationship": "Friend", "user_id": 999}, headers=headers)
    assert resp.status_code == 400

def test_contacts_user_isolation(client, auth_tokens, auth_tokens_user2):
    """Verify that User 1 cannot access, modify, or delete User 2's contact."""
    h1 = {"Authorization": f"Bearer {auth_tokens}"}
    h2 = {"Authorization": f"Bearer {auth_tokens_user2}"}

    # User 1 creates Contact 1
    c1 = {"contact_name": "User 1 Contact", "phone_number": "+919876543261", "relationship": "Parent"}
    id1 = client.post("/api/v1/contacts", json=c1, headers=h1).get_json()["data"]["id"]

    # User 2 creates Contact 2
    c2 = {"contact_name": "User 2 Contact", "phone_number": "+919876543262", "relationship": "Parent"}
    id2 = client.post("/api/v1/contacts", json=c2, headers=h2).get_json()["data"]["id"]

    # User 2 attempts to GET User 1's contact (should 404, not 403, preventing ID discovery)
    assert client.get(f"/api/v1/contacts/{id1}", headers=h2).status_code == 404

    # User 2 attempts to PUT User 1's contact
    assert client.put(f"/api/v1/contacts/{id1}", json={"contact_name": "Hacked"}, headers=h2).status_code == 404

    # User 2 attempts to DELETE User 1's contact
    assert client.delete(f"/api/v1/contacts/{id1}", headers=h2).status_code == 404

    # User 2 attempts to set User 1's contact as primary
    assert client.patch(f"/api/v1/contacts/{id1}/primary", headers=h2).status_code == 404

    # Verify User 1's contact remains unmodified
    data1 = client.get(f"/api/v1/contacts/{id1}", headers=h1).get_json()["data"]
    assert data1["contact_name"] == "User 1 Contact"
