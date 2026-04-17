"""
Application configuration — loaded once at startup.
All values come from environment variables (set in Render dashboard or .env).
"""
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load .env for local development (no-op in production where env vars are injected)
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(_env_path)

# ── LLM API Keys ──────────────────────────────────────────────
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
MINIMAX_API_KEY  = os.getenv("MINIMAX_API_KEY", "")

_llm_keys = [CEREBRAS_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, MINIMAX_API_KEY]
if not any(_llm_keys):
    # Warn but don't crash — TF-IDF still works without LLM keys
    logger.warning(
        "No LLM API keys configured. AI analysis will be unavailable. "
        "Set at least one of: CEREBRAS_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, MINIMAX_API_KEY"
    )

# ── ML Model Config ───────────────────────────────────────────
# On Render free tier (512MB): leave DEBERTA_MODEL empty → uses TF-IDF
# On paid tier: set DEBERTA_MODEL=Arko007/fact-check1-v3-final
DEBERTA_MODEL          = os.getenv("DEBERTA_MODEL", "")
FORCE_TRANSFORMER_LOAD = os.getenv("FORCE_TRANSFORMER_LOAD", "false").lower() == "true"
ENABLE_ENSEMBLE        = os.getenv("ENABLE_ENSEMBLE", "false").lower() == "true"
HF_TOKEN               = os.getenv("HF_TOKEN", "")

# ── Feature Flags ─────────────────────────────────────────────
WIKIDATA_ENABLED      = os.getenv("WIKIDATA_ENABLED", "false").lower() == "true"
SOCIAL_GRAPH_ENABLED  = os.getenv("SOCIAL_GRAPH_ENABLED", "false").lower() == "true"
REDIS_ENABLED         = os.getenv("REDIS_ENABLED", "false").lower() == "true"
SKIP_TRAIN_ON_STARTUP = os.getenv("SKIP_TRAIN_ON_STARTUP", "false").lower() == "true"
ENABLE_DOCS           = os.getenv("ENABLE_DOCS", "true").lower() == "true"
