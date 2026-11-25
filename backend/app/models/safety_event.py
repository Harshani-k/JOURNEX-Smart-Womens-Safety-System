from datetime import datetime, timezone
from app.extensions import db

VALID_EVENT_TYPES = ("ROUTE_DEVIATION", "UNEXPECTED_STOP")
VALID_EVENT_STATUSES = ("ACTIVE", "ACKNOWLEDGED", "RESOLVED", "DISMISSED")
VALID_SEVERITIES = ("LOW", "MEDIUM", "HIGH")

class SafetyEvent(db.Model):
    """
    SafetyEvent entity representing detected route deviations and unexpected stops
    during an active journey.
    """
    __tablename__ = "safety_events"

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
    event_type = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    trigger_reason = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="MEDIUM")
    
    # Evidence fixes
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    deviation_distance = db.Column(db.Float, nullable=True)  # in meters
    duration_seconds = db.Column(db.Integer, nullable=True)   # in seconds
    consecutive_count = db.Column(db.Integer, default=1, nullable=False)

    # Lifecycle timestamps
    detected_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    acknowledged_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_notes = db.Column(db.String(255), nullable=True)

    # Idempotency token for client offline action sync
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
        db.Index("ix_safety_events_journey_status", "journey_id", "status"),
        db.Index("ix_safety_events_journey_type_status", "journey_id", "event_type", "status"),
    )

    journey = db.relationship("Journey", backref=db.backref("safety_events", cascade="all, delete-orphan", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("safety_events", cascade="all, delete-orphan", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "status": self.status,
            "trigger_reason": self.trigger_reason,
            "severity": self.severity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "deviation_distance": round(self.deviation_distance, 1) if self.deviation_distance is not None else None,
            "duration_seconds": self.duration_seconds,
            "consecutive_count": self.consecutive_count,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "client_action_id": self.client_action_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<SafetyEvent id={self.id} journey_id={self.journey_id} type={self.event_type} status={self.status}>"
