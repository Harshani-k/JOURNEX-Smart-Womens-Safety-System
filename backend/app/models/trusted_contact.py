from datetime import datetime, timezone
from app.extensions import db

class TrustedContact(db.Model):
    """
    TrustedContact entity representing emergency contacts nominated by the user.
    Each user can have up to 5 contacts, with priority order and a primary flag.
    """
    __tablename__ = "trusted_contacts"

    __table_args__ = (
        db.UniqueConstraint("user_id", "phone_number", name="uq_user_phone"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contact_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    consent_status = db.Column(db.String(20), default="PENDING", nullable=False)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    user = db.relationship(
        "User",
        backref=db.backref("trusted_contacts", cascade="all, delete-orphan", order_by="TrustedContact.priority")
    )

    def to_dict(self) -> dict:
        """Safe serialization eliminating sensitive database foreign keys."""
        return {
            "id": self.id,
            "contact_name": self.contact_name,
            "phone_number": self.phone_number,
            "relationship": self.relationship,
            "priority": self.priority,
            "is_primary": self.is_primary,
            "consent_status": self.consent_status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<TrustedContact id={self.id} user_id={self.user_id} name='{self.contact_name}' is_primary={self.is_primary}>"
