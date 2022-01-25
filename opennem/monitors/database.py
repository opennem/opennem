"""
OpenNEM Check Database Status
"""

from datetime import datetime
from typing import Optional

from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message

LAST_ALERTED: Optional[datetime] = None


def _test_connection() -> None:
    """Run a simple connection attempt to the database"""
    engine = get_database_engine()

    with engine.connect() as c:
        c.execute("select 1")


def alerted_once_recently() -> bool:
    if not LAST_ALERTED:
        return False

    time_since_last_alert = datetime.now() - LAST_ALERTED

    if time_since_last_alert.seconds > 60 * 60:
        return False

    return True


def check_database_live() -> None:
    """Check if the database is live and alert if not"""
    has_error = False
    msg = ""

    try:
        _test_connection()
    except Exception as e:
        has_error = True
        msg = "Database connection error: {}".format(e.__class__)

    if has_error:
        global LAST_ALERTED

        msg_was_sent = slack_message("Opennem {}".format(msg), tag_users=["nik"])

        if msg_was_sent:
            LAST_ALERTED = datetime.now()


if __name__ == "__main__":
    check_database_live()
