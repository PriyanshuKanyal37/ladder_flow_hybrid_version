import json
from datetime import datetime, timezone
import uuid
import logging

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_config import current_active_user
from app.core.config import settings
from app.db.database import get_async_session
from app.db.models import User, UserProfile, Interview
from app.schemas.requests import TopicRequest, AgentDispatchRequest, ExtractRequest
from app.services import memory_pack_builder, memory_extractor
from app.services.agent_config import build_agent_config
from app.services.livekit_token import create_room_token, generate_room_name
from app.services.rate_limiter import check_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)


def _safe_load_outline(outline: str | None) -> dict:
    if not outline:
        return {}
    try:
        parsed = json.loads(outline)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _assert_livekit_config() -> None:
    if not settings.LIVEKIT_URL or not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LiveKit is not configured on the backend",
        )


@router.post("/agent-config")
async def agent_config(
    req: TopicRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Build interview config and persist an interview row before voice starts.

    Returns a LiveKit session token. Dispatch is intentionally separated into
    /agent-dispatch to avoid race conditions after the client joins the room.
    """
    _assert_livekit_config()
    check_rate_limit(user.id, "voice_start")

    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    result = await session.execute(stmt)
    profile = result.scalars().first()

    topic_title = req.get_topic_title()
    resolved_user_name = req.get_user_name()
    if resolved_user_name == "Guest" and user.full_name:
        resolved_user_name = user.full_name

    try:
        memory_pack = await memory_pack_builder.build(
            session=session,
            user_id=str(user.id),
            topic=topic_title,
        )
    except Exception as exc:
        logger.warning("Memory pack build failed, continuing without memory context: %s", exc)
        memory_pack = ""

    config = build_agent_config(
        topic_title=topic_title,
        global_context=req.global_context or "",
        why_this_matters=req.why_this_matters or "",
        key_questions=req.key_questions or [],
        user_name=resolved_user_name,
        full_name=user.full_name,
        bio=profile.bio if profile else None,
        niche=profile.niche if profile else None,
        industry=profile.industry if profile else None,
        target_audience=profile.target_audience if profile else None,
        icp=profile.icp if profile else None,
        offer=profile.offer if profile else None,
        pain_solved=profile.pain_solved if profile else None,
        differentiator=profile.differentiator if profile else None,
        content_tone=profile.content_tone if profile else None,
        tone=profile.tone if profile else None,
        proof_points=profile.proof_points if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        key_themes=profile.key_themes if profile else None,
        platforms=profile.platforms if profile else None,
        memory_pack=memory_pack,
    )

    research_context = {
        "title": config["topicTitle"],
        "deep_context": req.global_context or "",
        "why_this_matters": req.why_this_matters or "",
        "key_questions": req.key_questions or [],
        "discussion_points": req.key_questions or [],
        "key_insights": [req.why_this_matters] if req.why_this_matters else [],
    }

    room_name = generate_room_name(str(user.id), topic_title)

    interview = Interview(
        user_id=user.id,
        topic=config["topicTitle"],
        status="INTERVIEWING",
        outline=json.dumps(
            {
                "path": "livekit",
                "room_name": room_name,
                "dispatch_sent_at": None,
                "dispatch_metadata": {
                    "system_prompt": config["systemPrompt"],
                    "greeting": config["greeting"],
                    "user_name": config["userName"],
                    "topic_title": config["topicTitle"],
                    "tts_provider": req.tts_provider,
                },
                "research_context": research_context,
            }
        ),
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)

    # Backfill interview_id into dispatch_metadata now that we have the PK
    _outline = json.loads(interview.outline)
    _outline["dispatch_metadata"]["interview_id"] = str(interview.id)
    interview.outline = json.dumps(_outline)
    await session.commit()

    token = create_room_token(
        room_name=room_name,
        participant_identity=str(user.id),
        participant_name=config["userName"],
        system_prompt=config["systemPrompt"],
        topic_title=config["topicTitle"],
        user_name=config["userName"],
        interview_id=str(interview.id),
    )

    return {
        "provider": "livekit",
        "token": token,
        "livekitUrl": settings.LIVEKIT_URL,
        "roomName": room_name,
        "topicTitle": config["topicTitle"],
        "userName": config["userName"],
        "greeting": config["greeting"],
        "interviewId": str(interview.id),
    }


@router.post("/agent-dispatch")
async def agent_dispatch(
    req: AgentDispatchRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Idempotent dispatch endpoint called only after the client has joined the room.
    """
    _assert_livekit_config()

    try:
        interview_uuid = uuid.UUID(req.interview_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview_id")

    stmt = (
        select(Interview)
        .where(
            Interview.id == interview_uuid,
            Interview.user_id == user.id,
        )
        .with_for_update()
    )
    result = await session.execute(stmt)
    interview = result.scalars().first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    outline = _safe_load_outline(interview.outline)
    room_name = outline.get("room_name")
    dispatch_metadata = outline.get("dispatch_metadata", {})

    if not room_name or not dispatch_metadata:
        raise HTTPException(status_code=400, detail="Interview missing dispatch metadata")

    if outline.get("dispatch_sent_at"):
        return {"status": "already_dispatched", "roomName": room_name}

    from livekit import api as lk_api_module

    lk_client = lk_api_module.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    try:
        await lk_client.agent_dispatch.create_dispatch(
            lk_api_module.CreateAgentDispatchRequest(
                agent_name="ladderflow-host",
                room=room_name,
                metadata=json.dumps(dispatch_metadata),
            )
        )
    finally:
        await lk_client.aclose()

    outline["dispatch_sent_at"] = datetime.now(timezone.utc).isoformat()
    interview.outline = json.dumps(outline)
    interview.status = "INTERVIEWING"
    await session.commit()

    return {"status": "dispatched", "roomName": room_name}


@router.post("/agent-config/resume")
async def agent_config_resume(
    req: AgentDispatchRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Resume an existing DRAFT interview.

    Loads the original research context + prior transcript from the interview
    row, re-runs the prompt pipeline with a PRIOR_CONVERSATION block, mints a
    fresh LiveKit token, and flips the status back to INTERVIEWING. The Interview
    row is reused so resumed sessions accumulate in one continuous row.
    """
    _assert_livekit_config()
    check_rate_limit(user.id, "voice_start")

    try:
        interview_uuid = uuid.UUID(req.interview_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview_id")

    stmt = select(Interview).where(
        Interview.id == interview_uuid,
        Interview.user_id == user.id,
    )
    result = await session.execute(stmt)
    interview = result.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status in ("COMPLETED", "FAILED"):
        raise HTTPException(status_code=400, detail="This interview is already closed")

    outline = _safe_load_outline(interview.outline)
    research_context = outline.get("research_context") or {}
    prior_metadata = outline.get("dispatch_metadata") or {}

    # Profile reload — onboarding may have changed since the original call
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    profile_result = await session.execute(profile_stmt)
    profile = profile_result.scalars().first()

    topic_title = interview.topic or research_context.get("title") or "General Discussion"
    resolved_user_name = prior_metadata.get("user_name") or user.full_name or "Guest"

    try:
        memory_pack = await memory_pack_builder.build(
            session=session,
            user_id=str(user.id),
            topic=topic_title,
        )
    except Exception as exc:
        logger.warning("Memory pack build failed on resume: %s", exc)
        memory_pack = ""

    # Trim to the last ~8000 chars so the prompt stays bounded
    prior_transcript = (interview.raw_transcript or "").strip()
    if len(prior_transcript) > 8000:
        prior_transcript = "[...earlier portion truncated...]\n" + prior_transcript[-8000:]

    config = build_agent_config(
        topic_title=topic_title,
        global_context=research_context.get("deep_context") or "",
        why_this_matters=research_context.get("why_this_matters") or "",
        key_questions=research_context.get("key_questions") or research_context.get("discussion_points") or [],
        user_name=resolved_user_name,
        full_name=user.full_name,
        bio=profile.bio if profile else None,
        niche=profile.niche if profile else None,
        industry=profile.industry if profile else None,
        target_audience=profile.target_audience if profile else None,
        icp=profile.icp if profile else None,
        offer=profile.offer if profile else None,
        pain_solved=profile.pain_solved if profile else None,
        differentiator=profile.differentiator if profile else None,
        content_tone=profile.content_tone if profile else None,
        tone=profile.tone if profile else None,
        proof_points=profile.proof_points if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        key_themes=profile.key_themes if profile else None,
        platforms=profile.platforms if profile else None,
        memory_pack=memory_pack,
        prior_conversation=prior_transcript or None,
    )

    room_name = generate_room_name(str(user.id), topic_title)

    resume_research_context = {
        "title": topic_title,
        "deep_context": research_context.get("deep_context") or "",
        "key_insights": research_context.get("key_insights") or [],
        "discussion_points": (
            research_context.get("discussion_points")
            or research_context.get("key_questions")
            or []
        ),
        "contrarian_angles": research_context.get("contrarian_angles") or [],
        "sources": research_context.get("sources") or [],
    }

    tts_provider = prior_metadata.get("tts_provider", "elevenlabs")

    outline["room_name"] = room_name
    outline["dispatch_sent_at"] = None
    outline["dispatch_metadata"] = {
        "system_prompt": config["systemPrompt"],
        "greeting": config["greeting"],
        "user_name": config["userName"],
        "topic_title": config["topicTitle"],
        "interview_id": str(interview.id),
        "tts_provider": tts_provider,
    }
    outline["resumed_at"] = datetime.now(timezone.utc).isoformat()
    interview.outline = json.dumps(outline)
    interview.status = "INTERVIEWING"
    await session.commit()
    await session.refresh(interview)

    prior_transcript = interview.raw_transcript or ""

    token = create_room_token(
        room_name=room_name,
        participant_identity=str(user.id),
        participant_name=config["userName"],
        system_prompt=config["systemPrompt"],
        topic_title=config["topicTitle"],
        user_name=config["userName"],
        interview_id=str(interview.id),
    )

    return {
        "provider": "livekit",
        "token": token,
        "livekitUrl": settings.LIVEKIT_URL,
        "roomName": room_name,
        "topicTitle": config["topicTitle"],
        "userName": config["userName"],
        "greeting": config["greeting"],
        "interviewId": str(interview.id),
        "resumed": True,
        "priorTranscript": prior_transcript,
        "researchContext": resume_research_context,
    }


@router.post("/extract")
async def extract(
    req: ExtractRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Fire background memory extraction for an already-saved interview.
    """
    try:
        interview_uuid = uuid.UUID(req.interview_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview_id")

    interview_id = str(interview_uuid)
    transcript = req.transcript
    topic = req.topic or "General Discussion"

    if not interview_id or not transcript:
        return {"status": "skipped", "reason": "missing interview_id or transcript"}

    stmt = select(Interview).where(Interview.id == interview_uuid, Interview.user_id == user.id)
    result = await session.execute(stmt)
    interview = result.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    background_tasks.add_task(
        _run_extraction,
        interview_id=str(interview_id),
        user_id=str(user.id),
        transcript=transcript,
        topic=topic,
    )
    return {"status": "queued"}


async def _run_extraction(
    interview_id: str,
    user_id: str,
    transcript: str,
    topic: str,
):
    """Background task - creates its own DB session for extraction."""
    from app.db.database import async_session_maker

    async with async_session_maker() as session:
        await memory_extractor.extract_and_save(
            session=session,
            interview_id=interview_id,
            user_id=user_id,
            transcript=transcript,
            topic=topic,
        )
