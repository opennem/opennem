import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from opennem.api.auth.key import get_api_key
from opennem.api.auth.schema import AuthApiKeyRecord
from opennem.api.exceptions import OpennemBaseHttpException
from opennem.db import get_database_session
from opennem.db.models.opennem import Feedback
from opennem.notifications.trello import post_trello_card
from opennem.schema.opennem import OpennemBaseSchema
from opennem.schema.types import TwitterHandle

logger = logging.getLogger(__name__)

router = APIRouter()


class NetworkNotFound(OpennemBaseHttpException):
    detail = "Network not found"


class UserFeedbackSubmission(BaseModel):
    subject: str
    description: Optional[str]
    email: Optional[EmailStr]
    twitter: Optional[TwitterHandle]


@router.post("")
@router.post("/")
def feedback_submissions(
    user_feedback: UserFeedbackSubmission,
    request: Request,
    session: Session = Depends(get_database_session),
    app_auth: AuthApiKeyRecord = Depends(get_api_key),
    user_agent: Optional[str] = Header(None),
) -> Any:
    """User feedback submission"""

    user_ip = request.client.host

    if not user_ip:
        user_ip = "127.0.0.1"

    feedback = Feedback(
        subject=user_feedback.subject,
        description=user_feedback.description,
        email=user_feedback.email,
        twitter=user_feedback.twitter,
        user_ip=user_ip,
        user_agent=user_agent,
    )

    session.add(feedback)

    trello_sent = False

    try:
        trello_sent = post_trello_card(
            subject=user_feedback.subject,
            description=user_feedback.description,
            email=user_feedback.email,
        )
    except Exception as e:
        logger.error(e)

    feedback.alert_sent = trello_sent

    session.add(feedback)

    session.commit()

    return OpennemBaseSchema()
