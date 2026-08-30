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
from app.models.system_design import SystemDesignQuestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def seed_canonical_sd():
    from scripts.generate_system_design_md import SYSTEM_DESIGN_TOPICS

    local_engine = create_async_engine(DATABASE_URL)
    LocalSession = sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)

    async with LocalSession() as session:
        logger.info(f"Syncing {len(SYSTEM_DESIGN_TOPICS)} Canonical System Design questions to PostgreSQL...")
        
        # Ensure schema table exists
        async with local_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        inserted, updated = 0, 0
        for topic in SYSTEM_DESIGN_TOPICS:
            title = topic["title"]
            domain = topic.get("domain", topic.get("category", "Backend / Distributed Systems"))
            role = topic.get("role", "Senior Software Engineer")
            
            # Format comprehensive markdown description
            desc_parts = [
                f"> **Summary:** {topic['summary']}\n",
                "### 1. Requirements & Scope",
                "**Functional Requirements:**",
                "\n".join(f"- {r}" for r in topic["functional_reqs"]),
                "\n**Non-Functional Requirements:**",
                "\n".join(f"- {r}" for r in topic["non_functional_reqs"]),
                "\n### 2. Capacity & Back-of-the-Envelope Estimations",
                topic["estimations"],
                "\n### 3. High-Level Architecture",
                topic["architecture_diagram"],
                "\n### 4. Data Model & Database Design",
                topic["data_model"]
            ]
            if "deep_dive" in topic:
                desc_parts.extend([
                    "\n### 5. Technical Deep Dive & Key Trade-offs",
                    topic["deep_dive"]
                ])
                
            full_description = "\n\n".join(desc_parts)

            res = await session.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.title == title))
            existing_q = res.scalars().first()

            if existing_q:
                existing_q.description = full_description
                existing_q.domain = domain
                existing_q.role = role
                updated += 1
            else:
                new_q = SystemDesignQuestion(
                    title=title,
                    description=full_description,
                    domain=domain,
                    role=role
                )
                session.add(new_q)
                inserted += 1

        await session.commit()
        logger.info(f"✅ System Design Questions Synced: {inserted} inserted, {updated} updated (Total: {len(SYSTEM_DESIGN_TOPICS)}).")

    # Invalidate Redis Question Caches
    try:
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        keys = await redis.keys("system_design:questions:all:*")
        if keys:
            await redis.delete(*keys)
            logger.info(f"🧹 Purged {len(keys)} stale Redis system design cache keys.")
        await redis.aclose()
    except Exception as e:
        logger.warning(f"Could not purge Redis cache: {e}")

if __name__ == "__main__":
    asyncio.run(seed_canonical_sd())
