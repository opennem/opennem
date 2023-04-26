""" Feedback API endpoint """
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.core.templates import serve_template
from opennem.db import get_database_session
from opennem.db.models.opennem import Feedback
from opennem.schema.opennem import OpennemBaseSchema
from opennem.schema.types import TwitterHandle

logger = logging.getLogger(__name__)

router = APIRouter()


class UserFeedbackSubmission(BaseModel):
    subject: str
    description: str | None = None
    email: EmailStr | None = None
    twitter: TwitterHandle | None = None


@router.post("")
@router.post("/")
def feedback_submissions(
    user_feedback: UserFeedbackSubmission,
    request: Request,
    session: Session = Depends(get_database_session),
    # app_auth: AuthApiKeyRecord = Depends(get_api_key),  # type: ignore
    user_agent: str | None = Header(None),
) -> OpennemBaseSchema:
    """User feedback submission"""

    if not user_feedback.subject:
        raise HTTPException(status_code=400, detail="Subject is required")

    user_ip = request.client.host if request.client else "127.0.0.1"

    feedback = Feedback(
        subject=user_feedback.subject,
        description=user_feedback.description,
        email=user_feedback.email,
        twitter=user_feedback.twitter,
        user_ip=user_ip,
        user_agent=user_agent,
        alert_sent=False,
    )

    try:
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")

    try:
        slack_message_format = serve_template(template_name="feedback_slack_message.md", **{"feedback": feedback})
        slack_message(msg=slack_message_format, alert_webhook_url=settings.feedback_slack_hook_url)
    except Exception as e:
        logger.error(f"Error sending slack feedback message: {e}")

    return OpennemBaseSchema()
