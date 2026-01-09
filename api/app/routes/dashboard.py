from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import LineImage
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
