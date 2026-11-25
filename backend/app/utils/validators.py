import re
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

FORBIDDEN_PROFILE_KEYS = {"id", "user_id", "created_at", "updated_at"}
FORBIDDEN_CONTACT_KEYS = {"id", "user_id", "consent_status", "verified_at", "created_at", "updated_at"}
FORBIDDEN_JOURNEY_KEYS = {
    "id", "user_id", "status", "actual_start_time", "actual_arrival_time",
    "created_at", "updated_at", "cancellation_reason"
}

def validate_registration_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
    """
    Validates user registration input.
    Returns: (is_valid, error_message, cleaned_dict)
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    full_name = data.get("full_name")
    email = data.get("email")
    phone_number = data.get("phone_number")
    password = data.get("password")

    # Full Name Validation
    if not full_name or not isinstance(full_name, str) or len(full_name.strip()) < 2:
        return False, "Full name is required and must be at least 2 characters.", None
    if len(full_name.strip()) > 100:
        return False, "Full name cannot exceed 100 characters.", None

    # Email Validation
    if not email or not isinstance(email, str):
        return False, "Valid email address is required.", None
    email_clean = email.strip().lower()
    if not EMAIL_REGEX.match(email_clean) or len(email_clean) > 120:
        return False, "Please provide a valid email address.", None

    # Phone Number Validation
    if not phone_number or not isinstance(phone_number, str):
        return False, "Phone number is required.", None
    phone_clean = phone_number.strip().replace(" ", "").replace("-", "")
    if not PHONE_REGEX.match(phone_clean):
        return False, "Phone number must contain 10 to 15 digits (optional leading +).", None

    # Password Strength Validation
    if not password or not isinstance(password, str):
        return False, "Password is required.", None
    if len(password) < 8:
        return False, "Password must be at least 8 characters in length.", None
    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter.", None
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one numeric digit.", None

    cleaned_data = {
        "full_name": full_name.strip(),
        "email": email_clean,
        "phone_number": phone_clean,
        "password": password
    }
    return True, None, cleaned_data

def validate_login_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
    """
    Validates user login input.
    Returns: (is_valid, error_message, cleaned_dict)
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    email = data.get("email")
    password = data.get("password")

    if not email or not isinstance(email, str) or not email.strip():
        return False, "Email address is required.", None

    if not password or not isinstance(password, str):
        return False, "Password is required.", None

    return True, None, {
        "email": email.strip().lower(),
        "password": password
    }

def validate_safety_profile_payload(data: Any, is_update: bool = False) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates SafetyProfile creation and update payloads.
    Guards against mass assignment of user_id, id, and timestamp fields.
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    # Mass assignment check
    for key in FORBIDDEN_PROFILE_KEYS:
        if key in data:
            return False, f"Modifying internal ownership or metadata field '{key}' is prohibited.", None

    cleaned: Dict[str, Any] = {}

    # Display Name
    if "display_name" in data or not is_update:
        val = data.get("display_name")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Display name is required and must be between 2 and 100 characters.", None
        if len(val.strip()) > 100:
            return False, "Display name cannot exceed 100 characters.", None
        cleaned["display_name"] = val.strip()

    # Preferred Language
    if "preferred_language" in data:
        val = data.get("preferred_language")
        if not isinstance(val, str) or len(val.strip()) < 2 or len(val.strip()) > 10:
            return False, "Preferred language must be a standard 2 to 10 character code (e.g., 'en', 'hi', 'ta').", None
        cleaned["preferred_language"] = val.strip().lower()
    elif not is_update:
        cleaned["preferred_language"] = "en"

    # Emergency Message
    if "emergency_message" in data or not is_update:
        val = data.get("emergency_message")
        if not val or not isinstance(val, str) or len(val.strip()) < 5:
            return False, "Emergency message is required and must be at least 5 characters.", None
        if len(val.strip()) > 500:
            return False, "Emergency message cannot exceed 500 characters.", None
        cleaned["emergency_message"] = val.strip()

    # Additional Safety Notes
    if "additional_safety_notes" in data:
        val = data.get("additional_safety_notes")
        if val is not None:
            if not isinstance(val, str):
                return False, "Additional safety notes must be text.", None
            if len(val.strip()) > 1000:
                return False, "Additional safety notes cannot exceed 1000 characters.", None
            cleaned["additional_safety_notes"] = val.strip()
        else:
            cleaned["additional_safety_notes"] = None
    elif not is_update:
        cleaned["additional_safety_notes"] = None

    if is_update and not cleaned:
        return False, "At least one valid profile field must be provided for update.", None

    return True, None, cleaned

