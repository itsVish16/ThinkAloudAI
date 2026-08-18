import json
import logging
import os
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.models.system_design import SystemDesignQuestion
from app.schemas.system_design import (
    SystemDesignQuestionCreate,
    SystemDesignQuestionOut,
    SystemDesignSubmitRequest,
    SystemDesignSubmitResponse,
)

logger = logging.getLogger(__name__)


class SystemDesignService:
    @staticmethod
    async def list_questions(
        db: AsyncSession,
        redis: Redis,
        domain: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[dict]:
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

        serialized = [_serialize(q) for q in questions]
        await redis.set(cache_key, json.dumps(serialized), ex=3600)
        return serialized

    @staticmethod
    async def get_question(question_id: int, db: AsyncSession) -> SystemDesignQuestion:
        result = await db.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.id == question_id))
        question = result.scalars().first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question

    @staticmethod
    async def create_question(
        request: SystemDesignQuestionCreate,
        db: AsyncSession,
        redis: Redis,
    ) -> SystemDesignQuestion:
        new_question = SystemDesignQuestion(
            title=request.title,
            description=request.description,
        )
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)

        try:
            async for key in redis.scan_iter("system_design:questions:all:*"):
                await redis.delete(key)
        except Exception as e:
            logger.warning("Failed to invalidate system design cache: %s", e)

        return new_question

    @staticmethod
    async def evaluate_submission(
        question_id: int,
        request: SystemDesignSubmitRequest,
        db: AsyncSession,
    ) -> SystemDesignSubmitResponse:
        question = await SystemDesignService.get_question(question_id, db)

        callbacks = []
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

        model_name = settings.FIREWORKS_MODEL
        if request.image_data:
            model_name = "accounts/fireworks/models/llama-v3p2-11b-vision-instruct"

        llm = ChatOpenAI(
            model=model_name,
            base_url=settings.FIREWORKS_BASE_URL,
            api_key=settings.FIREWORKS_API_KEY or "dummy-api-key-for-startup",
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        system_prompt = (
            "You are a senior staff engineer evaluating a system design interview answer. "
            "Return ONLY a JSON object with keys: score (0-100 int), feedback (string), "
            "strengths (array of strings), improvements (array of strings). "
            "Be specific and actionable."
        )

        content_list = [
            {"type": "text", "text": f"Question: {question.title}\n\nContext: {question.description}\n\nCandidate's text answer:\n{request.answer_text}"}
        ]
        if request.image_data:
            content_list.append({"type": "image_url", "image_url": {"url": request.image_data}})

        try:
            result = await llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=content_list)],
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
            logger.error("LLM evaluation error: %s", e)
            return SystemDesignSubmitResponse(
                score=0,
                feedback=f"Automatic evaluation unavailable: {e}",
                strengths=[],
                improvements=["Please request a manual review for detailed feedback."],
            )
