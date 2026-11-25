import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.contact_service import ContactService
from app.utils.validators import validate_trusted_contact_payload
from app.utils.response import api_response
from app.utils.exceptions import BadRequestException

logger = logging.getLogger(__name__)

contacts_bp = Blueprint("contacts", __name__)

@contacts_bp.route("", methods=["GET"])
@jwt_required()
def list_contacts():
    """List all trusted emergency contacts for the authenticated user."""
    user_id = int(get_jwt_identity())
    contacts = ContactService.list_contacts(user_id)
    return api_response(
        data=contacts,
        message="Trusted contacts retrieved successfully.",
        status_code=200,
        success=True
    )

@contacts_bp.route("", methods=["POST"])
@jwt_required()
def add_contact():
    """Add a new trusted emergency contact for the authenticated user."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_trusted_contact_payload(payload, is_update=False)
    if not is_valid:
        raise BadRequestException(error_msg)

    contact = ContactService.add_contact(user_id, cleaned_data)
    return api_response(
        data=contact,
        message="Trusted contact added successfully.",
        status_code=201,
        success=True
    )

@contacts_bp.route("/<int:contact_id>", methods=["GET"])
@jwt_required()
def get_contact(contact_id: int):
    """Retrieve an individual trusted contact belonging to the authenticated user."""
    user_id = int(get_jwt_identity())
    contact = ContactService.get_contact(user_id, contact_id)
    return api_response(
        data=contact,
        message="Trusted contact retrieved successfully.",
        status_code=200,
        success=True
    )

@contacts_bp.route("/<int:contact_id>", methods=["PUT"])
@jwt_required()
def update_contact(contact_id: int):
    """Update an existing trusted contact for the authenticated user."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True)
    is_valid, error_msg, cleaned_data = validate_trusted_contact_payload(payload, is_update=True)
    if not is_valid:
        raise BadRequestException(error_msg)

    contact = ContactService.update_contact(user_id, contact_id, cleaned_data)
    return api_response(
        data=contact,
        message="Trusted contact updated successfully.",
        status_code=200,
        success=True
    )

@contacts_bp.route("/<int:contact_id>", methods=["DELETE"])
@jwt_required()
def delete_contact(contact_id: int):
    """Delete a trusted contact belonging to the authenticated user."""
    user_id = int(get_jwt_identity())
    ContactService.delete_contact(user_id, contact_id)
    return api_response(
        data=None,
        message="Trusted contact deleted successfully.",
        status_code=200,
        success=True
    )

@contacts_bp.route("/<int:contact_id>/primary", methods=["PATCH"])
@jwt_required()
def set_primary(contact_id: int):
    """Designate a trusted contact as the primary emergency contact."""
    user_id = int(get_jwt_identity())
    contact = ContactService.set_primary_contact(user_id, contact_id)
    return api_response(
        data=contact,
        message="Primary trusted contact updated successfully.",
        status_code=200,
        success=True
    )