def validate_trusted_contact_payload(data: Any, is_update: bool = False) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates TrustedContact creation and update payloads.
    Enforces positive priorities, phone formatting, and protects from mass assignment.
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    for key in FORBIDDEN_CONTACT_KEYS:
        if key in data:
            return False, f"Modifying internal field '{key}' is prohibited.", None

    cleaned: Dict[str, Any] = {}

    # Contact Name
    if "contact_name" in data or not is_update:
        val = data.get("contact_name")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Contact name is required and must be between 2 and 100 characters.", None
        if len(val.strip()) > 100:
            return False, "Contact name cannot exceed 100 characters.", None
        cleaned["contact_name"] = val.strip()

    # Phone Number
    if "phone_number" in data or not is_update:
        val = data.get("phone_number")
        if not val or not isinstance(val, str):
            return False, "Phone number is required.", None
        phone_clean = val.strip().replace(" ", "").replace("-", "")
        if not PHONE_REGEX.match(phone_clean):
            return False, "Phone number must contain 10 to 15 digits (optional leading +).", None
        cleaned["phone_number"] = phone_clean

    # Relationship
    if "relationship" in data or not is_update:
        val = data.get("relationship")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Relationship is required and must be between 2 and 50 characters (e.g., Parent, Friend).", None
        if len(val.strip()) > 50:
            return False, "Relationship cannot exceed 50 characters.", None
        cleaned["relationship"] = val.strip()

    # Priority
    if "priority" in data:
        val = data.get("priority")
        if not isinstance(val, int) or isinstance(val, bool) or val < 1:
            return False, "Priority must be a positive integer starting from 1.", None
        cleaned["priority"] = val
    elif not is_update:
        cleaned["priority"] = 1

    # Is Primary
    if "is_primary" in data:
        val = data.get("is_primary")
        if not isinstance(val, bool):
            return False, "is_primary must be a boolean (true or false).", None
        cleaned["is_primary"] = val
    elif not is_update:
        cleaned["is_primary"] = False

    if is_update and not cleaned:
        return False, "At least one valid field must be provided for update.", None

    return True, None, cleaned

def _parse_datetime(dt_str: Any, field_name: str) -> Tuple[bool, Optional[str], Optional[datetime]]:
    if not dt_str or not isinstance(dt_str, str):
        return False, f"{field_name} must be a valid ISO 8601 datetime string.", None
    try:
        clean_str = dt_str.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return True, None, dt
    except (ValueError, TypeError):
        return False, f"Invalid datetime format for {field_name}. Use ISO 8601 format (e.g., 2026-11-22T14:30:00Z).", None

