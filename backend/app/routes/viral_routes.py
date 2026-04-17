"""
Viral Spread Detection Routes

Real-time monitoring of viral misinformation spread
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from database import get_db
from app.models import VelocityRecord, ClaimRecord
from app.analysis.velocity import get_stats, get_top_viral

router = APIRouter(prefix="/viral", tags=["viral"])
logger = logging.getLogger(__name__)


@router.get("/dashboard")
def get_viral_dashboard(db: Session = Depends(get_db)):
    """
    Get comprehensive viral spread dashboard data
    
    Returns:
        - Real-time velocity stats
        - Top viral claims (last 24h)
        - Trending claims
        - Historical spread patterns
        - Risk distribution
    """
    try:
        # Real-time velocity stats
        velocity_stats = get_stats()
        top_viral_live = get_top_viral(limit=20)
        
        # Database: Top viral claims from last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        viral_claims_db = db.query(VelocityRecord).filter(
            VelocityRecord.timestamp >= cutoff_time,
            VelocityRecord.is_viral == True
        ).order_by(desc(VelocityRecord.velocity_score)).limit(50).all()
        
        # Trending claims (high 1hr count but not viral)
        trending_claims_db = db.query(VelocityRecord).filter(
            VelocityRecord.timestamp >= cutoff_time,
            VelocityRecord.is_trending == True,
            VelocityRecord.is_viral == False
        ).order_by(desc(VelocityRecord.count_1hr)).limit(30).all()
        
        # Risk distribution (last 24h)
        risk_distribution = db.query(
            VelocityRecord.cooldown_level,
            func.count(VelocityRecord.id).label('count')
        ).filter(
            VelocityRecord.timestamp >= cutoff_time
        ).group_by(VelocityRecord.cooldown_level).all()
        
        risk_dist_dict = {level: count for level, count in risk_distribution}
        
        # Hourly spread pattern (last 24h)
        hourly_pattern = []
        for hour_offset in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=hour_offset+1)
            hour_end = datetime.utcnow() - timedelta(hours=hour_offset)
            
            hour_count = db.query(func.count(VelocityRecord.id)).filter(
                VelocityRecord.timestamp >= hour_start,
                VelocityRecord.timestamp < hour_end
            ).scalar()
            
            viral_count = db.query(func.count(VelocityRecord.id)).filter(
                VelocityRecord.timestamp >= hour_start,
                VelocityRecord.timestamp < hour_end,
                VelocityRecord.is_viral == True
            ).scalar()
            
            hourly_pattern.append({
                'hour': hour_start.strftime('%H:00'),
                'total_claims': hour_count,
                'viral_claims': viral_count
            })
        
        hourly_pattern.reverse()  # Oldest to newest
        
        # Format viral claims
        viral_claims_formatted = []
        for record in viral_claims_db:
            # Get claim details
            claim = db.query(ClaimRecord).filter(
                ClaimRecord.claim_hash == record.claim_hash
            ).first()
            
            viral_claims_formatted.append({
                'claim_hash': record.claim_hash,
                'claim_text': record.claim_text,
                'velocity_score': record.velocity_score,
                'count_5min': record.count_5min,
                'count_1hr': record.count_1hr,
                'count_24hr': record.count_24hr,
                'cooldown_level': record.cooldown_level,
                'cooldown_score': record.cooldown_score,
                'is_coordinated': record.is_coordinated,
                'cluster_size': record.cluster_size,
                'verdict': claim.verdict if claim else None,
                'timestamp': record.timestamp.isoformat()
            })
        
        # Format trending claims
        trending_claims_formatted = []
        for record in trending_claims_db:
            claim = db.query(ClaimRecord).filter(
                ClaimRecord.claim_hash == record.claim_hash
            ).first()
            
            trending_claims_formatted.append({
                'claim_hash': record.claim_hash,
                'claim_text': record.claim_text,
                'count_1hr': record.count_1hr,
                'count_24hr': record.count_24hr,
                'velocity_score': record.velocity_score,
                'verdict': claim.verdict if claim else None,
                'timestamp': record.timestamp.isoformat()
            })
        
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'realtime_stats': velocity_stats,
            'viral_claims': viral_claims_formatted,
            'trending_claims': trending_claims_formatted,
            'risk_distribution': {
                'VIRAL_PANIC': risk_dist_dict.get('VIRAL_PANIC', 0),
                'HIGH_CONCERN': risk_dist_dict.get('HIGH_CONCERN', 0),
                'CAUTION': risk_dist_dict.get('CAUTION', 0),
                'NORMAL': risk_dist_dict.get('NORMAL', 0)
            },
            'hourly_pattern': hourly_pattern,
            'top_viral_live': top_viral_live
        }
        
    except Exception as e:
        logger.error(f"Viral dashboard error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claim/{claim_hash}")
def get_claim_spread_history(claim_hash: str, db: Session = Depends(get_db)):
    """
    Get spread history for a specific claim
    
    Returns timeline of velocity changes
    """
    try:
        records = db.query(VelocityRecord).filter(
            VelocityRecord.claim_hash == claim_hash
        ).order_by(VelocityRecord.timestamp).all()
        
        if not records:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        timeline = []
        for record in records:
            timeline.append({
                'timestamp': record.timestamp.isoformat(),
                'velocity_score': record.velocity_score,
                'count_5min': record.count_5min,
                'count_1hr': record.count_1hr,
                'count_24hr': record.count_24hr,
                'is_viral': record.is_viral,
                'is_trending': record.is_trending,
                'cooldown_level': record.cooldown_level
            })
        
        # Get claim details
        claim = db.query(ClaimRecord).filter(
            ClaimRecord.claim_hash == claim_hash
        ).first()
        
        return {
            'success': True,
            'claim_hash': claim_hash,
            'claim_text': records[0].claim_text,
            'verdict': claim.verdict if claim else None,
            'first_seen': records[0].timestamp.isoformat(),
            'last_seen': records[-1].timestamp.isoformat(),
            'peak_velocity': max(r.velocity_score for r in records),
            'total_checks': len(records),
            'timeline': timeline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claim history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
def get_viral_alerts(
    limit: int = 20,
    min_velocity: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    Get recent viral alerts (high-risk claims)
    
    Args:
        limit: Max number of alerts
        min_velocity: Minimum velocity score threshold
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=6)
        
        alerts = db.query(VelocityRecord).filter(
            VelocityRecord.timestamp >= cutoff_time,
            VelocityRecord.velocity_score >= min_velocity,
            VelocityRecord.cooldown_level.in_(['VIRAL_PANIC', 'HIGH_CONCERN'])
        ).order_by(desc(VelocityRecord.timestamp)).limit(limit).all()
        
        alerts_formatted = []
        for alert in alerts:
            claim = db.query(ClaimRecord).filter(
                ClaimRecord.claim_hash == alert.claim_hash
            ).first()
            
            alerts_formatted.append({
                'id': alert.id,
                'claim_text': alert.claim_text,
                'velocity_score': alert.velocity_score,
                'cooldown_level': alert.cooldown_level,
                'cooldown_score': alert.cooldown_score,
                'is_viral': alert.is_viral,
                'is_coordinated': alert.is_coordinated,
                'count_5min': alert.count_5min,
                'count_1hr': alert.count_1hr,
                'verdict': claim.verdict if claim else None,
                'timestamp': alert.timestamp.isoformat()
            })
        
        return {
            'success': True,
            'alerts': alerts_formatted,
            'count': len(alerts_formatted)
        }
        
    except Exception as e:
        logger.error(f"Viral alerts error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
