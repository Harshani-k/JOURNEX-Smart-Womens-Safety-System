import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.extensions import db
from app.models.journey import Journey
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException

logger = logging.getLogger(__name__)

VALID_STATUSES = {"DRAFT", "ACTIVE", "COMPLETED", "CANCELLED"}

class JourneyService:
    """Business logic for Journey creation, retrieval, lifecycle transitions, and history."""

    @staticmethod
    def create_journey(user_id: int, data: dict) -> dict:
        """Create a new journey in DRAFT status."""
        journey = Journey(
            user_id=user_id,
            journey_title=data["journey_title"],
            start_location_name=data["start_location_name"],
            start_location_address=data["start_location_address"],
            start_latitude=data.get("start_latitude"),
            start_longitude=data.get("start_longitude"),
            destination_name=data["destination_name"],
            destination_address=data["destination_address"],
            destination_latitude=data.get("destination_latitude"),
            destination_longitude=data.get("destination_longitude"),
            planned_start_time=data["planned_start_time"],
            expected_arrival_time=data["expected_arrival_time"],
            status="DRAFT"
        )
        db.session.add(journey)
        db.session.commit()
        logger.info("Created DRAFT journey id=%d for user_id=%d", journey.id, user_id)
        return journey.to_dict()

    @staticmethod
    def get_journey(user_id: int, journey_id: int) -> dict:
        """Fetch journey enforcing authenticated ownership."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")
        return journey.to_dict()

    @staticmethod
    def list_journeys(user_id: int, page: int = 1, per_page: int = 10, status: Optional[str] = None) -> dict:
        """List journeys belonging to user with optional status filter and pagination."""
        query = Journey.query.filter_by(user_id=user_id)

        if status:
            status_clean = status.strip().upper()
            if status_clean not in VALID_STATUSES:
                raise BadRequestException(f"Invalid status filter '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
            query = query.filter_by(status=status_clean)

        query = query.order_by(Journey.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "journeys": [j.to_dict() for j in pagination.items],
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
    def update_journey(user_id: int, journey_id: int, data: dict) -> dict:
        """Update journey details; allowed only in DRAFT status."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status != "DRAFT":
            raise BadRequestException(f"Cannot edit journey with status '{journey.status}'. Only DRAFT journeys can be modified.")

        # Determine effective datetimes for consistency check
        new_start = data.get("planned_start_time", journey.planned_start_time)
        new_arrival = data.get("expected_arrival_time", journey.expected_arrival_time)
        if new_arrival <= new_start:
            raise BadRequestException("Expected arrival time must be strictly later than planned start time.")

        for key, value in data.items():
            if hasattr(journey, key):
                setattr(journey, key, value)

        db.session.commit()
        logger.info("Updated DRAFT journey id=%d for user_id=%d", journey_id, user_id)
        return journey.to_dict()

    @staticmethod
    def start_journey(user_id: int, journey_id: int) -> dict:
        """Transition DRAFT journey to ACTIVE; enforces max 1 active journey rule."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status == "ACTIVE":
            raise BadRequestException("Journey is already active.")
        if journey.status in ["COMPLETED", "CANCELLED"]:
            raise BadRequestException(f"Cannot start a journey with status '{journey.status}'. Only DRAFT journeys can be started.")

        # Enforce single active journey invariant
        active_journey = Journey.query.filter_by(user_id=user_id, status="ACTIVE").first()
        if active_journey:
            raise ConflictException(f"You already have an active journey (ID: {active_journey.id}, '{active_journey.journey_title}'). Please complete or cancel it before starting another.")

        journey.status = "ACTIVE"
        journey.actual_start_time = datetime.now(timezone.utc)
        db.session.commit()
        logger.info("Started journey id=%d (ACTIVE) for user_id=%d", journey_id, user_id)
        return journey.to_dict()

    @staticmethod
    def get_active_journey(user_id: int) -> Optional[dict]:
        """Retrieve user's active journey if one exists."""
        journey = Journey.query.filter_by(user_id=user_id, status="ACTIVE").first()
        return journey.to_dict() if journey else None

    @staticmethod
    def complete_journey(user_id: int, journey_id: int) -> dict:
        """Mark an ACTIVE journey as COMPLETED."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status == "COMPLETED":
            raise BadRequestException("Journey is already completed.")
        if journey.status == "CANCELLED":
            raise BadRequestException("Cannot complete a cancelled journey.")
        if journey.status == "DRAFT":
            raise BadRequestException("Cannot complete a draft journey. It must be started first.")

        journey.status = "COMPLETED"
        journey.actual_arrival_time = datetime.now(timezone.utc)
        db.session.commit()
        logger.info("Completed journey id=%d for user_id=%d", journey_id, user_id)
        return journey.to_dict()

    @staticmethod
    def cancel_journey(user_id: int, journey_id: int, reason: Optional[str] = None) -> dict:
        """Cancel a DRAFT or ACTIVE journey."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status == "COMPLETED":
            raise BadRequestException("Cannot cancel an already completed journey.")
        if journey.status == "CANCELLED":
            raise BadRequestException("Journey is already cancelled.")

        journey.status = "CANCELLED"
        journey.cancellation_reason = reason
        db.session.commit()
        logger.info("Cancelled journey id=%d (reason: %s) for user_id=%d", journey_id, reason, user_id)
        return journey.to_dict()

    @staticmethod
    def list_history(user_id: int, page: int = 1, per_page: int = 10) -> dict:
        """List COMPLETED and CANCELLED journeys for history view."""
        query = (
            Journey.query.filter(
                Journey.user_id == user_id,
                Journey.status.in_(["COMPLETED", "CANCELLED"])
            )
            .order_by(Journey.updated_at.desc(), Journey.id.desc())
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "journeys": [j.to_dict() for j in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
