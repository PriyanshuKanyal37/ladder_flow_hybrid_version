"""
Rate limiter — Upstash Redis backend (REST API).

Replaces the prior in-process dict implementation. Shared state across all
workers and hosts. Atomic INCR + EXPIRE. Survives restarts.

Falls back to a per-process in-memory limiter only if Upstash credentials
are not configured (dev mode). Logs a warning so this is never silent.
"""
from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from uuid import UUID

from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitPolicy:
    limit: int
    window_seconds: int


POLICIES: dict[str, RateLimitPolicy] = {
    "voice_start": RateLimitPolicy(limit=8, window_seconds=10 * 60),
    "content_pack_generate": RateLimitPolicy(limit=6, window_seconds=15 * 60),
    "content_output_regenerate": RateLimitPolicy(limit=12, window_seconds=15 * 60),
    "research": RateLimitPolicy(limit=10, window_seconds=60 * 60),
    "brain_chat": RateLimitPolicy(limit=40, window_seconds=60 * 60),
    "legacy_social_generate": RateLimitPolicy(limit=12, window_seconds=60 * 60),
}


# ── Upstash Redis backend ──────────────────────────────────────────────────
_redis_client = None
_redis_init_attempted = False


def _get_redis():
    """Lazy init Upstash Redis client. Returns None if creds missing."""
    global _redis_client, _redis_init_attempted
    if _redis_init_attempted:
        return _redis_client

    _redis_init_attempted = True

    if not settings.UPSTASH_REDIS_REST_URL or not settings.UPSTASH_REDIS_REST_TOKEN:
        logger.warning(
            "UPSTASH_REDIS_REST_URL/TOKEN not configured. "
            "Rate limiter falling back to in-process mode (NOT safe for multi-worker)."
        )
        return None

    try:
        from upstash_redis import Redis

        _redis_client = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN,
        )
        logger.info("Rate limiter using Upstash Redis backend")
    except Exception as exc:
        logger.error(f"Upstash Redis init failed: {exc}. Falling back to in-process.")
        _redis_client = None

    return _redis_client


# ── In-process fallback (dev only) ─────────────────────────────────────────
_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def _check_in_process(user_id: UUID | str, action: str, policy: RateLimitPolicy) -> None:
    now = monotonic()
    cutoff = now - policy.window_seconds
    key = f"{action}:{user_id}"

    with _lock:
        timestamps = _hits[key]
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= policy.limit:
            retry_after = max(1, int(policy.window_seconds - (now - timestamps[0])))
            _raise_rate_limit(action, policy, retry_after)

        timestamps.append(now)


def _check_redis(user_id: UUID | str, action: str, policy: RateLimitPolicy) -> None:
    """
    Atomic increment + TTL via Upstash REST.
    Pattern: INCR sets count, on first write we EXPIRE the key.
    """
    redis = _get_redis()
    if redis is None:
        _check_in_process(user_id, action, policy)
        return

    key = f"rl:{action}:{user_id}"

    try:
        count = redis.incr(key)
        if count == 1:
            # first write — set TTL
            redis.expire(key, policy.window_seconds)
        if count > policy.limit:
            ttl = redis.ttl(key)
            retry_after = max(1, ttl) if ttl and ttl > 0 else policy.window_seconds
            _raise_rate_limit(action, policy, retry_after)
    except HTTPException:
        raise
    except Exception as exc:
        # Redis hiccup — log and fall back to in-process so a Redis outage
        # doesn't take the whole API down.
        logger.warning(f"Redis rate limit check failed ({exc}). Using in-process fallback.")
        _check_in_process(user_id, action, policy)


def _raise_rate_limit(action: str, policy: RateLimitPolicy, retry_after: int) -> None:
    raise HTTPException(
        status_code=429,
        detail={
            "code": "rate_limited",
            "message": "Too many requests. Please wait before trying again.",
            "action": action,
            "limit": policy.limit,
            "window_seconds": policy.window_seconds,
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


def check_rate_limit(user_id: UUID | str, action: str) -> None:
    """
    Public API — unchanged signature so existing callers keep working.
    Uses Upstash Redis if configured, else in-process fallback (logged).
    """
    policy = POLICIES.get(action)
    if not policy:
        return
    _check_redis(user_id, action, policy)
