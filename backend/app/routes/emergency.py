"""
JOURNEX – Emergency Alert & Escalation Routes
Phase 8: SOS & Multi-Level Emergency Alert Escalation

Provides RESTful endpoints for SOS triggering, multi-level escalation,
cancellation, and alert delivery tracking.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.emergency_service import EmergencyService
from app.utils.validators import (
    validate_emergency_event_create_payload,
    validate_emergency_event_cancel_payload,
    validate_emergency_event_escalate_payload
)
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

emergency_bp = Blueprint("emergency", __name__)

@emergency_bp.route("", methods=["POST"])
@jwt_required()
def trigger_standalone_emergency():
    """Trigger a manual or silent SOS alert (can be standalone or journey-linked)."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned = validate_emergency_event_create_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    event = EmergencyService.create_emergency_event(
        user_id=user_id,
        journey_id=cleaned.get("journey_id"),
        trigger_type=cleaned.get("trigger_type", "MANUAL_SOS"),
        latitude=cleaned.get("latitude"),
        longitude=cleaned.get("longitude"),
        accuracy=cleaned.get("accuracy"),
        location_address=cleaned.get("location_address"),
        client_action_id=cleaned.get("client_action_id")
    )

    return api_response(
        data=EmergencyService.get_emergency_event(event.id, user_id),
        message="Emergency SOS alert triggered successfully. Level 1 contacts notified.",
        status_code=201,
        success=True
    )

@emergency_bp.route("/<int:event_id>", methods=["GET"])
@jwt_required()
def get_emergency_event_details(event_id: int):
    """Retrieve full details and dispatch history for an emergency event."""
    user_id = int(get_jwt_identity())
    details = EmergencyService.get_emergency_event(event_id, user_id)
    return api_response(
        data=details,
        message="Emergency event retrieved successfully.",
        status_code=200,
        success=True
    )

@emergency_bp.route("", methods=["GET"])
@jwt_required()
def list_emergency_events():
    """List paginated history of emergency events for the authenticated user."""
    user_id = int(get_jwt_identity())
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

    result = EmergencyService.list_user_emergency_events(user_id, page=page, per_page=per_page)
    return api_response(
        data=result,
        message="Emergency events retrieved successfully.",
        status_code=200,
        success=True
    )

@emergency_bp.route("/<int:event_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_emergency(event_id: int):
    """User cancels an active emergency alert."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned = validate_emergency_event_cancel_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    event = EmergencyService.cancel_emergency_event(
        event_id=event_id,
        user_id=user_id,
        cancellation_reason=cleaned.get("cancellation_reason")
    )
    return api_response(
        data=EmergencyService.get_emergency_event(event.id, user_id),
        message="Emergency event cancelled successfully. Contacts notified of cancellation.",
        status_code=200,
        success=True
    )

@emergency_bp.route("/<int:event_id>/escalate", methods=["POST"])
@jwt_required()
def escalate_emergency(event_id: int):
    """Escalate active emergency event to the next escalation tier."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned = validate_emergency_event_escalate_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    event = EmergencyService.escalate_emergency_event(
        event_id=event_id,
        user_id=user_id,
        target_level=cleaned.get("target_level")
    )
    return api_response(
        data=EmergencyService.get_emergency_event(event.id, user_id),
        message=f"Emergency event escalated to Level {event.current_escalation_level}.",
        status_code=200,
        success=True
    )

@emergency_bp.route("/<int:event_id>/delivery-status", methods=["GET"])
@jwt_required()
def get_alert_delivery_status(event_id: int):
    """Retrieve real-time delivery status for all alert dispatches."""
    user_id = int(get_jwt_identity())
    status_summary = EmergencyService.get_delivery_status(event_id, user_id)
    return api_response(
        data=status_summary,
        message="Emergency alert delivery status retrieved successfully.",
        status_code=200,
        success=True
    )
