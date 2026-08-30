import asyncio
import json
import logging
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
import redis.asyncio as aioredis

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import DATABASE_URL, engine, Base
from app.config import settings
from app.models.dsa import DSAQuestion, ProblemTag, CodeSubmission

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def seed_canonical_dsa():
    json_path = os.path.join(os.path.dirname(__file__), "..", "canonical_dsa_questions.json")
    if not os.path.exists(json_path):
        logger.error(f"Canonical dataset not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    local_engine = create_async_engine(DATABASE_URL)
    LocalSession = sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)

    async with LocalSession() as session:
        logger.info("Syncing canonical DSA questions to PostgreSQL...")
        
        # Create schema if not exists
        async with local_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        inserted, updated = 0, 0
        for item in questions_data:
            title = item["title"]
            tags = item.pop("tags", [])
            
            res = await session.execute(select(DSAQuestion).filter(DSAQuestion.title == title))
            existing_q = res.scalars().first()

            if existing_q:
                existing_q.description = item["description"]
                existing_q.difficulty = item["difficulty"]
                existing_q.function_name = item["function_name"]
                existing_q.python_starter_code = item["python_starter_code"]
                existing_q.cpp_starter_code = item["cpp_starter_code"]
                existing_q.cpp_test_harness = item["cpp_test_harness"]
                existing_q.test_cases = item["test_cases"]
                existing_q.hints = item["hints"]
                existing_q.optimal_time_complexity = item["optimal_time_complexity"]
                existing_q.optimal_space_complexity = item["optimal_space_complexity"]
                q_id = existing_q.id
                updated += 1
            else:
                new_q = DSAQuestion(**item)
                session.add(new_q)
                await session.flush()
                q_id = new_q.id
                inserted += 1

            # Sync tags
            if tags:
                existing_tags_res = await session.execute(select(ProblemTag).filter(ProblemTag.question_id == q_id))
                existing_tags = {t.tag_name for t in existing_tags_res.scalars().all()}
                for tag_name in tags:
                    if tag_name not in existing_tags:
                        session.add(ProblemTag(question_id=q_id, tag_name=tag_name))

        await session.commit()
        logger.info(f"✅ DSA Questions Synced: {inserted} inserted, {updated} updated (Total: {len(questions_data)}).")

    # Invalidate Redis Question Caches
    try:
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        keys = await redis.keys("dsa:questions:all:*")
        if keys:
            await redis.delete(*keys)
            logger.info(f"🧹 Purged {len(keys)} stale Redis question cache keys.")
        await redis.aclose()
    except Exception as e:
        logger.warning(f"Could not purge Redis cache: {e}")

if __name__ == "__main__":
    asyncio.run(seed_canonical_dsa())
