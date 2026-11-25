from datetime import datetime, timezone
from app.extensions import db

VALID_DISPATCH_CHANNELS = ("SMS", "CALL_INTENT", "PUSH_NOTIFICATION")
VALID_DISPATCH_STATUSES = ("PENDING", "SENT", "DELIVERED", "FAILED", "ACKNOWLEDGED")

class EmergencyAlertDispatch(db.Model):
    """
    EmergencyAlertDispatch entity representing individual alert notifications dispatched
    to designated trusted contacts per escalation level.
    """
    __tablename__ = "emergency_alert_dispatches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emergency_event_id = db.Column(
        db.Integer,
        db.ForeignKey("emergency_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contact_id = db.Column(
        db.Integer,
        db.ForeignKey("trusted_contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    escalation_level = db.Column(db.Integer, nullable=False, default=1, index=True)
    channel = db.Column(db.String(20), nullable=False, default="SMS")
    status = db.Column(db.String(20), nullable=False, default="PENDING", index=True)

    # Provider tracking & message metadata
    provider_message_id = db.Column(db.String(100), nullable=True, index=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    max_retries = db.Column(db.Integer, nullable=False, default=3)
    message_content = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.String(255), nullable=True)

    # Timestamps
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    acknowledged_at = db.Column(db.DateTime(timezone=True), nullable=True)

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
        db.Index("ix_dispatches_event_status", "emergency_event_id", "status"),
        db.Index("ix_dispatches_event_level", "emergency_event_id", "escalation_level"),
    )

    contact = db.relationship("TrustedContact")

    def to_dict(self) -> dict:
        """Safe serialization of alert dispatch status."""
        return {
            "id": self.id,
            "emergency_event_id": self.emergency_event_id,
            "contact_id": self.contact_id,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "escalation_level": self.escalation_level,
            "channel": self.channel,
            "status": self.status,
            "provider_message_id": self.provider_message_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
