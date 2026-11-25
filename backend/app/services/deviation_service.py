import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List, Dict, Any
from app.extensions import db
from app.models.journey import Journey
from app.models.journey_location import JourneyLocation
from app.models.safety_event import SafetyEvent
from app.utils.exceptions import NotFoundException, BadRequestException, ConflictException

logger = logging.getLogger(__name__)

EARTH_RADIUS_METERS = 6371000.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in meters."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_METERS * c

def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the initial bearing from point 1 to point 2 in radians (-pi to +pi)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return math.atan2(y, x)

def point_to_segment_distance(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float
) -> float:
    """
    Calculate the shortest distance from point P to the great-circle corridor segment AB in meters.
    Clamps to endpoints A or B if P lies beyond the segment span.
    """
    d_ab = haversine_distance(a_lat, a_lon, b_lat, b_lon)
    if d_ab < 1.0:
        return haversine_distance(p_lat, p_lon, a_lat, a_lon)

    d_ap = haversine_distance(a_lat, a_lon, p_lat, p_lon)
    delta_ap = d_ap / EARTH_RADIUS_METERS

    theta_ab = initial_bearing(a_lat, a_lon, b_lat, b_lon)
    theta_ap = initial_bearing(a_lat, a_lon, p_lat, p_lon)

    # Cross-track distance
    sin_xt = math.sin(delta_ap) * math.sin(theta_ap - theta_ab)
    sin_xt = max(-1.0, min(1.0, sin_xt))
    d_xt = abs(math.asin(sin_xt)) * EARTH_RADIUS_METERS

    # Along-track distance
    cos_delta_ap = math.cos(delta_ap)
    cos_xt = math.cos(d_xt / EARTH_RADIUS_METERS)
    if abs(cos_xt) < 1e-9:
        d_at = 0.0
    else:
        val = max(-1.0, min(1.0, cos_delta_ap / cos_xt))
        d_at = math.acos(val) * EARTH_RADIUS_METERS

    # Check if projection falls before A
    if math.cos(theta_ap - theta_ab) < 0:
        return d_ap

    # Check if projection falls after B
    if d_at > d_ab:
        return haversine_distance(p_lat, p_lon, b_lat, b_lon)

    return d_xt


