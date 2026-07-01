import json
from livekit.api import AccessToken, VideoGrants
from app.config import settings

def generate_livekit_token(identity: str, room_name: str, user_id: str = "guest_user", interview_type: str = "general", ai_selected_questions: list = None) -> str:
    """
    Generates a secure Access Token with embedded candidate metadata.
    """
    token = AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )
    
    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True
    )
    
    token.with_identity(identity)
    token.with_name(identity)
    token.with_grants(grants)
    
    # Embed metadata into the participant token
    metadata = {
        "candidate_name": identity,
        "user_id": user_id,
        "interview_type": interview_type,
        "ai_selected_questions": ai_selected_questions or []
    }
    token.with_metadata(json.dumps(metadata))
    
    return token.to_jwt()