def validate_journey_payload(data: Any, is_update: bool = False) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates Journey creation and update payloads.
    Guards against mass assignment and verifies valid geographic and schedule boundaries.
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    for key in FORBIDDEN_JOURNEY_KEYS:
        if key in data:
            return False, f"Modifying system-controlled or ownership field '{key}' is prohibited.", None

    cleaned: Dict[str, Any] = {}

    # Title
    if "journey_title" in data or not is_update:
        val = data.get("journey_title")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Journey title is required and must be between 2 and 150 characters.", None
        if len(val.strip()) > 150:
            return False, "Journey title cannot exceed 150 characters.", None
        cleaned["journey_title"] = val.strip()

    # Start Location
    if "start_location_name" in data or not is_update:
        val = data.get("start_location_name")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Start location name is required and must be between 2 and 150 characters.", None
        if len(val.strip()) > 150:
            return False, "Start location name cannot exceed 150 characters.", None
        cleaned["start_location_name"] = val.strip()

    if "start_location_address" in data or not is_update:
        val = data.get("start_location_address")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Start location address is required and must be between 2 and 255 characters.", None
        if len(val.strip()) > 255:
            return False, "Start location address cannot exceed 255 characters.", None
        cleaned["start_location_address"] = val.strip()

    # Start coordinates (optional)
    if "start_latitude" in data:
        val = data.get("start_latitude")
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < -90.0 or val > 90.0:
                return False, "Start latitude must be a valid number between -90.0 and 90.0.", None
            cleaned["start_latitude"] = float(val)
        else:
            cleaned["start_latitude"] = None

    if "start_longitude" in data:
        val = data.get("start_longitude")
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < -180.0 or val > 180.0:
                return False, "Start longitude must be a valid number between -180.0 and 180.0.", None
            cleaned["start_longitude"] = float(val)
        else:
            cleaned["start_longitude"] = None

    # Destination
    if "destination_name" in data or not is_update:
        val = data.get("destination_name")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Destination name is required and must be between 2 and 150 characters.", None
        if len(val.strip()) > 150:
            return False, "Destination name cannot exceed 150 characters.", None
        cleaned["destination_name"] = val.strip()

    if "destination_address" in data or not is_update:
        val = data.get("destination_address")
        if not val or not isinstance(val, str) or len(val.strip()) < 2:
            return False, "Destination address is required and must be between 2 and 255 characters.", None
        if len(val.strip()) > 255:
            return False, "Destination address cannot exceed 255 characters.", None
        cleaned["destination_address"] = val.strip()

    # Destination coordinates (optional)
    if "destination_latitude" in data:
        val = data.get("destination_latitude")
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < -90.0 or val > 90.0:
                return False, "Destination latitude must be a valid number between -90.0 and 90.0.", None
            cleaned["destination_latitude"] = float(val)
        else:
            cleaned["destination_latitude"] = None

    if "destination_longitude" in data:
        val = data.get("destination_longitude")
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < -180.0 or val > 180.0:
                return False, "Destination longitude must be a valid number between -180.0 and 180.0.", None
            cleaned["destination_longitude"] = float(val)
        else:
            cleaned["destination_longitude"] = None

    # Datetimes
    if "planned_start_time" in data or not is_update:
        ok, err, dt = _parse_datetime(data.get("planned_start_time"), "planned_start_time")
        if not ok:
            return False, err, None
        cleaned["planned_start_time"] = dt

    if "expected_arrival_time" in data or not is_update:
        ok, err, dt = _parse_datetime(data.get("expected_arrival_time"), "expected_arrival_time")
        if not ok:
            return False, err, None
        cleaned["expected_arrival_time"] = dt

    # Time logic check if both present
    if "planned_start_time" in cleaned and "expected_arrival_time" in cleaned:
        if cleaned["expected_arrival_time"] <= cleaned["planned_start_time"]:
            return False, "Expected arrival time must be strictly later than planned start time.", None

    if is_update and not cleaned:
        return False, "At least one valid field must be provided for update.", None

    return True, None, cleaned

