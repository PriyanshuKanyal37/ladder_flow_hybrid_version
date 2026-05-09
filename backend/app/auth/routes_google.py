import logging
import os
import secrets
import uuid

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from httpx_oauth.clients.google import GoogleOAuth2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_config import get_jwt_strategy
from app.db.database import get_async_session
from app.db.models import User

logger = logging.getLogger(__name__)

_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Public-facing backend URL — needed so Google can redirect back.
# Set BACKEND_PUBLIC_URL in prod (e.g. https://api.ladderflow.com).
_BACKEND_PUBLIC_URL = os.getenv(
    "BACKEND_PUBLIC_URL", os.getenv("BACKEND_INTERNAL_URL", "http://localhost:8000")
)

_google = GoogleOAuth2(_CLIENT_ID, _CLIENT_SECRET)
_CALLBACK_URL = f"{_BACKEND_PUBLIC_URL}/auth/google/callback"

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/authorize")
async def google_authorize():
    """Redirect browser to Google consent screen."""
    state = secrets.token_urlsafe(32)
    url = await _google.get_authorization_url(
        _CALLBACK_URL,
        state=state,
        scope=["openid", "email", "profile"],
    )
    response = RedirectResponse(url)
    response.set_cookie(
        "oauth_state", state, max_age=600, httponly=True, samesite="lax"
    )
    return response


@router.get("/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Exchange code → JWT, then redirect browser to frontend with token."""
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or cookie_state != state:
        return RedirectResponse(f"{_FRONTEND_URL}/login?error=invalid_state")

    # Exchange auth code for Google access token
    try:
        token_data = await _google.get_access_token(code, _CALLBACK_URL)
    except Exception as exc:
        logger.error("Google OAuth token exchange failed: %s", exc)
        return RedirectResponse(f"{_FRONTEND_URL}/login?error=oauth_failed")

    # Fetch user info from Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
    if resp.status_code != 200:
        return RedirectResponse(f"{_FRONTEND_URL}/login?error=userinfo_failed")

    info = resp.json()
    email: str | None = info.get("email")
    full_name: str = info.get("name", "")

    if not email:
        return RedirectResponse(f"{_FRONTEND_URL}/login?error=no_email")

    # Find or create user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        from fastapi_users.password import PasswordHelper
        _ph = PasswordHelper()
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=_ph.hash(secrets.token_urlsafe(32)),
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created new user %s via Google OAuth.", user.id)
    else:
        logger.info("Existing user %s logged in via Google OAuth.", user.id)

    # Issue JWT using the same strategy as password login
    strategy = get_jwt_strategy()
    token = await strategy.write_token(user)

    redirect = RedirectResponse(f"{_FRONTEND_URL}/auth/callback?token={token}")
    redirect.delete_cookie("oauth_state")
    return redirect
