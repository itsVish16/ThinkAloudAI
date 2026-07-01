import asyncio
import json
import logging
from datasets import load_dataset
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import sys
import os
# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, Base, engine
from app.models.dsa import DSAQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    async with engine.begin() as conn:
        # We don't drop all, we just ensure tables exist.
        await conn.run_sync(Base.metadata.create_all)

async def seed_problems(limit: int = 100):
    logger.info(f"Loading LeetCodeDataset from Hugging Face... Limit: {limit}")
    
    # Load dataset
    ds = load_dataset("newfacade/LeetCodeDataset", split="train")
    
    async with SessionLocal() as session:
        count = 0
        for i in range(min(limit, len(ds))):
            item = ds[i]
            
            title = item.get("task_id", f"Problem {i+1}")
            
            # Check if problem already exists
            existing = await session.execute(select(DSAQuestion).where(DSAQuestion.title == title))
            if existing.scalars().first():
                logger.info(f"Skipping {title} (already exists)")
                continue

            # Format test cases to JSON string
            test_cases = item.get("input_output", [])
            test_cases_json = json.dumps(test_cases)
            
            # Extract tags as hints
            tags = item.get("tags", [])
            hints_json = json.dumps(tags) if tags else None
            
            question = DSAQuestion(
                title=title,
                description=item.get("problem_description", ""),
                difficulty=item.get("difficulty", "Medium"),
                function_name=item.get("entry_point", "solution"),
                python_starter_code=item.get("starter_code", ""),
                test_cases=test_cases_json,
                hints=hints_json
            )
            
            session.add(question)
            count += 1
            
        await session.commit()
        logger.info(f"Successfully seeded {count} new problems into the database.")

async def main():
    await init_db()
    await seed_problems(limit=100)

if __name__ == "__main__":
    asyncio.run(main())
