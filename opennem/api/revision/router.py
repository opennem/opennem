from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from opennem.db import get_database_session
from opennem.db.models.opennem import Facility, Location, Revision, Station

from .schema import (
    RevisionModification,
    RevisionModificationResponse,
    UpdateResponse,
)

router = APIRouter()


@router.get("/")
def revisions(
    session: Session = Depends(get_database_session),
) -> List[Revision]:
    revisions = session.query(Revision).all()

    return revisions


@router.get("/{revision_id}")
def revision(
    revision_id: int, session: Session = Depends(get_database_session)
):
    revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    return revision


REVISION_TARGET_MAP = {
    "station": Station,
    "facility": Facility,
    "location": Location,
}


@router.put("/{revision_id}", name="revision update")
def revision_update(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision: Revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    if data.modification == "reject":
        revision.discarded = True
        revision.approved = False
        revision.discarded_by = "opennem.admin"
        revision.discarded_at = datetime.now()

        session.add(revision)
        session.commit()

        response = UpdateResponse(success=True, record=revision)

    revision.approved = True
    revision.approved_at = datetime.now()
    revision.approved_by = "opennem.admin"

    if revision.parent_type not in REVISION_TARGET_MAP.keys():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Revision schema type not supported",
        )

    revision_target_type = REVISION_TARGET_MAP[revision.parent_type]

    revision_target = session.query(revision_target_type).get(
        revision.parent_id
    )

    if not revision_target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision target record not found",
        )

    for target_field, target_value in revision.changes.items():
        if hasattr(revision_target, f"{target_field}_code"):
            target_field = "{}_code".format(target_field)

        if hasattr(revision_target, f"{target_field}_id"):
            target_field = "{}_id".format(target_field)

        if not hasattr(revision_target, target_field):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid revision field",
            )

        try:
            setattr(revision_target, target_field, target_value)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error setting revision",
            )

    session.add(revision_target)
    session.add(revision)
    session.commit()

    response = RevisionModificationResponse(
        success=True, record=revision, target=revision_target
    )

    return response


@router.post("/approve/{revision_id}", name="revision approve")
def revision_approve(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    revision.approved = True
    revision.approved_by = "opennem.admin"

    session.add(revision)
    session.commit()

    response = UpdateResponse(success=True, record=revision)

    return response


@router.post("/reject/{revision_id}", name="revision reject")
def revision_reject(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision: Revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    revision.approved = False
    revision.discarded = False
    revision.discarded_by = "opennem.admin"
    revision.discarded_at = datetime.now()

    session.add(revision)
    session.commit()

    response = UpdateResponse(success=True, record=revision)

    return response

