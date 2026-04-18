"""
Continuous Learning — Auto-Retraining Pipeline

Monitors user feedback count and triggers model retraining when:
- 50+ new corrections have accumulated since last retrain
- OR it's been 7 days since last retrain and 10+ corrections exist

Also runs a daily background job to collect fresh labeled training data
from live news sources (Reuters, BBC, AP, fact-checkers) via Tavily/NewsAPI.

Runs in background threads — non-blocking, won't affect request latency.
"""
import os
import json
import logging
import threading
import subprocess
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
_RETRAIN_THRESHOLD     = 50   # corrections before auto-retrain
_RETRAIN_MIN           = 10   # minimum corrections needed
_RETRAIN_INTERVAL_DAYS = 7    # days between scheduled retrains
_COLLECT_INTERVAL_HRS  = 24   # hours between auto data collection

_retrain_lock    = threading.Lock()
_is_retraining   = False
_collect_lock    = threading.Lock()
_is_collecting   = False
_last_collect_ts = 0.0        # epoch seconds of last collection


def _get_version_info() -> dict:
    path = os.path.join(_DATA_DIR, "model_version.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _should_retrain(feedback_count: int) -> tuple[bool, str]:
    """Returns (should_retrain, reason)."""
    if feedback_count < _RETRAIN_MIN:
        return False, f"Only {feedback_count} corrections (need {_RETRAIN_MIN})"

    version = _get_version_info()
    last_retrain_str = version.get("retrain_timestamp")

    # Check threshold
    new_since_last = feedback_count - version.get("feedback_at_retrain", 0)
    if new_since_last >= _RETRAIN_THRESHOLD:
        return True, f"{new_since_last} new corrections since last retrain"

    # Check time-based trigger
    if last_retrain_str:
        try:
            last_retrain = datetime.fromisoformat(last_retrain_str)
            days_since = (datetime.utcnow() - last_retrain).days
            if days_since >= _RETRAIN_INTERVAL_DAYS and feedback_count >= _RETRAIN_MIN:
                return True, f"{days_since} days since last retrain with {feedback_count} corrections"
        except Exception:
            pass
    elif feedback_count >= _RETRAIN_THRESHOLD:
        return True, f"{feedback_count} corrections accumulated"

    return False, "Threshold not reached"


def _run_retrain(feedback_count: int):
    """Run retraining in background thread."""
    global _is_retraining
    with _retrain_lock:
        if _is_retraining:
            return
        _is_retraining = True

    try:
        logger.info("Auto-retraining triggered with %d feedback corrections", feedback_count)
        import sys
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "training", "retrain_from_feedback.py")
        if not os.path.exists(script):
            logger.warning("retrain_from_feedback.py not found at %s", script)
            return

        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=300,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode == 0:
            logger.info("Auto-retrain completed successfully:\n%s", result.stdout[-500:])
            # Update version info with retrain metadata
            version = _get_version_info()
            version["retrain_timestamp"]   = datetime.utcnow().isoformat()
            version["feedback_at_retrain"] = feedback_count
            version["auto_retrain"]        = True
            path = os.path.join(_DATA_DIR, "model_version.json")
            with open(path, "w") as f:
                json.dump(version, f, indent=2)
        else:
            logger.error("Auto-retrain failed:\n%s", result.stderr[-500:])
    except subprocess.TimeoutExpired:
        logger.error("Auto-retrain timed out after 5 minutes")
    except Exception as e:
        logger.error("Auto-retrain error: %s", e)
    finally:
        with _retrain_lock:
            _is_retraining = False


def maybe_retrain(db) -> dict:
    """
    Check if retraining should be triggered and start it if so.
    Call this after each feedback submission.

    Returns status dict for logging.
    """
    try:
        from app.models import UserFeedback
        from sqlalchemy import func
        feedback_count = db.query(func.count(UserFeedback.id)).filter(
            UserFeedback.predicted != UserFeedback.actual
        ).scalar() or 0

        should, reason = _should_retrain(feedback_count)

        if should and not _is_retraining:
            thread = threading.Thread(
                target=_run_retrain,
                args=(feedback_count,),
                daemon=True,
                name="auto-retrain",
            )
            thread.start()
            logger.info("Auto-retrain started: %s", reason)
            return {"triggered": True, "reason": reason, "feedback_count": feedback_count}

        return {"triggered": False, "reason": reason, "feedback_count": feedback_count}
    except Exception as e:
        logger.debug("maybe_retrain check failed: %s", e)
        return {"triggered": False, "reason": str(e)}


