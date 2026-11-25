import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.journey_service import JourneyService
from app.services.location_service import LocationService
from app.services.checkin_service import CheckinService
from app.services.delay_service import JourneyDelayService
from app.services.deviation_service import DeviationService
from app.services.risk_service import evaluate_journey_risk, get_latest_risk_analysis, get_risk_analysis_history
from app.services.emergency_service import EmergencyService
from app.utils.validators import (
    validate_journey_payload,
    validate_cancellation_payload,
    validate_location_upload_payload,
    validate_checkin_create_payload,
    validate_safety_event_resolve_payload,
    validate_emergency_event_create_payload
)
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

logger = logging.getLogger(__name__)

journeys_bp = Blueprint("journeys", __name__)

def _get_pagination_params():
    """Extract page and per_page query parameters with sensible bounds."""
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", 10))
        if per_page < 1:
            per_page = 10
        elif per_page > 50:
            per_page = 50
    except (ValueError, TypeError):
        per_page = 10

    return page, per_page

@journeys_bp.route("", methods=["POST"])
@jwt_required()
def create_journey():
    """Create a new journey in DRAFT status."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_journey_payload(payload, is_update=False)
    if not is_valid:
        raise BadRequestException(error_msg)

    journey = JourneyService.create_journey(user_id, cleaned_data)
    return api_response(
        data=journey,
        message="Journey created successfully in DRAFT status.",
        status_code=201,
        success=True
    )

@journeys_bp.route("", methods=["GET"])
@jwt_required()
def list_journeys():
    """List authenticated user's journeys with pagination and optional status filter."""
    user_id = int(get_jwt_identity())
    page, per_page = _get_pagination_params()
    status_filter = request.args.get("status")

    result = JourneyService.list_journeys(
        user_id=user_id,
        page=page,
        per_page=per_page,
        status=status_filter
    )
    return api_response(
        data=result,
        message="Journeys retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_journey():
    """Retrieve the currently active journey for the authenticated user."""
    user_id = int(get_jwt_identity())
    journey = JourneyService.get_active_journey(user_id)
    if not journey:
        return api_response(
            data=None,
            message="No active journey found.",
            status_code=200,
            success=True
        )
    return api_response(
        data=journey,
        message="Active journey retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/history", methods=["GET"])
@jwt_required()
def list_history():
    """Retrieve completed and cancelled journeys for history display."""
    user_id = int(get_jwt_identity())
    page, per_page = _get_pagination_params()

    result = JourneyService.list_history(user_id=user_id, page=page, per_page=per_page)
    return api_response(
        data=result,
        message="Journey history retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>", methods=["GET"])
@jwt_required()
def get_journey(journey_id: int):
    """Retrieve a specific journey belonging to authenticated user."""
    user_id = int(get_jwt_identity())
    journey = JourneyService.get_journey(user_id, journey_id)
    return api_response(
        data=journey,
        message="Journey retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>", methods=["PUT"])
@jwt_required()
def update_journey(journey_id: int):
    """Update details of a DRAFT journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_journey_payload(payload, is_update=True)
    if not is_valid:
        raise BadRequestException(error_msg)

    journey = JourneyService.update_journey(user_id, journey_id, cleaned_data)
    return api_response(
        data=journey,
        message="Journey updated successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/start", methods=["POST"])
@jwt_required()
def start_journey(journey_id: int):
    """Start a DRAFT journey, transitioning it to ACTIVE."""
    user_id = int(get_jwt_identity())
    journey = JourneyService.start_journey(user_id, journey_id)
    return api_response(
        data=journey,
        message="Journey started successfully. Status is now ACTIVE.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/complete", methods=["POST"])
@jwt_required()
def complete_journey(journey_id: int):
    """Complete an ACTIVE journey, setting arrival timestamp."""
    user_id = int(get_jwt_identity())
    journey = JourneyService.complete_journey(user_id, journey_id)
    return api_response(
        data=journey,
        message="Journey completed successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_journey(journey_id: int):
    """Cancel a DRAFT or ACTIVE journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, reason = validate_cancellation_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    journey = JourneyService.cancel_journey(user_id, journey_id, reason)
    return api_response(
        data=journey,
        message="Journey cancelled successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/locations", methods=["POST"])
@jwt_required()
def upload_locations(journey_id: int):
    """Upload single or batch of GPS location fixes for an ACTIVE journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, items = validate_location_upload_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    result = LocationService.record_locations(user_id, journey_id, items)
    return api_response(
        data=result,
        message="Locations uploaded successfully.",
        status_code=201,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/locations", methods=["GET"])
@jwt_required()
def get_locations_history(journey_id: int):
    """Retrieve paginated location history for an authenticated user's journey."""
    user_id = int(get_jwt_identity())
    page, per_page = _get_pagination_params()

    result = LocationService.get_locations_history(
        user_id=user_id,
        journey_id=journey_id,
        page=page,
        per_page=per_page
    )
    return api_response(
        data=result,
        message="Location history retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/locations/latest", methods=["GET"])
@jwt_required()
def get_latest_location(journey_id: int):
    """Retrieve the latest valid GPS fix for an authenticated user's journey."""
    user_id = int(get_jwt_identity())
    result = LocationService.get_latest_location(user_id=user_id, journey_id=journey_id)
    msg = "Latest location retrieved successfully." if result else "No location fixes recorded yet."
    return api_response(
        data=result,
        message=msg,
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/checkins", methods=["POST"])
@jwt_required()
def create_or_schedule_checkin(journey_id: int):
    """Create or schedule an adaptive check-in for an ACTIVE journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_checkin_create_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    checkin = CheckinService.create_checkin(user_id, journey_id, cleaned_data)
    return api_response(
        data=checkin,
        message="Check-in scheduled successfully.",
        status_code=201,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/checkins", methods=["GET"])
@jwt_required()
def list_journey_checkins(journey_id: int):
    """Retrieve paginated check-in history for an authenticated user's journey."""
    user_id = int(get_jwt_identity())
    page, per_page = _get_pagination_params()

    result = CheckinService.list_checkins(
        user_id=user_id,
        journey_id=journey_id,
        page=page,
        per_page=per_page
    )
    return api_response(
        data=result,
        message="Check-in history retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/checkins/pending", methods=["GET"])
@jwt_required()
def get_pending_checkin(journey_id: int):
    """Retrieve the current pending safety check-in for an active journey."""
    user_id = int(get_jwt_identity())
    checkin = CheckinService.get_pending_checkin(user_id, journey_id)
    msg = "Pending check-in retrieved successfully." if checkin else "No pending check-in found for this journey."
    return api_response(
        data=checkin,
        message=msg,
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/delay", methods=["GET"])
@jwt_required()
def get_journey_delay_status(journey_id: int):
    """Retrieve delay status and statistics for a specific journey."""
    user_id = int(get_jwt_identity())
    summary = JourneyDelayService.get_delay_summary(journey_id, user_id)
    return api_response(
        data=summary,
        message="Journey delay status retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/detect-delayed", methods=["POST"])
@jwt_required()
def detect_delayed():
    """Trigger journey delay detection sweep across all ACTIVE journeys."""
    count = JourneyDelayService.detect_delayed_journeys()
    return api_response(
        data={"delayed_count": count},
        message=f"Journey delay detection sweep complete. {count} active journey(s) flagged as delayed.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/safety-events", methods=["GET"])
@jwt_required()
def list_journey_safety_events(journey_id: int):
    """Retrieve all safety events (route deviations, unexpected stops) for a journey."""
    user_id = int(get_jwt_identity())
    events = DeviationService.list_safety_events(user_id=user_id, journey_id=journey_id, active_only=False)
    return api_response(
        data={"safety_events": events},
        message="Safety events retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/safety-events/active", methods=["GET"])
@jwt_required()
def get_active_safety_events(journey_id: int):
    """Retrieve currently ACTIVE safety events for a journey."""
    user_id = int(get_jwt_identity())
    events = DeviationService.list_safety_events(user_id=user_id, journey_id=journey_id, active_only=True)
    return api_response(
        data={"active_events": events},
        message="Active safety events retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/safety-events/<int:event_id>/acknowledge", methods=["POST"])
@jwt_required()
def acknowledge_safety_event(journey_id: int, event_id: int):
    """User acknowledges an active safety event."""
    user_id = int(get_jwt_identity())
    result = DeviationService.acknowledge_safety_event(user_id=user_id, journey_id=journey_id, event_id=event_id)
    return api_response(
        data=result,
        message="Safety event acknowledged.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/safety-events/<int:event_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_safety_event(journey_id: int, event_id: int):
    """User resolves a safety event (e.g. expected stop, intentional detour)."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned = validate_safety_event_resolve_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    result = DeviationService.resolve_safety_event(
        user_id=user_id,
        journey_id=journey_id,
        event_id=event_id,
        resolution_notes=cleaned.get("resolution_notes"),
        client_action_id=cleaned.get("client_action_id")
    )
    return api_response(
        data=result,
        message="Safety event resolved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/risk-analysis", methods=["POST"])
@jwt_required()
def analyze_journey_risk(journey_id: int):
    """Execute on-demand or periodic ML risk analysis for an active journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    force_recompute = bool(payload.get("force_recompute", False))

    analysis = evaluate_journey_risk(
        journey_id=journey_id,
        user_id=user_id,
        force_recompute=force_recompute
    )
    return api_response(
        data=analysis.to_dict(),
        message="Risk analysis completed successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/risk-analysis/latest", methods=["GET"])
@jwt_required()
def get_journey_latest_risk(journey_id: int):
    """Retrieve the latest ML risk analysis for an authenticated user's journey."""
    user_id = int(get_jwt_identity())
    analysis = get_latest_risk_analysis(journey_id=journey_id, user_id=user_id)
    msg = "Latest risk analysis retrieved successfully." if analysis else "No risk analysis recorded yet for this journey."
    return api_response(
        data=analysis.to_dict() if analysis else None,
        message=msg,
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/risk-analysis/history", methods=["GET"])
@jwt_required()
def get_journey_risk_history(journey_id: int):
    """Retrieve chronological risk evaluation history for a journey."""
    user_id = int(get_jwt_identity())
    try:
        limit = int(request.args.get("limit", 20))
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 20

    history = get_risk_analysis_history(journey_id=journey_id, user_id=user_id, limit=limit)
    return api_response(
        data={
            "history": [a.to_dict() for a in history],
            "count": len(history)
        },
        message="Risk analysis history retrieved successfully.",
        status_code=200,
        success=True
    )

@journeys_bp.route("/<int:journey_id>/emergency-events", methods=["POST"])
@jwt_required()
def trigger_journey_emergency(journey_id: int):
    """Trigger an emergency SOS event directly associated with an active journey."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned = validate_emergency_event_create_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    event = EmergencyService.create_emergency_event(
        user_id=user_id,
        journey_id=journey_id,
        trigger_type=cleaned.get("trigger_type", "MANUAL_SOS"),
        latitude=cleaned.get("latitude"),
        longitude=cleaned.get("longitude"),
        accuracy=cleaned.get("accuracy"),
        location_address=cleaned.get("location_address"),
        client_action_id=cleaned.get("client_action_id")
    )
    return api_response(
        data=EmergencyService.get_emergency_event(event.id, user_id),
        message="Journey emergency SOS alert triggered successfully. Level 1 contacts notified.",
        status_code=201,
        success=True
    )




