import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.extensions import db
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.utils.exceptions import NotFoundException, BadRequestException

logger = logging.getLogger(__name__)

class LocationService:
    """Business logic for GPS location fixes ingestion, history retrieval, and queries."""

    @staticmethod
    def record_locations(user_id: int, journey_id: int, location_items: List[dict]) -> dict:
        """
        Record a batch of GPS location fixes for an authenticated user's ACTIVE journey.
        Handles duplicates safely based on (journey_id, recorded_at).
        """
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status != "ACTIVE":
            raise BadRequestException(f"Cannot upload locations for journey with status '{journey.status}'. Journey must be ACTIVE.")

        # Query existing timestamps for this journey in the incoming time window to deduplicate
        incoming_times = [item["recorded_at"] for item in location_items]
        min_time = min(incoming_times)
        max_time = max(incoming_times)

        existing_records = JourneyLocation.query.filter(
            JourneyLocation.journey_id == journey_id,
            JourneyLocation.recorded_at >= min_time,
            JourneyLocation.recorded_at <= max_time
        ).all()
        def _to_utc_epoch(dt):
            if dt is None:
                return 0
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())

        existing_timestamps = {_to_utc_epoch(rec.recorded_at) for rec in existing_records}

        new_entities = []
        accepted_count = 0
        rejected_count = 0

        for item in location_items:
            epoch = _to_utc_epoch(item["recorded_at"])
            # Check for duplicate timestamp for same journey
            if epoch in existing_timestamps:
                rejected_count += 1
                continue

            existing_timestamps.add(epoch)
            loc = JourneyLocation(
                journey_id=journey_id,
                latitude=item["latitude"],
                longitude=item["longitude"],
                accuracy=item["accuracy"],
                altitude=item.get("altitude"),
                speed=item.get("speed"),
                bearing=item.get("bearing"),
                recorded_at=item["recorded_at"]
            )
            new_entities.append(loc)
            accepted_count += 1

        if new_entities:
            db.session.add_all(new_entities)
            db.session.commit()
            logger.info("Inserted %d location fixes for journey_id=%d", len(new_entities), journey_id)

            # Route deviation and unexpected stop evaluation
            try:
                from app.services.deviation_service import DeviationService
                latest = new_entities[-1]
                fix_dict = {
                    "latitude": latest.latitude,
                    "longitude": latest.longitude,
                    "accuracy": latest.accuracy,
                    "speed": latest.speed,
                    "recorded_at": latest.recorded_at
                }
                DeviationService.evaluate_location_fix(journey=journey, current_fix=fix_dict)
            except Exception as e:
                logger.warning(f"Deviation check non-fatal error: {e}")

        return {
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "total_received": len(location_items)
        }

    @staticmethod
    def get_locations_history(user_id: int, journey_id: int, page: int = 1, per_page: int = 50) -> dict:
        """Retrieve paginated chronological location history for a user's journey."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        query = JourneyLocation.query.filter_by(journey_id=journey_id).order_by(JourneyLocation.recorded_at.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "locations": [loc.to_dict() for loc in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }

    @staticmethod
    def get_latest_location(user_id: int, journey_id: int) -> Optional[dict]:
        """Fetch the most recent valid GPS location fix for a user's journey."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        latest = (
            JourneyLocation.query.filter_by(journey_id=journey_id)
            .order_by(JourneyLocation.recorded_at.desc())
            .first()
        )
        return latest.to_dict() if latest else None
