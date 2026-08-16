import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db.redis import get_redis
from app.models.user import User
from app.schemas.profile import (
    AchievementResponse,
    FullUserProfileResponse,
    PublicUserProfileResponse,
    UpdateProfileDetailsRequest,
    UpdateUserPreferenceRequest,
    UserPreferenceResponse,
)
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
from app.services.auth_service import AuthService
from app.services.cache import (
    get_cached_user_profile,
    is_token_blacklisted,
    set_cached_user_profile,
)
from app.services.profile_service import ProfileService
from app.services.user_service import UserService, get_user_by_id

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
logger = structlog.get_logger(__name__)


def _decode_and_validate_token(token: str, expected_type: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != expected_type:
            logger.error("JWT decode validation failed", user_id=user_id, token_type=token_type, expected=expected_type)
            raise credentials_exception
    except JWTError as e:
        logger.error("JWT decoding error", error=str(e))
        raise credentials_exception

    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = _decode_and_validate_token(token, "access")
    user_id = payload["sub"]

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        logger.error("Token is blacklisted")
        raise credentials_exception

    cached_profile = await get_cached_user_profile(redis, int(user_id))
    if cached_profile is not None:
        return cached_profile

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        logger.error("User not found for token subject", user_id=user_id)
        raise credentials_exception

    response_data = UserResponse.model_validate(user).model_dump(mode="json")
    await set_cached_user_profile(redis, user.id, response_data)
    return response_data


async def get_current_user_db(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = _decode_and_validate_token(token, "access")
    user_id = payload["sub"]

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        raise credentials_exception

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and sends a 6-digit OTP for email verification.",
)
@limiter.limit(settings.rate_limit_signup)
async def signup(
    request: Request,
    payload: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    verification_otp = await AuthService.signup(payload, background_tasks, db, redis)
    if settings.debug:
        return {"message": f"User registered successfully. Verification OTP: {verification_otp}"}
    return {"message": "User registered successfully. Please verify your email using the OTP."}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access tokens",
    description="Authenticates a user via email and password. Returns JWT access and refresh tokens.",
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
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
    description="Takes a valid refresh token and issues a new pair of access and refresh tokens.",
)
@limiter.limit(settings.rate_limit_refresh)
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.refresh_token(payload, db, redis)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logs the user out by blacklisting both the current access token and refresh token.",
)
async def logout(
    payload: LogoutRequest,
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.logout(token, payload, redis)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Initiates the password reset flow by sending an OTP.",
)
@limiter.limit(settings.rate_limit_forgot_password)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.forgot_password(payload, background_tasks, db, redis)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password via OTP",
    description="Verifies the OTP and resets the user password.",
)
@limiter.limit(settings.rate_limit_reset_password)
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.reset_password(payload, db, redis)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieves profile information for the authenticated user.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Updates username or full_name for the authenticated user.",
)
async def update_me(
    payload: UpdateUserRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await UserService.update_me(current_user, payload, db, redis)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email via OTP",
    description="Verifies user email address using OTP.",
)
@limiter.limit(settings.rate_limit_verify_email)
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.verify_email(payload, background_tasks, db, redis)


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification OTP",
    description="Generates and sends a new verification OTP.",
)
@limiter.limit(settings.rate_limit_resend_verification)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await AuthService.resend_verification(payload, background_tasks, db, redis)


@router.get(
    "/me/profile",
    response_model=FullUserProfileResponse,
    summary="Get full user profile",
    description="Returns full aggregated user profile and achievements.",
)
async def get_user_full_profile(
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await ProfileService.get_user_full_profile(current_user, db, redis)


@router.get(
    "/profile/{username}",
    response_model=PublicUserProfileResponse,
    summary="Get public user profile",
    description="Returns aggregated public profile for a username.",
)
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await ProfileService.get_public_profile(username, db, redis)


@router.patch("/me/profile/details", response_model=dict, summary="Update profile details")
async def update_profile_details(
    payload: UpdateProfileDetailsRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await ProfileService.update_profile_details(current_user.id, payload, db, redis)


@router.get("/me/preferences", response_model=UserPreferenceResponse, summary="Get user preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    return await ProfileService.get_preferences(current_user.id, db)


@router.put("/me/preferences", response_model=UserPreferenceResponse, summary="Update user preferences")
async def update_preferences(
    payload: UpdateUserPreferenceRequest,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    return await ProfileService.update_preferences(current_user.id, payload, db)


@router.get("/achievements", response_model=list[AchievementResponse], summary="List all global achievements")
async def list_achievements(db: AsyncSession = Depends(get_db)):
    return await ProfileService.list_achievements(db)
