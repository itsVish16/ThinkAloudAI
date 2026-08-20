import hmac
from datetime import UTC, datetime

import structlog
from fastapi import BackgroundTasks, HTTPException, status
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignupRequest,
    VerifyEmailRequest,
)
from app.services.cache import (
    MAX_LOGIN_ATTEMPTS,
    blacklist_token,
    delete_cached_user_profile,
    delete_email_verification_token,
    delete_password_reset_token,
    get_email_verification_token,
    get_login_attempts,
    get_password_reset_token,
    increment_login_attempts,
    is_token_blacklisted,
    reset_login_attempts,
    set_email_verification_token,
    set_password_reset_token,
)
from app.services.email_queue import enqueue_email
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    mark_user_verified,
    update_last_login,
    update_user_password,
)

logger = structlog.get_logger(__name__)


class AuthService:
    @staticmethod
    async def signup(
        payload: SignupRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession,
        redis: Redis,
    ) -> str:
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
                    if not existing_username.is_verified and existing_username.created_at:
                        age = (datetime.now(UTC).replace(tzinfo=None) - existing_username.created_at.replace(tzinfo=None)).total_seconds()
                        if age > 86400:
                            await db.delete(existing_username)
                            await db.flush()
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail="Username is already taken",
                            )
                    else:
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
                if not existing_username.is_verified and existing_username.created_at:
                    age = (datetime.now(UTC).replace(tzinfo=None) - existing_username.created_at.replace(tzinfo=None)).total_seconds()
                    if age > 86400:
                        await db.delete(existing_username)
                        await db.flush()
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Username is already taken",
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username is already taken",
                    )

            password_hash = await hash_password(payload.password)
            try:
                user = await create_user(db, payload, password_hash)
            except IntegrityError:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or username already exists",
                )

        verification_otp = generate_otp()
        await set_email_verification_token(redis, str(user.email), verification_otp)
        await redis.publish("user_events", f"user.created:{user.id}")

        logger.info("verification_otp_generated", email=str(user.email))
        background_tasks.add_task(enqueue_email, "verification_email", str(user.email), {"otp": verification_otp})

        return verification_otp

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession, redis: Redis) -> tuple[str, str]:
        attempts = await get_login_attempts(redis, str(payload.email))
        if attempts >= MAX_LOGIN_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )

        user = await get_user_by_email(db, str(payload.email))

        if user is None:
            await verify_password("dummy", DUMMY_HASH)
            await increment_login_attempts(redis, str(payload.email))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not await verify_password(payload.password, user.password_hash):
            await increment_login_attempts(redis, str(payload.email))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in",
            )

        await reset_login_attempts(redis, str(payload.email))
        await update_last_login(db, user)

        access_token = create_access_token(
            subject=str(user.id),
            username=user.username,
            email=str(user.email),
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            username=user.username,
            email=str(user.email),
        )

        return access_token, refresh_token

    @staticmethod
    async def refresh_token(
        payload: RefreshTokenRequest,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

        try:
            decode_payload = jwt.decode(
                payload.refresh_token,
                settings.JWT_SECRET_KEY,
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
        remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 1)
        await blacklist_token(redis, jti, remaining_ttl)

        new_access_token = create_access_token(
            subject=str(user.id),
            username=user.username,
            email=str(user.email),
        )
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            username=user.username,
            email=str(user.email),
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def logout(
        token: str,
        payload: LogoutRequest,
        redis: Redis,
    ) -> dict:
        # Blacklist access token
        try:
            access_payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.algorithm])
            access_jti = access_payload.get("jti")
            if access_jti:
                exp = access_payload.get("exp", 0)
                remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 1)
                await blacklist_token(redis, access_jti, remaining_ttl)
        except JWTError:
            pass

        # Blacklist refresh token
        try:
            refresh_payload = jwt.decode(
                payload.refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.algorithm],
            )
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                exp = refresh_payload.get("exp", 0)
                remaining_ttl = max(int(exp - datetime.now(UTC).timestamp()), 1)
                await blacklist_token(redis, refresh_jti, remaining_ttl)
        except JWTError:
            pass

        return {"message": "Logged out successfully"}

    @staticmethod
    async def forgot_password(
        payload: ForgotPasswordRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        user = await get_user_by_email(db, str(payload.email))

        if user is not None:
            reset_otp = generate_otp()
            await set_password_reset_token(redis, str(payload.email), reset_otp)
            logger.info("password_reset_otp_generated", email=str(payload.email))
            background_tasks.add_task(
                enqueue_email, "password_reset_email", str(payload.email), {"otp": reset_otp}
            )

            if settings.debug:
                return {"message": f"Password reset OTP generated: {reset_otp}"}

        return {"message": "If the email exists, password reset instructions are ready."}

    @staticmethod
    async def reset_password(
        payload: ResetPasswordRequest,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        attempts_key = f"user:otp_attempts:{payload.email}"
        attempts = int(await redis.get(attempts_key) or 0)
        if attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed OTP attempts. Please request a new OTP after 15 minutes.",
            )

        user = await get_user_by_email(db, str(payload.email))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset request",
            )

        stored_token = await get_password_reset_token(redis, str(payload.email))
        if stored_token is None or not hmac.compare_digest(stored_token, payload.otp):
            new_attempts = await redis.incr(attempts_key)
            if new_attempts == 1:
                await redis.expire(attempts_key, 900)
            if new_attempts >= 5:
                await delete_password_reset_token(redis, str(payload.email))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed OTP attempts. Please request a new OTP after 15 minutes.",
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        
        await redis.delete(attempts_key)

        password_hash = await hash_password(payload.new_password)
        await update_user_password(db, user, password_hash)
        await delete_password_reset_token(redis, str(payload.email))
        await delete_cached_user_profile(redis, user.id)

        return {"message": "Password reset successful"}

    @staticmethod
    async def verify_email(
        payload: VerifyEmailRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        attempts_key = f"user:otp_attempts:{payload.email}"
        attempts = int(await redis.get(attempts_key) or 0)
        if attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed OTP attempts. Please request a new OTP after 15 minutes.",
            )

        user = await get_user_by_email(db, str(payload.email))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification request",
            )

        stored_token = await get_email_verification_token(redis, str(payload.email))
        if stored_token is None or not hmac.compare_digest(stored_token, payload.token):
            new_attempts = await redis.incr(attempts_key)
            if new_attempts == 1:
                await redis.expire(attempts_key, 900)
            if new_attempts >= 5:
                await delete_email_verification_token(redis, str(payload.email))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed OTP attempts. Please request a new OTP after 15 minutes.",
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )
        
        await redis.delete(attempts_key)

        await mark_user_verified(db, user)
        await redis.publish("user_events", f"user.verified:{user.id}")

        await delete_email_verification_token(redis, str(payload.email))
        await delete_cached_user_profile(redis, user.id)
        background_tasks.add_task(
            enqueue_email, "welcome_email", str(user.email), {"full_name": user.full_name}
        )

        return {"message": "Email verified successfully"}

    @staticmethod
    async def resend_verification(
        payload: ResendVerificationRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        user = await get_user_by_email(db, str(payload.email))

        if user is None:
            return {"message": "If the email exists, verification instructions are ready."}

        if user.is_verified:
            return {"message": "Email is already verified"}

        verification_otp = generate_otp()
        await set_email_verification_token(redis, str(payload.email), verification_otp)
        logger.info("verification_otp_regenerated", email=str(payload.email))
        background_tasks.add_task(
            enqueue_email, "verification_email", str(payload.email), {"otp": verification_otp}
        )

        if settings.debug:
            return {"message": f"Verification OTP generated: {verification_otp}"}

        return {"message": "If the email exists, verification instructions are ready."}
