from datetime import datetime, timezone
from app.extensions import db

class JourneyLocation(db.Model):
    """
    JourneyLocation entity storing historical GPS coordinates, accuracy,
    and velocity fixes recorded during an active journey.
    """
    __tablename__ = "journey_locations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journey_id = db.Column(
        db.Integer,
        db.ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)  # Horizontal accuracy in meters
    altitude = db.Column(db.Float, nullable=True)   # Altitude above sea level in meters
    speed = db.Column(db.Float, nullable=True)      # Speed over ground in meters/second
    bearing = db.Column(db.Float, nullable=True)    # Bearing/heading in degrees (0.0 to 360.0)
    
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    received_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        db.Index("ix_journey_locations_journey_recorded", "journey_id", "recorded_at"),
    )

    journey = db.relationship("Journey", backref=db.backref("locations", cascade="all, delete-orphan", lazy="dynamic"))

    def to_dict(self) -> dict:
        """Safe serialization of GPS location fix."""
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "altitude": self.altitude,
            "speed": self.speed,
            "bearing": self.bearing,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None
        }

    def __repr__(self) -> str:
        return f"<JourneyLocation id={self.id} journey_id={self.journey_id} lat={self.latitude} lng={self.longitude}>"
