from datetime import datetime, timezone
from app.extensions import db

VALID_TRIGGER_TYPES = ("MANUAL_SOS", "MISSED_CHECKIN_ESCALATION", "SILENT_ALERT")
VALID_EMERGENCY_STATUSES = ("ACTIVE", "CANCELLED", "ESCALATED", "RESOLVED")

class EmergencyEvent(db.Model):
    """
    EmergencyEvent entity tracking initiated panic alerts, location snapshots,
    cancellation state, and multi-level escalation progression.
    """
    __tablename__ = "emergency_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journey_id = db.Column(
        db.Integer,
        db.ForeignKey("journeys.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    trigger_type = db.Column(db.String(30), nullable=False, default="MANUAL_SOS", index=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)

    # Trigger & Lifecycle Timestamps
    trigger_timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    cancellation_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    cancellation_reason = db.Column(db.String(255), nullable=True)

    # Location Evidence Snapshot at time of SOS trigger
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    location_address = db.Column(db.String(255), nullable=True)

    # Optional Machine Learning Context snapshot
    risk_analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("risk_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Multi-level escalation progression
    current_escalation_level = db.Column(db.Integer, nullable=False, default=1)
    max_escalation_level = db.Column(db.Integer, nullable=False, default=3)

    # Client-side idempotency key (prevents double SOS triggers on network retries)
    client_action_id = db.Column(db.String(64), nullable=True, unique=True, index=True)

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
        db.Index("ix_emergency_events_user_status", "user_id", "status"),
        db.Index("ix_emergency_events_journey_status", "journey_id", "status"),
    )

    user = db.relationship("User", backref=db.backref("emergency_events", cascade="all, delete-orphan", lazy="dynamic"))
    journey = db.relationship("Journey", backref=db.backref("emergency_events", lazy="dynamic"))
    risk_analysis = db.relationship("RiskAnalysis")
    dispatches = db.relationship(
        "EmergencyAlertDispatch",
        backref="emergency_event",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="EmergencyAlertDispatch.escalation_level.asc(), EmergencyAlertDispatch.created_at.asc()"
    )

    def to_dict(self) -> dict:
        """Safe serialization of emergency event attributes."""
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "user_id": self.user_id,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "trigger_timestamp": self.trigger_timestamp.isoformat() if self.trigger_timestamp else None,
            "cancellation_timestamp": self.cancellation_timestamp.isoformat() if self.cancellation_timestamp else None,
            "cancellation_reason": self.cancellation_reason,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "location_address": self.location_address,
            "risk_analysis_id": self.risk_analysis_id,
            "current_escalation_level": self.current_escalation_level,
            "max_escalation_level": self.max_escalation_level,
            "client_action_id": self.client_action_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
