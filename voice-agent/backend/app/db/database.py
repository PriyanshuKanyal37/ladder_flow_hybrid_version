import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load connection string from environment variable
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=env_path)
# Neon connection string — uses Neon's `-pooler` host (PgBouncer in front).
DATABASE_URL = os.environ.get("DATABASE_URL")

# Small warm pool — keeps 10 connections alive so we skip the ~2.5s cold
# connect (Neon serverless wake-up + TLS handshake) on every request.
# pool_recycle=300 keeps each conn fresh for 5min, then rotates so PgBouncer
# never silently drops us. max_overflow=15 = up to 25 conns under burst.
# Scales to ~50 concurrent users; bump pool_size if you scale beyond that.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=15,
    pool_timeout=10,
)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
