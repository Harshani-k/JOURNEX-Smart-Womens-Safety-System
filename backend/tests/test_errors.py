def test_404_not_found(client):
    """
    Test that invalid routes return a consistent standardized JSON 404 envelope.
    """
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404

    json_data = response.get_json()
    assert json_data["success"] is False
    assert "Resource Not Found" in json_data["message"]
    assert json_data["errors"]["code"] == 404
    assert "timestamp" in json_data

def test_405_method_not_allowed(client):
    """
    Test that unsupported HTTP methods return standardized JSON 405 envelope.
    """
    response = client.post("/api/v1/health")
    assert response.status_code == 405

    json_data = response.get_json()
    assert json_data["success"] is False
    assert "Method Not Allowed" in json_data["message"]
    assert json_data["errors"]["code"] == 405