def validate_cancellation_payload(data: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validates optional cancellation reason payload."""
    if data is None:
        return True, None, None
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None
    reason = data.get("cancellation_reason")
    if reason is not None:
        if not isinstance(reason, str):
            return False, "cancellation_reason must be a string.", None
        if len(reason.strip()) > 255:
            return False, "cancellation_reason cannot exceed 255 characters.", None
        return True, None, reason.strip()
    return True, None, None

def validate_location_item(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates a single GPS location coordinate fix."""
    if not isinstance(data, dict):
        return False, "Each location item must be a JSON object.", None

    lat = data.get("latitude")
    lng = data.get("longitude")
    accuracy = data.get("accuracy")
    recorded_at_str = data.get("recorded_at")

    if lat is None or not isinstance(lat, (int, float)) or isinstance(lat, bool) or lat < -90.0 or lat > 90.0:
        return False, "Latitude is required and must be a number between -90.0 and 90.0.", None

    if lng is None or not isinstance(lng, (int, float)) or isinstance(lng, bool) or lng < -180.0 or lng > 180.0:
        return False, "Longitude is required and must be a number between -180.0 and 180.0.", None

    if accuracy is None or not isinstance(accuracy, (int, float)) or isinstance(accuracy, bool) or accuracy < 0.0:
        return False, "Accuracy is required and must be a non-negative number.", None

    ok, err, recorded_at = _parse_datetime(recorded_at_str, "recorded_at")
    if not ok:
        return False, err, None

    cleaned: Dict[str, Any] = {
        "latitude": float(lat),
        "longitude": float(lng),
        "accuracy": float(accuracy),
        "recorded_at": recorded_at,
        "altitude": None,
        "speed": None,
        "bearing": None
    }

    if "altitude" in data and data["altitude"] is not None:
        alt = data["altitude"]
        if not isinstance(alt, (int, float)) or isinstance(alt, bool):
            return False, "Altitude must be a numeric value.", None
        cleaned["altitude"] = float(alt)

    if "speed" in data and data["speed"] is not None:
        spd = data["speed"]
        if not isinstance(spd, (int, float)) or isinstance(spd, bool) or spd < 0.0:
            return False, "Speed must be a non-negative number in m/s.", None
        cleaned["speed"] = float(spd)

    if "bearing" in data and data["bearing"] is not None:
        brg = data["bearing"]
        if not isinstance(brg, (int, float)) or isinstance(brg, bool) or brg < 0.0 or brg > 360.0:
            return False, "Bearing must be between 0.0 and 360.0 degrees.", None
        cleaned["bearing"] = float(brg)

    return True, None, cleaned

def validate_location_upload_payload(payload: Any) -> Tuple[bool, Optional[str], Optional[list]]:
    """
    Validates batch or single location upload payloads.
    Supports formats:
      - {"locations": [ {...}, ... ]}
      - [ {...}, ... ]
      - {...} (single location object)
    """
    if payload is None:
        return False, "Request payload cannot be empty.", None

    raw_items = []
    if isinstance(payload, dict):
        if "locations" in payload:
            if not isinstance(payload["locations"], list):
                return False, "'locations' field must be a JSON array.", None
            raw_items = payload["locations"]
        else:
            raw_items = [payload]
    elif isinstance(payload, list):
        raw_items = payload
    else:
        return False, "Payload must be a JSON object or array of location fixes.", None

    if not raw_items:
        return False, "At least one location fix must be provided.", None

    if len(raw_items) > 100:
        return False, "Batch size exceeds maximum limit of 100 locations per request.", None

    cleaned_items = []
    for idx, item in enumerate(raw_items):
        ok, err, cleaned = validate_location_item(item)
        if not ok:
            return False, f"Location item at index {idx} invalid: {err}", None
        cleaned_items.append(cleaned)

    return True, None, cleaned_items


def validate_checkin_create_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates check-in creation payload.
    Supports manual timestamps or automatic scheduling when timestamps omitted.
    """
    if data is None:
        data = {}

    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "scheduled_at": None,
        "deadline_at": None,
        "client_action_id": None
    }

    if "client_action_id" in data and data["client_action_id"] is not None:
        cid = data["client_action_id"]
        if not isinstance(cid, str) or not cid.strip() or len(cid.strip()) > 100:
            return False, "client_action_id must be a string up to 100 characters.", None
        cleaned["client_action_id"] = cid.strip()

    has_sched = "scheduled_at" in data and data["scheduled_at"] is not None
    has_dead = "deadline_at" in data and data["deadline_at"] is not None

    if has_sched != has_dead:
        return False, "Both scheduled_at and deadline_at must be provided together, or both omitted for auto-scheduling.", None

    if has_sched:
        ok_s, err_s, dt_s = _parse_datetime(data["scheduled_at"], "scheduled_at")
        if not ok_s:
            return False, err_s, None

        ok_d, err_d, dt_d = _parse_datetime(data["deadline_at"], "deadline_at")
        if not ok_d:
            return False, err_d, None

        if dt_d <= dt_s:
            return False, "deadline_at must be strictly after scheduled_at.", None

        cleaned["scheduled_at"] = dt_s
        cleaned["deadline_at"] = dt_d

    return True, None, cleaned


def validate_checkin_confirm_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates check-in confirmation payload.
    Supports offline sync with client response timestamp.
    """
    if data is None:
        data = {}

    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "responded_at": None,
        "response_type": "MANUAL_TAP",
        "client_action_id": None
    }

    if "responded_at" in data and data["responded_at"] is not None:
        ok, err, dt = _parse_datetime(data["responded_at"], "responded_at")
        if not ok:
            return False, err, None
        cleaned["responded_at"] = dt

    if "response_type" in data and data["response_type"] is not None:
        rt = data["response_type"]
        if not isinstance(rt, str) or not rt.strip() or len(rt.strip()) > 50:
            return False, "response_type must be a string up to 50 characters.", None
        cleaned["response_type"] = rt.strip().upper()

    if "client_action_id" in data and data["client_action_id"] is not None:
        cid = data["client_action_id"]
        if not isinstance(cid, str) or not cid.strip() or len(cid.strip()) > 100:
            return False, "client_action_id must be a string up to 100 characters.", None
        cleaned["client_action_id"] = cid.strip()

    return True, None, cleaned

