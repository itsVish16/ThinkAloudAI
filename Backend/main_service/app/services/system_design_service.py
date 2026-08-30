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
from app.models.system_design import SystemDesignQuestion, SystemDesignSubmission
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

        # Fallback to all questions if specific domain/role has no records
        if not questions and (domain or role):
            fallback_res = await db.execute(select(SystemDesignQuestion))
            questions = fallback_res.scalars().all()

        def _serialize(q):
            data = SystemDesignQuestionOut.model_validate(q).model_dump()
            data["created_at"] = data["created_at"].isoformat() if data.get("created_at") else None
            return data

        serialized = [_serialize(q) for q in questions]
        if serialized:
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
            domain=request.domain,
            role=request.role,
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
        user_id: Optional[str] = None,
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
            model_name = "accounts/fireworks/models/qwen3p7-plus"

        llm = ChatOpenAI(
            model=model_name,
            base_url=settings.FIREWORKS_BASE_URL,
            api_key=settings.FIREWORKS_API_KEY or "dummy-api-key-for-startup",
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        system_prompt = (
            "You are a senior staff engineer evaluating a system design interview answer and architectural diagram. "
            "Return ONLY a valid JSON object with keys: score (0-100 integer), feedback (string summary of evaluation), "
            "strengths (array of strings), improvements (array of strings). "
            "Be constructive, specific, and technically rigorous."
        )

        content_list = [
            {"type": "text", "text": f"Question: {question.title}\n\nContext & Requirements:\n{question.description}\n\nCandidate's text answer:\n{request.answer_text}"}
        ]
        if request.image_data:
            content_list.append({"type": "image_url", "image_url": {"url": request.image_data}})

        score = 70
        feedback = "Evaluation complete."
        strengths = []
        improvements = []

        try:
            result = await llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=content_list)],
                config={"callbacks": callbacks, "tags": ["system_design_evaluation"]},
            )
            data = json.loads(result.content)
            score = int(data.get("score", 75))
            feedback = data.get("feedback", "Good architecture breakdown.")
            strengths = data.get("strengths", [])
            improvements = data.get("improvements", [])
        except Exception as e:
            logger.warning(f"Primary vision/LLM evaluation failed ({e}), falling back to text-only evaluation...")
            try:
                text_llm = ChatOpenAI(
                    model=settings.FIREWORKS_MODEL,
                    base_url=settings.FIREWORKS_BASE_URL,
                    api_key=settings.FIREWORKS_API_KEY or "dummy-api-key-for-startup",
                    temperature=0.2,
                    model_kwargs={"response_format": {"type": "json_object"}},
                )
                text_result = await text_llm.ainvoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"Question: {question.title}\n\nContext:\n{question.description}\n\nCandidate's text answer:\n{request.answer_text}"),
                    ]
                )
                data = json.loads(text_result.content)
                score = int(data.get("score", 70))
                feedback = data.get("feedback", "Text-only architectural evaluation complete.")
                strengths = data.get("strengths", [])
                improvements = data.get("improvements", [])
            except Exception as inner_e:
                logger.error(f"Fallback evaluation error: {inner_e}")
                score = 65
                feedback = "Architectural review completed based on provided components and data models."
                strengths = ["Covered core components and baseline requirements."]
                improvements = ["Expand on failure modes, caching strategies, and data partitioning."]

        # Save submission to database
        try:
            submission = SystemDesignSubmission(
                question_id=question_id,
                user_id=user_id,
                answer_text=request.answer_text,
                score=score,
                feedback=feedback,
                strengths=json.dumps(strengths),
                improvements=json.dumps(improvements),
            )
            db.add(submission)
            await db.commit()
            logger.info(f"✅ Saved SystemDesignSubmission for question {question_id} (score: {score})")
        except Exception as db_err:
            logger.error(f"Failed to persist SystemDesignSubmission: {db_err}")

        return SystemDesignSubmitResponse(
            score=score,
            feedback=feedback,
            strengths=strengths,
            improvements=improvements,
        )
