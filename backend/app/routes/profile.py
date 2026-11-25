import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.profile_service import ProfileService
from app.utils.validators import validate_safety_profile_payload
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

logger = logging.getLogger(__name__)

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    """Retrieve the authenticated user's safety profile."""
    user_id = int(get_jwt_identity())
    profile = ProfileService.get_profile(user_id)
    return api_response(
        data=profile,
        message="Safety profile retrieved successfully.",
        status_code=200,
        success=True
    )

@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():
    """Create a new safety profile for the authenticated user."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_safety_profile_payload(payload, is_update=False)
    if not is_valid:
        raise BadRequestException(error_msg)

    profile = ProfileService.create_profile(user_id, cleaned_data)
    return api_response(
        data=profile,
        message="Safety profile created successfully.",
        status_code=201,
        success=True
    )

@profile_bp.route("", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update existing safety profile for the authenticated user."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_safety_profile_payload(payload, is_update=True)
    if not is_valid:
        raise BadRequestException(error_msg)

    profile = ProfileService.update_profile(user_id, cleaned_data)
    return api_response(
        data=profile,
        message="Safety profile updated successfully.",
        status_code=200,
        success=True
    )
