import jwt
import logging
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger("auth")

async def get_current_user(request: Request) -> dict:
    """
    Decodes and verifies a JWT token issued by the external User Service statelessly.
    Resilient to formatting issues (e.g. raw token, Bearer prefix, or duplicate prefixes).
    """
    # Dev mode: skip auth entirely when User Service is unavailable
    if settings.AUTH_BYPASS:
        return {
            "user_id": "dev_user",
            "email": "dev@localhost",
            "username": "Developer",
            "full_name": "Dev User",
            "is_verified": True
        }
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Fallback to query param (useful for SSE/WebSockets)
        auth_header = request.query_params.get("token")
    if not auth_header:
        # Fallback to alternative common header names
        auth_header = request.headers.get("token") or request.headers.get("x-access-token")
        
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Clean up the token string to handle any prefix format
    token = auth_header.strip()
    
    # Handle duplicate/single Bearer prefixes case-insensitively
    prefixes = ["bearer ", "Bearer "]
    for prefix in prefixes:
        while token.lower().startswith(prefix.lower()):
            token = token[len(prefix):].strip()
            
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Stateless JWT verification using shared secret key
        payload = jwt.decode(
            token,
            settings.jwt_secret, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # The User Service sets 'sub' to session_id/user_id in Main Service
        # We need the user_id (which might be in sub or another claim)
        # We will extract whatever is available
        user_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
        
        if not user_id:
            raise credentials_exception
            
        username = payload.get("username") or payload.get("email", "").split("@")[0] or "Candidate"
        full_name = payload.get("full_name") or payload.get("name") or username

        return {
            "user_id": str(user_id),
            "email": payload.get("email", "unknown@domain.com"),
            "username": username,
            "full_name": full_name,
            "is_verified": payload.get("is_verified", True),
            "raw_token": token
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        raise credentials_exception

