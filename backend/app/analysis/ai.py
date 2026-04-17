from __future__ import annotations

import os
import re
import json
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

CEREBRAS_URL  = "https://api.cerebras.ai/v1/chat/completions"
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL    = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
# MiniMax M2.7 — 229B MoE, recursive self-improvement, SOTA real-world engineering
# OpenAI-compatible endpoint. Falls back to M2.7-highspeed for lower latency.
MINIMAX_URL   = "https://api.minimax.io/v1/chat/completions"
# Gemma 4 31B-it — Google's latest open model, 256K context, reasoning mode
# Uses the same Google AI Studio key as Gemini (GEMINI_API_KEY)
GEMMA4_MODEL  = "gemma-4-31B-it"

# ── Structured JSON prompt ────────────────────────────────────
SYSTEM_PROMPT = """You are a professional fact-checker. Analyze the given claim and respond with ONLY a JSON object — no markdown, no extra text.

JSON format:
{
  "verdict": "fake" | "real" | "uncertain",
  "confidence": <float 0.0–1.0>,
  "explanation": "<3–5 sentence factual explanation>"
}

Rules:
- verdict must be exactly one of: fake, real, uncertain
- confidence is how certain you are (0.0 = no idea, 1.0 = certain)
- explanation must be factual, calm, and natural — no AI disclaimers
- Do NOT include markdown fences or any text outside the JSON"""

# ── Cached API keys (lazy init) ───────────────────────────────
_KEYS: Optional[dict] = None


def _get_keys() -> dict:
    global _KEYS
    if _KEYS is None:
        _KEYS = {
            "cerebras": os.getenv("CEREBRAS_API_KEY"),
            "groq":     os.getenv("GROQ_API_KEY"),
            "gemini":   os.getenv("GEMINI_API_KEY"),
            "minimax":  os.getenv("MINIMAX_API_KEY"),
        }
    return _KEYS


def _parse_structured(raw: str) -> dict:
    """Extract JSON from LLM response, handling minor formatting issues."""
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON found in response: {raw[:200]}")


def _verdict_to_score(verdict: str) -> float:
    """Convert structured verdict to a fake probability score."""
    v = verdict.lower().strip()
    if v == "fake":      return 0.85
    if v == "real":      return 0.15
    if v == "uncertain": return 0.5
    return 0.5


def _call_openai_compat(url: str, key: str, model: str, text: str,
                         timeout: int = 12, max_tokens: int = 300) -> dict:
    """Shared helper for OpenAI-compatible chat completion endpoints."""
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Claim: {text}"}
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"].strip()
    return _parse_structured(raw)


def _call_cerebras(text: str) -> dict:
    key = _get_keys()["cerebras"]
    if not key:
        raise ValueError("Cerebras API key missing")
    return _call_openai_compat(CEREBRAS_URL, key, "llama3.1-8b", text)


def _call_groq(text: str) -> dict:
    key = _get_keys()["groq"]
    if not key:
        raise ValueError("Groq API key missing")
    return _call_openai_compat(GROQ_URL, key, "llama3-8b-8192", text)


def _call_gemini(text: str) -> dict:
    key = _get_keys()["gemini"]
    if not key:
        raise ValueError("Gemini API key missing")
    prompt = f"{SYSTEM_PROMPT}\n\nClaim: {text}"
    r = requests.post(
        f"{GEMINI_URL}?key={key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300}
        },
        timeout=12
    )
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return _parse_structured(raw)


def _call_minimax(text: str) -> dict:
    """
    MiniMax M2.7 — 229B MoE model, recursive self-improvement, SOTA real-world engineering.
    OpenAI-compatible endpoint at api.minimax.io.
    Falls back to MiniMax-M2.7-highspeed for lower latency if the flagship times out.
    """
    key = _get_keys()["minimax"]
    if not key:
        raise ValueError("MiniMax API key missing")

    for model in ["MiniMax-M2.7", "MiniMax-M2.7-highspeed"]:
        try:
            return _call_openai_compat(MINIMAX_URL, key, model, text,
                                       timeout=20, max_tokens=500)
        except Exception:
            continue
    raise ValueError("MiniMax M2.7 and M2.7-highspeed both failed")


def _call_gemma4(text: str) -> dict:
    """
    Google Gemma 4 31B-it — 256K context, multimodal, reasoning mode (April 2026).
    Uses the same Google AI Studio key as Gemini (GEMINI_API_KEY).
    Superior multilingual understanding and nuanced fact-checking.
    Falls back through model chain if a specific version isn't available yet on the API.
    """
    key = _get_keys()["gemini"]
    if not key:
        raise ValueError("Gemini/Gemma API key missing")
    prompt = f"{SYSTEM_PROMPT}\n\nClaim: {text}"
    # Try newest Gemma 4 first, then Gemma 3 27B, then Gemini Flash as last resort
    for model in ["gemma-4-31b-it", "gemma-3-27b-it", "gemini-1.5-flash"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            r = requests.post(
                f"{url}?key={key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 400,
                    }
                },
                timeout=15
            )
            r.raise_for_status()
            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return _parse_structured(raw)
        except Exception:
            continue
    raise ValueError("Gemma 4 31B / Gemma 3 27B / Gemini Flash all failed")


