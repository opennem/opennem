"""
OpenNEM Twilio SMS and Whatsapp alert notifications
"""

import logging
from typing import Optional

from twilio.rest import Client as TwilioClient

from opennem.settings import settings

logger = logging.getLogger("opennem.notifications.twilio")

twilio_client = TwilioClient(settings.twilio_sid, settings.twilio_auth_token)


def _get_twilio_client() -> Optional[TwilioClient]:
    """Creates and returns a Twilio REST API client using opennem
    settings.

    Returns:
        Optional[TwilioClient]: The twilio client object
    """
    if not settings.twilio_auth_token or not settings.twilio_sid:
        logger.error("No twilio account setup on environment {}".format(settings.env))
        return None

    _tc = TwilioClient(settings.twilio_sid, settings.twilio_auth_token)

    return _tc


def twilio_message(msg: str) -> bool:
    twilio_client = _get_twilio_client()

    if not twilio_client:
        return False

    if not settings.monitoring_alert_sms:
        logger.warn("No receiving alert SMS defined")
        return False

    twilio_client.messages.create(
        to=settings.monitoring_alert_sms, from_=settings.twilio_from_number, body=msg
    )

    return True


if __name__ == "__main__":
    twilio_message("test message")
