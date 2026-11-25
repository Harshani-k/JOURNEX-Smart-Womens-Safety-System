"""
JOURNEX – Phase 7 Test Suite: Explainable ML Risk Analysis
Tests dataset generation, Random Forest model inference, feature extraction,
explainability factors, service layer idempotency, database persistence,
and REST API endpoints with authentication and ownership verification.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import User
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.models.checkin import CheckIn
from app.models.safety_event import SafetyEvent
from app.models.risk_analysis import RiskAnalysis
from app.ml.dataset_generator import generate_synthetic_data, FEATURE_NAMES, RISK_LABELS
from app.ml.predictor import risk_predictor
from app.services.risk_service import evaluate_journey_risk, get_latest_risk_analysis, get_risk_analysis_history

@pytest.fixture
def auth_user(client):
    """Fixture to register and login a test user, returning auth token and user."""
    payload = {
        "full_name": "Risk Test Traveler",
        "email": "traveler.risk@journex.internal",
        "phone_number": "+919876543210",
        "password": "StrongPassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    token = res.get_json()["data"]["tokens"]["access_token"]
    user = User.query.filter_by(email=payload["email"]).first()
    return token, user

@pytest.fixture
def other_user(client):
    """Fixture for a second user to test cross-user access controls."""
    payload = {
        "full_name": "Other Traveler",
        "email": "other.traveler@journex.internal",
        "phone_number": "+919876543211",
        "password": "StrongPassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    token = res.get_json()["data"]["tokens"]["access_token"]
    user = User.query.filter_by(email=payload["email"]).first()
    return token, user

@pytest.fixture
def active_journey(auth_user):
    """Create an active journey in Coimbatore."""
    token, user = auth_user
    now = datetime.now(timezone.utc)
    journey = Journey(
        user_id=user.id,
        journey_title="Evening Commute to Peelamedu",
        start_location_name="Gandhipuram Bus Stand",
        start_location_address="Gandhipuram, Coimbatore",
        start_latitude=11.0168,
        start_longitude=76.9558,
        destination_name="Peelamedu Tech Park",
        destination_address="Peelamedu, Coimbatore",
        destination_latitude=11.0280,
        destination_longitude=77.0120,
        planned_start_time=now - timedelta(minutes=20),
        expected_arrival_time=now + timedelta(minutes=40),
        actual_start_time=now - timedelta(minutes=20),
        status="ACTIVE"
    )
    db.session.add(journey)
    db.session.commit()
    return journey

# --- 1. Dataset & PII Prevention Tests ---

def test_dataset_reproducibility_and_non_pii():
    """Verify synthetic dataset generates deterministically and contains no PII."""
    X1, y1 = generate_synthetic_data(n_samples=500, random_seed=42)
    X2, y2 = generate_synthetic_data(n_samples=500, random_seed=42)
    assert X1.shape == (500, len(FEATURE_NAMES))
    assert (X1 == X2).all()
    assert (y1 == y2).all()

    # Ensure no PII in feature names
    forbidden_terms = ["name", "email", "phone", "contact", "identity", "user_id"]
    for feat in FEATURE_NAMES:
        for term in forbidden_terms:
            assert term not in feat.lower(), f"Forbidden PII term '{term}' found in feature '{feat}'"

# --- 2. Insufficient Data Handling ---

def test_insufficient_data_baseline(active_journey):
    """A newly started journey with no fixes or check-ins returns a safe baseline."""
    result = risk_predictor.predict(active_journey)
    assert result["is_insufficient_data"] is True
    assert result["risk_category"] == "LOW"
    assert result["risk_score"] < 0.30
    assert len(result["contributing_factors"]) >= 1
    assert "Insufficient" in result["contributing_factors"][0]["factor"]

# --- 3. Telemetry Feature Extraction & Normal Journey ---

def test_normal_journey_low_risk(active_journey):
    """Journey with valid in-corridor GPS and confirmed check-in evaluates to LOW risk."""
    now = datetime.now(timezone.utc)
    # Add in-corridor GPS locations
    loc1 = JourneyLocation(
        journey_id=active_journey.id,
        latitude=11.0180,
        longitude=76.9650,
        accuracy=8.5,
        recorded_at=now - timedelta(minutes=10)
    )
    loc2 = JourneyLocation(
        journey_id=active_journey.id,
        latitude=11.0200,
        longitude=76.9750,
        accuracy=9.0,
        recorded_at=now - timedelta(minutes=5)
    )
    # Confirmed safe check-in
    checkin = CheckIn(
        journey_id=active_journey.id,
        user_id=active_journey.user_id,
        scheduled_at=now - timedelta(minutes=15),
        deadline_at=now - timedelta(minutes=10),
        responded_at=now - timedelta(minutes=12),
        status="CONFIRMED_SAFE"
    )
    db.session.add_all([loc1, loc2, checkin])
    db.session.commit()

    result = risk_predictor.predict(active_journey)
    assert result["is_insufficient_data"] is False
    assert result["risk_category"] in ("LOW", "MODERATE")
    assert result["risk_score"] < 0.50
    assert any("Normal" in f["factor"] or f["impact"] == "POSITIVE" for f in result["contributing_factors"])

# --- 4. Critical Compounding Risk Scenario ---

def test_critical_compounding_risk(active_journey):
    """Journey with missed check-in, route deviation, and unexpected stop evaluates to HIGH or CRITICAL."""
    now = datetime.now(timezone.utc)
    # Flag journey as delayed
    active_journey.is_delayed = True
    active_journey.expected_arrival_time = now - timedelta(minutes=35)

    # Missed check-in
    missed_checkin = CheckIn(
        journey_id=active_journey.id,
        user_id=active_journey.user_id,
        scheduled_at=now - timedelta(minutes=30),
        deadline_at=now - timedelta(minutes=25),
        status="MISSED"
    )
    # Route deviation event
    dev_event = SafetyEvent(
        journey_id=active_journey.id,
        user_id=active_journey.user_id,
        event_type="ROUTE_DEVIATION",
        status="ACTIVE",
        trigger_reason="Deviated 650m from planned corridor",
        severity="HIGH",
        deviation_distance=650.0,
        consecutive_count=4,
        detected_at=now - timedelta(minutes=15)
    )
    # Unexpected stop event
    stop_event = SafetyEvent(
        journey_id=active_journey.id,
        user_id=active_journey.user_id,
        event_type="UNEXPECTED_STOP",
        status="ACTIVE",
        trigger_reason="Stationary for 15 minutes",
        severity="HIGH",
        duration_seconds=900,
        detected_at=now - timedelta(minutes=5)
    )
    # Degraded GPS fixes
    loc = JourneyLocation(
        journey_id=active_journey.id,
        latitude=10.9800,
        longitude=76.9200,
        accuracy=45.0,
        recorded_at=now - timedelta(minutes=2)
    )
    db.session.add_all([missed_checkin, dev_event, stop_event, loc])
    db.session.commit()

    result = risk_predictor.predict(active_journey)
    assert result["risk_category"] in ("HIGH", "CRITICAL")
    assert result["risk_score"] >= 0.55

    factor_names = [f["factor"] for f in result["contributing_factors"]]
    assert any("Missed" in name for name in factor_names)
    assert any("Route Deviation" in name for name in factor_names)
    assert any("Stop" in name for name in factor_names)

# --- 5. Service Layer Idempotency & Persistence ---

def test_service_evaluate_and_idempotency(active_journey):
    """Verify risk evaluation persists to database and does not re-compute redundantly."""
    now = datetime.now(timezone.utc)
    loc = JourneyLocation(
        journey_id=active_journey.id,
        latitude=11.0200,
        longitude=76.9750,
        accuracy=10.0,
        recorded_at=now
    )
    db.session.add(loc)
    db.session.commit()

    analysis1 = evaluate_journey_risk(active_journey.id, active_journey.user_id)
    assert analysis1.id is not None
    assert analysis1.journey_id == active_journey.id
    assert analysis1.risk_category in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    # Immediate second call without telemetry changes returns cached analysis1
    analysis2 = evaluate_journey_risk(active_journey.id, active_journey.user_id, force_recompute=False)
    assert analysis2.id == analysis1.id

    # Forcing recompute creates a new evaluation
    analysis3 = evaluate_journey_risk(active_journey.id, active_journey.user_id, force_recompute=True)
    assert analysis3.id != analysis1.id

# --- 6. REST API Endpoints & Access Control ---

def test_api_risk_analysis_endpoints(client, auth_user, active_journey):
    """Test POST /risk-analysis, GET /latest, and GET /history."""
    token, user = auth_user
    headers = {"Authorization": f"Bearer {token}"}

    # 1. POST /risk-analysis
    res = client.post(f"/api/v1/journeys/{active_journey.id}/risk-analysis", headers=headers, json={"force_recompute": True})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "risk_score" in data
    assert "risk_category" in data
    assert "contributing_factors" in data
    assert "model_version" in data

    # 2. GET /risk-analysis/latest
    res_latest = client.get(f"/api/v1/journeys/{active_journey.id}/risk-analysis/latest", headers=headers)
    assert res_latest.status_code == 200
    latest_data = res_latest.get_json()["data"]
    assert latest_data["id"] == data["id"]
    assert latest_data["risk_category"] == data["risk_category"]

    # 3. GET /risk-analysis/history
    res_hist = client.get(f"/api/v1/journeys/{active_journey.id}/risk-analysis/history", headers=headers)
    assert res_hist.status_code == 200
    hist_data = res_hist.get_json()["data"]
    assert hist_data["count"] >= 1
    assert len(hist_data["history"]) >= 1

def test_api_unauthorized_and_forbidden(client, other_user, active_journey):
    """Test unauthenticated request (401) and cross-user request (403)."""
    # 401 without token
    res_no_auth = client.post(f"/api/v1/journeys/{active_journey.id}/risk-analysis")
    assert res_no_auth.status_code == 401

    # 403 when User B tries to analyze User A's journey
    other_token, _ = other_user
    headers = {"Authorization": f"Bearer {other_token}"}
    res_forbidden = client.post(f"/api/v1/journeys/{active_journey.id}/risk-analysis", headers=headers)
    assert res_forbidden.status_code == 403

def test_api_not_found_journey(client, auth_user):
    """Test non-existent journey returns 404."""
    token, _ = auth_user
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/v1/journeys/99999/risk-analysis", headers=headers)
    assert res.status_code == 404
