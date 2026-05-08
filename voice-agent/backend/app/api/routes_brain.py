import logging
import uuid

import httpx
from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_config import current_active_user
from app.core.config import settings
from app.db.database import get_async_session
from app.db.models import MemoryItem, UserProfile
from app.services import neo4j_service
from app.services.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain"])

TRUST_MAP = {"A": "high", "B": "medium", "C": "low"}
TYPE_MAP = {"proof": "proof_point"}

# Module-level async clients with explicit timeouts.
# AsyncOpenAI / AsyncAnthropic share underlying httpx pool — safe singletons.
_openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=httpx.Timeout(60.0, connect=5.0),
)
_anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=httpx.Timeout(60.0, connect=5.0),
)


class BrainChatRequest(BaseModel):
    query: str


async def _require_onboarded_user(
    user=Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalars().first()
    if not profile or not profile.onboarding_completed:
        raise HTTPException(
            status_code=403,
            detail="Complete onboarding before accessing Digital Brain.",
        )
    return user


@router.get("/graph")
async def get_brain_graph(
    user=Depends(_require_onboarded_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Return the user's Neo4j knowledge graph for visualization."""
    try:
        user_id = str(user.id)
        data = neo4j_service.get_user_graph(user_id)

        # Read-repair for older users whose onboarding data exists in Neon but
        # was never synced to Neo4j (e.g. historical silent failures).
        if not data["nodes"]:
            profile_result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            profile = profile_result.scalars().first()
            if profile and profile.onboarding_completed:
                try:
                    neo4j_service.sync_onboarding_to_neo4j(
                        user_id=user_id,
                        niche=profile.niche,
                        industry=profile.industry,
                        content_tone=profile.content_tone,
                        target_audience=profile.target_audience,
                        display_name=user.full_name,
                        bio=profile.bio,
                        icp=profile.icp,
                        offer=profile.offer,
                        pain_solved=profile.pain_solved,
                        differentiator=profile.differentiator,
                        primary_goal=profile.primary_goal,
                        key_themes=profile.key_themes,
                        platforms=profile.platforms,
                    )
                    data = neo4j_service.get_user_graph(user_id)
                except Exception as sync_error:
                    logger.warning(
                        "Neo4j read-repair sync failed for user %s: %s",
                        user_id,
                        sync_error,
                    )
        return data
    except Exception as e:
        logger.warning(f"Neo4j graph fetch failed for user {user.id}: {e}")
        return {"nodes": [], "links": []}


@router.get("/memories")
async def list_brain_memories(
    user=Depends(_require_onboarded_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        text("""
            SELECT mi.id, mi.type, mi.content_text, mi.trust_tier, mi.privacy_mode,
                   mi.created_at, COALESCE(i.topic, '') AS topic
            FROM memory_items mi
            LEFT JOIN interviews i ON mi.source_interview_id = i.id
            WHERE mi.user_id = :user_id AND mi.is_active = true
            ORDER BY mi.created_at DESC
        """),
        {"user_id": str(user.id)},
    )
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "type": TYPE_MAP.get(r.type, r.type),
            "content": r.content_text,
            "topic": r.topic,
            "trust_tier": TRUST_MAP.get(r.trust_tier, "medium"),
            "visibility": r.privacy_mode,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


_TIER_ALLOWED = {"A", "B", "C"}
_PRIVACY_ALLOWED = {"private", "publishable"}


class MemoryPatchRequest(BaseModel):
    """Allow partial edits to a memory. Any field omitted is left unchanged."""
    content_text: str | None = None
    trust_tier: str | None = None  # "A" | "B" | "C"
    privacy_mode: str | None = None  # "private" | "publishable"


async def _load_owned_memory(
    memory_id: str,
    user_id,
    session: AsyncSession,
) -> MemoryItem:
    try:
        mem_uuid = uuid.UUID(memory_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid memory id")
    stmt = select(MemoryItem).where(
        MemoryItem.id == mem_uuid,
        MemoryItem.user_id == user_id,
    )
    result = await session.execute(stmt)
    mem = result.scalars().first()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    return mem


@router.patch("/memories/{memory_id}")
async def update_brain_memory(
    memory_id: str,
    req: MemoryPatchRequest,
    user=Depends(_require_onboarded_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Edit a memory's content, trust tier, or privacy mode.
    Updates Postgres + mirrors changes to the Neo4j Memory node.
    """
    mem = await _load_owned_memory(memory_id, user.id, session)

    if req.trust_tier is not None and req.trust_tier not in _TIER_ALLOWED:
        raise HTTPException(status_code=400, detail="trust_tier must be A, B, or C")
    if req.privacy_mode is not None and req.privacy_mode not in _PRIVACY_ALLOWED:
        raise HTTPException(status_code=400, detail="privacy_mode must be 'private' or 'publishable'")

    if req.content_text is not None:
        mem.content_text = req.content_text
    if req.trust_tier is not None:
        mem.trust_tier = req.trust_tier
    if req.privacy_mode is not None:
        mem.privacy_mode = req.privacy_mode

    await session.commit()
    await session.refresh(mem)

    # Mirror to Neo4j (non-fatal on failure — Postgres is source of truth).
    try:
        neo4j_service.update_memory_node(
            neon_id=str(mem.id),
            content=req.content_text,
            trust_tier=req.trust_tier,
        )
    except Exception as exc:
        logger.warning("Neo4j memory update failed for %s: %s", mem.id, exc)

    return {
        "id": str(mem.id),
        "type": TYPE_MAP.get(mem.type, mem.type),
        "content": mem.content_text,
        "trust_tier": TRUST_MAP.get(mem.trust_tier, "medium"),
        "visibility": mem.privacy_mode,
    }


@router.delete("/memories/{memory_id}", status_code=204)
async def delete_brain_memory(
    memory_id: str,
    user=Depends(_require_onboarded_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Soft-delete a memory: sets is_active=false in Postgres so the row is
    excluded from all reads (memory pack, list, search) but kept for audit.
    Hard-removes the Neo4j Memory node so the graph stays clean.
    """
    mem = await _load_owned_memory(memory_id, user.id, session)
    mem.is_active = False
    await session.commit()

    try:
        neo4j_service.delete_memory_node(neon_id=str(mem.id))
    except Exception as exc:
        logger.warning("Neo4j memory delete failed for %s: %s", mem.id, exc)

    return None


@router.post("/chat")
async def brain_chat(
    req: BrainChatRequest,
    user=Depends(_require_onboarded_user),
    session: AsyncSession = Depends(get_async_session),
):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    check_rate_limit(user.id, "brain_chat")

    count_result = await session.execute(
        text(
            "SELECT COUNT(*) FROM memory_items "
            "WHERE user_id = :uid AND is_active = true AND embedding IS NOT NULL"
        ),
        {"uid": str(user.id)},
    )
    if not count_result.scalar():
        return {
            "answer": "You don't have any stored memories yet. Complete some interviews first to build your Digital Brain.",
            "citations": [],
        }

    # Async + timeout — never blocks event loop, never hangs.
    emb_response = await _openai_client.embeddings.create(
        input=req.query,
        model="text-embedding-3-small",
    )
    emb = emb_response.data[0].embedding
    emb_str = "[" + ",".join(str(x) for x in emb) + "]"

    # Parameterized SQL — vector is bound, not interpolated.
    result = await session.execute(
        text("""
            SELECT mi.content_text, mi.type, COALESCE(i.topic, '') AS topic
            FROM memory_items mi
            LEFT JOIN interviews i ON mi.source_interview_id = i.id
            WHERE mi.user_id = :user_id
              AND mi.is_active = true
              AND mi.embedding IS NOT NULL
            ORDER BY mi.embedding <=> CAST(:emb AS vector)
            LIMIT 5
        """),
        {"user_id": str(user.id), "emb": emb_str},
    )
    memories = result.fetchall()

    context = "\n".join(f"- [{m.type}] {m.content_text}" for m in memories)
    citations = list({m.topic for m in memories if m.topic})

    response = await _anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                "You are a Digital Brain assistant. Answer the user's question using ONLY the memories below. "
                "Be concise (2-4 sentences). If the memories don't directly answer the question, say so honestly.\n\n"
                f"Memories:\n{context}\n\n"
                f"Question: {req.query}\n\nAnswer:"
            ),
        }],
    )
    answer = response.content[0].text

    return {"answer": answer, "citations": citations}