class DeviationService:
    """Service for route deviation and unexpected stop detection."""

    DEFAULT_CORRIDOR_THRESHOLD_METERS = 300.0
    DEFAULT_MAX_ACCURACY_METERS = 50.0
    DEFAULT_MIN_CONSECUTIVE_FIXES = 3
    DEFAULT_STOP_THRESHOLD_SECONDS = 600  # 10 minutes

    @classmethod
    def evaluate_location_fix(
        cls,
        journey: Journey,
        current_fix: Dict[str, Any],
        recent_fixes: Optional[List[JourneyLocation]] = None,
        corridor_threshold: float = DEFAULT_CORRIDOR_THRESHOLD_METERS,
        max_accuracy: float = DEFAULT_MAX_ACCURACY_METERS,
        min_consecutive: int = DEFAULT_MIN_CONSECUTIVE_FIXES,
        stop_threshold_sec: int = DEFAULT_STOP_THRESHOLD_SECONDS
    ) -> List[SafetyEvent]:
        """
        Evaluate a single or incoming location fix against route corridor and stop heuristic.
        Returns list of newly triggered or updated SafetyEvent entities.
        """
        if journey.status != "ACTIVE":
            return []

        generated_events: List[SafetyEvent] = []

        # 1. Route Deviation Evaluation
        dev_event = cls.check_route_deviation(
            journey=journey,
            current_fix=current_fix,
            recent_fixes=recent_fixes,
            corridor_threshold=corridor_threshold,
            max_accuracy=max_accuracy,
            min_consecutive=min_consecutive
        )
        if dev_event:
            generated_events.append(dev_event)

        # 2. Unexpected Stop Evaluation
        stop_event = cls.check_unexpected_stop(
            journey=journey,
            current_fix=current_fix,
            recent_fixes=recent_fixes,
            stop_threshold_sec=stop_threshold_sec
        )
        if stop_event:
            generated_events.append(stop_event)

        return generated_events

    @classmethod
    def check_route_deviation(
        cls,
        journey: Journey,
        current_fix: Dict[str, Any],
        recent_fixes: Optional[List[JourneyLocation]] = None,
        corridor_threshold: float = DEFAULT_CORRIDOR_THRESHOLD_METERS,
        max_accuracy: float = DEFAULT_MAX_ACCURACY_METERS,
        min_consecutive: int = DEFAULT_MIN_CONSECUTIVE_FIXES
    ) -> Optional[SafetyEvent]:
        """
        Evaluate route deviation using provisional great-circle corridor between origin and destination.
        Filters out low-accuracy GPS noise and requires multiple consecutive fixes beyond threshold.
        """
        # Journey coordinates validation
        if (journey.start_latitude is None or journey.start_longitude is None or
            journey.destination_latitude is None or journey.destination_longitude is None):
            logger.info("Route corridor unavailable: missing origin or destination coordinates.")
            return None

        accuracy = float(current_fix.get("accuracy", 0.0))
        # Rule: Ignore inaccurate GPS fixes (e.g. accuracy > 50m)
        if accuracy > max_accuracy:
            logger.debug(f"Ignoring inaccurate GPS fix (accuracy {accuracy}m > {max_accuracy}m)")
            return None

        p_lat = float(current_fix["latitude"])
        p_lon = float(current_fix["longitude"])

        distance_from_corridor = point_to_segment_distance(
            p_lat=p_lat, p_lon=p_lon,
            a_lat=journey.start_latitude, a_lon=journey.start_longitude,
            b_lat=journey.destination_latitude, b_lon=journey.destination_longitude
        )

        # Check if current fix is deviated beyond corridor threshold
        if distance_from_corridor <= corridor_threshold:
            # Not deviated: If there is an existing ACTIVE route deviation, we do not resolve automatically,
            # but user can resolve or acknowledge it.
            return None

        # Fix exceeds threshold. Now verify consecutive deviation fixes to avoid transient noise.
        # Fetch the most recent historical fixes if not provided
        if recent_fixes is None:
            recent_fixes = JourneyLocation.query.filter_by(journey_id=journey.id)\
                .order_by(JourneyLocation.recorded_at.desc())\
                .limit(min_consecutive * 2).all()

        # Count consecutive fixes that exceed the threshold with acceptable accuracy
        deviated_count = 1  # current fix counts as 1
        for fix in recent_fixes:
            if fix.accuracy > max_accuracy:
                continue  # skip poor accuracy in historical window
            dist = point_to_segment_distance(
                p_lat=fix.latitude, p_lon=fix.longitude,
                a_lat=journey.start_latitude, a_lon=journey.start_longitude,
                b_lat=journey.destination_latitude, b_lon=journey.destination_longitude
            )
            if dist > corridor_threshold:
                deviated_count += 1
            else:
                break  # consecutive chain broken

        if deviated_count < min_consecutive:
            logger.info(f"Deviation detected ({distance_from_corridor:.1f}m), but only {deviated_count}/{min_consecutive} consecutive fixes. Transient noise filtered.")
            return None

        # Check for existing ACTIVE event for this journey and type to prevent duplicate incidents
        existing_event = SafetyEvent.query.filter_by(
            journey_id=journey.id,
            event_type="ROUTE_DEVIATION",
            status="ACTIVE"
        ).first()

        now = datetime.now(timezone.utc)
        severity = "HIGH" if distance_from_corridor > (corridor_threshold * 2) else "MEDIUM"
        reason = f"Route deviation detected: {round(distance_from_corridor)}m from planned corridor ({deviated_count} consecutive observations)."

        if existing_event:
            # Update existing active incident with latest evidence
            existing_event.deviation_distance = distance_from_corridor
            existing_event.consecutive_count = deviated_count
            existing_event.latitude = p_lat
            existing_event.longitude = p_lon
            existing_event.accuracy = accuracy
            existing_event.trigger_reason = reason
            existing_event.severity = severity
            existing_event.updated_at = now
            db.session.commit()
            return existing_event

        # Create new ACTIVE SafetyEvent
        event = SafetyEvent(
            journey_id=journey.id,
            user_id=journey.user_id,
            event_type="ROUTE_DEVIATION",
            status="ACTIVE",
            trigger_reason=reason,
            severity=severity,
            latitude=p_lat,
            longitude=p_lon,
            accuracy=accuracy,
            deviation_distance=distance_from_corridor,
            consecutive_count=deviated_count,
            detected_at=now
        )
        db.session.add(event)
        db.session.commit()
        logger.warning(f"Triggered ROUTE_DEVIATION for journey {journey.id}: {reason}")
        return event

    @classmethod
    def check_unexpected_stop(
        cls,
        journey: Journey,
        current_fix: Dict[str, Any],
        recent_fixes: Optional[List[JourneyLocation]] = None,
        stop_threshold_sec: int = DEFAULT_STOP_THRESHOLD_SECONDS
    ) -> Optional[SafetyEvent]:
        """
        Detect prolonged unexpected stops.
        Distinguishes normal traffic delays (intermittent movement) from unexpected stationary stops.
        Ignores stops within 100m of the destination (normal arrival).
        """
        p_lat = float(current_fix["latitude"])
        p_lon = float(current_fix["longitude"])

        # Check proximity to destination: if within 100m, it's destination arrival
        if journey.destination_latitude is not None and journey.destination_longitude is not None:
            dist_to_dest = haversine_distance(p_lat, p_lon, journey.destination_latitude, journey.destination_longitude)
            if dist_to_dest <= 100.0:
                logger.debug("Vehicle near destination (<100m); not an unexpected stop.")
                return None

        # Fetch recent fixes over the stop threshold window
        if recent_fixes is None:
            # Query recent fixes for this journey ordered chronologically
            recent_fixes = JourneyLocation.query.filter_by(journey_id=journey.id)\
                .order_by(JourneyLocation.recorded_at.desc())\
                .limit(30).all()
            recent_fixes.reverse()

        if not recent_fixes or len(recent_fixes) < 3:
            return None

        # Identify stationary cluster backwards from latest fix
        anchor_lat = p_lat
        anchor_lon = p_lon

        stationary_cluster = []
        for fix in reversed(recent_fixes):
            disp = haversine_distance(anchor_lat, anchor_lon, fix.latitude, fix.longitude)
            speed = fix.speed if fix.speed is not None else 0.0
            if disp <= 25.0 and speed < 1.0:
                stationary_cluster.append(fix)
            else:
                break  # Movement detected before this point

        if len(stationary_cluster) < 2:
            return None

        # Evaluate time span of the stationary cluster
        cluster_first = stationary_cluster[-1].recorded_at
        cluster_last = stationary_cluster[0].recorded_at
        if cluster_first.tzinfo is None:
            cluster_first = cluster_first.replace(tzinfo=timezone.utc)
        if cluster_last.tzinfo is None:
            cluster_last = cluster_last.replace(tzinfo=timezone.utc)

        duration_sec = int((cluster_last - cluster_first).total_seconds())
        if duration_sec < stop_threshold_sec:
            return None

        max_displacement = max(haversine_distance(anchor_lat, anchor_lon, f.latitude, f.longitude) for f in stationary_cluster)

        # Check for existing ACTIVE UNEXPECTED_STOP event to prevent duplicate incidents
        existing_event = SafetyEvent.query.filter_by(
            journey_id=journey.id,
            event_type="UNEXPECTED_STOP",
            status="ACTIVE"
        ).first()

        now = datetime.now(timezone.utc)
        mins = int(duration_sec // 60)
        reason = f"Vehicle stationary for {mins} minutes (displacement {max_displacement:.1f}m)."

        if existing_event:
            existing_event.duration_seconds = duration_sec
            existing_event.latitude = p_lat
            existing_event.longitude = p_lon
            existing_event.trigger_reason = reason
            existing_event.updated_at = now
            db.session.commit()
            return existing_event

        event = SafetyEvent(
            journey_id=journey.id,
            user_id=journey.user_id,
            event_type="UNEXPECTED_STOP",
            status="ACTIVE",
            trigger_reason=reason,
            severity="MEDIUM",
            latitude=p_lat,
            longitude=p_lon,
            accuracy=current_fix.get("accuracy"),
            duration_seconds=duration_sec,
            consecutive_count=len(recent_fixes),
            detected_at=now
        )
        db.session.add(event)
        db.session.commit()
        logger.warning(f"Triggered UNEXPECTED_STOP for journey {journey.id}: {reason}")
        return event

    @staticmethod
    def acknowledge_safety_event(user_id: int, journey_id: int, event_id: int) -> dict:
        """User acknowledges an active safety event."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        event = SafetyEvent.query.filter_by(id=event_id, journey_id=journey_id, user_id=user_id).first()
        if not event:
            raise NotFoundException("Safety event not found.")

        if event.status in ("RESOLVED", "DISMISSED"):
            return event.to_dict()

        now = datetime.now(timezone.utc)
        event.status = "ACKNOWLEDGED"
        event.acknowledged_at = now
        event.updated_at = now
        db.session.commit()
        return event.to_dict()

    @staticmethod
    def resolve_safety_event(
        user_id: int,
        journey_id: int,
        event_id: int,
        resolution_notes: Optional[str] = None,
        client_action_id: Optional[str] = None
    ) -> dict:
        """User resolves an event or marks it expected (e.g. 'Taking shortcut', 'Traffic jam')."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        # Idempotency check with client_action_id
        if client_action_id:
            existing = SafetyEvent.query.filter_by(client_action_id=client_action_id).first()
            if existing:
                return existing.to_dict()

        event = SafetyEvent.query.filter_by(id=event_id, journey_id=journey_id, user_id=user_id).first()
        if not event:
            raise NotFoundException("Safety event not found.")

        now = datetime.now(timezone.utc)
        event.status = "RESOLVED"
        event.resolved_at = now
        event.resolution_notes = resolution_notes or "Marked safe by traveler"
        if client_action_id:
            event.client_action_id = client_action_id
        event.updated_at = now
        db.session.commit()
        return event.to_dict()

    @staticmethod
    def list_safety_events(user_id: int, journey_id: int, active_only: bool = False) -> List[dict]:
        """List safety events for an authenticated user's journey."""
        journey = Journey.query.filter_by(id=journey_id, user_id=user_id).first()
        if not journey:
            raise NotFoundException("Journey not found.")

        query = SafetyEvent.query.filter_by(journey_id=journey_id, user_id=user_id)
        if active_only:
            query = query.filter_by(status="ACTIVE")

        events = query.order_by(SafetyEvent.detected_at.desc()).all()
        return [e.to_dict() for e in events]
