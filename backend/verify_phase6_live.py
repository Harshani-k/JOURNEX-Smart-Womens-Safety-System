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

def run_live_phase6_verification():
    print("=== STARTING LIVE BACKEND PHASE 6 VERIFICATION ===")

    # 1. Register & Login User
    email = f"phase6_traveler_{int(datetime.now().timestamp())}@journex.org"
    status, reg_resp = http_req(f"{BASE_URL}/auth/register", method="POST", payload={
        "full_name": "Phase 6 Verified Traveler",
        "email": email,
        "password": "SecurePassword123!",
        "phone_number": "+91 98840 55443"
    })
    assert status == 201, f"Register failed: {reg_resp}"
    token = reg_resp["data"]["tokens"]["access_token"]
    print(f"[OK] Step 1: User registered & logged in: {email}")

    # 2. Create and Start Journey (Corridor from 11.0000, 77.0000 to 11.0100, 77.0000)
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(minutes=5)
    eta = now + timedelta(minutes=30)
    status, journey_resp = http_req(f"{BASE_URL}/journeys", method="POST", payload={
        "journey_title": "Phase 6 Safety Corridor Test",
        "start_location_name": "Central Library",
        "start_location_address": "Main Campus",
        "start_latitude": 11.0000,
        "start_longitude": 77.0000,
        "destination_name": "East Tech Park",
        "destination_address": "Tech Park Ave",
        "destination_latitude": 11.0100,
        "destination_longitude": 77.0000,
        "planned_start_time": start_time.isoformat(),
        "expected_arrival_time": eta.isoformat()
    }, token=token)
    assert status == 201, f"Create journey failed: {journey_resp}"
    journey_id = journey_resp["data"]["id"]

    status, start_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/start", method="POST", token=token)
    assert status == 200, f"Start journey failed: {start_resp}"
    print(f"[OK] Step 2: Journey created and started. ID={journey_id}, Status=ACTIVE")

    # 3. Upload 3 consecutive deviated location fixes (lon = 77.0050 -> ~546m off corridor)
    deviated_fixes = [
        {"latitude": 11.0040, "longitude": 77.0050, "accuracy": 12.0, "speed": 6.0, "recorded_at": (now - timedelta(seconds=30)).isoformat()},
        {"latitude": 11.0050, "longitude": 77.0050, "accuracy": 10.0, "speed": 6.0, "recorded_at": (now - timedelta(seconds=15)).isoformat()},
        {"latitude": 11.0060, "longitude": 77.0050, "accuracy": 11.0, "speed": 6.0, "recorded_at": now.isoformat()}
    ]
    status, loc_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/locations", method="POST", payload={"locations": deviated_fixes}, token=token)
    assert status == 201, f"Location upload failed: {loc_resp}"
    print(f"[OK] Step 3: Uploaded 3 consecutive deviated fixes (>500m off corridor).")

    # 4. Verify Route Deviation Safety Event Triggered
    status, active_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/safety-events/active", token=token)
    assert status == 200
    active_events = active_resp["data"]["active_events"]
    assert len(active_events) >= 1, f"Expected active safety events, got {active_events}"
    dev_event = next((e for e in active_events if e["event_type"] == "ROUTE_DEVIATION"), None)
    assert dev_event is not None, "Expected ROUTE_DEVIATION event"
    event_id = dev_event["id"]
    print(f"[OK] Step 4: Route deviation successfully triggered: ID={event_id}, status={dev_event['status']}, distance={dev_event['deviation_distance']}m, reason='{dev_event['trigger_reason']}'")

    # 5. Acknowledge the Route Deviation
    status, ack_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/safety-events/{event_id}/acknowledge", method="POST", token=token)
    assert status == 200
    assert ack_resp["data"]["status"] == "ACKNOWLEDGED"
    print(f"[OK] Step 5: Event {event_id} acknowledged: status={ack_resp['data']['status']}")

    # 6. Resolve the Route Deviation with Reason Notes
    action_id = f"act-resolve-{int(datetime.now().timestamp())}"
    status, res_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/safety-events/{event_id}/resolve", method="POST", payload={
        "resolution_notes": "Verified intentional detour to avoid highway construction",
        "client_action_id": action_id
    }, token=token)
    assert status == 200
    assert res_resp["data"]["status"] == "RESOLVED"
    print(f"[OK] Step 6: Event {event_id} resolved: status={res_resp['data']['status']}, notes='{res_resp['data']['resolution_notes']}'")

    # 7. Upload Stationary Fixes to test UNEXPECTED_STOP
    # The vehicle stops AFTER the deviation and remains stationary for > 10 minutes
    stop_start = now + timedelta(minutes=1)
    stop_mid = now + timedelta(minutes=7)
    stop_end = now + timedelta(minutes=14)
    stop_fixes = [
        {"latitude": 11.00500, "longitude": 77.00000, "accuracy": 8.0, "speed": 0.0, "recorded_at": stop_start.isoformat()},
        {"latitude": 11.00501, "longitude": 77.00001, "accuracy": 8.0, "speed": 0.1, "recorded_at": stop_mid.isoformat()},
        {"latitude": 11.00500, "longitude": 77.00000, "accuracy": 8.0, "speed": 0.0, "recorded_at": stop_end.isoformat()}
    ]
    status, loc2_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/locations", method="POST", payload={"locations": stop_fixes}, token=token)
    assert status == 201
    assert loc2_resp["data"]["accepted_count"] >= 3, f"Expected 3 accepted fixes, got {loc2_resp}"

    # 8. Verify Unexpected Stop Event
    status, all_events_resp = http_req(f"{BASE_URL}/journeys/{journey_id}/safety-events", token=token)
    assert status == 200
    all_events = all_events_resp["data"]["safety_events"]
    stop_event = next((e for e in all_events if e["event_type"] == "UNEXPECTED_STOP"), None)
    assert stop_event is not None, "Expected UNEXPECTED_STOP event"
    print(f"[OK] Step 7 & 8: Unexpected stop event triggered: ID={stop_event['id']}, duration={stop_event['duration_seconds']}s, reason='{stop_event['trigger_reason']}'")

    # 9. Verify Journey Remains ACTIVE (safety rules mandate never canceling or completing journey)
    status, journey_final = http_req(f"{BASE_URL}/journeys/{journey_id}", token=token)
    assert status == 200
    assert journey_final["data"]["status"] == "ACTIVE"
    print(f"[OK] Step 9: Safety rule verified: Journey remains ACTIVE after all safety events. Status={journey_final['data']['status']}")

    print("\nALL PHASE 6 LIVE VERIFICATION STEPS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_live_phase6_verification()
