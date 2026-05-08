"""
GET /api/tts-credits — pre-flight credit check for every configured TTS provider.

Returned to /interview/new BEFORE the user starts a session, so we can show a
warning banner when a provider is running out of credits and block selection
of fully-exhausted providers.

Response shape:
{
  "providers": {
    "elevenlabs": {
      "available": true,           # has API key + has remaining credits
      "configured": true,          # API key is set in .env
      "remaining_chars": 4521,     # chars left this billing cycle (provider-specific)
      "limit_chars": 10000,        # total chars allowed this cycle
      "warning": true,             # < 20% remaining
      "exhausted": false,          # 0 chars left
      "error": null                # message if status check itself failed
    },
    "cartesia":  { ... },
    "inworld":   { ... },
    "deepgram":  { ... }
  }
}

Note: only ElevenLabs exposes a subscription/credit endpoint that's reliable.
For the others we report `configured` (API key present) and let runtime errors
surface mid-call. Future enhancement: add provider-specific billing API checks.
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends

from app.auth.auth_config import current_active_user
from app.core.config import settings
from app.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


# Below this fraction we set warning=true (UI shows yellow "low credits" badge)
WARNING_THRESHOLD = 0.20

# Conversion constants for human-friendly "minutes of speech" estimates.
# 150 words/min × ~6 chars/word (incl. spaces) ≈ 900 chars/min agent speech.
CHARS_PER_MIN = 900
# Deepgram Aura-2 pricing: $0.030 / 1000 chars  →  $0.027 / minute
DEEPGRAM_USD_PER_MIN = 0.027


async def _check_elevenlabs() -> dict:
    """
    Query ElevenLabs `/v1/user/subscription` for character usage.
    Returns remaining character allowance for this billing cycle.
    """
    if not settings.ELEVENLABS_API_KEY:
        return {
            "available": False,
            "configured": False,
            "remaining_chars": 0,
            "limit_chars": 0,
            "warning": False,
            "exhausted": False,
            "error": "API key not configured",
        }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
            )
        if resp.status_code != 200:
            # Fail-open: most common cause is API key without `user_read` scope.
            # Don't block selection — let runtime surface real failures.
            return {
                "available": True,
                "configured": True,
                "remaining_chars": None,
                "limit_chars": None,
                "warning": False,
                "exhausted": False,
                "error": (
                    "Credit check unavailable — your API key may lack the "
                    "`user_read` permission. Voice will still work."
                ),
            }
        data = resp.json()
        used = int(data.get("character_count", 0))
        limit = int(data.get("character_limit", 0))
        remaining = max(0, limit - used)
        warning = limit > 0 and (remaining / limit) < WARNING_THRESHOLD
        exhausted = limit > 0 and remaining <= 0
        return {
            "available": not exhausted,
            "configured": True,
            "remaining_chars": remaining,
            "limit_chars": limit,
            "warning": warning,
            "exhausted": exhausted,
            "error": None,
            "estimated_minutes_remaining": round(remaining / CHARS_PER_MIN, 1),
        }
    except Exception as exc:
        logger.warning("ElevenLabs credit check failed: %s", exc)
        return {
            "available": True,  # fail open — let interview start, runtime will surface real failure
            "configured": True,
            "remaining_chars": 0,
            "limit_chars": 0,
            "warning": False,
            "exhausted": False,
            "error": "credit check failed",
        }


async def _check_deepgram() -> dict:
    """
    Real-time Deepgram balance check.

    Steps:
      1. GET /v1/projects → fetch projects (need project_id)
      2. GET /v1/projects/{id}/balances → fetch USD balance
    Returns remaining USD as `remaining_chars` (re-purposed) for unified shape.
    """
    if not settings.DEEPGRAM_API_KEY:
        return {
            "available": False,
            "configured": False,
            "remaining_chars": 0,
            "limit_chars": 0,
            "warning": False,
            "exhausted": False,
            "error": "API key not configured",
        }

    headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            proj_resp = await client.get("https://api.deepgram.com/v1/projects", headers=headers)
            if proj_resp.status_code != 200:
                return {
                    "available": True,  # fail open
                    "configured": True,
                    "remaining_chars": None,
                    "limit_chars": None,
                    "warning": False,
                    "exhausted": False,
                    "error": f"Deepgram projects returned {proj_resp.status_code}",
                }
            projects = proj_resp.json().get("projects", [])
            if not projects:
                return {
                    "available": True,
                    "configured": True,
                    "remaining_chars": None,
                    "limit_chars": None,
                    "warning": False,
                    "exhausted": False,
                    "error": "No Deepgram project found",
                }
            project_id = projects[0]["project_id"]

            bal_resp = await client.get(
                f"https://api.deepgram.com/v1/projects/{project_id}/balances",
                headers=headers,
            )
            if bal_resp.status_code != 200:
                return {
                    "available": True,  # fail open — most likely missing billing:read scope
                    "configured": True,
                    "remaining_chars": None,
                    "limit_chars": None,
                    "warning": False,
                    "exhausted": False,
                    "error": (
                        "Credit check unavailable — your API key may lack the "
                        "`billing:read` scope. Voice will still work."
                    ),
                }
            balances = bal_resp.json().get("balances", [])
            if not balances:
                return {
                    "available": True,
                    "configured": True,
                    "remaining_chars": None,
                    "limit_chars": None,
                    "warning": False,
                    "exhausted": False,
                    "error": None,
                }
            # Sum the remaining USD across all balance buckets.
            total_amount = sum(float(b.get("amount", 0) or 0) for b in balances)
            # Keep "remaining_chars" name for shape compat, but it's USD here.
            # UI distinguishes via the unit info below.
            warning = total_amount > 0 and total_amount < 1.00  # < $1 left
            exhausted = total_amount <= 0
            return {
                "available": not exhausted,
                "configured": True,
                "remaining_chars": None,
                "limit_chars": None,
                "warning": warning,
                "exhausted": exhausted,
                "error": None,
                "remaining_usd": round(total_amount, 2),
                "estimated_minutes_remaining": round(total_amount / DEEPGRAM_USD_PER_MIN, 0),
            }
    except Exception as exc:
        logger.warning("Deepgram credit check failed: %s", exc)
        return {
            "available": True,  # fail open
            "configured": True,
            "remaining_chars": None,
            "limit_chars": None,
            "warning": False,
            "exhausted": False,
            "error": "credit check failed",
        }


def _basic_status(api_key: str, provider_name: str, no_billing_api: bool = False) -> dict:
    """
    For providers without a public billing/credit API (Cartesia, Inworld).
    Returns `available` based on key presence; surface a hint to the UI that
    credits can only be checked in the provider's web dashboard.
    """
    configured = bool(api_key)
    return {
        "available": configured,
        "configured": configured,
        "remaining_chars": None,
        "limit_chars": None,
        "warning": False,
        "exhausted": False,
        "error": (
            None
            if configured and not no_billing_api
            else (
                f"{provider_name} doesn't expose a public billing API — check usage in their web dashboard"
                if no_billing_api
                else f"{provider_name} API key not configured"
            )
        ),
        "credit_check_supported": not no_billing_api,
    }


@router.get("/api/tts-credits")
async def tts_credits(user: User = Depends(current_active_user)):
    """
    Per-provider credit status. Frontend calls this on /interview/new mount.

    Cache-friendly: response changes slowly, frontend can cache 60s. The
    underlying ElevenLabs API call is ~150-300ms — well under the page's
    initial-load budget.
    """
    # Real-time checks where supported (ElevenLabs + Deepgram).
    # Cartesia + Inworld don't expose public billing APIs — check key presence only.
    elevenlabs_status = await _check_elevenlabs()
    deepgram_status = await _check_deepgram()

    return {
        "providers": {
            "elevenlabs": elevenlabs_status,
            "deepgram": deepgram_status,
            "cartesia": _basic_status(settings.CARTESIA_API_KEY, "Cartesia", no_billing_api=True),
            "inworld": _basic_status(settings.INWORLD_API_KEY, "Inworld", no_billing_api=True),
        },
    }
