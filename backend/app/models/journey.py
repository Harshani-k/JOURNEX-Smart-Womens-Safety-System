from datetime import datetime, timezone
from app.extensions import db

class Journey(db.Model):
    """
    Journey entity representing planned, ongoing, completed, and cancelled travel journeys.
    Enforces user ownership, strict lifecycle transitions, and indexed lookup performance.
    """
    __tablename__ = "journeys"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    journey_title = db.Column(db.String(150), nullable=False)
    
    # Origin details
    start_location_name = db.Column(db.String(150), nullable=False)
    start_location_address = db.Column(db.String(255), nullable=False)
    start_latitude = db.Column(db.Float, nullable=True)
    start_longitude = db.Column(db.Float, nullable=True)

    # Destination details
    destination_name = db.Column(db.String(150), nullable=False)
    destination_address = db.Column(db.String(255), nullable=False)
    destination_latitude = db.Column(db.Float, nullable=True)
    destination_longitude = db.Column(db.Float, nullable=True)

    # Schedule and Timestamps (Timezone-aware UTC)
    planned_start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    expected_arrival_time = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    actual_start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    actual_arrival_time = db.Column(db.DateTime(timezone=True), nullable=True)

    # Lifecycle Status: DRAFT, ACTIVE, COMPLETED, CANCELLED
    status = db.Column(db.String(20), nullable=False, default="DRAFT", index=True)
    cancellation_reason = db.Column(db.String(255), nullable=True)

    # Delay tracking
    is_delayed = db.Column(db.Boolean, default=False, server_default=db.text('0'), nullable=False, index=True)
    delayed_at = db.Column(db.DateTime(timezone=True), nullable=True)

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

    # Composite index for lightning-fast user journey status queries
    __table_args__ = (
        db.Index("ix_journeys_user_status", "user_id", "status"),
    )

    user = db.relationship(
        "User",
        backref=db.backref("journeys", cascade="all, delete-orphan", order_by="Journey.created_at.desc()")
    )

    def to_dict(self) -> dict:
        """Safe serialization of journey attributes into standard dictionary."""
        return {
            "id": self.id,
            "journey_title": self.journey_title,
            "start_location": {
                "name": self.start_location_name,
                "address": self.start_location_address,
                "latitude": self.start_latitude,
                "longitude": self.start_longitude
            },
            "destination": {
                "name": self.destination_name,
                "address": self.destination_address,
                "latitude": self.destination_latitude,
                "longitude": self.destination_longitude
            },
            "planned_start_time": self.planned_start_time.isoformat() if self.planned_start_time else None,
            "expected_arrival_time": self.expected_arrival_time.isoformat() if self.expected_arrival_time else None,
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_arrival_time": self.actual_arrival_time.isoformat() if self.actual_arrival_time else None,
            "status": self.status,
            "cancellation_reason": self.cancellation_reason,
            "is_delayed": self.is_delayed,
            "delayed_at": self.delayed_at.isoformat() if self.delayed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Journey id={self.id} user_id={self.user_id} title='{self.journey_title}' status='{self.status}'>"
