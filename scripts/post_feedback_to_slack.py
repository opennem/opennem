#!/usr/bin/env python
""" Post old feedback to slack to action it """

import logging

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import SessionLocal
from opennem.db.models.opennem import Feedback

logger = logging.getLogger("opennem.feedback")


def post_feedback_to_slack(limit: int | None = None) -> None:
    """Get all feedback and post to slack"""

    with SessionLocal() as session:
        feedbacks: list[Feedback] = session.query(Feedback).order_by(Feedback.created_at.asc()).all()

    for feedback in feedbacks:
        logger.debug(f"Posting feedback to slack: {feedback.created_at} - {feedback.subject} {feedback.description}")

    # slack_message(msg="Feedback: {}".format(feedback.subject), channel=settings.slack_feedback_channel)


if __name__ == "__main__":
    post_feedback_to_slack(limit=1)
