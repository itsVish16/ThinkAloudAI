import asyncio
import json
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models.dsa import DSAQuestion, ProblemTag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_data():
    file_path = "scripts/enriched_leetcode.jsonl"
    
    async with SessionLocal() as db:
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            inserted_count = 0
            updated_count = 0
            
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    title = data.get("title")
                    
                    if not title:
                        continue
                        
                    # Check if question already exists
                    result = await db.execute(select(DSAQuestion).filter(DSAQuestion.title == title))
                    existing_q = result.scalars().first()
                    
                    if existing_q:
                        # Update existing
                        existing_q.description = data.get("description", existing_q.description)
                        existing_q.difficulty = data.get("difficulty", existing_q.difficulty)
                        existing_q.function_name = data.get("function_name", existing_q.function_name)
                        existing_q.python_starter_code = data.get("python_starter_code", existing_q.python_starter_code)
                        existing_q.hints = json.dumps(data.get("hints", []))
                        
                        test_cases = data.get("test_cases")
                        if isinstance(test_cases, str):
                            existing_q.test_cases = test_cases
                        else:
                            existing_q.test_cases = json.dumps(test_cases)
                            
                        updated_count += 1
                        logger.info(f"Updated: {title}")
                        q_id = existing_q.id
                    else:
                        # Create new
                        test_cases = data.get("test_cases")
                        if not isinstance(test_cases, str):
                            test_cases = json.dumps(test_cases)
                            
                        new_q = DSAQuestion(
                            title=title,
                            description=data.get("description", ""),
                            difficulty=data.get("difficulty", "Medium"),
                            function_name=data.get("function_name", "solution"),
                            python_starter_code=data.get("python_starter_code", ""),
                            hints=json.dumps(data.get("hints", [])),
                            test_cases=test_cases
                        )
                        db.add(new_q)
                        await db.flush() # flush to get the id
                        inserted_count += 1
                        logger.info(f"Inserted: {title}")
                        q_id = new_q.id
                        
                    # Handle tags
                    tags = data.get("tags", [])
                    if tags:
                        # Delete existing tags for this question to keep it clean
                        await db.execute(
                            ProblemTag.__table__.delete().where(ProblemTag.question_id == q_id)
                        )
                        
                        # Add new tags
                        for tag_name in tags:
                            new_tag = ProblemTag(question_id=q_id, tag_name=tag_name)
                            db.add(new_tag)
                            
                except Exception as ex:
                    logger.error(f"Error processing line: {ex}")
                    
            await db.commit()
            logger.info(f"Success! Inserted {inserted_count} new questions, updated {updated_count} existing questions.")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error loading data: {e}")

if __name__ == "__main__":
    asyncio.run(load_data())
