"""
JOURNEX – Phase 7 Live Integration Verification Script
Tests explainable ML risk analysis endpoints against running Flask daemon on port 5000.
"""

import urllib.request
import urllib.error
import json
import sys
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:5000/api/v1"

def http_req(url, method="GET", payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}

def run_live_verification():
    print("=" * 70)
    print("JOURNEX PHASE 7: LIVE ML RISK ANALYSIS INTEGRATION VERIFICATION")
    print("=" * 70)

    # Step 1: Register User
    user_email = f"live.ml.{int(datetime.now().timestamp())}@journex.internal"
    print(f"\n[Step 1] Registering test user: {user_email}")
    status, reg_res = http_req(f"{BASE_URL}/auth/register", method="POST", payload={
        "full_name": "ML Live Test Traveler",
        "email": user_email,
        "phone_number": "+919988776655",
        "password": "StrongPassword123!"
    })
    assert status == 201, f"Reg failed: {reg_res}"
    token = reg_res["data"]["tokens"]["access_token"]
    print("  -> User registered successfully, JWT acquired.")

    # Step 2: Create and Start Active Journey
    print("\n[Step 2] Creating and starting active journey...")
    now = datetime.now(timezone.utc)
    status, journey_res = http_req(f"{BASE_URL}/journeys", method="POST", token=token, payload={
        "journey_title": "Gandhipuram to Peelamedu Live ML Test",
        "start_location_name": "Gandhipuram Bus Stand",
        "start_location_address": "Gandhipuram, Coimbatore",
        "start_latitude": 11.0168,
        "start_longitude": 76.9558,
        "destination_name": "Peelamedu Tech Park",
        "destination_address": "Peelamedu, Coimbatore",
        "destination_latitude": 11.0280,
        "destination_longitude": 77.0120,
        "planned_start_time": (now - timedelta(minutes=15)).isoformat(),
        "expected_arrival_time": (now + timedelta(minutes=45)).isoformat()
    })
    assert status == 201, f"Journey create failed: {journey_res}"
    journey_id = journey_res["data"]["id"]

    status, start_res = http_req(f"{BASE_URL}/journeys/{journey_id}/start", method="POST", token=token)
    assert status == 200, f"Start failed: {start_res}"
    print(f"  -> Journey {journey_id} started (ACTIVE).")

    # Step 3: Initial Insufficient Data Risk Evaluation
    print("\n[Step 3] Evaluating baseline risk on newly created journey (insufficient data)...")
    status, risk_res = http_req(f"{BASE_URL}/journeys/{journey_id}/risk-analysis", method="POST", token=token, payload={"force_recompute": True})
    assert status == 200, f"Risk eval failed: {risk_res}"
    risk_data = risk_res["data"]
    print(f"  -> Risk Category: {risk_data['risk_category']}, Score: {risk_data['risk_score']}")
    print(f"  -> Factors: {risk_data['contributing_factors']}")
    assert risk_data["risk_category"] == "LOW"

    # Step 4: Add In-Corridor Location and Schedule Confirmed Check-In
    print("\n[Step 4] Adding in-corridor GPS fixes and confirmed safe check-in...")
    status, loc_res = http_req(f"{BASE_URL}/journeys/{journey_id}/locations", method="POST", token=token, payload={
        "locations": [
            {
                "latitude": 11.0185,
                "longitude": 76.9650,
                "accuracy": 8.0,
                "speed": 6.5,
                "recorded_at": (now - timedelta(minutes=10)).isoformat()
            },
            {
                "latitude": 11.0205,
                "longitude": 76.9750,
                "accuracy": 7.5,
                "speed": 7.0,
                "recorded_at": (now - timedelta(minutes=5)).isoformat()
            }
        ]
    })
    assert status == 201

    # Ingest check-in
    status, checkin_res = http_req(f"{BASE_URL}/journeys/{journey_id}/checkins", method="POST", token=token, payload={
        "scheduled_at": (now - timedelta(minutes=2)).isoformat(),
        "deadline_at": (now + timedelta(minutes=10)).isoformat()
    })
    assert status == 201, f"Checkin create failed: {checkin_res}"
    checkin_id = checkin_res["data"]["id"]

    status, confirm_res = http_req(f"{BASE_URL}/checkins/{checkin_id}/confirm", method="POST", token=token, payload={
        "response_type": "MANUAL_TAP",
        "responded_at": now.isoformat()
    })
    assert status == 200, f"Checkin confirm failed: {status} {confirm_res}"
    print("  -> GPS fixes added and check-in confirmed safe.")

    # Re-evaluate risk
    status, risk_res2 = http_req(f"{BASE_URL}/journeys/{journey_id}/risk-analysis", method="POST", token=token, payload={"force_recompute": True})
    assert status == 200
    risk_data2 = risk_res2["data"]
    print(f"  -> Normal Travel Risk Category: {risk_data2['risk_category']}, Score: {risk_data2['risk_score']}")
    assert risk_data2["risk_category"] in ("LOW", "MODERATE")

    # Step 5: Simulate Compounding Risk (Route Deviation Fixes)
    print("\n[Step 5] Simulating route deviation (3 fixes 550m off route corridor)...")
    dev_fixes = [
        {
            "latitude": 11.0120,
            "longitude": 76.9700,
            "accuracy": 12.0,
            "speed": 8.0,
            "recorded_at": (now - timedelta(minutes=4)).isoformat()
        },
        {
            "latitude": 11.0118,
            "longitude": 76.9705,
            "accuracy": 11.0,
            "speed": 8.0,
            "recorded_at": (now - timedelta(minutes=3)).isoformat()
        },
        {
            "latitude": 11.0115,
            "longitude": 76.9710,
            "accuracy": 10.0,
            "speed": 7.5,
            "recorded_at": (now - timedelta(minutes=2)).isoformat()
        }
    ]
    status, dev_res = http_req(f"{BASE_URL}/journeys/{journey_id}/locations", method="POST", token=token, payload={"locations": dev_fixes})
    assert status == 201
    print("  -> Deviated fixes ingested.")

    status, risk_res3 = http_req(f"{BASE_URL}/journeys/{journey_id}/risk-analysis", method="POST", token=token, payload={"force_recompute": True})
    assert status == 200
    risk_data3 = risk_res3["data"]
    print(f"  -> Elevated Risk Category: {risk_data3['risk_category']}, Score: {risk_data3['risk_score']}")
    print(f"  -> Contributing Factors: {risk_data3['contributing_factors']}")
    assert risk_data3["risk_score"] > risk_data2["risk_score"]
    assert risk_data3["risk_category"] in ("HIGH", "CRITICAL")

    # Step 6: Verify GET /risk-analysis/latest
    print("\n[Step 6] Verifying GET /risk-analysis/latest endpoint...")
    status, latest_res = http_req(f"{BASE_URL}/journeys/{journey_id}/risk-analysis/latest", method="GET", token=token)
    assert status == 200
    latest_data = latest_res["data"]
    assert latest_data["id"] == risk_data3["id"]
    assert latest_data["risk_category"] == risk_data3["risk_category"]
    print(f"  -> Latest analysis id {latest_data['id']} matches with category {latest_data['risk_category']}.")

    # Step 7: Verify GET /risk-analysis/history
    print("\n[Step 7] Verifying GET /risk-analysis/history endpoint...")
    status, hist_res = http_req(f"{BASE_URL}/journeys/{journey_id}/risk-analysis/history", method="GET", token=token)
    assert status == 200
    hist_data = hist_res["data"]
    print(f"  -> Retrieved {hist_data['count']} historical risk records.")
    assert hist_data["count"] >= 3

    print("\n" + "=" * 70)
    print("ALL 7 LIVE INTEGRATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_verification()
