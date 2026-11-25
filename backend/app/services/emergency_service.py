"""
JOURNEX – Emergency Escalation & SOS Management Service
Phase 8: SOS & Multi-Level Emergency Alert Escalation

Handles emergency event lifecycle, multi-level alert escalation across trusted contacts,
provider integration, delivery status tracking, and cancellation safeguards.
"""

import logging
from datetime import datetime, timezone
from app.extensions import db
from app.models.user import User
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.models.trusted_contact import TrustedContact
from app.models.risk_analysis import RiskAnalysis
from app.models.emergency_event import EmergencyEvent, VALID_TRIGGER_TYPES, VALID_EMERGENCY_STATUSES
from app.models.emergency_alert_dispatch import EmergencyAlertDispatch
from app.services.alert_provider import get_alert_provider
from app.utils.exceptions import NotFoundException, ForbiddenException, ConflictException, BadRequestException

logger = logging.getLogger(__name__)

class EmergencyService:

    @staticmethod
    def create_emergency_event(
        user_id: int,
        journey_id: int | None = None,
        trigger_type: str = "MANUAL_SOS",
        latitude: float | None = None,
        longitude: float | None = None,
        accuracy: float | None = None,
        location_address: str | None = None,
        client_action_id: str | None = None
    ) -> EmergencyEvent:
        """
        Trigger a new emergency event with initial Level 1 dispatch to primary contacts.
        Guarantees idempotency via client_action_id.
        """
        if trigger_type not in VALID_TRIGGER_TYPES:
            raise BadRequestException(f"Invalid trigger_type: '{trigger_type}'. Must be one of {VALID_TRIGGER_TYPES}.")

        user = User.query.filter_by(id=user_id).first()
        if not user:
            raise NotFoundException("User not found.")

        # Idempotency check
        if client_action_id:
            existing = EmergencyEvent.query.filter_by(client_action_id=client_action_id).first()
            if existing:
                if existing.user_id != user_id:
                    raise ForbiddenException("Action ID belongs to another user.")
                return existing

        # Validate journey if specified
        risk_analysis_id = None
        if journey_id is not None:
            journey = Journey.query.filter_by(id=journey_id).first()
            if not journey:
                raise NotFoundException("Journey not found.")
            if journey.user_id != user_id:
                raise ForbiddenException("You do not have permission to trigger SOS for this journey.")

            # Grab latest risk analysis
            latest_risk = RiskAnalysis.query.filter_by(journey_id=journey_id).order_by(RiskAnalysis.analyzed_at.desc()).first()
            if latest_risk:
                risk_analysis_id = latest_risk.id

            # Fallback coordinates from journey locations if not explicitly supplied
            if latitude is None or longitude is None:
                latest_loc = JourneyLocation.query.filter_by(journey_id=journey_id).order_by(JourneyLocation.recorded_at.desc()).first()
                if latest_loc:
                    latitude = latest_loc.latitude
                    longitude = latest_loc.longitude
                    accuracy = latest_loc.accuracy

        now_utc = datetime.now(timezone.utc)

        event = EmergencyEvent(
            journey_id=journey_id,
            user_id=user_id,
            trigger_type=trigger_type,
            status="ACTIVE",
            trigger_timestamp=now_utc,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            location_address=location_address or "Location coordinates recorded",
            risk_analysis_id=risk_analysis_id,
            current_escalation_level=1,
            max_escalation_level=3,
            client_action_id=client_action_id
        )

        db.session.add(event)
        db.session.flush()

        # Execute Level 1 Dispatch
        EmergencyService._dispatch_escalation_level(event, user, target_level=1)
        db.session.commit()

        logger.warning(f"[EmergencyService] SOS Triggered: event_id={event.id}, user_id={user_id}, type={trigger_type}")
        return event

    @staticmethod
    def escalate_emergency_event(event_id: int, user_id: int, target_level: int | None = None) -> EmergencyEvent:
        """
        Escalate an active emergency event to the next escalation level (notifying secondary/remaining contacts).
        Prevents duplicate dispatches and rejects escalation on cancelled events.
        """
        event = EmergencyEvent.query.filter_by(id=event_id).first()
        if not event:
            raise NotFoundException("Emergency event not found.")

        if event.user_id != user_id:
            raise ForbiddenException("You do not have permission to escalate this emergency event.")

        if event.status != "ACTIVE":
            raise ConflictException(f"Cannot escalate an emergency event with status '{event.status}'.")

        current_level = event.current_escalation_level
        next_level = target_level if target_level is not None else current_level + 1

        if next_level > event.max_escalation_level:
            # Already at maximum escalation tier, idempotent return
            return event

        if next_level <= current_level:
            return event

        event.current_escalation_level = next_level
        user = User.query.filter_by(id=user_id).first()
        EmergencyService._dispatch_escalation_level(event, user, target_level=next_level)
        db.session.commit()

        logger.warning(f"[EmergencyService] Escalated event_id={event.id} to Level {next_level}")
        return event

    @staticmethod
    def cancel_emergency_event(event_id: int, user_id: int, cancellation_reason: str | None = None) -> EmergencyEvent:
        """
        Cancel an active emergency event and broadcast cancellation update to notified contacts.
        """
        event = EmergencyEvent.query.filter_by(id=event_id).first()
        if not event:
            raise NotFoundException("Emergency event not found.")

        if event.user_id != user_id:
            raise ForbiddenException("You do not have permission to cancel this emergency event.")

        if event.status == "CANCELLED":
            return event

        now_utc = datetime.now(timezone.utc)
        event.status = "CANCELLED"
        event.cancellation_timestamp = now_utc
        event.cancellation_reason = cancellation_reason or "Cancelled by user"

        # Cancel any pending dispatches
        pending_dispatches = EmergencyAlertDispatch.query.filter_by(
            emergency_event_id=event.id,
            status="PENDING"
        ).all()
        for d in pending_dispatches:
            d.status = "FAILED"
            d.error_message = "Event cancelled before delivery."

        # Send cancellation SMS update to contacts who received earlier alerts
        user = User.query.filter_by(id=user_id).first()
        delivered_dispatches = EmergencyAlertDispatch.query.filter(
            EmergencyAlertDispatch.emergency_event_id == event.id,
            EmergencyAlertDispatch.status.in_(["SENT", "DELIVERED"])
        ).all()

        provider = get_alert_provider()
        user_name = user.full_name if user else "Traveler"
        cancel_msg = f"JOURNEX UPDATE: The SOS alert initiated by {user_name} has been CANCELLED. Traveler confirmed safe."

        for d in delivered_dispatches:
            provider.send_sms(d.contact_phone, cancel_msg)

        db.session.commit()
        logger.info(f"[EmergencyService] Cancelled event_id={event.id}: {event.cancellation_reason}")
        return event

    @staticmethod
    def resolve_emergency_event(event_id: int, user_id: int) -> EmergencyEvent:
        """Mark an emergency event as safely resolved."""
        event = EmergencyEvent.query.filter_by(id=event_id).first()
        if not event:
            raise NotFoundException("Emergency event not found.")

        if event.user_id != user_id:
            raise ForbiddenException("You do not have permission to resolve this emergency event.")

        event.status = "RESOLVED"
        db.session.commit()
        return event

    @staticmethod
    def get_emergency_event(event_id: int, user_id: int) -> dict:
        """Retrieve emergency event details including dispatch history."""
        event = EmergencyEvent.query.filter_by(id=event_id).first()
        if not event:
            raise NotFoundException("Emergency event not found.")

        if event.user_id != user_id:
            raise ForbiddenException("You do not have permission to view this emergency event.")

        data = event.to_dict()
        dispatches = EmergencyAlertDispatch.query.filter_by(emergency_event_id=event.id).all()
        data["dispatches"] = [d.to_dict() for d in dispatches]
        return data

    @staticmethod
    def get_delivery_status(event_id: int, user_id: int) -> dict:
        """Retrieve delivery status summary for all alerts in an emergency event."""
        event = EmergencyEvent.query.filter_by(id=event_id).first()
        if not event:
            raise NotFoundException("Emergency event not found.")

        if event.user_id != user_id:
            raise ForbiddenException("You do not have permission to view delivery status for this event.")

        dispatches = EmergencyAlertDispatch.query.filter_by(emergency_event_id=event.id).all()
        return {
            "emergency_event_id": event.id,
            "status": event.status,
            "current_escalation_level": event.current_escalation_level,
            "total_dispatches": len(dispatches),
            "dispatches": [d.to_dict() for d in dispatches]
        }

    @staticmethod
    def list_user_emergency_events(user_id: int, page: int = 1, per_page: int = 10) -> dict:
        """List paginated emergency events for authenticated user."""
        query = EmergencyEvent.query.filter_by(user_id=user_id).order_by(EmergencyEvent.trigger_timestamp.desc())
        total = query.count()
        events = query.offset((page - 1) * per_page).limit(per_page).all()
        return {
            "events": [e.to_dict() for e in events],
            "page": page,
            "per_page": per_page,
            "total": total
        }

    # --- Internal Escalation Logic ---

    @staticmethod
    def _dispatch_escalation_level(event: EmergencyEvent, user: User, target_level: int):
        """
        Dispatch alerts for a specific escalation level.
        Level 1: Primary contact(s) (is_primary=True or priority=1)
        Level 2: Secondary contact (priority=2)
        Level 3: All remaining trusted contacts (priority>=3)
        """
        contacts = TrustedContact.query.filter_by(user_id=user.id).order_by(TrustedContact.priority.asc()).all()
        if not contacts:
            logger.warning(f"[EmergencyService] No trusted contacts configured for user {user.id}")
            return

        # Determine target contacts for this escalation tier
        target_contacts = []
        if target_level == 1:
            target_contacts = [c for c in contacts if c.is_primary or c.priority == 1]
            if not target_contacts and contacts:
                target_contacts = [contacts[0]]
        elif target_level == 2:
            target_contacts = [c for c in contacts if c.priority == 2]
        else: # Level 3
            target_contacts = [c for c in contacts if c.priority >= 3]

        if not target_contacts:
            # If no contacts defined specifically for Level 2 or 3, find un-notified contacts
            already_notified_ids = {
                d.contact_id for d in EmergencyAlertDispatch.query.filter_by(emergency_event_id=event.id).all()
            }
            target_contacts = [c for c in contacts if c.id not in already_notified_ids]

        provider = get_alert_provider()
        user_name = user.full_name or "Traveler"
        loc_str = ""
        if event.latitude is not None and event.longitude is not None:
            loc_str = f" Location: {event.latitude:.5f}, {event.longitude:.5f} ({event.location_address})."

        sos_msg = (
            f"JOURNEX EMERGENCY ALERT [Level {target_level}]: {user_name} has triggered an SOS alert!{loc_str} "
            f"Please check in immediately or call {user.phone_number}."
        )

        now_utc = datetime.now(timezone.utc)

        for contact in target_contacts:
            # Check if this contact was already dispatched at this level
            existing_dispatch = EmergencyAlertDispatch.query.filter_by(
                emergency_event_id=event.id,
                contact_id=contact.id,
                escalation_level=target_level
            ).first()
            if existing_dispatch:
                continue

            dispatch_res = provider.send_sms(contact.phone_number, sos_msg)

            dispatch = EmergencyAlertDispatch(
                emergency_event_id=event.id,
                contact_id=contact.id,
                contact_name=contact.contact_name,
                contact_phone=contact.phone_number,
                escalation_level=target_level,
                channel="SMS",
                status=dispatch_res["status"],
                provider_message_id=dispatch_res.get("provider_message_id"),
                message_content=sos_msg,
                error_message=dispatch_res.get("error"),
                sent_at=now_utc if dispatch_res["status"] in ("SENT", "DELIVERED") else None,
                delivered_at=now_utc if dispatch_res["status"] == "DELIVERED" else None
            )
            db.session.add(dispatch)
