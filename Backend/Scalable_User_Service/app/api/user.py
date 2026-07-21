import hmac
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from sqlalchemy import select

from app.config import settings
from app.core.rate_limit import limiter
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.db.redis import get_redis
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.schemas.profile import SkillResponse, LearningEventResponse
from app.services.cache import (
    MAX_LOGIN_ATTEMPTS,
    blacklist_token,
    delete_cached_user_profile,
    delete_email_verification_token,
    delete_password_reset_token,
    get_cached_user_profile,
    get_email_verification_token,
    get_login_attempts,
    get_password_reset_token,
    increment_login_attempts,
    is_token_blacklisted,
    reset_login_attempts,
    set_cached_user_profile,
    set_email_verification_token,
    set_password_reset_token,
)
from app.services.event_publisher import publish_user_event
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    mark_user_verified,
    update_user,
    update_user_password,
)
from app.services.sqs_publisher import publish_email_task

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
logger = structlog.get_logger(__name__)


def _decode_and_validate_token(token: str, expected_type: str) -> dict:
    """Shared JWT decoding logic. Raises credentials_exception on any failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != expected_type:
            logger.error(f"JWT decode failed: user_id={user_id}, token_type={token_type}, expected={expected_type}")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT decoding error: {e}")
        raise credentials_exception

    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = _decode_and_validate_token(token, "access")
    user_id = payload["sub"]

    # Check if this specific token has been revoked (e.g. via logout)
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        logger.error("Token is blacklisted")
        raise credentials_exception

    # Try cache first
    cached_profile = await get_cached_user_profile(redis, int(user_id))
    if cached_profile is not None:
        return cached_profile

    # Cache miss -> DB Query
    user = await get_user_by_id(db, int(user_id))
    if user is None:
        logger.error(f"User not found for id {user_id}")
        raise credentials_exception

    # Cache the profile
    response_data = UserResponse.model_validate(user).model_dump(mode="json")
    await set_cached_user_profile(redis, user.id, response_data)

    return response_data


async def get_current_user_db(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = _decode_and_validate_token(token, "access")
    user_id = payload["sub"]

    # Check if this specific token has been revoked
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        raise credentials_exception

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks

@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and sends a 6-digit OTP for email verification.",
    responses={
        201: {"description": "User created and verification email sent"},
        409: {"description": "Email or username already exists"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_signup)
async def signup(
    request: Request,
    payload: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    existing_email = await get_user_by_email(db, str(payload.email))
    existing_username = await get_user_by_username(db, payload.username)

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
            password_hash = await hash_password(payload.password)
            existing_email.username = payload.username
            existing_email.full_name = payload.full_name
            existing_email.password_hash = password_hash
            try:
                await db.commit()
                await db.refresh(existing_email)
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

        password_hash = await hash_password(payload.password)
        try:
            user = await create_user(db, payload, password_hash)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already exists",
            )

    verification_otp = generate_otp()
    await set_email_verification_token(redis, str(user.email), verification_otp)
    logger.info("verification_otp_generated", email=str(user.email))
    background_tasks.add_task(publish_email_task, "verification_email", str(user.email), {"otp": verification_otp})

    background_tasks.add_task(
        publish_user_event,
        redis,
        "user.created",
        {
            "id": user.id,
            "email": str(user.email),
            "username": user.username,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
        },
    )

    if settings.debug:
        return {"message": f"User registered successfully. Verification OTP: {verification_otp}"}

    return {"message": "User registered successfully. Please verify your email using the OTP."}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access tokens",
    description="Authenticates a user via email and password. Returns JWT access and refresh tokens. Fails if email is unverified.",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Invalid email or password"},
        403: {"description": "Email not verified"},
        429: {"description": "Too many failed login attempts"},
    },
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    attempts = await get_login_attempts(redis, str(payload.email))
    if attempts >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    user = await get_user_by_email(db, str(payload.email))

    # Timing side-channel fix: always run bcrypt verification even if user doesn't exist.
    # This normalizes response time so attackers can't distinguish "user exists" from "user doesn't".
    if user is None:
        await db.close()
        await verify_password("dummy", DUMMY_HASH)
        await increment_login_attempts(redis, str(payload.email))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_hash = user.password_hash
    user_id = user.id
    user_is_verified = user.is_verified

    # Release connection back to pool BEFORE doing the slow bcrypt verification!
    await db.close()

    if not await verify_password(payload.password, password_hash):
        await increment_login_attempts(redis, str(payload.email))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user_is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    await reset_login_attempts(redis, str(payload.email))

    # Open a new short-lived session using the same engine as the request session
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(db.bind, expire_on_commit=False) as new_db:
        await new_db.execute(update(User).where(User.id == user_id).values(last_login_at=datetime.now(UTC)))
        await new_db.commit()

    access_token = create_access_token(str(user_id))
    refresh_token = create_refresh_token(str(user_id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Takes a valid refresh token and issues a new pair of access and refresh tokens. The old refresh token is blacklisted.",
    responses={
        200: {"description": "Successfully refreshed tokens"},
        401: {"description": "Invalid, expired, or blacklisted refresh token"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_refresh)
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        decode_payload = jwt.decode(
            payload.refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = decode_payload.get("sub")
        token_type = decode_payload.get("type")
        jti = decode_payload.get("jti")

        if user_id is None or token_type != "refresh" or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if await is_token_blacklisted(redis, jti):
        raise credentials_exception

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception

    exp = decode_payload.get("exp", 0)
    remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 0)
    await blacklist_token(redis, jti, remaining_ttl)

    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logs the user out by blacklisting both the current access token and the provided refresh token.",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Missing or invalid authorization header"},
    },
)
async def logout(
    payload: LogoutRequest,
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
):
    # Blacklist the access token (from Authorization header)
    try:
        access_payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        access_jti = access_payload.get("jti")
        if access_jti:
            exp = access_payload.get("exp", 0)
            remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 0)
            await blacklist_token(redis, access_jti, remaining_ttl)
    except JWTError:
        pass

    # Blacklist the refresh token (from request body)
    try:
        refresh_payload = jwt.decode(
            payload.refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        refresh_jti = refresh_payload.get("jti")
        if refresh_jti:
            exp = refresh_payload.get("exp", 0)
            remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 0)
            await blacklist_token(redis, refresh_jti, remaining_ttl)
    except JWTError:
        pass

    return {"message": "Logged out successfully"}


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Initiates the password reset flow. Sends a 6-digit OTP to the user's email if it exists.",
    responses={
        200: {"description": "Password reset instructions sent (or email ignored if non-existent)"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_forgot_password)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = await get_user_by_email(db, str(payload.email))

    if user is not None:
        reset_otp = generate_otp()
        await set_password_reset_token(redis, str(payload.email), reset_otp)
        logger.info("password_reset_otp_generated", email=str(payload.email))
        background_tasks.add_task(publish_email_task, "password_reset_email", str(payload.email), {"otp": reset_otp})

        if settings.debug:
            return {"message": f"Password reset OTP generated: {reset_otp}"}

    return {"message": "If the email exists, password reset instructions are ready."}


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password via OTP",
    description="Completes the password reset flow by verifying the 6-digit OTP and setting the new password.",
    responses={
        200: {"description": "Password successfully reset"},
        400: {"description": "Invalid or expired OTP"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_reset_password)
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = await get_user_by_email(db, str(payload.email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset request",
        )

    stored_token = await get_password_reset_token(redis, str(payload.email))
    if stored_token is None or not hmac.compare_digest(stored_token, payload.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    password_hash = await hash_password(payload.new_password)
    await update_user_password(db, user, password_hash)
    await delete_password_reset_token(redis, str(payload.email))
    await delete_cached_user_profile(redis, user.id)

    return {"message": "Password reset successful"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieves the profile information for the currently authenticated user. Uses Redis caching for high performance.",
    responses={200: {"description": "User profile returned"}, 401: {"description": "Not authenticated"}},
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Updates the profile information (username, full_name) for the currently authenticated user.",
    responses={
        200: {"description": "User profile successfully updated"},
        401: {"description": "Not authenticated"},
        409: {"description": "Username already taken"},
    },
)
async def update_me(
    payload: UpdateUserRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    try:
        updated_user = await update_user(db, current_user, payload)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    await delete_cached_user_profile(redis, updated_user.id)

    response_data = UserResponse.model_validate(updated_user).model_dump(mode="json")
    await set_cached_user_profile(redis, updated_user.id, response_data)

    await publish_user_event(
        redis,
        "user.updated",
        {
            "id": updated_user.id,
            "email": str(updated_user.email),
            "username": updated_user.username,
            "full_name": updated_user.full_name,
        },
    )

    return response_data


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email via OTP",
    description="Verifies a user's email address using the 6-digit OTP sent during registration.",
    responses={
        200: {"description": "Email successfully verified"},
        400: {"description": "Invalid or expired verification token"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit(settings.rate_limit_verify_email)
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = await get_user_by_email(db, str(payload.email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification request",
        )

    stored_token = await get_email_verification_token(redis, str(payload.email))
    if stored_token is None or not hmac.compare_digest(stored_token, payload.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    await mark_user_verified(db, user)
    await delete_email_verification_token(redis, str(payload.email))
    await delete_cached_user_profile(redis, user.id)
    background_tasks.add_task(publish_email_task, "welcome_email", str(user.email), {"full_name": user.full_name})

    background_tasks.add_task(
        publish_user_event,
        redis,
        "user.verified",
        {
            "id": user.id,
            "email": str(user.email),
            "is_verified": True,
        },
    )

    return {"message": "Email verified successfully"}


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification OTP",
    description="Generates and sends a new 6-digit verification OTP to the user's email.",
    responses={200: {"description": "Verification instructions resent"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit(settings.rate_limit_resend_verification)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = await get_user_by_email(db, str(payload.email))

    if user is None:
        return {"message": "If the email exists, verification instructions are ready."}

    if user.is_verified:
        return {"message": "Email is already verified"}

    verification_otp = generate_otp()
    await set_email_verification_token(redis, str(payload.email), verification_otp)
    logger.info("verification_otp_regenerated", email=str(payload.email))
    background_tasks.add_task(publish_email_task, "verification_email", str(payload.email), {"otp": verification_otp})

    if settings.debug:
        return {"message": f"Verification OTP generated: {verification_otp}"}

    return {"message": "If the email exists, verification instructions are ready."}


@router.get(
    "/me/skills",
    response_model=list[SkillResponse],
    summary="Get user skills",
    description="Retrieves the current user's learning skills and scores.",
    responses={200: {"description": "List of user skills"}, 401: {"description": "Not authenticated"}},
)
async def get_me_skills(current_user: User = Depends(get_current_user_db), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.learning import UserSkillScore

    result = await db.execute(select(UserSkillScore).filter_by(user_id=current_user.id))
    return result.scalars().all()


@router.get(
    "/me/events",
    response_model=list[LearningEventResponse],
    summary="Get user learning events",
    description="Retrieves the current user's recent learning events (max 100).",
    responses={200: {"description": "List of learning events"}, 401: {"description": "Not authenticated"}},
)
async def get_me_events(current_user: User = Depends(get_current_user_db), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.learning import LearningEvent

    result = await db.execute(
        select(LearningEvent).filter_by(user_id=current_user.id).order_by(LearningEvent.created_at.desc()).limit(100)
    )
    return result.scalars().all()

from app.schemas.profile import FullUserProfileResponse, PublicUserProfileResponse
from app.models.profile import UserProfile
from app.models.learning import UserStats, DailyActivity, UserSkillScore, UserAchievement, Achievement, LearningEvent

FULL_PROFILE_CACHE_TTL = 60  # 60 seconds

def _full_profile_cache_key(user_id: int) -> str:
    return f"user:full_profile:{user_id}"

@router.get(
    "/me/profile",
    response_model=FullUserProfileResponse,
    summary="Get full user profile",
    description="Returns the aggregated user profile, stats, skills, achievements, and heatmap. Redis-cached for 60s.",
)
async def get_user_full_profile(
    current_user: User = Depends(get_current_user_db), 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    import json as _json

    # 1. Try Redis cache first
    cache_key = _full_profile_cache_key(current_user.id)
    cached = await redis.get(cache_key)
    if cached:
        return _json.loads(cached)

    # 2. Sequential queries (asyncpg doesn't support concurrent queries on one connection)
    profile_res = await db.execute(select(UserProfile).filter_by(user_id=current_user.id))
    profile = profile_res.scalar_one_or_none()

    stats_res = await db.execute(select(UserStats).filter_by(user_id=current_user.id))
    stats = stats_res.scalar_one_or_none()

    heatmap_res = await db.execute(
        select(DailyActivity)
        .filter_by(user_id=current_user.id)
        .order_by(DailyActivity.activity_date.desc())
        .limit(365)
    )
    heatmap = heatmap_res.scalars().all()

    skills_res = await db.execute(select(UserSkillScore).filter_by(user_id=current_user.id))
    skills = skills_res.scalars().all()

    ach_res = await db.execute(
        select(Achievement, UserAchievement.earned_at)
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = [
        {"title": a.title, "description": a.description, "icon_url": a.icon_url, "earned_at": earned_at.isoformat()}
        for a, earned_at in ach_res.all()
    ]

    events_res = await db.execute(
        select(LearningEvent)
        .filter_by(user_id=current_user.id)
        .order_by(LearningEvent.created_at.desc())
        .limit(10)
    )
    recent_activity = events_res.scalars().all()

    # 3. Build response
    response_data = {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat(),

        "bio": profile.bio if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "github_url": profile.github_url if profile else None,
        "linkedin_url": profile.linkedin_url if profile else None,
        "headline": profile.headline if profile else None,
        "location": profile.location if profile else None,
        "institution": profile.institution if profile else None,
        "preferred_language": profile.preferred_language if profile else None,
        "resume_url": profile.resume_url if profile else None,

        "stats": {
            "problems_solved_total": stats.problems_solved_total if stats else 0,
            "problems_solved_easy": stats.problems_solved_easy if stats else 0,
            "problems_solved_medium": stats.problems_solved_medium if stats else 0,
            "problems_solved_hard": stats.problems_solved_hard if stats else 0,
            "total_submissions": stats.total_submissions if stats else 0,
            "acceptance_rate": stats.acceptance_rate if stats else 0.0,
            "interviews_completed": stats.interviews_completed if stats else 0,
            "avg_interview_score": stats.avg_interview_score if stats else 0.0,
            "best_interview_score": stats.best_interview_score if stats else 0,
            "current_streak": stats.current_streak if stats else 0,
            "longest_streak": stats.longest_streak if stats else 0,
            "last_activity_date": stats.last_activity_date.isoformat() if stats and stats.last_activity_date else None,
            "rating": stats.rating if stats else 0,
        },
        "heatmap": [
            {
                "activity_date": h.activity_date.isoformat(),
                "problems_solved": h.problems_solved,
                "problems_attempted": h.problems_attempted,
                "submissions_count": h.submissions_count,
                "interviews_done": h.interviews_done,
                "study_minutes": h.study_minutes,
            } for h in heatmap
        ],
        "skills": [
            {"domain": s.domain, "score": s.score, "problems_solved": s.problems_solved, "interviews_done": s.interviews_done}
            for s in skills
        ],
        "achievements": achievements,
        "recent_activity": [
            {
                "event_type": e.event_type,
                "reference_id": e.reference_id,
                "score_change": e.score_change,
                "domain": e.domain,
                "metadata_json": e.metadata_json,
                "created_at": e.created_at.isoformat(),
            } for e in recent_activity
        ],
    }

    # 4. Cache in Redis
    await redis.set(cache_key, _json.dumps(response_data), ex=FULL_PROFILE_CACHE_TTL)

    return response_data

@router.get(
    "/profile/{username}",
    response_model=PublicUserProfileResponse,
    summary="Get public user profile",
    description="Returns the aggregated public user profile. Redis-cached for 60s.",
)
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    import json as _json

    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cache_key = f"user:public_profile:{user.id}"
    cached = await redis.get(cache_key)
    if cached:
        return _json.loads(cached)

    profile_res = await db.execute(select(UserProfile).filter_by(user_id=user.id))
    profile = profile_res.scalar_one_or_none()

    stats_res = await db.execute(select(UserStats).filter_by(user_id=user.id))
    stats = stats_res.scalar_one_or_none()

    heatmap_res = await db.execute(
        select(DailyActivity)
        .filter_by(user_id=user.id)
        .order_by(DailyActivity.activity_date.desc())
        .limit(365)
    )
    heatmap = heatmap_res.scalars().all()

    skills_res = await db.execute(select(UserSkillScore).filter_by(user_id=user.id))
    skills = skills_res.scalars().all()

    ach_res = await db.execute(
        select(Achievement, UserAchievement.earned_at)
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
        .filter(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.earned_at.desc())
    )
    achievements = [
        {"title": a.title, "description": a.description, "icon_url": a.icon_url, "earned_at": earned_at.isoformat()}
        for a, earned_at in ach_res.all()
    ]

    events_res = await db.execute(
        select(LearningEvent)
        .filter_by(user_id=user.id)
        .order_by(LearningEvent.created_at.desc())
        .limit(10)
    )
    recent_activity = events_res.scalars().all()

    response_data = {
        "username": user.username,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat(),

        "bio": profile.bio if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "github_url": profile.github_url if profile else None,
        "linkedin_url": profile.linkedin_url if profile else None,
        "headline": profile.headline if profile else None,
        "location": profile.location if profile else None,
        "institution": profile.institution if profile else None,
        "preferred_language": profile.preferred_language if profile else None,
        "resume_url": profile.resume_url if profile else None,

        "stats": {
            "problems_solved_total": stats.problems_solved_total if stats else 0,
            "problems_solved_easy": stats.problems_solved_easy if stats else 0,
            "problems_solved_medium": stats.problems_solved_medium if stats else 0,
            "problems_solved_hard": stats.problems_solved_hard if stats else 0,
            "total_submissions": stats.total_submissions if stats else 0,
            "acceptance_rate": stats.acceptance_rate if stats else 0.0,
            "interviews_completed": stats.interviews_completed if stats else 0,
            "avg_interview_score": stats.avg_interview_score if stats else 0.0,
            "best_interview_score": stats.best_interview_score if stats else 0,
            "current_streak": stats.current_streak if stats else 0,
            "longest_streak": stats.longest_streak if stats else 0,
            "last_activity_date": stats.last_activity_date.isoformat() if stats and stats.last_activity_date else None,
            "rating": stats.rating if stats else 0,
        },
        "heatmap": [
            {
                "activity_date": h.activity_date.isoformat(),
                "problems_solved": h.problems_solved,
                "problems_attempted": h.problems_attempted,
                "submissions_count": h.submissions_count,
                "interviews_done": h.interviews_done,
                "study_minutes": h.study_minutes,
            } for h in heatmap
        ],
        "skills": [
            {"domain": s.domain, "score": s.score, "problems_solved": s.problems_solved, "interviews_done": s.interviews_done}
            for s in skills
        ],
        "achievements": achievements,
        "recent_activity": [
            {
                "event_type": e.event_type,
                "reference_id": e.reference_id,
                "score_change": e.score_change,
                "domain": e.domain,
                "metadata_json": e.metadata_json,
                "created_at": e.created_at.isoformat(),
            } for e in recent_activity
        ],
    }

    await redis.set(cache_key, _json.dumps(response_data), ex=FULL_PROFILE_CACHE_TTL)
    return response_data

from app.schemas.profile import UpdateProfileDetailsRequest, UserPreferenceResponse, UpdateUserPreferenceRequest, AchievementResponse
from app.models.profile import UserPreference

@router.patch("/me/profile/details", response_model=dict, summary="Update profile details")
async def update_profile_details(
    payload: UpdateProfileDetailsRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    res = await db.execute(select(UserProfile).filter_by(user_id=current_user.id))
    profile = res.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    await db.commit()
    await db.refresh(profile)
    
    await redis.delete(_full_profile_cache_key(current_user.id))
    return {"message": "Profile details updated"}

@router.get("/me/preferences", response_model=UserPreferenceResponse, summary="Get user preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(UserPreference).filter_by(user_id=current_user.id))
    pref = res.scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref

@router.put("/me/preferences", response_model=UserPreferenceResponse, summary="Update user preferences")
async def update_preferences(
    payload: UpdateUserPreferenceRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(UserPreference).filter_by(user_id=current_user.id))
    pref = res.scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pref, key, value)
        
    await db.commit()
    await db.refresh(pref)
    return pref

@router.get("/achievements", response_model=list[AchievementResponse], summary="List all global achievements")
async def list_achievements(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Achievement))
    achievements = res.scalars().all()
    # Mocking earned_at for the global list to satisfy response model
    from datetime import datetime, UTC
    return [
        {
            "title": a.title,
            "description": a.description,
            "icon_url": a.icon_url,
            "earned_at": datetime.now(UTC)
        } for a in achievements
    ]

