import urllib.request
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
    print("=== STARTING LIVE BACKEND CHECK-IN VERIFICATION ===")
    
    # 1. Register / Login test user
    email = f"traveler_p5_{int(datetime.now().timestamp())}@journex.org"
    password = "SecurePassword123!"
    
    status, reg_resp = http_req(f"{BASE_URL}/auth/register", method="POST", payload={
        "full_name": "Phase 5 Traveler",
        "email": email,
        "password": password,
        "phone_number": "+91 98840 12345"
    })
    assert status == 201, f"Register failed: {reg_resp}"
    token = reg_resp["data"]["tokens"]["access_token"]
    print(f"[OK] Step 1: User registered & logged in: {email}")
    
    # 2. Create Active Journey
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=5)
    eta = now + timedelta(minutes=25)
    status, journey_resp = http_req(f"{BASE_URL}/journeys", method="POST", payload={
        "journey_title": "University Central Campus Commute",
        "start_location_name": "Home Base",
        "start_location_address": "123 Safe St",
        "start_latitude": 11.0168,
        "start_longitude": 76.9558,
        "destination_name": "University Central Campus",
        "destination_address": "456 University Road",
        "destination_latitude": 11.03592,
        "destination_longitude": 77.01715,
        "planned_start_time": start.isoformat(),
        "expected_arrival_time": eta.isoformat()
    }, token=token)
    assert status == 201, f"Create journey failed: {journey_resp}"
    journey_id = journey_resp["data"]["id"]
    
    status, start_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/start", method="POST", token=token)
    assert status == 200, f"Start journey failed: {start_resp}"
    print(f"[OK] Step 2 & 3: Journey created and started. ID={journey_id}, Status=ACTIVE")
    
    # 4 & 5. Schedule check-in & verify timestamps
    status, chk_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/checkins", method="POST", payload={}, token=token)
    assert status == 201, f"Schedule checkin failed: {chk_resp}"
    chk_data = chk_resp["data"]
    checkin_id = chk_data["id"]
    sched_at = chk_data["scheduled_at"]
    dead_at = chk_data["deadline_at"]
    status_field = chk_data["status"]
    assert status_field == "SCHEDULED", f"Expected SCHEDULED, got {status_field}"
    print(f"[OK] Step 4 & 5: Check-in scheduled: ID={checkin_id}, status={status_field}, scheduled_at={sched_at}, deadline_at={dead_at}")
    
    # 6. Retrieve pending check-in
    status, pending_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/checkins/pending", token=token)
    assert status == 200
    assert pending_resp["data"]["id"] == checkin_id
    print(f"[OK] Step 6: Pending check-in retrieved successfully.")
    
    # 7 & 8. Confirm Safety ("I'm Safe")
    status, confirm_resp = http_req(f"{BASE_URL}/checkins/{checkin_id}/confirm", method="POST", payload={
        "response_type": "MANUAL_TAP",
        "client_action_id": f"action-p5-{int(datetime.now().timestamp())}"
    }, token=token)
    assert status == 200, f"Confirm failed: {confirm_resp}"
    confirmed_data = confirm_resp["data"]
    assert confirmed_data["status"] == "CONFIRMED_SAFE"
    assert confirmed_data["responded_at"] is not None
    print(f"[OK] Step 7 & 8: Safety confirmed and recorded: status={confirmed_data['status']}, responded_at={confirmed_data['responded_at']}")
    
    # 9. Test Missed Check-In (Schedule check-in with past deadline)
    past_sched = now - timedelta(minutes=10)
    past_dead = now - timedelta(minutes=5)
    status, missed_chk_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/checkins", method="POST", payload={
        "scheduled_at": past_sched.isoformat(),
        "deadline_at": past_dead.isoformat(),
        "client_action_id": f"missed-action-{int(datetime.now().timestamp())}"
    }, token=token)
    assert status == 201, f"Create missed checkin failed: {missed_chk_resp}"
    missed_chk_id = missed_chk_resp["data"]["id"]
    
    # Trigger detect-missed sweep
    status, detect_resp = http_req(f"{BASE_URL}/checkins/detect-missed", method="POST", token=token)
    assert status == 200
    detected_count = detect_resp["data"]["missed_count"]
    print(f"[OK] Step 9: detect-missed executed: detected {detected_count} missed check-in(s)")
    
    # Verify the checkin is now MISSED
    status, all_chks_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/checkins", token=token)
    all_chks = all_chks_resp["data"]["checkins"]
    missed_item = next(c for c in all_chks if c["id"] == missed_chk_id)
    assert missed_item["status"] == "MISSED", f"Expected MISSED, got {missed_item['status']}"
    print(f"[OK] Step 9 Verified: Check-in {missed_chk_id} transitioned to MISSED status past its deadline.")
    
    # 10. Verify Journey remains ACTIVE
    status, journey_verify = http_req(f"{BASE_URL}/journeys/{journey_id}", token=token)
    assert journey_verify["data"]["status"] == "ACTIVE", f"Expected ACTIVE, got {journey_verify['data']['status']}"
    print(f"[OK] Step 10: Journey remains ACTIVE after missed check-in (requires explicit user action to complete or cancel). Status={journey_verify['data']['status']}")
    
    print("\nALL 10 VERIFICATION STEPS PASSED PERFECTLY ON LIVE BACKEND!")

if __name__ == "__main__":
    run_live_verification()
