"""
Review Queue Routes — PiNE AI

Human-in-the-loop for uncertain and viral claims.
Reviewers correct verdicts → stored as feedback → triggers auto-retraining.

Priority tiers:
  VIRAL     — is_viral=True (spreading fast, highest urgency)
  TRENDING  — is_trending=True
  COORDINATED — suspected bot/campaign activity
  UNCERTAIN — confidence 0.45–0.55 (model unsure)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from database import get_db
from app.models import ClaimRecord, UserFeedback, User, VelocityRecord
from app.auth import get_current_user
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


class ReviewSubmission(BaseModel):
    """User's review decision for an uncertain claim"""
    claim_id: int
    verdict: str  # "real" or "fake"
    confidence: Optional[float] = None
    notes: Optional[str] = None


class ReviewQueueItem(BaseModel):
    """Claim in review queue with all analysis data"""
    id: int
    claim_text: str
    current_verdict: str
    confidence: float
    ml_score: float
    ai_score: Optional[float]
    evidence_score: Optional[float]
    created_at: datetime
    # Priority signals
    velocity_score: Optional[float] = None
    is_viral: Optional[bool] = None
    is_trending: Optional[bool] = None
    cluster_size: Optional[int] = None
    # Review status
    already_reviewed: bool = False


class ReviewStats(BaseModel):
    """Statistics about review queue"""
    total_pending: int
    reviewed_today: int
    reviewed_total: int
    avg_confidence_gain: Optional[float]
    high_priority_count: int


