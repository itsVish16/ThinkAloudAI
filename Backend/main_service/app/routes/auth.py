from fastapi import APIRouter
from pydantic import BaseModel
import jwt
from datetime import UTC, datetime, timedelta
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

class TokenRequest(BaseModel):
    session_id: str

@router.post("/token")
def create_token(request: TokenRequest):
    """
    Generate a JWT token for the given session_id.
    """
    payload = {
        "sub": request.session_id,
        "exp": datetime.now(UTC) + timedelta(days=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
