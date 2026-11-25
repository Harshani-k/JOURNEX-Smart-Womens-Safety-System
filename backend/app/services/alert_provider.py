"""
JOURNEX – Alert Provider Abstraction
Phase 8: SOS & Multi-Level Emergency Alert Escalation

Provides a decoupled interface for SMS and voice dispatch providers.
Ensures zero hardcoded credentials and supports test mocking.
"""

import abc
import logging
import uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlertProviderInterface(abc.ABC):
    """Abstract provider interface for emergency notification dispatch."""

    @abc.abstractmethod
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send an emergency SMS alert to a recipient.
        Returns dictionary containing:
        - success (bool)
        - provider_message_id (str)
        - status ("DELIVERED", "SENT", "FAILED")
        - error (str or None)
        """
        pass

class MockAlertProvider(AlertProviderInterface):
    """
    Mock SMS provider for local testing and development.
    Simulates real-world SMS delivery with message tracking and verification IDs.
    """

    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure
        self.dispatched_messages = []

    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        msg_id = f"mock_sms_{uuid.uuid4().hex[:12]}"
        masked_phone = f"{phone_number[:3]}***{phone_number[-4:]}" if len(phone_number) >= 7 else phone_number

        if self.simulate_failure:
            logger.warning(f"[MockAlertProvider] Simulated dispatch FAILURE to {masked_phone}")
            return {
                "success": False,
                "provider_message_id": msg_id,
                "status": "FAILED",
                "error": "Simulated carrier gateway timeout."
            }

        logger.info(f"[MockAlertProvider] Dispatched emergency alert to {masked_phone} (ID: {msg_id})")
        record = {
            "msg_id": msg_id,
            "recipient": phone_number,
            "message": message,
            "status": "DELIVERED"
        }
        self.dispatched_messages.append(record)

        return {
            "success": True,
            "provider_message_id": msg_id,
            "status": "DELIVERED",
            "error": None
        }

_default_provider = MockAlertProvider()

def get_alert_provider() -> AlertProviderInterface:
    """Return active alert provider instance."""
    return _default_provider

def set_alert_provider(provider: AlertProviderInterface):
    """Override provider instance (useful for unit testing failure modes)."""
    global _default_provider
    _default_provider = provider
