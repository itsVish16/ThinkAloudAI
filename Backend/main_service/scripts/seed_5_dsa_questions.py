import json
import asyncio
import os
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.dsa import DSAQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def run():
    db_url = os.environ.get("DATABASE_URL")
    logger.info(f"Connecting to database at {db_url}...")
    engine = create_async_engine(db_url)
    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    json_path = os.path.join(os.path.dirname(__file__), '..', 'five_curated_dsa_questions.json')
    if not os.path.exists(json_path):
        logger.error(f"Cannot find {json_path}")
        return
        
    with open(json_path, "r") as f:
        questions = json.load(f)
        
    async with LocalSession() as session:
        # Clear out existing questions
        await session.execute(text("TRUNCATE TABLE submissions RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE dsa_questions RESTART IDENTITY CASCADE"))
        
        count = 0
        for q in questions:
            db_q = DSAQuestion(
                title=q["title"],
                description=q["description"],
                difficulty=q["difficulty"],
                function_name=q["function_name"],
                python_starter_code=q["python_starter_code"],
                cpp_starter_code=q["cpp_starter_code"],
                cpp_test_harness=q["cpp_test_harness"],
                test_cases=q["test_cases"] if isinstance(q["test_cases"], str) else json.dumps(q["test_cases"]),
                hints=json.dumps(q["hints"]) if isinstance(q["hints"], list) else q["hints"],
                optimal_time_complexity=q["optimal_time_complexity"],
                optimal_space_complexity=q["optimal_space_complexity"]
            )
            session.add(db_q)
            count += 1
            
        await session.commit()
        logger.info(f"Imported {count} 5-star curated DSA questions successfully.")

if __name__ == "__main__":
    asyncio.run(run())
