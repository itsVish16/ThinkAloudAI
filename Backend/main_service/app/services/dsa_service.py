import json
import asyncio
from typing import List, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.models.dsa import DSAQuestion, CodeSubmission, UserProblemStatus, Recommendation
from app.schemas.dsa import DSAQuestionCreate, DSAQuestionOut, CodeSubmitRequest, CodeSubmitResponse, CodeSubmissionOut
from app.config import settings

class DSAService:
    @staticmethod
    async def get_median_debug(db: AsyncSession) -> dict:
        result = await db.execute(select(DSAQuestion).filter(DSAQuestion.title == "Median of Two Sorted Arrays"))
        q = result.scalar_one_or_none()
        if q:
            return {"raw": q.description}
        return {"raw": "not found"}

    @staticmethod
    async def list_questions(db: AsyncSession, redis: Redis, skip: int, limit: int) -> List[DSAQuestion]:
        cache_key = f"dsa:questions:all:skip={skip}:limit={limit}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        result = await db.execute(
            select(DSAQuestion)
            .order_by(DSAQuestion.id.asc())
            .offset(skip)
            .limit(limit)
        )
        questions = result.scalars().all()

        def _serialize(q):
            data = DSAQuestionOut.model_validate(q).model_dump()
            data["created_at"] = data["created_at"].isoformat()
            return data

        serialized_q = [_serialize(q) for q in questions]
        await redis.set(cache_key, json.dumps(serialized_q), ex=3600)

        return questions

    @staticmethod
    async def get_question(question_id: int, db: AsyncSession) -> DSAQuestion:
        result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
        question = result.scalars().first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question

    @staticmethod
    async def create_question(request: DSAQuestionCreate, db: AsyncSession, redis: Redis) -> DSAQuestion:
        new_question = DSAQuestion(
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            test_cases=request.test_cases,
            python_starter_code=request.python_starter_code,
            cpp_starter_code=request.cpp_starter_code
        )
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)
        
        try:
            async for key in redis.scan_iter("dsa:questions:all:*"):
                await redis.delete(key)
        except Exception:
            pass
            
        return new_question

    @staticmethod
    async def get_latest_submission(question_id: int, language: Optional[str], user_id: str, db: AsyncSession) -> Optional[CodeSubmission]:
        query = select(CodeSubmission).filter(
            CodeSubmission.question_id == question_id,
            CodeSubmission.session_id == user_id
        )
        if language:
            query = query.filter(CodeSubmission.language == language)
            
        query = query.order_by(CodeSubmission.created_at.desc())
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def run_solution(question_id: int, request: CodeSubmitRequest, db: AsyncSession, redis: Redis) -> CodeSubmitResponse:
        result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
        question = result.scalars().first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
            
        from app.services.mq_producer import publish_execution_task
        
        func_name = question.function_name
        test_cases_json = question.test_cases
        test_harness = question.cpp_test_harness

        submission = CodeSubmission(
            session_id=request.session_id,
            question_id=question_id,
            code=request.code,
            language=request.language,
            status="Pending",
            is_submission=False
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        
        task_data = {
            "submission_id": submission.id,
            "code": request.code,
            "language": request.language,
            "function_name": func_name,
            "test_cases_json": test_cases_json,
            "test_harness": test_harness
        }
        await publish_execution_task(task_data)
            
        return CodeSubmitResponse(
            status="Pending",
            submission_id=submission.id,
            output=f"Execution queued with ID: {submission.id}",
            passed_tests=0,
            total_tests=0,
            execution_time_ms=0.0,
        )

    @staticmethod
    async def submit_solution(question_id: int, request: CodeSubmitRequest, db: AsyncSession, redis: Redis) -> CodeSubmitResponse:
        result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
        question = result.scalars().first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
            
        from app.services.mq_producer import publish_execution_task
        
        func_name = question.function_name
        test_cases_json = question.test_cases
        test_harness = question.cpp_test_harness

        submission = CodeSubmission(
            session_id=request.session_id,
            question_id=question_id,
            code=request.code,
            language=request.language,
            status="Pending",
            is_submission=True
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        
        task_data = {
            "submission_id": submission.id,
            "code": request.code,
            "language": request.language,
            "function_name": func_name,
            "test_cases_json": test_cases_json,
            "test_harness": test_harness
        }
        await publish_execution_task(task_data)
        
        return CodeSubmitResponse(
            status="Pending",
            submission_id=submission.id,
            output=f"Submission queued with ID: {submission.id}",
            passed_tests=0,
            total_tests=0,
            execution_time_ms=0.0,
        )

    @staticmethod
    def stream_submission_status(submission_id: int):
        import redis.asyncio as aioredis
        import time
        from app.database import SessionLocal
        
        async def event_generator():
            # Check if submission is already finished in DB
            try:
                async with SessionLocal() as db:
                    result = await db.execute(select(CodeSubmission).filter(CodeSubmission.id == submission_id))
                    sub = result.scalars().first()
                    if sub and sub.status != "Pending":
                        final_data = json.dumps({
                            "status": sub.status,
                            "error_message": sub.error_message,
                            "execution_time_ms": sub.execution_time_ms,
                            "passed_tests": sub.passed_tests,
                            "total_tests": sub.total_tests
                        })
                        yield f"event: result\ndata: {final_data}\n\n"
                        return
            except Exception:
                pass

            redis_client = aioredis.from_url(settings.REDIS_URL)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"submission_updates_{submission_id}")

            try:
                yield "event: connected\ndata: connected\n\n"
                start_time = time.time()
                last_poll = start_time

                while True:
                    if time.time() - start_time > 45:
                        error_data = json.dumps({"status": "Error", "error_message": "Execution timed out waiting for worker."})
                        yield f"event: result\ndata: {error_data}\n\n"
                        break

                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        data = message["data"].decode("utf-8")
                        yield f"event: result\ndata: {data}\n\n"
                        break

                    # Fallback DB check every 2 seconds
                    if time.time() - last_poll >= 2.0:
                        last_poll = time.time()
                        try:
                            async with SessionLocal() as db:
                                result = await db.execute(select(CodeSubmission).filter(CodeSubmission.id == submission_id))
                                sub = result.scalars().first()
                                if sub and sub.status != "Pending":
                                    final_data = json.dumps({
                                        "status": sub.status,
                                        "error_message": sub.error_message,
                                        "execution_time_ms": sub.execution_time_ms,
                                        "passed_tests": sub.passed_tests,
                                        "total_tests": sub.total_tests
                                    })
                                    yield f"event: result\ndata: {final_data}\n\n"
                                    break
                        except Exception:
                            pass

                    yield ":\n\n"
            except Exception as e:
                error_data = json.dumps({"status": "Error", "error_message": f"Stream error: {str(e)}"})
                yield f"event: result\ndata: {error_data}\n\n"
            finally:
                await pubsub.unsubscribe()
                await redis_client.close()

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @staticmethod
    async def get_session_submissions(session_id: str, db: AsyncSession) -> List[CodeSubmission]:
        result = await db.execute(
            select(CodeSubmission)
            .filter(
                or_(
                    CodeSubmission.session_id == session_id,
                    CodeSubmission.session_id.ilike(session_id)
                ),
                CodeSubmission.is_submission == True
            )
            .order_by(CodeSubmission.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_question_submissions(question_id: int, session_id: str, db: AsyncSession) -> List[CodeSubmission]:
        result = await db.execute(
            select(CodeSubmission)
            .filter(
                CodeSubmission.question_id == question_id,
                or_(
                    CodeSubmission.session_id == session_id,
                    CodeSubmission.session_id.ilike(session_id)
                ),
                CodeSubmission.is_submission == True
            )
            .order_by(CodeSubmission.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_user_dsa_status(db: AsyncSession, user_id: str) -> List[UserProblemStatus]:
        result = await db.execute(
            select(UserProblemStatus)
            .filter(UserProblemStatus.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_user_recommendations(db: AsyncSession, user_id: str) -> List[Recommendation]:
        result = await db.execute(
            select(Recommendation)
            .filter(Recommendation.session_id == user_id)
            .order_by(Recommendation.created_at.desc())
        )
        return result.scalars().all()
