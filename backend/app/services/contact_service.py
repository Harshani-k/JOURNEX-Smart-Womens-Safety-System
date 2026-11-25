import logging
from typing import List, Dict, Any
from app.extensions import db
from app.models.trusted_contact import TrustedContact
from app.utils.exceptions import NotFoundException, ConflictException, BadRequestException

logger = logging.getLogger(__name__)

MAX_TRUSTED_CONTACTS = 5

class ContactService:
    """Business logic for Managing Trusted Emergency Contacts."""

    @staticmethod
    def list_contacts(user_id: int) -> List[Dict[str, Any]]:
        """Return all contacts for authenticated user, sorted by priority."""
        contacts = (
            TrustedContact.query.filter_by(user_id=user_id)
            .order_by(TrustedContact.priority.asc(), TrustedContact.id.asc())
            .all()
        )
        return [contact.to_dict() for contact in contacts]

    @staticmethod
    def get_contact(user_id: int, contact_id: int) -> Dict[str, Any]:
        """Fetch an individual contact ensuring ownership check."""
        contact = TrustedContact.query.filter_by(id=contact_id, user_id=user_id).first()
        if not contact:
            raise NotFoundException("Trusted contact not found.")
        return contact.to_dict()

    @staticmethod
    def add_contact(user_id: int, data: dict) -> Dict[str, Any]:
        """Add a new contact under max 5 contacts quota and unique phone constraint."""
        count = TrustedContact.query.filter_by(user_id=user_id).count()
        if count >= MAX_TRUSTED_CONTACTS:
            raise BadRequestException(f"Maximum limit of {MAX_TRUSTED_CONTACTS} trusted contacts reached.")

        duplicate = TrustedContact.query.filter_by(user_id=user_id, phone_number=data["phone_number"]).first()
        if duplicate:
            raise ConflictException(f"A trusted contact with phone number '{data['phone_number']}' already exists.")

        is_primary = data.get("is_primary", False)
        # Auto-designate first contact as primary if not specified
        if count == 0 and "is_primary" not in data:
            is_primary = True

        if is_primary:
            TrustedContact.query.filter_by(user_id=user_id).update({"is_primary": False})

        contact = TrustedContact(
            user_id=user_id,
            contact_name=data["contact_name"],
            phone_number=data["phone_number"],
            relationship=data["relationship"],
            priority=data.get("priority", 1),
            is_primary=is_primary,
            consent_status="PENDING"
        )

        db.session.add(contact)
        db.session.commit()
        logger.info("Added trusted contact id=%d for user_id=%d", contact.id, user_id)
        return contact.to_dict()

    @staticmethod
    def update_contact(user_id: int, contact_id: int, data: dict) -> Dict[str, Any]:
        """Update contact fields with ownership and phone uniqueness verification."""
        contact = TrustedContact.query.filter_by(id=contact_id, user_id=user_id).first()
        if not contact:
            raise NotFoundException("Trusted contact not found.")

        if "phone_number" in data and data["phone_number"] != contact.phone_number:
            duplicate = TrustedContact.query.filter(
                TrustedContact.user_id == user_id,
                TrustedContact.id != contact_id,
                TrustedContact.phone_number == data["phone_number"]
            ).first()
            if duplicate:
                raise ConflictException(f"A trusted contact with phone number '{data['phone_number']}' already exists.")
            contact.phone_number = data["phone_number"]

        if "contact_name" in data:
            contact.contact_name = data["contact_name"]
        if "relationship" in data:
            contact.relationship = data["relationship"]
        if "priority" in data:
            contact.priority = data["priority"]

        if "is_primary" in data:
            if data["is_primary"]:
                TrustedContact.query.filter(
                    TrustedContact.user_id == user_id,
                    TrustedContact.id != contact_id
                ).update({"is_primary": False})
                contact.is_primary = True
            else:
                contact.is_primary = False

        db.session.commit()
        logger.info("Updated contact id=%d for user_id=%d", contact_id, user_id)
        return contact.to_dict()

    @staticmethod
    def delete_contact(user_id: int, contact_id: int) -> None:
        """Delete contact with automatic primary promotion if needed."""
        contact = TrustedContact.query.filter_by(id=contact_id, user_id=user_id).first()
        if not contact:
            raise NotFoundException("Trusted contact not found.")

        was_primary = contact.is_primary
        db.session.delete(contact)
        db.session.commit()

        if was_primary:
            remaining = (
                TrustedContact.query.filter_by(user_id=user_id)
                .order_by(TrustedContact.priority.asc())
                .first()
            )
            if remaining:
                remaining.is_primary = True
                db.session.commit()

        logger.info("Deleted contact id=%d for user_id=%d", contact_id, user_id)

    @staticmethod
    def set_primary_contact(user_id: int, contact_id: int) -> Dict[str, Any]:
        """Atomically promote contact to primary and demote all other contacts."""
        contact = TrustedContact.query.filter_by(id=contact_id, user_id=user_id).first()
        if not contact:
            raise NotFoundException("Trusted contact not found.")

        TrustedContact.query.filter_by(user_id=user_id).update({"is_primary": False})
        contact.is_primary = True
        db.session.commit()

        logger.info("Set contact id=%d as primary for user_id=%d", contact_id, user_id)
        return contact.to_dict()