@router.get("/queue", response_model=List[ReviewQueueItem])
def get_review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    priority: str = Query(default="all", pattern="^(all|viral|trending|coordinated|uncertain)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get claims that need human review.

    Priority filters:
    - viral       — spreading fast right now (highest urgency)
    - trending    — gaining traction
    - coordinated — suspected bot/campaign activity
    - uncertain   — model confidence 0.45–0.55
    - all         — all of the above
    """
    # Base query — all claims
    query = db.query(ClaimRecord)

    if priority == "uncertain":
        query = query.filter(
            and_(ClaimRecord.confidence >= 0.45, ClaimRecord.confidence <= 0.55)
        )
    elif priority == "viral":
        query = query.join(
            VelocityRecord, ClaimRecord.claim_hash == VelocityRecord.claim_hash
        ).filter(VelocityRecord.is_viral == True)
    elif priority == "trending":
        query = query.join(
            VelocityRecord, ClaimRecord.claim_hash == VelocityRecord.claim_hash
        ).filter(VelocityRecord.is_trending == True)
    elif priority == "coordinated":
        query = query.join(
            VelocityRecord, ClaimRecord.claim_hash == VelocityRecord.claim_hash
        ).filter(VelocityRecord.is_coordinated == True)
    else:  # all — uncertain OR viral/trending/coordinated
        query = query.filter(
            or_(
                and_(ClaimRecord.confidence >= 0.45, ClaimRecord.confidence <= 0.55),
                ClaimRecord.claim_hash.in_(
                    db.query(VelocityRecord.claim_hash).filter(
                        or_(
                            VelocityRecord.is_viral == True,
                            VelocityRecord.is_trending == True,
                            VelocityRecord.is_coordinated == True,
                        )
                    )
                )
            )
        )
    
    # Order by most recent first
    query = query.order_by(desc(ClaimRecord.created_at))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    claims = query.offset(offset).limit(limit).all()
    
    # Enrich with velocity data and check review status
    result = []
    for claim in claims:
        # Get velocity data if exists
        velocity = db.query(VelocityRecord).filter(
            VelocityRecord.claim_hash == claim.claim_hash
        ).order_by(desc(VelocityRecord.created_at)).first()
        
        # Check if already reviewed by this user
        already_reviewed = db.query(UserFeedback).filter(
            and_(
                UserFeedback.user_id == user.id,
                UserFeedback.claim_text == claim.claim_text
            )
        ).first() is not None
        
        result.append(ReviewQueueItem(
            id=claim.id,
            claim_text=claim.claim_text,
            current_verdict=claim.verdict,
            confidence=claim.confidence,
            ml_score=claim.ml_score or 0.0,
            ai_score=claim.ai_score,
            evidence_score=claim.evidence_score,
            created_at=claim.created_at,
            velocity_score=velocity.velocity_score if velocity else None,
            is_viral=velocity.is_viral if velocity else None,
            is_trending=velocity.is_trending if velocity else None,
            cluster_size=velocity.cluster_size if velocity else None,
            already_reviewed=already_reviewed,
        ))
    
    logger.info(f"Review queue: {len(result)} items (total: {total}, priority: {priority})")
    return result


@router.post("/submit")
def submit_review(
    review: ReviewSubmission,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Submit a human review for a claim.
    - Stores correction in UserFeedback for retraining
    - Immediately triggers retraining if the claim is viral (high urgency)
    - Otherwise uses the normal threshold-based auto-retrain
    """
    if review.verdict not in ("real", "fake"):
        raise HTTPException(status_code=400, detail="verdict must be 'real' or 'fake'")

    claim = db.query(ClaimRecord).filter(ClaimRecord.id == review.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Check if already reviewed by this user
    existing = db.query(UserFeedback).filter(
        and_(
            UserFeedback.user_id == user.id,
            UserFeedback.claim_text == claim.claim_text
        )
    ).first()

    if existing:
        existing.actual     = review.verdict
        existing.confidence = review.confidence or claim.confidence
        existing.created_at = datetime.utcnow()
        logger.info("Updated review for claim %d by user %d", claim.id, user.id)
    else:
        feedback = UserFeedback(
            user_id    = user.id,
            claim_text = claim.claim_text[:1000],
            predicted  = claim.verdict,
            actual     = review.verdict,
            confidence = review.confidence or claim.confidence,
        )
        db.add(feedback)
        logger.info("New review claim %d by user %d: %s → %s",
                    claim.id, user.id, claim.verdict, review.verdict)

    db.commit()

    # Check if this is a viral claim — if so, trigger immediate retraining
    velocity = db.query(VelocityRecord).filter(
        VelocityRecord.claim_hash == claim.claim_hash
    ).order_by(desc(VelocityRecord.created_at)).first()

    is_viral_claim = velocity and (velocity.is_viral or velocity.is_trending)

    if is_viral_claim:
        # Immediate background retrain for viral misinformation
        logger.info("Viral claim reviewed — triggering immediate retraining")
        background_tasks.add_task(_trigger_retrain_for_viral, db, claim.claim_text, review.verdict)
        retrain_triggered = True
    else:
        # Normal threshold-based retrain check
        try:
            from app.analysis.continuous_learning import maybe_retrain
            retrain_status = maybe_retrain(db)
            retrain_triggered = retrain_status.get("triggered", False)
        except Exception as e:
            logger.debug("Continuous learning check failed: %s", e)
            retrain_triggered = False

    # WebSocket notification
    try:
        from app.websocket import notify_review_queue_update
        import asyncio
        asyncio.create_task(notify_review_queue_update("all"))
    except Exception:
        pass

    return {
        "success":          True,
        "message":          "Review submitted successfully",
        "claim_id":         claim.id,
        "verdict":          review.verdict,
        "is_viral_claim":   is_viral_claim,
        "retrain_triggered": retrain_triggered,
    }


def _trigger_retrain_for_viral(db, claim_text: str, correct_verdict: str):
    """
    Background task: immediately retrain when a viral claim is corrected.
    Adds the correction with high weight and runs retrain_from_feedback.py.
    """
    import threading
    from app.analysis.continuous_learning import _run_retrain
    from app.models import UserFeedback
    from sqlalchemy import func

    try:
        feedback_count = db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.predicted != UserFeedback.actual
        ).scalar() or 0

        logger.info("Viral claim retrain: %d total corrections, triggering now", feedback_count)
        thread = threading.Thread(
            target=_run_retrain,
            args=(feedback_count,),
            daemon=True,
            name="viral-retrain",
        )
        thread.start()
    except Exception as e:
        logger.error("Viral retrain trigger failed: %s", e)


@router.post("/collect-training-data")
def collect_training_data(
    topic: str = "misinformation",
    max_samples: int = Query(default=50, ge=10, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Collect labeled training samples from live news sources.
    Fetches real news (label=real) and debunked claims (label=fake)
    and stores them as UserFeedback for the next retraining cycle.
    """
    try:
        from app.analysis.news_aggregator import collect_training_samples
        samples = collect_training_samples(topic=topic, max_samples=max_samples)

        added = 0
        for s in samples:
            text = s.get("text", "").strip()
            if not text or len(text) < 30:
                continue
            label   = s.get("label", 0)
            verdict = "fake" if label == 1 else "real"
            # Store as auto-labeled feedback (user_id=None = system-generated)
            fb = UserFeedback(
                user_id    = None,
                claim_text = text[:1000],
                predicted  = "uncertain",
                actual     = verdict,
                confidence = 0.8,
            )
            db.add(fb)
            added += 1

        db.commit()
        logger.info("Collected %d training samples for topic: %s", added, topic)

        return {
            "success":        True,
            "samples_added":  added,
            "topic":          topic,
            "message":        f"Added {added} labeled samples. Retraining will trigger automatically.",
        }
    except Exception as e:
        logger.error("Training data collection failed: %s", e)
        raise HTTPException(500, f"Collection failed: {e}")


@router.get("/stats", response_model=ReviewStats)
def get_review_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get statistics about the review queue and user's review activity.
    """
    
    # Total pending reviews (uncertain claims)
    total_pending = db.query(ClaimRecord).filter(
        and_(
            ClaimRecord.confidence >= 0.45,
            ClaimRecord.confidence <= 0.55
        )
    ).count()
    
    # Reviews by this user today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    reviewed_today = db.query(UserFeedback).filter(
        and_(
            UserFeedback.user_id == user.id,
            UserFeedback.created_at >= today_start
        )
    ).count()
    
    # Total reviews by this user
    reviewed_total = db.query(UserFeedback).filter(
        UserFeedback.user_id == user.id
    ).count()
    
    # High priority count (viral + trending + coordinated)
    high_priority_count = db.query(ClaimRecord).join(
        VelocityRecord,
        ClaimRecord.claim_hash == VelocityRecord.claim_hash
    ).filter(
        and_(
            ClaimRecord.confidence >= 0.45,
            ClaimRecord.confidence <= 0.55,
            or_(
                VelocityRecord.is_viral == True,
                VelocityRecord.is_trending == True,
                VelocityRecord.is_coordinated == True
            )
        )
    ).count()
    
    # Calculate average confidence gain (simplified - would need model retraining to measure accurately)
    # For now, just return None
    avg_confidence_gain = None
    
    return ReviewStats(
        total_pending=total_pending,
        reviewed_today=reviewed_today,
        reviewed_total=reviewed_total,
        avg_confidence_gain=avg_confidence_gain,
        high_priority_count=high_priority_count,
    )


@router.delete("/feedback/{feedback_id}")
def delete_review(
    feedback_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a review (only your own reviews).
    """
    
    feedback = db.query(UserFeedback).filter(
        and_(
            UserFeedback.id == feedback_id,
            UserFeedback.user_id == user.id
        )
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    
    db.delete(feedback)
    db.commit()
    
    logger.info(f"Deleted review {feedback_id} by user {user.id}")
    
    return {"success": True, "message": "Review deleted"}


@router.get("/history")
def get_review_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get user's review history.
    """
    
    feedbacks = db.query(UserFeedback).filter(
        UserFeedback.user_id == user.id
    ).order_by(desc(UserFeedback.created_at)).offset(offset).limit(limit).all()
    
    return {
        "reviews": [
            {
                "id": fb.id,
                "claim_text": fb.claim_text,
                "predicted": fb.predicted,
                "actual": fb.actual,
                "confidence": fb.confidence,
                "created_at": fb.created_at,
            }
            for fb in feedbacks
        ],
        "total": db.query(UserFeedback).filter(UserFeedback.user_id == user.id).count(),
    }
