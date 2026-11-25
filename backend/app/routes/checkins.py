import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.checkin_service import CheckinService
from app.utils.validators import (
    validate_checkin_confirm_payload
)
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

logger = logging.getLogger(__name__)

checkins_bp = Blueprint("checkins", __name__)

@checkins_bp.route("/<int:checkin_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_checkin(checkin_id: int):
    """
    Confirm safety for a scheduled check-in.
    Enforces deadline rules, idempotency, and records confirmation time.
    """
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_checkin_confirm_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    checkin = CheckinService.confirm_checkin(user_id, checkin_id, cleaned_data)
    return api_response(
        data=checkin,
        message="Check-in confirmed safe successfully.",
        status_code=200,
        success=True
    )

@checkins_bp.route("/<int:checkin_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_checkin(checkin_id: int):
    """
    Cancel an active scheduled check-in.
    """
    user_id = int(get_jwt_identity())
    checkin = CheckinService.cancel_checkin(user_id, checkin_id)
    return api_response(
        data=checkin,
        message="Check-in cancelled successfully.",
        status_code=200,
        success=True
    )

@checkins_bp.route("/detect-missed", methods=["POST"])
@jwt_required()
def detect_missed():
    """
    Trigger missed check-in detection sweep.
    Scans overdue scheduled check-ins and marks them MISSED.
    """
    count = CheckinService.detect_missed_checkins()
    return api_response(
        data={"missed_count": count},
        message=f"Missed check-in detection sweep complete. {count} overdue check-in(s) marked MISSED.",
        status_code=200,
        success=True
    )
