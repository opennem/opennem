"""
OpenNEM Check Database Status
"""

from opennem.db import get_database_engine
from opennem.notifications.twilio import twilio_message


def _test_connection() -> None:
    """Run a simple connection attempt to the database"""
    engine = get_database_engine()

    with engine.connect() as c:
        c.execute("select 1")


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
        twilio_message("Opennem {}".format(msg))


if __name__ == "__main__":
    check_database_live()
