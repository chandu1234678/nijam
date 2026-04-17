"""
Meta-decision engine.

Uses a trained Logistic Regression (CalibratedClassifierCV) that learned
to combine ML + AI + evidence + manipulation scores from labeled examples.

Falls back to the weighted heuristic if the model file is missing
(e.g. first deploy before training runs).

Signals used:
  ml_fake        — TF-IDF / transformer fake probability (0–1)
  ai_fake        — LLM ensemble fake probability (0–1)
  evidence_score — News consistency score (1 = strongly real)
  manip_score    — Manipulation/conspiracy signal score (0–1)  ← NEW
"""

import os
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_META_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "meta_model.joblib"
)
_meta_model = None


def _load_meta_model():
    global _meta_model
    if _meta_model is not None:
        return _meta_model
    if os.path.exists(_META_MODEL_PATH):
        try:
            import joblib
            _meta_model = joblib.load(_META_MODEL_PATH)
            logger.info("Meta-decision model loaded from %s", _META_MODEL_PATH)
        except Exception as e:
            logger.warning("Failed to load meta model: %s", e)
    return _meta_model


def _heuristic(ml_fake, ai_fake, evidence_score, manip_score=0.0, text_len=0):
    """
    Weighted heuristic — used as fallback when meta-model unavailable.

    Weights (must sum to 1.0):
      AI LLM ensemble:  50% (most reliable signal)
      Evidence:         28% (real-world corroboration)
      ML model:         14% (TF-IDF / transformer)
      Manipulation:      8% (conspiracy/emotional language)
    """
    ml_weight    = 0.08 if text_len < 50 else 0.14
    ai_weight    = 0.60 if text_len < 50 else 0.50
    ev_weight    = 0.28
    manip_weight = 0.08

    fake_score   = 0.0
    total_weight = 0.0

    if ai_fake is not None:
        fake_score   += float(ai_fake) * ai_weight
        total_weight += ai_weight
    if evidence_score is not None:
        fake_score   += (1.0 - float(evidence_score)) * ev_weight
        total_weight += ev_weight
    if ml_fake is not None:
        fake_score   += float(ml_fake) * ml_weight
        total_weight += ml_weight
    if manip_score is not None and manip_score > 0:
        fake_score   += float(manip_score) * manip_weight
        total_weight += manip_weight

    if total_weight == 0:
        return "uncertain", 0.5

    normalized = fake_score / total_weight
    confidence = round(min(0.97, max(0.50, abs(normalized - 0.5) * 2 + 0.5)), 2)
    verdict    = "fake" if normalized >= 0.5 else "real"
    return verdict, confidence


def decide(
    ml_fake: Optional[float],
    ai_fake: Optional[float],
    evidence_score: Optional[float],
    text_len: int = 0,
    manip_score: Optional[float] = None,
):
    """
    Combine ML + AI + evidence + manipulation scores into a final verdict.

    Uses trained meta-model when available, heuristic as fallback.
    Returns "uncertain" when signals conflict heavily or evidence is too weak.

    Args:
        ml_fake:        0–1, probability claim is FAKE (TF-IDF / transformer)
        ai_fake:        0–1, probability claim is FAKE (LLM ensemble)
        evidence_score: 0–1, news consistency score (1 = strongly real)
        text_len:       character length of the claim
        manip_score:    0–1, manipulation/conspiracy signal score

    Returns:
        (verdict: str, confidence: float)
    """
    ml    = float(ml_fake)        if ml_fake        is not None else 0.5
    ai    = float(ai_fake)        if ai_fake        is not None else 0.5
    ev    = float(evidence_score) if evidence_score is not None else 0.5
    manip = float(manip_score)    if manip_score    is not None else 0.0

    # ── Uncertainty detection (before model inference) ────────

    # Case 1: AI and evidence strongly disagree
    # Note: low evidence (ev < 0.35) only counts as "says fake" if AI also leans fake
    # — low evidence alone just means we couldn't find corroborating news
    ai_says_fake = ai > 0.65
    ai_says_real = ai < 0.35
    ev_says_real = ev > 0.65
    ev_says_fake = ev < 0.35 and ai > 0.45  # only conflict if AI also leans fake

    signals_conflict = (ai_says_fake and ev_says_real) or (ai_says_real and ev_says_fake)

    # Case 2: All signals near 0.5 — genuinely uncertain
    # Only trigger if AI is also near center (not when AI has a clear opinion)
    all_near_center = (
        abs(ml - 0.5) < 0.15
        and abs(ai - 0.5) < 0.20   # AI must also be near center
        and abs(ev - 0.5) < 0.15
        and manip < 0.3
    )

    # Case 3: High manipulation score overrides uncertainty — lean fake
    high_manip_override = manip >= 0.6 and ai > 0.45

    if (signals_conflict or all_near_center) and not high_manip_override:
        return "uncertain", 0.5

    model = _load_meta_model()

    if model is not None:
        try:
            # Try 4-feature model first (ml, ai, ev, manip)
            try:
                X = np.array([[ml, ai, ev, manip]])
                proba = model.predict_proba(X)[0]
            except Exception:
                # Fallback to 3-feature model (old meta_model.joblib)
                X = np.array([[ml, ai, ev]])
                proba = model.predict_proba(X)[0]

            fake_prob  = float(proba[1])
            verdict    = "fake" if fake_prob >= 0.5 else "real"
            confidence = round(min(0.97, max(0.50, abs(fake_prob - 0.5) * 2 + 0.50)), 2)

            # Boost confidence when manipulation is high and verdict is fake
            if verdict == "fake" and manip >= 0.5:
                confidence = min(0.97, confidence + 0.05)

            if confidence < 0.58:
                return "uncertain", confidence
            return verdict, confidence
        except Exception as e:
            logger.warning("Meta model inference failed, using heuristic: %s", e)

    return _heuristic(ml_fake, ai_fake, evidence_score, manip_score, text_len)
