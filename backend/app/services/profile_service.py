import logging
from app.extensions import db
from app.models.safety_profile import SafetyProfile
from app.utils.exceptions import NotFoundException, ConflictException

logger = logging.getLogger(__name__)

class ProfileService:
    """Business logic for Managing User Safety Profiles."""

    @staticmethod
    def get_profile(user_id: int) -> dict:
        """Fetch the safety profile belonging strictly to authenticated user_id."""
        profile = SafetyProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise NotFoundException("Safety profile has not been created yet.")
        return profile.to_dict()

    @staticmethod
    def create_profile(user_id: int, data: dict) -> dict:
        """Create a new safety profile for the authenticated user."""
        existing = SafetyProfile.query.filter_by(user_id=user_id).first()
        if existing:
            raise ConflictException("Safety profile already exists for your account. Use PUT to update.")

        profile = SafetyProfile(
            user_id=user_id,
            display_name=data["display_name"],
            preferred_language=data.get("preferred_language", "en"),
            emergency_message=data["emergency_message"],
            additional_safety_notes=data.get("additional_safety_notes")
        )

        db.session.add(profile)
        db.session.commit()
        logger.info("Created safety profile for user_id=%d", user_id)
        return profile.to_dict()

    @staticmethod
    def update_profile(user_id: int, data: dict) -> dict:
        """Update existing safety profile fields for the authenticated user."""
        profile = SafetyProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise NotFoundException("Safety profile not found. Please create your profile first.")

        if "display_name" in data:
            profile.display_name = data["display_name"]
        if "preferred_language" in data:
            profile.preferred_language = data["preferred_language"]
        if "emergency_message" in data:
            profile.emergency_message = data["emergency_message"]
        if "additional_safety_notes" in data:
            profile.additional_safety_notes = data["additional_safety_notes"]

        db.session.commit()
        logger.info("Updated safety profile for user_id=%d", user_id)
        return profile.to_dict()