def _ensemble_vote(results: List[dict]) -> dict:
    """
    Weighted ensemble voting across multiple LLM verdicts.
    
    Weights by model capability tier:
    - MiniMax M1 (reasoning model): 2.0x
    - Gemma 4 31B (large reasoning): 1.8x
    - Gemini 2.0 Flash: 1.2x
    - Groq / Cerebras (8B models): 1.0x
    
    Returns the consensus verdict with blended confidence and
    the explanation from the highest-weighted agreeing model.
    """
    if not results:
        return {"verdict": "uncertain", "confidence": 0.5, "explanation": ""}
    if len(results) == 1:
        return results[0]

    weights = {
        "minimax":  2.5,   # MiniMax M2.7 — 229B, SOTA real-world engineering
        "gemma4":   2.0,   # Gemma 4 31B — 256K ctx, reasoning mode
        "gemini":   1.2,   # Gemini 2.0 Flash
        "groq":     1.0,   # Llama 3 8B via Groq
        "cerebras": 1.0,   # Llama 3.1 8B via Cerebras
    }

    vote_scores = {"fake": 0.0, "real": 0.0, "uncertain": 0.0}
    total_weight = 0.0
    best_explanation = ""
    best_weight = 0.0

    for r in results:
        v = r.get("verdict", "uncertain").lower()
        conf = float(r.get("confidence", 0.5))
        src = r.get("_source", "groq")
        w = weights.get(src, 1.0) * conf  # weight by model tier × confidence
        vote_scores[v] = vote_scores.get(v, 0.0) + w
        total_weight += w
        if w > best_weight and r.get("explanation"):
            best_weight = w
            best_explanation = r["explanation"]

    winner = max(vote_scores, key=vote_scores.get)
    winner_weight = vote_scores[winner]
    ensemble_confidence = (winner_weight / total_weight) if total_weight > 0 else 0.5
    # Clamp to [0.3, 0.97] — never be overconfident or underconfident
    ensemble_confidence = max(0.3, min(0.97, ensemble_confidence))

    return {
        "verdict": winner,
        "confidence": ensemble_confidence,
        "explanation": best_explanation,
    }


def _run_all_parallel(text: str):
    """
    Run all available providers in parallel.
    Returns list of successful structured results with source tags.
    """
    keys = _get_keys()
    providers = []

    if keys["cerebras"]:
        providers.append(("cerebras", _call_cerebras))
    if keys["groq"]:
        providers.append(("groq", _call_groq))
    if keys["gemini"]:
        providers.append(("gemini", _call_gemini))
        providers.append(("gemma4", _call_gemma4))  # same key, different model
    if keys["minimax"]:
        providers.append(("minimax", _call_minimax))

    if not providers:
        return [], {"all": "No API keys configured"}

    successes = []
    errors = {}

    with ThreadPoolExecutor(max_workers=min(len(providers), 5)) as executor:
        futures = {executor.submit(fn, text): name for name, fn in providers}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                result["_source"] = name
                successes.append(result)
            except Exception as e:
                errors[name] = str(e)

    return successes, errors


def run_ai_analysis(text: str):
    """
    Runs all configured LLM providers in parallel (Cerebras, Groq, Gemini,
    Gemma 4 31B-it, MiniMax M2.7) and returns an ensemble-voted verdict.

    Ensemble voting weights larger/reasoning models more heavily:
    - MiniMax M2.7 (229B MoE, recursive self-improvement): 2.5x weight
    - Gemma 4 31B-it (Google, 256K ctx, reasoning mode):   2.0x weight
    - Gemini 2.0 Flash:                                    1.2x weight
    - Groq / Cerebras (8B models):                         1.0x weight

    Returns: (ai_fake_score: float | None, explanation: str)
    """
    # Try cache first
    try:
        from app.cache import partial_cache
        cached = partial_cache.get_ai_score(text)
        if cached is not None:
            logger.debug("AI analysis cache hit")
            return cached.get("score"), cached.get("explanation", "")
    except Exception as e:
        logger.debug("Cache lookup failed: %s", e)

    successes, errors = _run_all_parallel(text)

    if not successes:
        error_summary = " | ".join(f"{k}: {v}" for k, v in errors.items())
        return None, f"AI analysis unavailable. {error_summary}"

    # Ensemble vote across all successful responses
    ensemble = _ensemble_vote(successes)

    verdict = ensemble.get("verdict", "uncertain")
    llm_conf = float(ensemble.get("confidence", 0.5))
    explanation = ensemble.get("explanation", "")

    # Convert verdict → fake probability score, blended with ensemble confidence
    score = _verdict_to_score(verdict)
    if verdict == "fake":
        score = max(score, llm_conf * 0.95)
    elif verdict == "real":
        score = min(score, 1.0 - llm_conf * 0.95)

    logger.info(
        "AI ensemble: verdict=%s conf=%.2f score=%.3f providers=%s errors=%s",
        verdict, llm_conf, score,
        [r.get("_source") for r in successes],
        list(errors.keys()) if errors else "none"
    )

    # Cache the result
    try:
        from app.cache import partial_cache
        partial_cache.set_ai_score(text, score, explanation)
    except Exception as e:
        logger.debug("Cache set failed: %s", e)

    return score, explanation
