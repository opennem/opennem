""" " OpenNEM feedback module

Called from the API to send / store feedback
"""

import logging

from pydantic import BaseModel

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.core.templates import serve_template
from opennem.db import SessionLocal
from opennem.db.models.opennem import Feedback

logger = logging.getLogger("opennem.core.feedback")


class UserFeedbackSubmission(BaseModel):
    subject: str
    description: str | None = None
    email: str | None = None
    twitter: str | None = None
    user_ip: str | None = None
    user_agent: str | None = None


def persist_and_alert_user_feedback(
    user_feedback: UserFeedbackSubmission,
) -> None:
    """User feedback submission"""

    feedback = Feedback(
        subject=user_feedback.subject,
        description=user_feedback.description,
        email=user_feedback.email,
        twitter=user_feedback.twitter,
        user_ip=user_feedback.user_ip,
        user_agent=user_feedback.user_agent,
        alert_sent=False,
    )

    with SessionLocal() as session:
        try:
            session.add(feedback)
            session.commit()
            session.refresh(feedback)
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")

    try:
        slack_message_format = serve_template(template_name="feedback_slack_message.md", **{"feedback": feedback})
        slack_message(
            message=slack_message_format, webhook_url=settings.slack_hook_feedback, tag_users=settings.slack_admin_alert
        )
    except Exception as e:
        logger.error(f"Error sending slack feedback message: {e}")

    return None


if __name__ == "__main__":
    user_feedback = UserFeedbackSubmission(subject="test", description="test", email="test@test.com")

    persist_and_alert_user_feedback(user_feedback=user_feedback)
