from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from app.database import get_db
from app.models.dsa import CodeSubmission
from app.models.user_replica import UserProfileReplica
from app.schemas.user import UserProfileResponse, SubmissionSummary
from app.auth import verify_jwt

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the statistics and recent submissions for the authenticated user.
    Requires a valid JWT Bearer token. The JWT 'sub' contains the user ID.
    Submissions are stored by email, so we look up the user's email via the
    user_profile_replica table and match by either ID or email.
    """
    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(status_code=400, detail="Invalid token payload: 'sub' missing")

    # Look up user email from the replica table (populated by the event consumer)
    replica_result = await db.execute(
        select(UserProfileReplica).filter(UserProfileReplica.id == str(user_uuid))
    )
    replica = replica_result.scalars().first()
    email = replica.email if replica else None

    # Build OR filter: match by UUID or email (DSAPractice stores email as session_id)
    # Also ensure we only fetch actual submissions, not runs
    if email:
        filter_clause = and_(
            CodeSubmission.is_submission == True,
            or_(
                CodeSubmission.session_id == str(user_uuid),
                CodeSubmission.session_id == email
            )
        )
    else:
        filter_clause = and_(
            CodeSubmission.is_submission == True,
            CodeSubmission.session_id == str(user_uuid)
        )

    # Eager-load the related question to avoid N+1 queries
    query = (
        select(CodeSubmission)
        .options(selectinload(CodeSubmission.question))
        .filter(filter_clause)
        .order_by(CodeSubmission.created_at.desc())
    )
    result = await db.execute(query)
    all_submissions = result.scalars().all()

    # Only count Accepted submissions for profile stats
    submissions = [s for s in all_submissions if s.status == "Accepted"]
    total_submissions = len(submissions)

    solved = set()
    accepted_count = 0
    heatmap_dict = {}

    for s in submissions:
        solved.add(s.question_id)

        # Add to heatmap
        if s.created_at:
            date_str = s.created_at.strftime("%Y-%m-%d")
            heatmap_dict[date_str] = heatmap_dict.get(date_str, 0) + 1

    total_solved = len(solved)

    accuracy_percentage = 0.0
    total_all = len(all_submissions)
    accepted_count = len(submissions)
    if total_all > 0:
        accuracy_percentage = (accepted_count / total_all) * 100

    recent = []
    for s in all_submissions[:5]:
        recent.append(SubmissionSummary(
            id=s.id,
            question_id=s.question_id,
            question_title=s.question.title if s.question else "Unknown",
            language=s.language,
            status=s.status,
            created_at=s.created_at
        ))

    heatmap_data = [{"date": k, "count": v} for k, v in heatmap_dict.items()]
    
    # Calculate Streaks
    current_streak = 0
    max_streak = 0
    if heatmap_dict:
        import datetime
        
        # Sort dates descending
        sorted_dates = sorted(heatmap_dict.keys(), reverse=True)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Current Streak
        if sorted_dates and (sorted_dates[0] == today_str or sorted_dates[0] == yesterday_str):
            current_streak = 1
            idx = 0
            while idx < len(sorted_dates) - 1:
                d1 = datetime.datetime.strptime(sorted_dates[idx], "%Y-%m-%d").date()
                d2 = datetime.datetime.strptime(sorted_dates[idx+1], "%Y-%m-%d").date()
                if (d1 - d2).days == 1:
                    current_streak += 1
                    idx += 1
                else:
                    break
                    
        # Max Streak
        sorted_asc = sorted(heatmap_dict.keys())
        if sorted_asc:
            max_streak = 1
            cur = 1
            for i in range(len(sorted_asc) - 1):
                d1 = datetime.datetime.strptime(sorted_asc[i], "%Y-%m-%d").date()
                d2 = datetime.datetime.strptime(sorted_asc[i+1], "%Y-%m-%d").date()
                if (d2 - d1).days == 1:
                    cur += 1
                    max_streak = max(max_streak, cur)
                else:
                    cur = 1

    return UserProfileResponse(
        session_id=user_uuid,
        total_submissions=total_submissions,
        total_solved=total_solved,
        accuracy_percentage=round(accuracy_percentage, 2),
        current_streak=current_streak,
        max_streak=max_streak,
        heatmap=heatmap_data,
        recent_submissions=recent
    )
