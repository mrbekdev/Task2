import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import redis.asyncio as aioredis
import fakeredis.aioredis

DB_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_redis_client():
    real_redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)
    try:
        await real_redis.ping()
        print("🔗 Real Redis serveriga muvaffaqiyatli ulanindi (redis://localhost:6379).")
        return real_redis
    except Exception:
        await real_redis.aclose() if hasattr(real_redis, "aclose") else None
        print("ℹ️ Real Redis server topilmadi. FakeRedis (In-memory mock client) ishlatilmoqda.")
        return fakeredis.aioredis.FakeRedis(decode_responses=True)
