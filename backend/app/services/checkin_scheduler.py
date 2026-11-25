import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from app.models.journey import Journey

logger = logging.getLogger(__name__)

# Configurable Scheduling Bounds
MIN_INTERVAL_MINUTES = 5
MAX_INTERVAL_MINUTES = 60
DEFAULT_INTERVAL_MINUTES = 15
DEFAULT_GRACE_PERIOD_MINUTES = 3
DELAY_INTERVAL_MINUTES = 5

class CheckinScheduler:
    """
    Deterministic rule-based safety check-in scheduling engine.
    Calculates the next safety check-in timestamp and deadline based on journey parameters,
    elapsed time, delay status, and user safety preferences.
    """

    @staticmethod
    def compute_interval_minutes(
        journey: Journey,
        current_time: Optional[datetime] = None,
        user_preference_minutes: Optional[int] = None
    ) -> int:
        """
        Calculates the adaptive check-in interval in minutes.
        """
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        expected_arrival = journey.expected_arrival_time
        if expected_arrival.tzinfo is None:
            expected_arrival = expected_arrival.replace(tzinfo=timezone.utc)

        # 1. Check if journey is delayed
        is_delayed = journey.is_delayed or (now > expected_arrival)
        if is_delayed:
            logger.info("Journey id=%d is delayed. Using shortened interval %d mins.", journey.id, DELAY_INTERVAL_MINUTES)
            return DELAY_INTERVAL_MINUTES

        # 2. Check user preference if specified
        if user_preference_minutes is not None and isinstance(user_preference_minutes, int):
            clamped = max(MIN_INTERVAL_MINUTES, min(MAX_INTERVAL_MINUTES, user_preference_minutes))
            logger.debug("Using clamped user preference interval %d mins for journey id=%d.", clamped, journey.id)
            return clamped

        # 3. Derive from total planned journey duration
        start_time = journey.actual_start_time or journey.planned_start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        duration_minutes = max(1, int((expected_arrival - start_time).total_seconds() / 60))

        if duration_minutes <= 15:
            # Short journey (e.g. 10-15 mins) -> check halfway or min interval
            return max(MIN_INTERVAL_MINUTES, duration_minutes // 2)
        elif duration_minutes <= 45:
            return 10
        else:
            return DEFAULT_INTERVAL_MINUTES

    @classmethod
    def calculate_next_schedule(
        cls,
        journey: Journey,
        current_time: Optional[datetime] = None,
        user_preference_minutes: Optional[int] = None,
        last_checkin_time: Optional[datetime] = None,
        grace_period_minutes: int = DEFAULT_GRACE_PERIOD_MINUTES
    ) -> Tuple[datetime, datetime]:
        """
        Calculates (scheduled_at, deadline_at) for the next check-in.
        Returns:
            Tuple[datetime, datetime]: UTC timestamps for (scheduled_at, deadline_at).
        """
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        interval = cls.compute_interval_minutes(journey, current_time=now, user_preference_minutes=user_preference_minutes)

        if last_checkin_time:
            if last_checkin_time.tzinfo is None:
                last_checkin_time = last_checkin_time.replace(tzinfo=timezone.utc)
            scheduled_at = max(now, last_checkin_time + timedelta(minutes=interval))
        else:
            scheduled_at = now + timedelta(minutes=interval)

        deadline_at = scheduled_at + timedelta(minutes=grace_period_minutes)
        return scheduled_at, deadline_at
