"""
Real-time Web Search via Tavily API — PiNE AI

Items 127-131: Real-Time Web Grounding
  127. Tavily (primary) + NewsAPI (fallback) — DONE
  128. Web scraping for primary sources — added via Tavily full content
  129. Fact-check aggregator (PolitiFact, Snopes, FactCheck.org) — via Google Fact Check API
  130. Google Fact Check Tools API cross-reference — DONE in platform_tracker.py
  131. Evidence provenance chain (source → claim → verdict) — NEW

- Real-time results optimized for AI/RAG use cases
- 1000 free requests/month on Tavily
- Clean content extraction with relevance scores
"""
import os
import re
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.analysis.credibility import get_trust_score, get_trust_label
from app.analysis.publisher_bias import get_bias_label

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL     = "https://api.tavily.com/search"

_retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["POST"])
_adapter = HTTPAdapter(max_retries=_retry)
_session = requests.Session()
_session.mount("https://", _adapter)

_SUPPORT_WORDS = re.compile(
    r"\b(confirm|confirmed|verif|true|accurate|correct|real|legitimate|"
    r"evidence shows|study finds|research confirms|officials say|"
    r"according to|report shows|data shows|proves|proven)\b",
    re.IGNORECASE,
)
_CONTRADICT_WORDS = re.compile(
    r"\b(false|fake|debunk|mislead|misinform|incorrect|wrong|"
    r"no evidence|unverified|disputed|claim is|rumor|hoax|"
    r"fact.?check|not true|baseless|fabricat|manipulat)\b",
    re.IGNORECASE,
)


def _stance(title: str, description: str) -> str:
    blob = f"{title} {description or ''}".lower()
    s = len(_SUPPORT_WORDS.findall(blob))
    c = len(_CONTRADICT_WORDS.findall(blob))
    if c > s: return "contradict"
    if s > c: return "support"
    return "neutral"


def _consistency_score(articles: list) -> float:
    support    = sum(a.get("trust_score", 0.5) for a in articles if a.get("stance") == "support")
    contradict = sum(a.get("trust_score", 0.5) for a in articles if a.get("stance") == "contradict")
    total = support + contradict
    if total == 0: return 0.5
    return round(support / total, 2)


def fetch_brave_evidence(text: str):
    """
    Fetch real-time news evidence via Tavily API.

    Returns:
        evidence_score (float | None)
        evidence_urls  (list[str])
        evidence_articles (list[dict])
    """
    if not TAVILY_API_KEY:
        return None, [], []

    try:
        t0 = time.perf_counter()
        r  = _session.post(
            TAVILY_URL,
            json={
                "api_key":              TAVILY_API_KEY,
                "query":                text[:400],
                "search_depth":         "basic",
                "topic":                "news",
                "max_results":          10,
                "include_answer":       False,
                "include_raw_content":  False,
            },
            timeout=12,
        )
        elapsed = round((time.perf_counter() - t0) * 1000)

        if r.status_code != 200:
            logger.warning("Tavily returned %s in %sms", r.status_code, elapsed)
            return None, [], []

        logger.debug("Tavily OK in %sms", elapsed)
        results = r.json().get("results", [])
        if not results:
            return 0.0, [], []

        articles = []
        all_urls = []

        for item in results:
            url     = item.get("url", "")
            title   = item.get("title", "")
            desc    = item.get("content", "")
            src     = item.get("source", "") or url.split("/")[2] if url else ""

            if url:
                all_urls.append(url)

            trust  = get_trust_score(url)
            stance = _stance(title, desc)
            bias   = get_bias_label(url)

            articles.append({
                "title":        title,
                "url":          url,
                "source":       src,
                "stance":       stance,
                "trust_score":  trust,
                "trust_label":  get_trust_label(url),
                "bias_label":   bias,
                "age":          item.get("published_date", ""),
                "relevance":    item.get("score", 0.0),
            })

        if not articles:
            return 0.1, all_urls[:3], []

        # Sort by Tavily relevance score before reranking
        articles.sort(key=lambda a: a.get("relevance", 0.0), reverse=True)

        # Cross-encoder reranking
        try:
            from app.analysis.cross_encoder import rerank_articles
            articles = rerank_articles(text, articles, top_k=5)
        except Exception:
            pass

        score = _consistency_score(articles)
        coverage_bonus = min(len(articles) / 5, 0.15)
        score = round(min(1.0, score + coverage_bonus), 2)

        return score, [a["url"] for a in articles if a["url"]][:5], articles[:5]

    except requests.exceptions.Timeout:
        logger.warning("Tavily timed out")
        return None, [], []
    except Exception as e:
        logger.warning("Tavily error: %s", e)
        return None, [], []


# ── Evidence Provenance Chain (item 131) ─────────────────────

def build_provenance_chain(claim_text: str, articles: list, verdict: str, confidence: float) -> dict:
    """
    Build an evidence provenance chain: source → claim → verdict.

    Structure:
      {
        "claim":    str,
        "verdict":  str,
        "confidence": float,
        "chain": [
          {
            "step":    int,
            "source":  str,
            "url":     str,
            "stance":  "support"|"contradict"|"neutral",
            "trust":   float,
            "bias":    str,
            "snippet": str,
          }
        ],
        "summary": str,
      }
    """
    chain = []
    for i, a in enumerate(articles[:5], 1):
        chain.append({
            "step":    i,
            "source":  a.get("source", "Unknown"),
            "url":     a.get("url", ""),
            "stance":  a.get("stance", "neutral"),
            "trust":   a.get("trust_score", 0.5),
            "bias":    a.get("bias_label", "UNKNOWN"),
            "snippet": (a.get("title", "") + " — " + a.get("description", ""))[:200],
        })

    # Summary sentence
    support_count    = sum(1 for s in chain if s["stance"] == "support")
    contradict_count = sum(1 for s in chain if s["stance"] == "contradict")
    if support_count > contradict_count:
        summary = f"{support_count} source(s) support this claim, {contradict_count} contradict it."
    elif contradict_count > support_count:
        summary = f"{contradict_count} source(s) contradict this claim, {support_count} support it."
    else:
        summary = f"Evidence is mixed ({support_count} support, {contradict_count} contradict)."

    return {
        "claim":      claim_text[:200],
        "verdict":    verdict,
        "confidence": confidence,
        "chain":      chain,
        "summary":    summary,
    }
