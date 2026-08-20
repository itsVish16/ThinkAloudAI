from fastapi import APIRouter, Depends
from app.services.auth import get_current_user
from app.services.db import get_user_analytics
from app.services.events import redis_client

router = APIRouter(prefix="/api", tags=["analytics", "leaderboard"])


@router.get(
    "/interviews/me/analytics",
    summary="User Interview Analytics",
    description="Fetches aggregated interview statistics for the logged-in user to populate the dashboard."
)
async def my_interview_analytics(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await get_user_analytics(user_id)


@router.get(
    "/leaderboard",
    summary="Live Global Leaderboard",
    description="Fetches the top 10 users globally by their cumulative score."
)
async def get_leaderboard(current_user: dict = Depends(get_current_user)):
    top_users = await redis_client.zrevrange("global_leaderboard", 0, 9, withscores=True)
    
    leaderboard = []
    for i, (member, score) in enumerate(top_users):
        parts = member.split(":", 1)
        c_name = parts[1] if len(parts) > 1 else member
        leaderboard.append({
            "rank": i + 1,
            "candidate_name": c_name,
            "score": int(score)
        })
        
    username = current_user.get("username", "Candidate")
    user_id = current_user.get("user_id", "guest_user")
    member = f"{user_id}:{username}"
    user_rank = await redis_client.zrevrank("global_leaderboard", member)
    user_score = await redis_client.zscore("global_leaderboard", member)
    
    my_rank = {
        "rank": user_rank + 1 if user_rank is not None else None,
        "candidate_name": username,
        "score": int(user_score) if user_score is not None else 0
    }
    
    return {
        "leaderboard": leaderboard,
        "me": my_rank
    }
