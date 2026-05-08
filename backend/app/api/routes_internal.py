"""
Internal service-to-service endpoints.

These routes are called by agent_worker.py (same host) and are protected by
X-Internal-Secret header — NOT by FastAPI-Users auth.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_async_session
from app.db.models import Interview

router = APIRouter(prefix="/internal", tags=["internal"])


def _verify_secret(x_internal_secret: str = Header(...)) -> None:
    if not settings.INTERNAL_SECRET:
        raise HTTPException(status_code=503, detail="Internal secret not configured")
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/interviews/{interview_id}/mark-ended")
async def mark_interview_ended(
    interview_id: uuid.UUID,
    _: None = Depends(_verify_secret),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Called by agent_worker.py when the participant disconnects from the LiveKit
    room. Transitions the interview to DRAFT so it appears in the sessions list
    as resumable. Idempotent: COMPLETED/FAILED are terminal and ignored.
    """
    result = await session.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="interview_not_found")

    if interview.status not in ("COMPLETED", "FAILED"):
        interview.status = "DRAFT"
        interview.last_saved_at = datetime.now(timezone.utc)
        await session.commit()

    return {"status": "ok", "interview_status": interview.status}
