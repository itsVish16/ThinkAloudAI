import asyncio
import json
import logging
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import sys
import os
# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, Base, engine
from app.models.dsa import DSAQuestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def init_db():
    async with engine.begin() as conn:
        # Ensure tables exist
        await conn.run_sync(Base.metadata.create_all)

async def seed_problems(csv_path: str):
    logger.info(f"Loading DSA Problems from {csv_path}...")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return

    async with SessionLocal() as session:
        count = 0
        updated = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            title = row.get("title", f"Problem {idx+1}")
            
            # Check if problem already exists
            existing = await session.execute(select(DSAQuestion).where(DSAQuestion.title == title))
            question = existing.scalars().first()
            
            # Format hints (if tags exist)
            tags = row.get("tags")
            hints_json = None
            if pd.notna(tags):
                hints_json = json.dumps(tags.split("|"))
                
            test_cases = row.get("test_cases_json", "[]")
            if pd.isna(test_cases):
                test_cases = "[]"
                
            desc = row.get("description", "")
            if pd.isna(desc):
                desc = row.get("original_description", "")
                
            diff = row.get("difficulty", "Medium")
            if pd.isna(diff):
                diff = "Medium"
            # Normalize difficulty mapping (EASY, MEDIUM, HARD -> Easy, Medium, Hard)
            diff = diff.capitalize()

            py_code = row.get("starter_code_python", "")
            if pd.isna(py_code): py_code = ""
            cpp_code = row.get("starter_code_cpp", "")
            if pd.isna(cpp_code): cpp_code = ""

            if question:
                # Update existing question
                question.description = desc
                question.difficulty = diff
                question.python_starter_code = py_code
                question.cpp_starter_code = cpp_code
                question.test_cases = test_cases
                question.hints = hints_json
                updated += 1
            else:
                # Create new question
                question = DSAQuestion(
                    title=title,
                    description=desc,
                    difficulty=diff,
                    function_name="solution", # Default entry point
                    python_starter_code=py_code,
                    cpp_starter_code=cpp_code,
                    test_cases=test_cases,
                    hints=hints_json
                )
                session.add(question)
                count += 1
                
        await session.commit()
        logger.info(f"Successfully inserted {count} new problems and updated {updated} existing problems.")

async def main():
    await init_db()
    csv_path = "/Users/vishal/Desktop/ThinkAloudAI/dsa_problems.csv"
    await seed_problems(csv_path)

if __name__ == "__main__":
    asyncio.run(main())
