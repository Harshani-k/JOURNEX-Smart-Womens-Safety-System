from datetime import datetime, timezone
from app.extensions import db

class SafetyProfile(db.Model):
    """
    SafetyProfile entity representing a user's emergency profile, preferences,
    and personalized SOS messages. Enforces strict 1-to-1 relationship with User.
    """
    __tablename__ = "safety_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    preferred_language = db.Column(db.String(10), default="en", nullable=False)
    emergency_message = db.Column(db.String(500), nullable=False)
    additional_safety_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("User", backref=db.backref("safety_profile", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self) -> dict:
        """Safe serialization eliminating sensitive database foreign keys."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "preferred_language": self.preferred_language,
            "emergency_message": self.emergency_message,
            "additional_safety_notes": self.additional_safety_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<SafetyProfile id={self.id} user_id={self.user_id} display_name='{self.display_name}'>"