# ─────────────────────────────────────────────────────────────
# AUTO DATA COLLECTION — runs every 24 hours in background
# Fetches fresh labeled samples from web search + Wikipedia
# ─────────────────────────────────────────────────────────────

_COLLECTION_TOPICS = [
    "misinformation",
    "fake news health",
    "political misinformation",
    "climate misinformation",
    "vaccine misinformation",
    "election misinformation",
]


def _run_data_collection(db_factory):
    """
    Background thread: collect fresh labeled training data from:
    - Tavily/NewsAPI (real news from Reuters/BBC/AP + debunked claims from fact-checkers)
    - Wikipedia entity facts (via Wikidata)
    Stores results as UserFeedback records for the next retrain cycle.
    """
    global _is_collecting, _last_collect_ts
    with _collect_lock:
        if _is_collecting:
            return
        _is_collecting = True

    try:
        import time
        from app.analysis.news_aggregator import collect_training_samples

        logger.info("Auto data collection started — topics: %s", _COLLECTION_TOPICS)
        total_added = 0

        db = db_factory()
        try:
            from app.models import UserFeedback

            for topic in _COLLECTION_TOPICS:
                try:
                    samples = collect_training_samples(topic=topic, max_samples=30)
                    added = 0
                    for s in samples:
                        text = s.get("text", "").strip()
                        if not text or len(text) < 30:
                            continue
                        verdict = "fake" if s.get("label", 0) == 1 else "real"
                        # Dedup by SHA-256 hash of first 200 chars (fast, avoids full-text scan)
                        import hashlib
                        text_hash = hashlib.sha256(text[:200].lower().encode()).hexdigest()[:16]
                        exists = db.query(UserFeedback).filter(
                            UserFeedback.claim_text.like(f"%{text_hash}%")
                        ).first()
                        if not exists:
                            # Embed hash in claim_text so future dedup works
                            stored_text = f"[{text_hash}] {text[:990]}"
                            db.add(UserFeedback(
                                user_id    = None,
                                claim_text = stored_text,
                                predicted  = "uncertain",
                                actual     = verdict,
                                confidence = 0.75,
                            ))
                            added += 1

                    db.commit()
                    total_added += added
                    logger.info("Collected %d samples for topic '%s'", added, topic)
                    time.sleep(2)  # rate limit between topics

                except Exception as e:
                    logger.warning("Collection failed for topic '%s': %s", topic, e)
                    db.rollback()

        finally:
            db.close()

        _last_collect_ts = __import__("time").time()
        logger.info("Auto data collection complete — %d total new samples added", total_added)

        # Trigger retrain check after collection
        if total_added > 0:
            logger.info("Triggering retrain check after data collection")
            # Use a fresh DB session for retrain check
            db2 = db_factory()
            try:
                from app.models import UserFeedback
                from sqlalchemy import func
                count = db2.query(func.count(UserFeedback.id)).filter(
                    UserFeedback.predicted != UserFeedback.actual
                ).scalar() or 0
                should, reason = _should_retrain(count)
                if should and not _is_retraining:
                    thread = threading.Thread(
                        target=_run_retrain, args=(count,),
                        daemon=True, name="post-collect-retrain"
                    )
                    thread.start()
                    logger.info("Post-collection retrain triggered: %s", reason)
            finally:
                db2.close()

    except Exception as e:
        logger.error("Auto data collection error: %s", e)
    finally:
        with _collect_lock:
            _is_collecting = False


def maybe_collect_data(db_factory) -> dict:
    """
    Check if it's time to collect fresh training data and start if so.
    Call this from a periodic background task (e.g. every hour from lifespan).

    db_factory: callable that returns a new DB session (e.g. SessionLocal)
    """
    import time
    global _last_collect_ts

    elapsed_hrs = (time.time() - _last_collect_ts) / 3600
    if elapsed_hrs < _COLLECT_INTERVAL_HRS:
        return {
            "triggered": False,
            "reason": f"Last collection {elapsed_hrs:.1f}h ago (interval: {_COLLECT_INTERVAL_HRS}h)",
        }

    if _is_collecting:
        return {"triggered": False, "reason": "Collection already running"}

    thread = threading.Thread(
        target=_run_data_collection,
        args=(db_factory,),
        daemon=True,
        name="auto-collect",
    )
    thread.start()
    logger.info("Auto data collection scheduled")
    return {"triggered": True, "reason": f"Interval {_COLLECT_INTERVAL_HRS}h elapsed"}
