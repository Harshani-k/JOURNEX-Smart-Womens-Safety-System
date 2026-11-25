def test_health_check_endpoint(client):
    """
    Test GET /api/v1/health returns 200 OK and expected standard JSON structure.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["message"] == "JOURNEX Backend is operational."
    assert "timestamp" in json_data

    # Check diagnostic data payload
    data = json_data["data"]
    assert data["service"] == "JOURNEX Backend REST API"
    assert data["status"] == "operational"
    assert data["version"] == "1.0.0"
    assert data["api_version"] == "v1"
    assert data["database"]["status"] == "healthy"
    assert "sqlite" in data["database"]["engine"].lower()
