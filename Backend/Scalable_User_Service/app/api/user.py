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
    from app.services.auth_service import AuthService
    verification_otp = await AuthService.signup(payload, background_tasks, db, redis)
    
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
    from app.services.auth_service import AuthService
    access_token, refresh_token = await AuthService.login(payload, db, redis)

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

    new_access_token = create_access_token(str(user.id), username = user.username, email = user.email)
    new_refresh_token = create_refresh_token(str(user.id), username = user.username, email = user.email)

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
    await redis.publish("user_events", f"user.verified:{user.id}")
    
    await delete_email_verification_token(redis, str(payload.email))
    await delete_cached_user_profile(redis, user.id)
    background_tasks.add_task(publish_email_task, "welcome_email", str(user.email), {"full_name": user.full_name})

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


from app.schemas.profile import FullUserProfileResponse, PublicUserProfileResponse
from app.models.profile import UserProfile
from app.models.learning import UserAchievement, Achievement

FULL_PROFILE_CACHE_TTL = 60  # 60 seconds

def _full_profile_cache_key(user_id: int) -> str:
    return f"user:full_profile:{user_id}"

@router.get(
    "/me/profile",
    response_model=FullUserProfileResponse,
    summary="Get full user profile",
    description="Returns the aggregated user profile and achievements. Redis-cached for 60s.",
)
async def get_user_full_profile(
    current_user: User = Depends(get_current_user_db), 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    from app.services.profile_service import ProfileService
    return await ProfileService.get_user_full_profile(current_user, db, redis)


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
    from app.services.profile_service import ProfileService
    return await ProfileService.get_public_profile(username, db, redis)

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

