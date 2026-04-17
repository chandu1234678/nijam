"""
News & Social Media Aggregator — PiNE AI

Fetches live news, retweet data, and social spread metrics for:
1. Real-time evidence enrichment during fact-checking
2. Training data collection (auto-labeled from trusted sources)
3. Viral spread detection via retweet/share velocity

Sources:
- Tavily (real-time web search, primary)
- NewsAPI (news articles)
- Twitter/X v2 API (retweet counts, spread)
- Reddit API (cross-post tracking)
- RSS feeds (BBC, Reuters, AP — no key needed)
"""
from __future__ import annotations

import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# ── API keys ──────────────────────────────────────────────────
TAVILY_KEY          = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY        = os.getenv("NEWS_API_KEY")
TWITTER_BEARER      = os.getenv("TWITTER_BEARER_TOKEN")
REDDIT_CLIENT_ID    = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET= os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT   = os.getenv("REDDIT_USER_AGENT", "PiNEAI/2.0")

_session = requests.Session()
_session.headers.update({"User-Agent": "PiNEAI/2.0 (fact-checker)"})

# ── RSS feeds (no API key needed) ────────────────────────────
RSS_FEEDS = {
    "reuters":  "https://feeds.reuters.com/reuters/topNews",
    "bbc":      "https://feeds.bbci.co.uk/news/rss.xml",
    "ap":       "https://rsshub.app/apnews/topics/apf-topnews",
    "guardian": "https://www.theguardian.com/world/rss",
}


# ─────────────────────────────────────────────────────────────
# 1. LIVE NEWS SEARCH
# ─────────────────────────────────────────────────────────────

def search_news(query: str, max_results: int = 10) -> list[dict]:
    """
    Search for news articles about a claim using Tavily + NewsAPI.
    Returns list of {title, url, source, published, snippet, trust_score}.
    """
    results = []

    # Tavily (primary — real-time, AI-optimized)
    if TAVILY_KEY:
        try:
            r = _session.post(
                "https://api.tavily.com/search",
                json={
                    "api_key":     TAVILY_KEY,
                    "query":       query[:400],
                    "search_depth": "basic",
                    "topic":       "news",
                    "max_results": max_results,
                    "include_answer": False,
                },
                timeout=10,
            )
            if r.status_code == 200:
                for item in r.json().get("results", []):
                    results.append({
                        "title":     item.get("title", ""),
                        "url":       item.get("url", ""),
                        "source":    item.get("source", ""),
                        "published": item.get("published_date", ""),
                        "snippet":   item.get("content", "")[:300],
                        "relevance": item.get("score", 0.5),
                        "via":       "tavily",
                    })
        except Exception as e:
            logger.debug("Tavily search failed: %s", e)

    # NewsAPI fallback
    if NEWS_API_KEY and len(results) < 5:
        try:
            r = _session.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query[:100],
                    "language": "en",
                    "pageSize": max_results,
                    "sortBy":   "relevancy",
                    "apiKey":   NEWS_API_KEY,
                },
                timeout=10,
            )
            if r.status_code == 200:
                for a in r.json().get("articles", []):
                    results.append({
                        "title":     a.get("title", ""),
                        "url":       a.get("url", ""),
                        "source":    a.get("source", {}).get("name", ""),
                        "published": a.get("publishedAt", ""),
                        "snippet":   a.get("description", "")[:300],
                        "relevance": 0.5,
                        "via":       "newsapi",
                    })
        except Exception as e:
            logger.debug("NewsAPI search failed: %s", e)

    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in results:
        if item["url"] and item["url"] not in seen:
            seen.add(item["url"])
            deduped.append(item)

    return deduped[:max_results]


# ─────────────────────────────────────────────────────────────
# 2. TWITTER/X RETWEET DATA
# ─────────────────────────────────────────────────────────────

