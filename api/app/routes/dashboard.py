from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from app.database import get_db
from app.models import LineImage, User
from app.security import get_current_user

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
