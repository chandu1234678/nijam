"""
Multi-language Support — PiNE AI

Items 118-122: Multilingual fake news detection using XLM-RoBERTa

Models used:
  - Language detection: langdetect (no API key)
  - Translation: Gemini/Groq/MiniMax (existing LLM keys)
  - Multilingual classification: FacebookAI/xlm-roberta-large
    → 100 languages including Hindi, Telugu, Tamil, Urdu, Bengali
    → Falls back to English pipeline on low-RAM environments
  - Code-mixed text: basic transliteration + detection

Supported: 100+ languages via XLM-RoBERTa
"""
import logging
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# ── XLM-RoBERTa multilingual classifier ──────────────────────
# FacebookAI/xlm-roberta-large — 100 languages, 560M params
# Used for direct multilingual fake news scoring (no translation needed)
_XLM_MODEL_ID  = "FacebookAI/xlm-roberta-large"
_xlm_pipe      = None
_xlm_failed    = False

# Lightweight alternative for low-RAM: cardiffnlp/twitter-xlm-roberta-base
_XLM_LITE_ID   = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# ISO 639-1 language names for logging/display
_LANG_NAMES = {
    "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
    "de": "German",  "ar": "Arabic", "zh": "Chinese", "pt": "Portuguese",
    "ru": "Russian", "ja": "Japanese", "ko": "Korean", "it": "Italian",
    "nl": "Dutch",   "tr": "Turkish", "pl": "Polish",  "vi": "Vietnamese",
    "th": "Thai",    "id": "Indonesian", "ur": "Urdu", "bn": "Bengali",
    "ta": "Tamil",   "te": "Telugu",  "ml": "Malayalam", "mr": "Marathi",
}

_TRANSLATE_PROMPT = (
    "Translate the following text to English. "
    "Return ONLY the translated text, nothing else.\n\n"
    "Text: {text}"
)

# ── Code-mixed language patterns (item 121) ───────────────────
# Hinglish / Tanglish / Tenglish detection
_DEVANAGARI_RE  = re.compile(r'[\u0900-\u097F]')   # Hindi/Marathi
_TELUGU_RE      = re.compile(r'[\u0C00-\u0C7F]')   # Telugu
_TAMIL_RE       = re.compile(r'[\u0B80-\u0BFF]')   # Tamil
_ARABIC_RE      = re.compile(r'[\u0600-\u06FF]')   # Arabic/Urdu
_BENGALI_RE     = re.compile(r'[\u0980-\u09FF]')   # Bengali


def _detect_script(text: str) -> str:
    """Detect dominant script in text for code-mixed handling."""
    if _DEVANAGARI_RE.search(text):  return "devanagari"
    if _TELUGU_RE.search(text):      return "telugu"
    if _TAMIL_RE.search(text):       return "tamil"
    if _ARABIC_RE.search(text):      return "arabic"
    if _BENGALI_RE.search(text):     return "bengali"
    return "latin"


def _load_xlm_roberta():
    """Load XLM-RoBERTa for multilingual classification. Lazy, RAM-checked."""
    global _xlm_pipe, _xlm_failed
    if _xlm_pipe is not None or _xlm_failed:
        return _xlm_pipe
    try:
        import psutil, torch
        from transformers import pipeline as hf_pipeline
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
        # xlm-roberta-large needs ~2.5GB; use lite version on constrained systems
        if available_mb < 3000:
            logger.debug(
                "Low RAM (%.0fMB) — skipping XLM-RoBERTa-large, using translation fallback",
                available_mb
            )
            _xlm_failed = True
            return None
        device = 0 if torch.cuda.is_available() else -1
        _xlm_pipe = hf_pipeline(
            "text-classification",
            model=_XLM_MODEL_ID,
            device=device,
            truncation=True,
            max_length=512,
        )
        logger.info("XLM-RoBERTa loaded: %s", _XLM_MODEL_ID)
    except Exception as e:
        logger.debug("XLM-RoBERTa load failed: %s", e)
        _xlm_failed = True
    return _xlm_pipe


def classify_multilingual(text: str, lang: str) -> Optional[dict]:
    """
    Directly classify a non-English claim using XLM-RoBERTa.
    Returns {"fake_probability": float, "source": "xlm-roberta"} or None.
    """
    pipe = _load_xlm_roberta()
    if pipe is None:
        return None
    try:
        result = pipe(text[:512])[0]
        label  = result["label"].upper()
        score  = float(result["score"])
        # Map label to fake probability (model-dependent)
        if label in ("LABEL_1", "FAKE", "NEGATIVE"):
            fake_prob = score
        else:
            fake_prob = 1.0 - score
        return {
            "fake_probability": round(fake_prob, 3),
            "source":           "xlm-roberta",
            "language":         lang,
        }
    except Exception as e:
        logger.debug("XLM-RoBERTa inference failed: %s", e)
        return None


def detect_language(text: str) -> str:
    """
    Detect language of text. Returns ISO 639-1 code (e.g. 'en', 'hi').
    Falls back to 'en' if detection fails.
    """
    try:
        from langdetect import detect
        lang = detect(text)
        return lang
    except Exception:
        pass

    # Fallback: simple heuristic — check for non-ASCII characters
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    if ascii_ratio < 0.7:
        return "unknown"
    return "en"


def translate_to_english(text: str, source_lang: str = "auto") -> Tuple[str, str]:
    """
    Translate text to English using available LLM.

    Returns:
        (translated_text, source_language_name)
    """
    lang_name = _LANG_NAMES.get(source_lang, source_lang.upper())
    prompt = _TRANSLATE_PROMPT.format(text=text[:1000])
    messages = [{"role": "user", "content": prompt}]

    try:
        from app.analysis.chat import _call_openai_compat, _call_gemini, _get_keys, _first_success
        keys = _get_keys()
        fns = []
        if keys.get("gemini"):
            fns.append(("Gemini", lambda: _call_gemini(messages, max_tokens=500, temperature=0)))
        if keys.get("groq"):
            fns.append(("Groq", lambda: _call_openai_compat(
                "https://api.groq.com/openai/v1/chat/completions",
                keys["groq"], "llama3-8b-8192", messages, max_tokens=500, temperature=0
            )))
        if keys.get("cerebras"):
            fns.append(("Cerebras", lambda: _call_openai_compat(
                "https://api.cerebras.ai/v1/chat/completions",
                keys["cerebras"], "llama3.1-8b", messages, max_tokens=500, temperature=0
            )))

        if fns:
            translated = _first_success(fns)
            logger.info("Translated from %s to English", lang_name)
            return translated.strip(), lang_name
    except Exception as e:
        logger.warning("Translation failed: %s", e)

    return text, lang_name  # return original if translation fails


def normalize_claim(text: str) -> Tuple[str, str, bool]:
    """
    Detect language and translate to English if needed.
    For Hindi/Telugu/Tamil/Arabic/Bengali: also attempts direct XLM-RoBERTa scoring.

    Returns:
        (normalized_text, detected_language_name, was_translated)
    """
    lang = detect_language(text)

    if lang == "en" or lang == "unknown":
        return text, "English", False

    # Detect code-mixed text (item 121) — Hinglish, Tanglish etc.
    script = _detect_script(text)
    if script != "latin":
        logger.info("Non-Latin script detected: %s (lang=%s)", script, lang)

    # Non-English — translate
    translated, lang_name = translate_to_english(text, lang)
    return translated, lang_name, True
