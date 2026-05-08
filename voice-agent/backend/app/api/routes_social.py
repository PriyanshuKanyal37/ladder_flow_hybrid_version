from fastapi import APIRouter, Depends

from app.auth.auth_config import current_active_user
from app.db.models import User
from app.schemas.requests import LinkedInRequest, TwitterRequest
from app.services.linkedin_writer import generate_linkedin_post
from app.services.rate_limiter import check_rate_limit
from app.services.twitter_writer import generate_twitter_thread

router = APIRouter()


@router.post("/generate-linkedin")
def generate_linkedin(req: LinkedInRequest, user: User = Depends(current_active_user)):
    check_rate_limit(user.id, "legacy_social_generate")
    post = generate_linkedin_post(
        topic=req.topic,
        user_name=req.userName or "Guest",
        transcript=req.transcript,
    )
    return {"linkedin": post}


@router.post("/generate-twitter")
def generate_twitter(req: TwitterRequest, user: User = Depends(current_active_user)):
    check_rate_limit(user.id, "legacy_social_generate")
    post = generate_twitter_thread(
        topic=req.topic,
        user_name=req.userName or "Guest",
        transcript=req.transcript,
    )
    return {"twitter": post}


# Newsletter generation removed from product. Endpoint deleted.
# Old caller paths return 404 — frontend `/api/content/newsletter` proxy
# also removed. Re-enable by restoring `NewsletterRequest` import + handler.
