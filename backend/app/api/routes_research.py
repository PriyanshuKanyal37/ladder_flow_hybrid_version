import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.auth_config import current_active_user
from app.db.models import User
from app.schemas.requests import ResearchRequest
from app.services.perplexity_service import research_topic
from app.services.rate_limiter import check_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/research")
async def research_endpoint(
    request: ResearchRequest,
    user: User = Depends(current_active_user),
):
    check_rate_limit(user.id, "research")
    logger.info("research request keyword=%s user=%s", request.keyword, user.id)
    try:
        result = research_topic(request.keyword)
        return {"output": result}
    except Exception as exc:
        logger.exception("research endpoint failed")
        raise HTTPException(status_code=500, detail="Research failed. Please try again.") from exc