def get_twitter_spread(query: str, max_results: int = 50) -> dict:
    """
    Fetch Twitter/X data for a claim: tweet count, retweet count,
    bot score, temporal clustering.

    Returns spread metrics dict.
    """
    if not TWITTER_BEARER:
        return {"available": False, "reason": "TWITTER_BEARER_TOKEN not set"}

    try:
        headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}
        params = {
            "query":        f"{query[:200]} -is:retweet lang:en",
            "max_results":  min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions":   "author_id",
            "user.fields":  "created_at,public_metrics,verified",
        }
        r = _session.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=headers,
            params=params,
            timeout=10,
        )
        if r.status_code == 429:
            return {"available": False, "reason": "Twitter rate limited"}
        if r.status_code != 200:
            return {"available": False, "reason": f"HTTP {r.status_code}"}

        data   = r.json()
        tweets = data.get("data", [])
        users  = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        if not tweets:
            return {"available": True, "tweet_count": 0, "retweet_count": 0,
                    "unique_users": 0, "bot_score": 0.0, "is_viral": False}

        tweet_count   = len(tweets)
        retweet_count = sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets)
        unique_users  = len({t.get("author_id") for t in tweets})
        timestamps    = []
        bot_signals   = []

        for t in tweets:
            ts = t.get("created_at")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                except Exception:
                    pass
            uid = t.get("author_id")
            if uid and uid in users:
                u = users[uid]
                m = u.get("public_metrics", {})
                followers = m.get("followers_count", 0)
                following = m.get("following_count", 0)
                age_days  = _account_age_days(u.get("created_at"))
                score = 0.0
                if followers < 50:       score += 0.3
                if followers > 0 and following / followers > 5: score += 0.3
                if age_days < 30:        score += 0.2
                if not u.get("verified"): score += 0.1
                bot_signals.append(min(score, 1.0))

        bot_score = sum(bot_signals) / len(bot_signals) if bot_signals else 0.0
        temporal  = _temporal_clustering(timestamps)
        is_viral  = retweet_count > 500 or (tweet_count > 20 and temporal > 0.7)

        return {
            "available":           True,
            "tweet_count":         tweet_count,
            "retweet_count":       retweet_count,
            "unique_users":        unique_users,
            "bot_score":           round(bot_score, 3),
            "temporal_clustering": round(temporal, 3),
            "is_viral":            is_viral,
            "campaign_indicators": _twitter_indicators(bot_score, temporal, tweet_count, unique_users),
        }
    except Exception as e:
        logger.warning("Twitter spread fetch failed: %s", e)
        return {"available": False, "reason": str(e)}


def _account_age_days(created_at: Optional[str]) -> int:
    if not created_at:
        return 365
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return max((datetime.now(dt.tzinfo) - dt).days, 0)
    except Exception:
        return 365


def _temporal_clustering(timestamps: list[float]) -> float:
    if len(timestamps) < 2:
        return 0.0
    timestamps = sorted(timestamps)
    gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    short = sum(1 for g in gaps if g < 3600)
    return short / len(gaps)


def _twitter_indicators(bot_score, temporal, tweet_count, unique_users) -> list[str]:
    out = []
    if bot_score > 0.6:       out.append("high_bot_activity")
    if temporal > 0.7:        out.append("synchronized_posting")
    if tweet_count > 0 and unique_users / tweet_count < 0.3:
        out.append("few_unique_users")
    return out


# ─────────────────────────────────────────────────────────────
# 3. REDDIT SPREAD DATA
# ─────────────────────────────────────────────────────────────

def get_reddit_spread(query: str, max_results: int = 25) -> dict:
    """Fetch Reddit spread data for a claim."""
    if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET):
        return {"available": False, "reason": "Reddit API not configured"}

    try:
        # Get OAuth token
        auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        token_r = _session.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": REDDIT_USER_AGENT},
            timeout=8,
        )
        if token_r.status_code != 200:
            return {"available": False, "reason": f"Reddit auth failed: {token_r.status_code}"}

        token = token_r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "User-Agent": REDDIT_USER_AGENT}

        # Search
        r = _session.get(
            "https://oauth.reddit.com/search",
            headers=headers,
            params={"q": query[:200], "sort": "new", "limit": max_results, "type": "link"},
            timeout=10,
        )
        if r.status_code != 200:
            return {"available": False, "reason": f"Reddit search failed: {r.status_code}"}

        posts = r.json().get("data", {}).get("children", [])
        if not posts:
            return {"available": True, "post_count": 0, "subreddit_count": 0,
                    "cross_post_rate": 0.0, "is_coordinated": False}

        subreddits   = set()
        cross_posts  = 0
        account_ages = []

        for p in posts:
            d = p.get("data", {})
            subreddits.add(d.get("subreddit", ""))
            if d.get("crosspost_parent"):
                cross_posts += 1
            author_created = d.get("author_created_utc")
            if author_created:
                account_ages.append((time.time() - author_created) / 86400)

        cross_rate = cross_posts / len(posts)
        avg_age    = sum(account_ages) / len(account_ages) if account_ages else 365
        age_score  = max(0, 1 - avg_age / 365)

        indicators = []
        if len(subreddits) > len(posts) * 0.7: indicators.append("wide_subreddit_spread")
        if cross_rate > 0.5:                   indicators.append("high_cross_post_rate")
        if age_score > 0.6:                    indicators.append("new_accounts")

        return {
            "available":           True,
            "post_count":          len(posts),
            "subreddit_count":     len(subreddits),
            "cross_post_rate":     round(cross_rate, 3),
            "account_age_score":   round(age_score, 3),
            "campaign_indicators": indicators,
            "is_coordinated":      len(indicators) >= 2,
        }
    except Exception as e:
        logger.warning("Reddit spread fetch failed: %s", e)
        return {"available": False, "reason": str(e)}


