"""
JOURNEX – Phase 8 Live Integration Verification Script
Tests SOS trigger, multi-level escalation, delivery tracking, and cancellation
against the live Flask API server on port 5000.
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
    print("JOURNEX PHASE 8: LIVE EMERGENCY & ESCALATION VERIFICATION")
    print("=" * 70)

    # Step 1: Register User
    user_email = f"live.sos.{int(datetime.now().timestamp())}@journex.internal"
    print(f"\n[Step 1] Registering test traveler: {user_email}")
    status, reg_res = http_req(f"{BASE_URL}/auth/register", method="POST", payload={
        "full_name": "Emergency Live Traveler",
        "email": user_email,
        "phone_number": "+919876599901",
        "password": "StrongPassword123!"
    })
    assert status == 201, f"Reg failed: {reg_res}"
    token = reg_res["data"]["tokens"]["access_token"]
    print("  -> Traveler registered successfully, JWT token acquired.")

    # Step 2: Add 3 Trusted Contacts (Priorities 1, 2, 3)
    print("\n[Step 2] Adding 3 tiered trusted contacts...")
    contacts_data = [
        {"contact_name": "Mom (Primary)", "phone_number": "+919876599902", "relationship": "Mother", "priority": 1, "is_primary": True},
        {"contact_name": "Dad (Secondary)", "phone_number": "+919876599903", "relationship": "Father", "priority": 2, "is_primary": False},
        {"contact_name": "Sister (Tertiary)", "phone_number": "+919876599904", "relationship": "Sister", "priority": 3, "is_primary": False}
    ]
    for c in contacts_data:
        st, res = http_req(f"{BASE_URL}/contacts", method="POST", token=token, payload=c)
        assert st == 201, f"Contact add failed: {res}"
    print("  -> 3 contacts added across Escalation Levels 1, 2, and 3.")

    # Step 3: Create & Start Journey
    print("\n[Step 3] Creating and starting active journey...")
    now = datetime.now(timezone.utc)
    st, journey_res = http_req(f"{BASE_URL}/journeys", method="POST", token=token, payload={
        "journey_title": "Gandhipuram to Peelamedu Live SOS Journey",
        "start_location_name": "Gandhipuram",
        "start_location_address": "Gandhipuram, Coimbatore",
        "start_latitude": 11.0168,
        "start_longitude": 76.9558,
        "destination_name": "Peelamedu",
        "destination_address": "Peelamedu, Coimbatore",
        "destination_latitude": 11.0280,
        "destination_longitude": 77.0120,
        "planned_start_time": (now - timedelta(minutes=5)).isoformat(),
        "expected_arrival_time": (now + timedelta(minutes=25)).isoformat()
    })
    assert st == 201, f"Journey create failed: {journey_res}"
    journey_id = journey_res["data"]["id"]

    st, start_res = http_req(f"{BASE_URL}/journeys/{journey_id}/start", method="POST", token=token)
    assert st == 200, f"Start failed: {start_res}"
    print(f"  -> Journey {journey_id} active.")

    # Step 4: Trigger Journey Emergency SOS (Level 1)
    print("\n[Step 4] Triggering journey emergency SOS...")
    st, sos_res = http_req(f"{BASE_URL}/journeys/{journey_id}/emergency-events", method="POST", token=token, payload={
        "trigger_type": "MANUAL_SOS",
        "latitude": 11.0190,
        "longitude": 76.9660,
        "accuracy": 6.5,
        "location_address": "Avinashi Road near CIT",
        "client_action_id": f"live-sos-{int(now.timestamp())}"
    })
    assert st == 201, f"SOS trigger failed: {sos_res}"
    event = sos_res["data"]
    event_id = event["id"]
    print(f"  -> Emergency Event ID {event_id} created in state '{event['status']}'.")
    assert event["status"] == "ACTIVE"
    assert event["current_escalation_level"] == 1
    assert len(event["dispatches"]) == 1
    d1 = event["dispatches"][0]
    print(f"  -> Level 1 Dispatched to {d1['contact_name']} ({d1['contact_phone']}) - Status: {d1['status']}")
    assert d1["status"] == "DELIVERED"

    # Step 5: Escalate to Level 2
    print("\n[Step 5] Escalating emergency alert to Level 2 (Secondary Contact)...")
    st, esc2_res = http_req(f"{BASE_URL}/emergency-events/{event_id}/escalate", method="POST", token=token, payload={})
    assert st == 200, f"Escalate Level 2 failed: {esc2_res}"
    event2 = esc2_res["data"]
    assert event2["current_escalation_level"] == 2
    assert len(event2["dispatches"]) == 2
    d2 = event2["dispatches"][1]
    print(f"  -> Level 2 Dispatched to {d2['contact_name']} ({d2['contact_phone']}) - Status: {d2['status']}")
    assert d2["status"] == "DELIVERED"

    # Step 6: Escalate to Level 3
    print("\n[Step 6] Escalating emergency alert to Level 3 (All Remaining Contacts)...")
    st, esc3_res = http_req(f"{BASE_URL}/emergency-events/{event_id}/escalate", method="POST", token=token, payload={})
    assert st == 200, f"Escalate Level 3 failed: {esc3_res}"
    event3 = esc3_res["data"]
    assert event3["current_escalation_level"] == 3
    assert len(event3["dispatches"]) == 3
    d3 = event3["dispatches"][2]
    print(f"  -> Level 3 Dispatched to {d3['contact_name']} ({d3['contact_phone']}) - Status: {d3['status']}")
    assert d3["status"] == "DELIVERED"

    # Step 7: Verify Delivery Status
    print("\n[Step 7] Checking delivery status summary...")
    st, status_res = http_req(f"{BASE_URL}/emergency-events/{event_id}/delivery-status", method="GET", token=token)
    assert st == 200, f"Delivery status failed: {status_res}"
    summary = status_res["data"]
    print(f"  -> Total dispatches tracked: {summary['total_dispatches']}")
    assert summary["total_dispatches"] == 3

    # Step 8: Cancel Emergency Alert
    print("\n[Step 8] Cancelling emergency alert (Traveler confirmed safe)...")
    st, cancel_res = http_req(f"{BASE_URL}/emergency-events/{event_id}/cancel", method="POST", token=token, payload={
        "cancellation_reason": "Live test complete, traveler is safe."
    })
    assert st == 200, f"Cancel failed: {cancel_res}"
    cancelled_event = cancel_res["data"]
    print(f"  -> Event Status: {cancelled_event['status']}")
    print(f"  -> Cancellation Reason: {cancelled_event['cancellation_reason']}")
    assert cancelled_event["status"] == "CANCELLED"
    assert cancelled_event["cancellation_timestamp"] is not None

    print("\n" + "=" * 70)
    print("ALL 8 LIVE EMERGENCY INTEGRATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_verification()
