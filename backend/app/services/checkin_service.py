import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.extensions import db
from app.models.journey import Journey
from app.models.checkin import CheckIn
from app.services.checkin_scheduler import CheckinScheduler
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException

logger = logging.getLogger(__name__)

class CheckinService:
    """
    Business logic for safety check-ins: creation, adaptive scheduling,
    safe confirmation, cancellation, and missed check-in detection.
    """

    @staticmethod
    def create_checkin(user_id: int, journey_id: int, data: dict) -> dict:
        """
        Create or schedule a check-in for the user's ACTIVE journey.
        Prevents duplicate scheduling.
        """
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        if journey.status != "ACTIVE":
            raise BadRequestException(f"Cannot schedule check-ins for journey with status '{journey.status}'. Journey must be ACTIVE.")

        client_action_id = data.get("client_action_id")

        # Check for existing active check-in
        existing = CheckIn.query.filter_by(journey_id=journey_id).filter(
            CheckIn.status.in_(["SCHEDULED", "REMINDED"])
        ).first()

        if existing:
            if client_action_id and existing.client_action_id == client_action_id:
                logger.info("Idempotent check-in create returned existing id=%d", existing.id)
                return existing.to_dict()
            raise ConflictException(f"An active check-in (id={existing.id}) is already scheduled for this journey.")

        # Determine timestamps
        if data.get("scheduled_at") and data.get("deadline_at"):
            scheduled_at = data["scheduled_at"]
            deadline_at = data["deadline_at"]
        else:
            # Auto-schedule using adaptive rule engine
            last_checkin = CheckIn.query.filter_by(journey_id=journey_id).order_by(
                CheckIn.scheduled_at.desc()
            ).first()
            last_time = last_checkin.scheduled_at if last_checkin else None
            scheduled_at, deadline_at = CheckinScheduler.calculate_next_schedule(
                journey=journey,
                last_checkin_time=last_time
            )

        checkin = CheckIn(
            journey_id=journey_id,
            user_id=user_id,
            scheduled_at=scheduled_at,
            deadline_at=deadline_at,
            status="SCHEDULED",
            client_action_id=client_action_id
        )
        db.session.add(checkin)
        db.session.commit()
        logger.info("Scheduled check-in id=%d for journey_id=%d at %s", checkin.id, journey_id, scheduled_at.isoformat())
        return checkin.to_dict()

    @staticmethod
    def list_checkins(user_id: int, journey_id: int, page: int = 1, per_page: int = 10) -> dict:
        """
        List check-in history for a journey, paginated and sorted chronologically.
        """
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        query = CheckIn.query.filter_by(journey_id=journey_id, user_id=user_id).order_by(
            CheckIn.scheduled_at.desc()
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "checkins": [c.to_dict() for c in pagination.items],
            "pagination": {
                "total_items": pagination.total,
                "total_pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": pagination.per_page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }

    @staticmethod
    def get_pending_checkin(user_id: int, journey_id: int) -> Optional[dict]:
        """
        Retrieve the current pending (SCHEDULED or REMINDED) check-in for an active journey.
        """
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        checkin = CheckIn.query.filter_by(journey_id=journey_id, user_id=user_id).filter(
            CheckIn.status.in_(["SCHEDULED", "REMINDED"])
        ).order_by(CheckIn.scheduled_at.asc()).first()

        return checkin.to_dict() if checkin else None

    @staticmethod
    def confirm_checkin(user_id: int, checkin_id: int, data: dict) -> dict:
        """
        Confirm safety for a scheduled check-in.
        Guards against late confirmations, duplicates, and cancelled check-ins.
        """
        checkin = CheckIn.query.filter_by(id=checkin_id, user_id=user_id).first()
        if not checkin:
            raise NotFoundException("Check-in not found.")

        client_action_id = data.get("client_action_id")

        # Idempotent confirmation check
        if checkin.status == "CONFIRMED_SAFE":
            if client_action_id and checkin.client_action_id == client_action_id:
                logger.info("Idempotent confirmation returned existing checkin id=%d", checkin.id)
                return checkin.to_dict()
            raise ConflictException("Check-in has already been confirmed safe.")

        if checkin.status == "CANCELLED":
            raise BadRequestException("Cannot confirm a cancelled check-in.")

        if checkin.status == "MISSED":
            raise ConflictException("Check-in deadline has already passed and was marked MISSED.")

        # Validate against deadline
        now = datetime.now(timezone.utc)
        deadline = checkin.deadline_at
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        # Allow client timestamp for offline sync if provided and sensible
        responded_at = data.get("responded_at") or now
        if responded_at.tzinfo is None:
            responded_at = responded_at.replace(tzinfo=timezone.utc)

        # If confirmation arrives after deadline, mark MISSED
        if responded_at > deadline or now > deadline:
            checkin.status = "MISSED"
            db.session.commit()
            logger.warning("Check-in id=%d expired before confirmation. Marked MISSED.", checkin.id)
            raise ConflictException("Check-in deadline has expired. Check-in is marked as MISSED.")

        checkin.status = "CONFIRMED_SAFE"
        checkin.responded_at = responded_at
        checkin.response_type = data.get("response_type") or "MANUAL_TAP"
        if client_action_id:
            checkin.client_action_id = client_action_id

        db.session.commit()
        logger.info("Check-in id=%d confirmed safe by user_id=%d", checkin.id, user_id)
        return checkin.to_dict()

    @staticmethod
    def cancel_checkin(user_id: int, checkin_id: int) -> dict:
        """
        Cancel a scheduled check-in.
        """
        checkin = CheckIn.query.filter_by(id=checkin_id, user_id=user_id).first()
        if not checkin:
            raise NotFoundException("Check-in not found.")

        if checkin.status not in ("SCHEDULED", "REMINDED"):
            raise BadRequestException(f"Cannot cancel check-in with status '{checkin.status}'.")

        checkin.status = "CANCELLED"
        db.session.commit()
        logger.info("Check-in id=%d cancelled by user_id=%d", checkin.id, user_id)
        return checkin.to_dict()

    @staticmethod
    def detect_missed_checkins(reference_time: Optional[datetime] = None) -> int:
        """
        Scans for overdue check-ins whose deadline has passed and marks them MISSED.
        Idempotent and safe for concurrent execution.
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        overdue_checkins = (
            CheckIn.query.join(Journey, CheckIn.journey_id == Journey.id)
            .filter(
                CheckIn.status.in_(["SCHEDULED", "REMINDED"]),
                CheckIn.deadline_at < now,
                Journey.status == "ACTIVE"
            )
            .all()
        )

        count = 0
        for c in overdue_checkins:
            c.status = "MISSED"
            count += 1

        if count > 0:
            db.session.commit()
            logger.info("Detected and updated %d overdue check-ins to MISSED.", count)

        return count
