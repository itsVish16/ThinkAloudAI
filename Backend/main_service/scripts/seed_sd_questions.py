import asyncio
import os
import sys

# Add the main_service path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.future import select
from app.models.system_design import SystemDesignQuestion

async def main():
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://thinkaloud:thinkaloud_secret@localhost:5432/main_service')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Alter table (ignore errors if columns already exist)
        try:
            await session.execute(text("ALTER TABLE system_design_questions ADD COLUMN domain VARCHAR;"))
            await session.execute(text("ALTER TABLE system_design_questions ADD COLUMN role VARCHAR;"))
            await session.commit()
            print("Columns added successfully.")
        except Exception as e:
            print("Columns might already exist:", e)
            await session.rollback()

        # Seed questions
        questions_to_seed = [
            {
                "title": "Design a Distributed Message Queue",
                "description": "Design a distributed message queue system like Apache Kafka or RabbitMQ. Focus on partitioning, replication, message durability, and consumer groups.",
                "domain": "Backend",
                "role": "Senior Software Engineer"
            },
            {
                "title": "Design a URL Shortener",
                "description": "Design a scalable URL shortener like bit.ly. Focus on collision prevention, capacity estimation, caching strategies, and highly available reads.",
                "domain": "Backend",
                "role": "Software Engineer"
            },
            {
                "title": "Design a Recommendation System for Netflix",
                "description": "Design a video recommendation system. Focus on the ML pipeline, feature store, real-time vs batch inference, and model serving infrastructure.",
                "domain": "AI/ML",
                "role": "Senior Software Engineer"
            },
            {
                "title": "Design a RAG-based Customer Support Chatbot",
                "description": "Design a Retrieval-Augmented Generation (RAG) customer support agent. Discuss vector database scaling, embedding generation, context window management, and handling hallucinations.",
                "domain": "AI/ML",
                "role": "Software Engineer"
            }
        ]

        # Check existing
        result = await session.execute(select(SystemDesignQuestion))
        existing = result.scalars().all()
        
        if len(existing) < 4:
            # clear existing to avoid duplicates if we want clean state
            await session.execute(text("TRUNCATE TABLE system_design_questions;"))
            
            for q in questions_to_seed:
                new_q = SystemDesignQuestion(
                    title=q["title"],
                    description=q["description"],
                    domain=q["domain"],
                    role=q["role"]
                )
                session.add(new_q)
            await session.commit()
            print("Seeded 4 questions!")
        else:
            print(f"Already found {len(existing)} questions.")

if __name__ == "__main__":
    asyncio.run(main())
