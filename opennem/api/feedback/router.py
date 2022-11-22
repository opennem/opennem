""" Feedback API endpoint """
import logging

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from opennem.api.auth.key import get_api_key
from opennem.api.auth.schema import AuthApiKeyRecord
from opennem.clients.github import post_github_issue
from opennem.db import get_database_session
from opennem.db.models.opennem import Feedback
from opennem.schema.opennem import OpennemBaseSchema
from opennem.schema.types import TwitterHandle

logger = logging.getLogger(__name__)

router = APIRouter()


class UserFeedbackSubmission(BaseModel):
    subject: str
    description: str | None
    email: EmailStr | None
    twitter: TwitterHandle | None


@router.post("")
@router.post("/")
def feedback_submissions(
    user_feedback: UserFeedbackSubmission,
    request: Request,
    session: Session = Depends(get_database_session),
    app_auth: AuthApiKeyRecord = Depends(get_api_key),  # type: ignore
    user_agent: str | None = Header(None),
) -> OpennemBaseSchema:
    """User feedback submission"""

    user_ip = request.client.host if request.client else "127.0.0.1"

    feedback = Feedback(
        subject=user_feedback.subject,
        description=user_feedback.description,
        email=user_feedback.email,
        twitter=user_feedback.twitter,
        user_ip=user_ip,
        user_agent=user_agent,
    )

    session.add(feedback)

    github_issue_filed = False

    try:
        github_issue_filed = post_github_issue(
            title=user_feedback.subject,
            body=user_feedback.description,
        )
    except Exception as e:
        logger.error(e)

    feedback.alert_sent = github_issue_filed

    session.add(feedback)

    session.commit()

    return OpennemBaseSchema()
