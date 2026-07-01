import asyncio
import json
import logging
import os
import sys
from pydantic import BaseModel
from typing import List, Optional
from datasets import load_dataset
from openai import AsyncOpenAI
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base
from app.models.dsa import DSAQuestion
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url=settings.FEATHERLESS_BASE_URL,
    api_key=settings.FEATHERLESS_API_KEY,
)
MODEL_NAME = "zai-org/GLM-5.2"  # or THUDM/glm-4-9b-chat if zai-org fails

class Example(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class EnrichedProblem(BaseModel):
    title: str
    description: str
    examples: List[Example]
    constraints: List[str]
    hints: List[str]
    tags: List[str]

async def enrich_problem(raw_title: str, raw_desc: str, test_cases_str: str) -> Optional[EnrichedProblem]:
    system_prompt = """You are an expert technical writer and software engineer. Your task is to clean and enrich a raw LeetCode problem description and its test cases into a highly structured JSON format.

Return ONLY a valid JSON object matching this schema exactly:
{
  "title": "A clean, proper title (string)",
  "description": "A highly detailed, extended description of the problem (string)",
  "examples": [
    {
      "input": "...",
      "output": "...",
      "explanation": "..."
    }
  ],
  "constraints": [
    "Constraint 1",
    "Constraint 2"
  ],
  "hints": [
    "Hint 1",
    "Hint 2"
  ],
  "tags": ["Array", "Algorithm"]
}

Important:
- Provide exactly 2 well-thought-out examples based on the provided test cases.
- Extract or deduce proper constraints based on common competitive programming standards if none exist.
- Provide 2 helpful hints.
- Output ONLY the JSON. Do not include markdown code blocks like ```json.
"""

    user_prompt = f"Raw Title: {raw_title}\n\nRaw Description:\n{raw_desc}\n\nRaw Test Cases (Sample):\n{test_cases_str[:500]}"

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        json_str = response.choices[0].message.content
        # sometimes LLMs return markdown despite json_object
        if json_str.startswith("```json"):
            json_str = json_str[7:-3]
        elif json_str.startswith("```"):
            json_str = json_str[3:-3]
            
        data = json.loads(json_str.strip())
        return EnrichedProblem(**data)
    except Exception as e:
        logger.error(f"Failed to enrich problem {raw_title}: {e}")
        return None

def format_markdown(enriched: EnrichedProblem) -> str:
    md = f"{enriched.description}\n\n"
    for i, ex in enumerate(enriched.examples):
        md += f"**Example {i+1}:**\n"
        md += f"- **Input:** `{ex.input}`\n"
        md += f"- **Output:** `{ex.output}`\n"
        if ex.explanation:
            md += f"- **Explanation:** {ex.explanation}\n"
        md += "\n"
    
    if enriched.constraints:
        md += "**Constraints:**\n"
        for c in enriched.constraints:
            md += f"- {c}\n"
            
    return md.strip()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def run_enrichment(limit: int = 30):
    await init_db()
    
    ds = load_dataset("newfacade/LeetCodeDataset", split="train")
    
    jsonl_path = os.path.join(os.path.dirname(__file__), "enriched_leetcode.jsonl")
    
    async with SessionLocal() as session:
        for i in range(min(limit, len(ds))):
            item = ds[i]
            raw_title = item.get("task_id", f"Problem {i+1}")
            raw_desc = item.get("problem_description", "")
            
            # test cases
            test_cases = item.get("input_output", [])
            test_cases_json = json.dumps(test_cases)
            
            logger.info(f"Enriching problem {i+1}/{limit}: {raw_title}")
            
            enriched = await enrich_problem(raw_title, raw_desc, test_cases_json)
            if not enriched:
                logger.warning(f"Skipping {raw_title} due to enrichment failure.")
                continue
                
            # Create full markdown
            full_markdown = format_markdown(enriched)
            
            # Save to jsonl for huggingface
            with open(jsonl_path, "a") as f:
                record = {
                    "task_id": raw_title,
                    "title": enriched.title,
                    "description": full_markdown,
                    "hints": enriched.hints,
                    "tags": enriched.tags,
                    "test_cases": test_cases_json,
                    "python_starter_code": item.get("starter_code", ""),
                    "function_name": item.get("entry_point", "solution"),
                    "difficulty": item.get("difficulty", "Medium")
                }
                f.write(json.dumps(record) + "\n")
                
            # Save to DB
            question = DSAQuestion(
                title=enriched.title,
                description=full_markdown,
                difficulty=item.get("difficulty", "Medium"),
                function_name=item.get("entry_point", "solution"),
                python_starter_code=item.get("starter_code", ""),
                test_cases=test_cases_json,
                hints=json.dumps(enriched.hints)
            )
            
            session.add(question)
            
        await session.commit()
        logger.info(f"Finished enriching and saving {limit} problems.")

if __name__ == "__main__":
    # Ensure jsonl is fresh
    jsonl_path = os.path.join(os.path.dirname(__file__), "enriched_leetcode.jsonl")
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)
        
    asyncio.run(run_enrichment(limit=30))
