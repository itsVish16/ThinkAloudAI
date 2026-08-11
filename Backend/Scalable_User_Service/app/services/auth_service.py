import time
import structlog
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.config import settings
from app.core.security import hash_password, verify_password, DUMMY_HASH, generate_otp, create_access_token, create_refresh_token
from app.schemas.user import SignupRequest, LoginRequest
from app.services.cache import (
    get_login_attempts,
    increment_login_attempts,
    reset_login_attempts,
    MAX_LOGIN_ATTEMPTS,
    set_email_verification_token
)
from app.services.user_service import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_last_login
)
from app.services.sqs_publisher import publish_email_task

logger = structlog.get_logger(__name__)

class AuthService:
    
    @staticmethod
    async def signup(payload: SignupRequest, background_tasks: BackgroundTasks, db: AsyncSession, redis: Redis):
        start_time = time.time()
        existing_email = await get_user_by_email(db, str(payload.email))
        t_db1 = time.time()
        logger.info(f"PERF_LOG: get_user_by_email took {t_db1 - start_time:.4f}s")
        
        existing_username = await get_user_by_username(db, payload.username)
        t_db2 = time.time()
        logger.info(f"PERF_LOG: get_user_by_username took {t_db2 - t_db1:.4f}s")

        if existing_email is not None:
            if existing_email.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already registered",
                )
            else:
                if existing_username and existing_username.id != existing_email.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username is already taken",
                    )
                
                t_hash_start = time.time()
                password_hash = await hash_password(payload.password)
                t_hash_end = time.time()
                logger.info(f"PERF_LOG: hash_password took {t_hash_end - t_hash_start:.4f}s")
                
                existing_email.username = payload.username
                existing_email.full_name = payload.full_name
                existing_email.password_hash = password_hash
                try:
                    t_commit_start = time.time()
                    await db.commit()
                    await db.refresh(existing_email)
                    logger.info(f"PERF_LOG: db_commit_update took {time.time() - t_commit_start:.4f}s")
                except IntegrityError:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email or username already exists",
                    )
                user = existing_email
        else:
            if existing_username is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username is already taken",
                )

            t_hash_start = time.time()
            password_hash = await hash_password(payload.password)
            t_hash_end = time.time()
            logger.info(f"PERF_LOG: hash_password took {t_hash_end - t_hash_start:.4f}s")
            
            try:
                t_create_start = time.time()
                user = await create_user(db, payload, password_hash)
                logger.info(f"PERF_LOG: create_user (db) took {time.time() - t_create_start:.4f}s")
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or username already exists",
                )

        verification_otp = generate_otp()
        
        t_redis_start = time.time()
        await set_email_verification_token(redis, str(user.email), verification_otp)
        logger.info(f"PERF_LOG: redis_set_token took {time.time() - t_redis_start:.4f}s")
        
        await redis.publish("user_events", f"user.created:{user.id}")
        
        logger.info("verification_otp_generated", email=str(user.email))
        
        t_bg_start = time.time()
        background_tasks.add_task(publish_email_task, "verification_email", str(user.email), {"otp": verification_otp})
        logger.info(f"PERF_LOG: add_bg_tasks took {time.time() - t_bg_start:.4f}s")
        logger.info(f"PERF_LOG: TOTAL REQUEST TIME took {time.time() - start_time:.4f}s")
        
        return verification_otp

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession, redis: Redis):
        attempts = await get_login_attempts(redis, str(payload.email))
        if attempts >= MAX_LOGIN_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )

        user = await get_user_by_email(db, str(payload.email))

        if user is None:
            await db.close()
            await verify_password("dummy", DUMMY_HASH)
            await increment_login_attempts(redis, str(payload.email))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not await verify_password(payload.password, user.password_hash):
            await increment_login_attempts(redis, str(payload.email))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in",
            )

        await reset_login_attempts(redis, str(payload.email))
        await update_last_login(db, user)

        access_token = create_access_token(data={"sub": str(user.id), "email": str(user.email), "type": "access"})
        refresh_token = create_refresh_token(data={"sub": str(user.id), "email": str(user.email), "type": "refresh"})

        return access_token, refresh_token
