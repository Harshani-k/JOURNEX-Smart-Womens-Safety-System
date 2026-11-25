import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.extensions import db
from app.models.journey import Journey

logger = logging.getLogger(__name__)

class JourneyDelayService:
    """
    Dedicated safety service for monitoring and detecting journey delays.
    Compares expected arrival times against current UTC time without marking
    journeys completed or assuming danger without corroborating telemetry.
    """

    @staticmethod
    def detect_delayed_journeys(reference_time: Optional[datetime] = None) -> int:
        """
        Identifies ACTIVE journeys that have exceeded their expected arrival time
        and flags them as delayed. Idempotent: skips already flagged journeys.
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delayed_journeys = Journey.query.filter(
            Journey.status == "ACTIVE",
            Journey.is_delayed == False,
            Journey.expected_arrival_time < now
        ).all()

        count = 0
        for journey in delayed_journeys:
            journey.is_delayed = True
            journey.delayed_at = now
            count += 1

        if count > 0:
            db.session.commit()
            logger.info("Flagged %d active journeys as delayed at %s.", count, now.isoformat())

        return count

    @staticmethod
    def get_delay_summary(journey_id: int, user_id: int) -> dict:
        """
        Retrieves delay status and minutes exceeded for a specific journey.
        """
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            return {"is_delayed": False, "minutes_delayed": 0}

        now = datetime.now(timezone.utc)
        expected = journey.expected_arrival_time
        if expected.tzinfo is None:
            expected = expected.replace(tzinfo=timezone.utc)

        minutes_delayed = max(0, int((now - expected).total_seconds() / 60)) if (journey.status == "ACTIVE" and now > expected) else 0

        return {
            "journey_id": journey.id,
            "status": journey.status,
            "is_delayed": journey.is_delayed or (journey.status == "ACTIVE" and minutes_delayed > 0),
            "delayed_at": journey.delayed_at.isoformat() if journey.delayed_at else None,
            "expected_arrival_time": expected.isoformat(),
            "minutes_delayed": minutes_delayed
        }
