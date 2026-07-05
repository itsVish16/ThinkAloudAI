import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import text

from app.database import get_db, get_redis
from app.config import settings
from app.models.system_design import SystemDesignQuestion
from app.schemas.system_design import SystemDesignQuestionCreate, SystemDesignQuestionOut
from redis.asyncio import Redis
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter(prefix="/system-design", tags=["System Design Questions"])

@router.post("/seed")
async def seed_questions(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    # Delete all existing
    await db.execute(text("TRUNCATE TABLE system_design_questions RESTART IDENTITY CASCADE"))
    
    questions = [
        {"title": "Design a Distributed Message Queue", "description": "Design a distributed message queue system like Apache Kafka or RabbitMQ. Focus on partitioning, replication, message durability, and consumer groups.", "domain": "Backend", "role": "Senior Software Engineer"},
        {"title": "Design a URL Shortener", "description": "Design a scalable URL shortener like bit.ly. Focus on collision prevention, capacity estimation, caching strategies, and highly available reads.", "domain": "Backend", "role": "Software Engineer"},
        {"title": "Design a Recommendation System for Netflix", "description": "Design a video recommendation system. Focus on the ML pipeline, feature store, real-time vs batch inference, and model serving infrastructure.", "domain": "AI/ML", "role": "Senior Software Engineer"},
        {"title": "Design a RAG-based Customer Support Chatbot", "description": "Design a Retrieval-Augmented Generation (RAG) customer support agent. Discuss vector database scaling, embedding generation, context window management, and handling hallucinations.", "domain": "AI/ML", "role": "Software Engineer"}
    ]
    
    for q in questions:
        new_q = SystemDesignQuestion(**q)
        db.add(new_q)
    
    await db.commit()
    
    # Flush redis cache
    await redis.flushall()
    
    return {"message": "Seeded 4 questions and flushed cache"}

@router.get("/questions", response_model=List[SystemDesignQuestionOut])
async def list_questions(
    domain: str = None,
    role: str = None,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    List all available System Design questions.
    """
    cache_key = f"system_design:questions:all:{domain}:{role}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(SystemDesignQuestion)
    if domain:
        query = query.filter(SystemDesignQuestion.domain == domain)
    if role:
        query = query.filter(SystemDesignQuestion.role == role)

    result = await db.execute(query)
    questions = result.scalars().all()

    def _serialize(q):
        data = SystemDesignQuestionOut.model_validate(q).model_dump()
        data["created_at"] = data["created_at"].isoformat()
        return data

    serialized_q = [_serialize(q) for q in questions]
    await redis.set(cache_key, json.dumps(serialized_q), ex=3600)

    return questions

@router.get("/questions/{question_id}", response_model=SystemDesignQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific System Design question by its ID.
    """
    result = await db.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/questions", response_model=SystemDesignQuestionOut)
async def create_question(request: SystemDesignQuestionCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new System Design question.
    """
    new_question = SystemDesignQuestion(
        title=request.title,
        description=request.description
    )
    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)
    return new_question

from app.schemas.system_design import SystemDesignSubmitRequest, SystemDesignSubmitResponse
import os


async def evaluate_system_design(question_title: str, question_description: str, answer: str) -> SystemDesignSubmitResponse:
    """
    Evaluates a system-design submission with the configured Featherless LLM,
    traced via Opik. Falls back to a neutral evaluation on any error so the
    endpoint never 500s purely because the LLM is unavailable.
    """
    from langchain_openai import ChatOpenAI
    try:
        from opik.integrations.langchain import OpikTracer
        os.environ.setdefault("OPIK_API_KEY", settings.OPIK_API_KEY)
        if getattr(settings, "OPIK_WORKSPACE", None):
            os.environ.setdefault("OPIK_WORKSPACE", settings.OPIK_WORKSPACE)
        if getattr(settings, "OPIK_PROJECT_NAME", None):
            os.environ.setdefault("OPIK_PROJECT_NAME", settings.OPIK_PROJECT_NAME)
        callbacks = [OpikTracer()]
    except Exception:
        callbacks = []

    llm = ChatOpenAI(
        model=os.environ.get("FEATHERLESS_MODEL", "meta-llama/Meta-Llama-3-70B-Instruct"),
        base_url=settings.FEATHERLESS_BASE_URL,
        api_key=settings.FEATHERLESS_API_KEY,
        temperature=0.2,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    system_prompt = (
        "You are a senior staff engineer evaluating a system design interview answer. "
        "Return ONLY a JSON object with keys: score (0-100 int), feedback (string), "
        "strengths (array of strings), improvements (array of strings). "
        "Be specific and actionable."
    )
    user_prompt = (
        f"Question: {question_title}\n\nContext: {question_description}\n\n"
        f"Candidate's design:\n{answer}"
    )

    try:
        result = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
            config={"callbacks": callbacks, "tags": ["system_design_evaluation"]},
        )
        data = json.loads(result.content)
        return SystemDesignSubmitResponse(
            score=int(data.get("score", 70)),
            feedback=data.get("feedback", "No feedback returned."),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
        )
    except Exception as e:
        # Degraded-but-functional fallback so the user still gets a structured response
        return SystemDesignSubmitResponse(
            score=0,
            feedback=f"Automatic evaluation unavailable: {e}",
            strengths=[],
            improvements=["Please request a manual review for detailed feedback."],
        )


@router.post("/questions/{question_id}/submit", response_model=SystemDesignSubmitResponse)
async def submit_system_design(question_id: int, request: SystemDesignSubmitRequest, db: AsyncSession = Depends(get_db)):
    """
    Submit an answer for a System Design question and receive an LLM evaluation
    (score, feedback, strengths, improvements) traced through Opik.
    """
    result = await db.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return await evaluate_system_design(question.title, question.description, request.answer_text)
