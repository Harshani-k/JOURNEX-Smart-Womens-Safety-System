from datetime import datetime, timezone
from app.extensions import db

VALID_CHECKIN_STATUSES = {
    "SCHEDULED",
    "REMINDED",
    "CONFIRMED_SAFE",
    "MISSED",
    "CANCELLED"
}

class CheckIn(db.Model):
    """
    CheckIn entity representing scheduled, active, confirmed, or missed safety check-ins
    during an active journey.
    """
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journey_id = db.Column(
        db.Integer,
        db.ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    deadline_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="SCHEDULED",
        index=True
    )
    response_type = db.Column(db.String(50), nullable=True)  # e.g., "MANUAL_TAP", "OFFLINE_SYNC"
    reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    client_action_id = db.Column(db.String(100), nullable=True, unique=True, index=True)

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

    __table_args__ = (
        db.Index("ix_checkins_journey_status", "journey_id", "status"),
        db.Index("ix_checkins_status_deadline", "status", "deadline_at"),
    )

    journey = db.relationship(
        "Journey",
        backref=db.backref("checkins", cascade="all, delete-orphan", order_by="CheckIn.scheduled_at.asc()")
    )
    user = db.relationship(
        "User",
        backref=db.backref("checkins", cascade="all, delete-orphan")
    )

    def to_dict(self) -> dict:
        """Safe serialization of check-in attributes."""
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "user_id": self.user_id,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "status": self.status,
            "response_type": self.response_type,
            "reminder_sent_at": self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
            "client_action_id": self.client_action_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<CheckIn id={self.id} journey_id={self.journey_id} status='{self.status}'>"