def validate_safety_event_resolve_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates safety event resolution payload."""
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "resolution_notes": None,
        "client_action_id": None
    }

    if "resolution_notes" in data and data["resolution_notes"] is not None:
        notes = data["resolution_notes"]
        if not isinstance(notes, str) or len(notes.strip()) > 255:
            return False, "resolution_notes must be a string up to 255 characters.", None
        cleaned["resolution_notes"] = notes.strip()

    if "client_action_id" in data and data["client_action_id"] is not None:
        cid = data["client_action_id"]
        if not isinstance(cid, str) or not cid.strip() or len(cid.strip()) > 64:
            return False, "client_action_id must be a string up to 64 characters.", None
        cleaned["client_action_id"] = cid.strip()

    return True, None, cleaned

def validate_emergency_event_create_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates emergency event creation payload."""
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "trigger_type": "MANUAL_SOS",
        "journey_id": None,
        "latitude": None,
        "longitude": None,
        "accuracy": None,
        "location_address": None,
        "client_action_id": None
    }

    if "trigger_type" in data and data["trigger_type"] is not None:
        tt = str(data["trigger_type"]).strip().upper()
        if tt not in ("MANUAL_SOS", "MISSED_CHECKIN_ESCALATION", "SILENT_ALERT"):
            return False, "trigger_type must be MANUAL_SOS, MISSED_CHECKIN_ESCALATION, or SILENT_ALERT.", None
        cleaned["trigger_type"] = tt

    if "journey_id" in data and data["journey_id"] is not None:
        try:
            cleaned["journey_id"] = int(data["journey_id"])
        except (ValueError, TypeError):
            return False, "journey_id must be an integer.", None

    if "latitude" in data and data["latitude"] is not None:
        try:
            lat = float(data["latitude"])
            if lat < -90.0 or lat > 90.0:
                return False, "latitude must be between -90.0 and 90.0.", None
            cleaned["latitude"] = lat
        except (ValueError, TypeError):
            return False, "latitude must be a valid float.", None

    if "longitude" in data and data["longitude"] is not None:
        try:
            lng = float(data["longitude"])
            if lng < -180.0 or lng > 180.0:
                return False, "longitude must be between -180.0 and 180.0.", None
            cleaned["longitude"] = lng
        except (ValueError, TypeError):
            return False, "longitude must be a valid float.", None

    if "accuracy" in data and data["accuracy"] is not None:
        try:
            acc = float(data["accuracy"])
            if acc < 0:
                return False, "accuracy must be non-negative.", None
            cleaned["accuracy"] = acc
        except (ValueError, TypeError):
            return False, "accuracy must be a valid float.", None

    if "location_address" in data and data["location_address"] is not None:
        addr = str(data["location_address"]).strip()
        if len(addr) > 255:
            return False, "location_address cannot exceed 255 characters.", None
        cleaned["location_address"] = addr

    if "client_action_id" in data and data["client_action_id"] is not None:
        cid = str(data["client_action_id"]).strip()
        if len(cid) > 64:
            return False, "client_action_id cannot exceed 64 characters.", None
        cleaned["client_action_id"] = cid

    return True, None, cleaned

def validate_emergency_event_cancel_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates emergency event cancellation payload."""
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "cancellation_reason": "Cancelled by user"
    }

    if "cancellation_reason" in data and data["cancellation_reason"] is not None:
        reason = str(data["cancellation_reason"]).strip()
        if len(reason) > 255:
            return False, "cancellation_reason cannot exceed 255 characters.", None
        cleaned["cancellation_reason"] = reason

    return True, None, cleaned

def validate_emergency_event_escalate_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates emergency event escalation payload."""
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object.", None

    cleaned: Dict[str, Any] = {
        "target_level": None
    }

    if "target_level" in data and data["target_level"] is not None:
        try:
            lvl = int(data["target_level"])
            if lvl < 1 or lvl > 3:
                return False, "target_level must be between 1 and 3.", None
            cleaned["target_level"] = lvl
        except (ValueError, TypeError):
            return False, "target_level must be an integer.", None

    return True, None, cleaned


