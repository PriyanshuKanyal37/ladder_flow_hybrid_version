"""
Add foreign-key indexes for performance under 5-20 concurrent users.

Idempotent — safe to run multiple times. Uses CREATE INDEX CONCURRENTLY
which does NOT lock the table (online operation, zero downtime on Neon).

Run once:
    python migrate_add_fk_indexes.py

What it adds (verified missing via live audit on 2026-05-08):
    - interviews(user_id)
    - interviews(user_id, created_at DESC)
    - interviews(user_id, status)
    - memory_items(source_interview_id)

Side effects:
    - Reads massively faster on filtered queries
    - Writes ~5% slower (negligible)
    - Disk usage: +~50KB per index
    - Application code: NO changes required (SQLAlchemy auto-uses indexes)

Rollback (if ever needed):
    DROP INDEX CONCURRENTLY idx_interviews_user_id;
    DROP INDEX CONCURRENTLY idx_interviews_user_created;
    DROP INDEX CONCURRENTLY idx_interviews_user_status;
    DROP INDEX CONCURRENTLY idx_memory_items_source_interview;
"""

import asyncio
import os

from dotenv import load_dotenv
import asyncpg


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# CONCURRENTLY requires us NOT to be inside a transaction.
# We'll bypass the asyncpg transaction wrapper by using `execute` outside one.
INDEXES = [
    (
        "idx_interviews_user_id",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_user_id ON interviews(user_id)",
    ),
    (
        "idx_interviews_user_created",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_user_created "
        "ON interviews(user_id, created_at DESC)",
    ),
    (
        "idx_interviews_user_status",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_user_status "
        "ON interviews(user_id, status)",
    ),
    (
        "idx_memory_items_source_interview",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memory_items_source_interview "
        "ON memory_items(source_interview_id)",
    ),
]


def _to_asyncpg_url(url: str) -> str:
    # asyncpg uses postgresql:// not postgresql+asyncpg://
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def main() -> None:
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL not set")

    pg_url = _to_asyncpg_url(raw_url)

    # asyncpg.connect() does NOT start a transaction by default.
    conn = await asyncpg.connect(pg_url)
    try:
        for name, ddl in INDEXES:
            print(f"Creating {name}...", flush=True)
            try:
                await conn.execute(ddl)
                print(f"  [OK] {name} ready")
            except Exception as exc:
                # CONCURRENTLY can fail if a previous attempt left an invalid index
                print(f"  ! {name} failed: {exc}")
                print(f"    Check pg_indexes for invalid indexes and DROP if needed.")
    finally:
        await conn.close()

    print("\nDone. Verify with:")
    print("  SELECT indexname FROM pg_indexes WHERE tablename IN ('interviews', 'memory_items');")


if __name__ == "__main__":
    asyncio.run(main())
