from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.models import LineImage, User
from app.security import get_current_user
from app.schemas import UserActivityResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/verification-stats")
def get_verification_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return aggregate verification stats for line images."""
    # Exclude invalid (soft-deleted) lines from counts
    base_query = db.query(LineImage).filter(LineImage.is_invalid == False)  # noqa: E712

    total_lines = base_query.with_entities(func.count(LineImage.id)).scalar() or 0
    verified_lines = (
        base_query.filter(LineImage.verified == True)  # noqa: E712
        .with_entities(func.count(LineImage.id))
        .scalar()
        or 0
    )
    pending_review = (
        base_query
        .filter(LineImage.verified == False)  # noqa: E712
        .filter(LineImage.corrected_text.isnot(None))
        .with_entities(func.count(LineImage.id))
        .scalar()
        or 0
    )

    unverified_lines = max(total_lines - verified_lines - pending_review, 0)

    return {
        "total_lines": total_lines,
        "verified_lines": verified_lines,
        "unverified_lines": unverified_lines,
        "pending_reviews": pending_review,
    }


@router.get("/team-activity")
def get_team_activity(
    range: str = Query("weekly", description="Range for stats: weekly, monthly, all"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return verified line counts per reviewer (annotator activity)."""

    now = datetime.utcnow()
    if range == "weekly":
        since = now - timedelta(days=7)
    elif range == "monthly":
        since = now - timedelta(days=30)
    elif range == "all":
        since = None
    else:
        # default to weekly if invalid value provided
        since = now - timedelta(days=7)

    query = (
        db.query(
            User.id.label("user_id"),
            User.name.label("name"),
            func.count(LineImage.id).label("verified_lines"),
        )
        .join(LineImage, LineImage.reviewer_id == User.id)
        .filter(LineImage.is_invalid == False)  # noqa: E712
        .filter(LineImage.verified == True)  # noqa: E712
    )

    if since:
        query = query.filter(LineImage.updated_at >= since)

    results = (
        query
        .group_by(User.id, User.name)
        .order_by(func.count(LineImage.id).desc())
        .all()
    )

    return [
        {
            "user_id": str(row.user_id),
            "name": row.name,
            "verified_lines": row.verified_lines,
        }
        for row in results
    ]


@router.get("/verification-weekly")
def get_verification_weekly(
    days: int = Query(7, ge=1, le=60, description="Number of days to look back (default 7)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return daily verified/pending counts for the last N days."""

    since = datetime.utcnow() - timedelta(days=days - 1)

    day_trunc = func.date_trunc("day", LineImage.updated_at).label("day")
    day_label = func.to_char(func.date_trunc("day", LineImage.updated_at), "Dy").label("day_label")

    query = (
        db.query(
            day_trunc,
            day_label,
            func.sum(case((LineImage.verified == True, 1), else_=0)).label("verified"),  # noqa: E712
            func.sum(
                case(
                    (
                        (LineImage.verified == False) & (LineImage.corrected_text.isnot(None)),  # noqa: E712
                        1,
                    ),
                    else_=0,
                )
            ).label("pending"),
        )
        .filter(LineImage.is_invalid == False)  # noqa: E712
        .filter(LineImage.updated_at >= since)
        .group_by(day_trunc, day_label)
        .order_by(day_trunc.asc())
    )

    rows = query.all()

    return [
        {
            "day": row.day_label,
            "verified": int(row.verified or 0),
            "pending": int(row.pending or 0),
        }
        for row in rows
    ]

@router.get("/users/activity", response_model=List[UserActivityResponse])
def get_users_activity(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return user activity aggregation with line annotation and verification counts.
    
    Data sources:
    - linesAnnotated: count of lines created/assigned (LineImage.created_at)
    - linesVerified: count of verified lines (LineImage.verified == True)
    - lastActive: max(LineImage.created_at, LineImage.updated_at, User.last_login_at)
    - status: based on is_active and last_login_at
    """
    
    # Get all active users and their activity metrics
    results = db.query(
        User.id,
        User.name,
        User.email,
        User.role,
        User.is_active,
        User.last_login_at,
        func.count(LineImage.id).label("total_lines"),
        func.sum(case((LineImage.verified == True, 1), else_=0)).label("verified_lines"),  # noqa: E712
    ).outerjoin(
        LineImage,
        (LineImage.reviewer_id == User.id) & (LineImage.is_invalid == False)  # noqa: E712
    ).group_by(
        User.id,
        User.name,
        User.email,
        User.role,
        User.is_active,
        User.last_login_at,
    ).all()

    # For each user, also get their max activity timestamp
    activities = []
    for user in results:
        # Get the most recent activity timestamp for this user
        max_activity = db.query(
            func.greatest(
                func.max(LineImage.created_at),
                func.max(LineImage.updated_at),
                user.last_login_at
            )
        ).filter(
            LineImage.reviewer_id == user.id,
            LineImage.is_invalid == False  # noqa: E712
        ).scalar()

        # If no lineimage activity, use last_login_at
        last_active = max_activity or user.last_login_at

        # Determine status
        status = "active" if user.is_active else "inactive"

        activities.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": status,
            "linesAnnotated": user.total_lines or 0,
            "linesVerified": user.verified_lines or 0,
            "lastActive": last_active,
        })

    # Sort by most recent activity
    activities.sort(
        key=lambda x: x["lastActive"] if x["lastActive"] else datetime.min,
        reverse=True
    )

    return activities