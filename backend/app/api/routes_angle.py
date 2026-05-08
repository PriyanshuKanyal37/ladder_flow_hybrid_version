"""
POST /api/refine-angle — synthesize a custom interview angle from user input.

Used by the Angles step on the frontend (/discover/trending) when a user
types a free-form direction in the "Or type your own angle" field. Combines:

  - The user's typed text (the new direction they want)
  - The full research context (title, deep_context, key_insights)
  - The currently-selected angle's title + summary (if any)

Returns a single refined angle: { title, summary, quote, tags } that can
slot in as a fifth card on the Angles UI.

Uses Claude Sonnet 4.6 with prompt caching — same model used elsewhere.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.auth_config import current_active_user
from app.core.config import settings
from app.db.models import User
from app.services.rate_limiter import check_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)

# Module-level async client with timeout — same pattern as routes_brain.
_anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=httpx.Timeout(30.0, connect=5.0),
)


class _SelectedAngle(BaseModel):
    title: str | None = None
    summary: str | None = None


class _ResearchCtx(BaseModel):
    title: str | None = None
    deep_context: str | None = None
    key_insights: list[str] = Field(default_factory=list)
    discussion_points: list[str] = Field(default_factory=list)


class RefineAngleRequest(BaseModel):
    user_input: str
    research_context: _ResearchCtx
    selected_angle: _SelectedAngle | None = None


SYSTEM_INSTRUCTION = (
    "You are an editorial strategist for a B2B founder podcast. "
    "Given a research brief and a user-supplied creative direction, you "
    "synthesize ONE focused interview angle. The angle must be specific, "
    "non-generic, and grounded in the research. Return ONLY a JSON object."
)


def _build_prompt(req: RefineAngleRequest) -> str:
    research_block = (
        f"Title: {req.research_context.title or '(none)'}\n"
        f"Deep context:\n{(req.research_context.deep_context or '')[:4000]}\n"
        f"Key insights:\n- "
        + "\n- ".join((req.research_context.key_insights or [])[:6])
    )
    selected_block = ""
    if req.selected_angle and (req.selected_angle.title or req.selected_angle.summary):
        selected_block = (
            "\n\n[CURRENTLY SELECTED ANGLE]\n"
            f"Title: {req.selected_angle.title or ''}\n"
            f"Summary: {req.selected_angle.summary or ''}\n"
        )

    return (
        "Synthesize one custom interview angle from the user's direction below.\n\n"
        "[RESEARCH BRIEF]\n"
        f"{research_block}\n"
        f"{selected_block}\n\n"
        f"[USER DIRECTION]\n{req.user_input.strip()}\n\n"
        "Return ONE angle as a JSON object with exactly these keys:\n"
        "  - title: 8-14 words, sharp, non-generic, leads the interview\n"
        "  - summary: 2 short sentences explaining the angle\n"
        "  - quote: a one-line provocative quote that captures the angle (in straight quotes)\n"
        "  - tags: array of 2 short tags (e.g., 'Strategy', 'Counter-narrative')\n\n"
        "Constraints:\n"
        "  - Stay grounded in the research brief — no fabricated stats\n"
        "  - Honour the user's direction as the primary frame\n"
        "  - Title and summary must NOT be a generic 'how to' phrasing\n"
        "  - Output the JSON only — no markdown, no preamble"
    )


def _extract_json(raw: str) -> dict[str, Any]:
    """Pull the first balanced {...} object out of Claude's response."""
    raw = raw.strip()
    # Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Strip markdown fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    # First {...} block
    start = raw.find("{")
    if start == -1:
        raise ValueError("no JSON object in response")
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError("unterminated JSON object")


@router.post("/api/refine-angle")
async def refine_angle(
    req: RefineAngleRequest,
    user: User = Depends(current_active_user),
):
    """Generate one custom angle. Rate-limited under the 'research' policy
    (10 per hour) since it costs LLM tokens."""
    user_input = (req.user_input or "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="user_input required")
    if len(user_input) > 500:
        raise HTTPException(status_code=400, detail="user_input too long (max 500 chars)")

    check_rate_limit(user.id, "research")

    prompt = _build_prompt(req)
    try:
        response = await _anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            temperature=0.7,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        logger.exception("refine-angle Claude call failed")
        raise HTTPException(status_code=502, detail="Angle synthesis failed") from exc

    # Claude returns a list of content blocks — the first text block is the JSON.
    text_parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
    if not text_parts:
        raise HTTPException(status_code=502, detail="Empty response from model")
    raw = text_parts[0]

    try:
        data = _extract_json(raw)
    except Exception:
        logger.warning("refine-angle: could not parse JSON from response: %r", raw[:200])
        raise HTTPException(status_code=502, detail="Model returned malformed JSON")

    # Defensive shape — drop any keys we don't expect, fill defaults if missing.
    title = str(data.get("title") or user_input)[:160]
    summary = str(data.get("summary") or "Custom angle synthesized from your direction.")[:600]
    quote = str(data.get("quote") or f'"{user_input}"')[:240]
    tags_raw = data.get("tags") or ["Custom"]
    if not isinstance(tags_raw, list):
        tags_raw = ["Custom"]
    tags = [str(t)[:24] for t in tags_raw if t][:3]
    if not tags:
        tags = ["Custom"]

    return {
        "angle": {
            "id": "angle-custom-generated",
            "title": title,
            "summary": summary,
            "quote": quote,
            "tags": tags,
            "match": "Custom",
            "trending": False,
            "generated": True,
        },
    }
