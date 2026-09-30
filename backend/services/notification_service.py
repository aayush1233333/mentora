"""
Mentora - Notification Service

Push notifications are currently disabled.
The methods are retained as no-op compatibility methods so existing
backend code can continue to call NotificationService safely.
"""

import logging

logger = logging.getLogger(__name__)

THRESHOLDS = {
    "stressed": 35,
    "fatigued": 65,
}


class NotificationService:
    """Notification compatibility service."""

    def __init__(self):
        self._available = False

    def send_fatigue_alert(
        self,
        notification_token: str,
        fatigue_score: float,
        state: str,
    ) -> bool:
        """
        Notification delivery is currently disabled.
        Returns False because no push-notification provider is configured.
        """
        return False

    def send_break_reminder(
        self,
        notification_token: str,
        session_minutes: float,
    ) -> bool:
        """
        Notification delivery is currently disabled.
        Returns False because no push-notification provider is configured.
        """
        return False