# ─────────────────────────────────────────────────────────────
# 4. COMBINED SPREAD ANALYSIS
# ─────────────────────────────────────────────────────────────

def get_full_spread_analysis(claim_text: str, velocity_data: dict = None) -> dict:
    """
    Run Twitter + Reddit spread analysis in parallel.
    Returns combined campaign score and indicators.
    """
    velocity_data = velocity_data or {}
    twitter_data  = {}
    reddit_data   = {}

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {
            ex.submit(get_twitter_spread, claim_text): "twitter",
            ex.submit(get_reddit_spread,  claim_text): "reddit",
        }
        for f in as_completed(futures):
            key = futures[f]
            try:
                if key == "twitter": twitter_data = f.result()
                else:                reddit_data  = f.result()
            except Exception as e:
                logger.warning("%s spread failed: %s", key, e)

    # Campaign score
    signals    = []
    indicators = []

    if twitter_data.get("bot_score", 0) > 0.6:
        signals.append(0.30); indicators.append("twitter_bot_activity")
    if twitter_data.get("temporal_clustering", 0) > 0.7:
        signals.append(0.25); indicators.append("synchronized_twitter_posts")
    if twitter_data.get("is_viral"):
        signals.append(0.20); indicators.append("twitter_viral")
    indicators.extend(twitter_data.get("campaign_indicators", []))

    if reddit_data.get("is_coordinated"):
        signals.append(0.20); indicators.append("reddit_coordinated")
    indicators.extend(reddit_data.get("campaign_indicators", []))

    if velocity_data.get("is_viral"):
        signals.append(0.30); indicators.append("velocity_viral")
    if velocity_data.get("is_trending"):
        signals.append(0.15); indicators.append("velocity_trending")

    campaign_score = min(sum(signals), 1.0)
    indicators     = list(set(indicators))

    return {
        "twitter":                twitter_data,
        "reddit":                 reddit_data,
        "campaign_score":         round(campaign_score, 3),
        "campaign_indicators":    indicators,
        "is_coordinated_campaign": campaign_score > 0.6,
    }


# ─────────────────────────────────────────────────────────────
# 5. TRAINING DATA COLLECTION
# ─────────────────────────────────────────────────────────────

def collect_training_samples(topic: str = "misinformation", max_samples: int = 100) -> list[dict]:
    """
    Collect labeled training samples from trusted news sources.

    Fetches recent articles from Reuters/BBC/AP (trusted = label 0/real)
    and from known misinformation trackers (label 1/fake).

    Returns list of {text, label, source, url, collected_at}.
    """
    samples = []

    # Real news from trusted sources
    real_queries = [
        f"{topic} site:reuters.com OR site:apnews.com OR site:bbc.com",
        f"fact check {topic} site:snopes.com OR site:factcheck.org OR site:politifact.com",
    ]
    for q in real_queries:
        articles = search_news(q, max_results=20)
        for a in articles:
            if a.get("snippet") and len(a["snippet"]) > 50:
                samples.append({
                    "text":         a["title"] + " " + a["snippet"],
                    "label":        0,  # real
                    "source":       a.get("source", ""),
                    "url":          a.get("url", ""),
                    "collected_at": datetime.utcnow().isoformat(),
                })
        if len(samples) >= max_samples // 2:
            break

    # Debunked claims from fact-checkers (label = fake)
    fake_queries = [
        f"debunked false claim {topic}",
        f"misinformation {topic} fact check false",
    ]
    for q in fake_queries:
        articles = search_news(q, max_results=20)
        for a in articles:
            snippet = a.get("snippet", "")
            # Only include if the article explicitly debunks something
            if any(w in snippet.lower() for w in ["false", "debunked", "misleading", "fake", "hoax"]):
                if len(snippet) > 50:
                    samples.append({
                        "text":         a["title"] + " " + snippet,
                        "label":        1,  # fake
                        "source":       a.get("source", ""),
                        "url":          a.get("url", ""),
                        "collected_at": datetime.utcnow().isoformat(),
                    })
        if len(samples) >= max_samples:
            break

    logger.info("Collected %d training samples for topic: %s", len(samples), topic)
    return samples[:max_samples]
