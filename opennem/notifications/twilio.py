"""
OpenNEM Twilio SMS and Whatsapp alert notifications
"""

import logging
from typing import Optional

_HAVE_TWILIO = False

try:
    from twilio.rest import Client as TwilioClient

    _HAVE_TWILIO = True
except ImportError:
    pass

from opennem.settings import settings  # noqa: E402

logger = logging.getLogger("opennem.notifications.twilio")


def _get_twilio_client() -> Optional[TwilioClient]:
    """Creates and returns a Twilio REST API client using opennem
    settings.

    Returns:
        Optional[TwilioClient]: The twilio client object
    """
    if not settings.twilio_auth_token or not settings.twilio_sid or not _HAVE_TWILIO:
        logger.error("No twilio account setup on environment {}".format(settings.env))
        return None

    _tc = None

    try:
        _tc = TwilioClient(settings.twilio_sid, settings.twilio_auth_token)
    except Exception as e:
        logger.error("Could not initiate Twilio client: {}".format(e))

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
