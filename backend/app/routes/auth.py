import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import limiter
from app.services.auth_service import AuthService
from app.utils.validators import validate_registration_payload, validate_login_payload
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    """Register a new user account."""
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_registration_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    result = AuthService.register_user(cleaned_data)
    return api_response(
        data=result,
        message="User registered successfully.",
        status_code=201,
        success=True
    )

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """Authenticate existing user credentials."""
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_login_payload(payload)
    if not is_valid:
        raise BadRequestException(error_msg)

    result = AuthService.authenticate_user(
        email=cleaned_data["email"],
        password=cleaned_data["password"]
    )
    return api_response(
        data=result,
        message="Authentication successful.",
        status_code=200,
        success=True
    )

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Generate a refreshed access token using valid refresh token."""
    identity = get_jwt_identity()
    result = AuthService.refresh_access_token(identity)
    return api_response(
        data=result,
        message="Access token refreshed successfully.",
        status_code=200,
        success=True
    )

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user_profile():
    """Retrieve authenticated user's profile details."""
    identity = get_jwt_identity()
    profile = AuthService.get_user_profile(int(identity))
    return api_response(
        data=profile,
        message="User profile retrieved successfully.",
        status_code=200,
        success=True
    )

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(verify_type=False)
def logout():
    """Revoke current JWT token (access or refresh) to terminate session."""
    jwt_payload = get_jwt()
    AuthService.revoke_token(jwt_payload)
    return api_response(
        data=None,
        message="Successfully logged out and revoked session token.",
        status_code=200,
        success=True
    )
