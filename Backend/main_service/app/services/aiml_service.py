import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from redis.asyncio import Redis

from app.models.aiml import AIMLQuestion
from app.schemas.aiml import AIMLQuestionCreate, AIMLQuestionOut

class AIMLService:
    @staticmethod
    async def list_questions(limit: int, db: AsyncSession, redis: Redis):
        cache_key = f"aiml:questions:all"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        query = select(AIMLQuestion).limit(limit)
        result = await db.execute(query)
        questions = result.scalars().all()

        def _serialize(q):
            data = AIMLQuestionOut.model_validate(q).model_dump()
            data["created_at"] = data["created_at"].isoformat()
            return data

        serialized_q = [_serialize(q) for q in questions]
        await redis.set(cache_key, json.dumps(serialized_q), ex=3600)
        return questions

    @staticmethod
    async def get_question(question_id: int, db: AsyncSession):
        result = await db.execute(select(AIMLQuestion).filter(AIMLQuestion.id == question_id))
        question = result.scalars().first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question

    @staticmethod
    async def create_question(request: AIMLQuestionCreate, db: AsyncSession, redis: Redis):
        new_question = AIMLQuestion(
            title=request.title,
            description=request.description,
            domain=request.domain,
            role=request.role
        )
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)
        await redis.delete("aiml:questions:all")
        return new_question
