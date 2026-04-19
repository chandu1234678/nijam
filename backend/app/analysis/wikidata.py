"""
Wikidata Entity Verification + Transformer NER

Item 108: Named entity extraction using dslim/bert-large-NER (HuggingFace)
  — No spaCy dependency
  — Extracts PER / ORG / LOC / MISC entities
  — Falls back to regex patterns if model unavailable (RAM constrained)

Items 107, 109, 110: Wikidata verification, relationship check, entity risk score
Item 111: Local knowledge graph from verified claims (in-memory cache)
Item 112: Multi-hop reasoning stub (Wikidata SPARQL chains)
"""
import re
import logging
import requests
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"

_session = requests.Session()
_session.headers.update({"User-Agent": "PiNEAI/2.6 (fact-checking research)"})

# ── HuggingFace NER model ─────────────────────────────────────
# dslim/bert-large-NER — BERT-large fine-tuned on CoNLL-2003
# Extracts: PER, ORG, LOC, MISC — no spaCy needed
# ~1.3GB, loads lazily, skipped on low-RAM environments
_NER_MODEL_ID = "dslim/bert-large-NER"
_ner_pipe     = None
_ner_failed   = False


def _load_ner():
    global _ner_pipe, _ner_failed
    if _ner_pipe is not None or _ner_failed:
        return _ner_pipe
    try:
        import psutil, torch
        from transformers import pipeline
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
        if available_mb < 2000:
            logger.debug("Skipping NER model — only %.0fMB RAM (need 2000MB)", available_mb)
            _ner_failed = True
            return None
        device = 0 if torch.cuda.is_available() else -1
        _ner_pipe = pipeline(
            "ner",
            model=_NER_MODEL_ID,
            aggregation_strategy="simple",
            device=device,
        )
        logger.info("NER model loaded: %s", _NER_MODEL_ID)
    except Exception as e:
        logger.debug("NER model load failed, using regex fallback: %s", e)
        _ner_failed = True
    return _ner_pipe


# ── Regex fallback NER ────────────────────────────────────────
_PERSON_RE = re.compile(r'\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+)\b')
_ORG_RE    = re.compile(r'\b((?:the )?(?:US|UK|UN|EU|WHO|CDC|NASA|FBI|CIA|NATO|[A-Z]{2,6}))\b')
_YEAR_RE   = re.compile(r'\b((?:19|20)\d{2})\b')
_NUM_RE    = re.compile(
    r'\b(\d[\d,]*(?:\.\d+)?(?:\s*(?:million|billion|trillion|percent|%))?)\b',
    re.IGNORECASE,
)


def extract_entities(text: str) -> dict:
    """
    Extract named entities using dslim/bert-large-NER (HuggingFace).
    Falls back to regex if model unavailable.

    Returns: {"persons": [...], "orgs": [...], "locations": [...], "years": [...], "numbers": [...]}
    """
    pipe = _load_ner()

    if pipe is not None:
        try:
            ner_results = pipe(text[:512])  # BERT max 512 tokens
            persons   = []
            orgs      = []
            locations = []
            misc      = []
            for ent in ner_results:
                word  = ent.get("word", "").strip()
                label = ent.get("entity_group", "")
                score = ent.get("score", 0.0)
                if score < 0.7 or len(word) < 2:
                    continue
                if label == "PER":   persons.append(word)
                elif label == "ORG": orgs.append(word)
                elif label == "LOC": locations.append(word)
                elif label == "MISC": misc.append(word)

            return {
                "persons":   list(dict.fromkeys(persons))[:4],
                "orgs":      list(dict.fromkeys(orgs))[:4],
                "locations": list(dict.fromkeys(locations))[:4],
                "misc":      list(dict.fromkeys(misc))[:3],
                "years":     list(set(_YEAR_RE.findall(text)))[:3],
                "numbers":   list(set(_NUM_RE.findall(text)))[:3],
                "source":    "bert-ner",
            }
        except Exception as e:
            logger.debug("NER inference failed, using regex: %s", e)

    # Regex fallback
    return {
        "persons":   list(set(_PERSON_RE.findall(text)))[:3],
        "orgs":      list(set(_ORG_RE.findall(text)))[:3],
        "locations": [],
        "misc":      [],
        "years":     list(set(_YEAR_RE.findall(text)))[:3],
        "numbers":   list(set(_NUM_RE.findall(text)))[:3],
        "source":    "regex",
    }


# ── Wikidata lookup ───────────────────────────────────────────

def _search_entity(name: str) -> Optional[dict]:
    """Search Wikidata for an entity by name."""
    try:
        r = _session.get(WIKIDATA_SEARCH, params={
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "limit": 1,
            "format": "json",
        }, timeout=5)
        results = r.json().get("search", [])
        if results:
            return {
                "id":          results[0]["id"],
                "label":       results[0].get("label", name),
                "description": results[0].get("description", ""),
            }
    except Exception as e:
        logger.debug("Wikidata search failed for '%s': %s", name, e)
    return None


def _get_entity_facts(entity_id: str) -> dict:
    """Get key facts about a Wikidata entity via SPARQL."""
    try:
        query = f"""
        SELECT ?propLabel ?valueLabel WHERE {{
          wd:{entity_id} ?prop ?value .
          ?propEntity wikibase:directClaim ?prop .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }} LIMIT 15
        """
        r = _session.get(WIKIDATA_SPARQL, params={"query": query, "format": "json"}, timeout=8)
        bindings = r.json().get("results", {}).get("bindings", [])
        facts = {}
        for b in bindings:
            prop  = b.get("propLabel", {}).get("value", "")
            value = b.get("valueLabel", {}).get("value", "")
            if prop and value and not prop.startswith("P"):
                facts[prop] = value
        return facts
    except Exception:
        return {}


# ── Local knowledge graph (item 111) ─────────────────────────
# In-memory graph: entity_id → {facts, related_claims, verified_at}
_knowledge_graph: dict = {}


def _update_knowledge_graph(entity_id: str, facts: dict, claim_text: str):
    """Add verified entity facts to the local knowledge graph."""
    if entity_id not in _knowledge_graph:
        _knowledge_graph[entity_id] = {"facts": {}, "claims": [], "count": 0}
    _knowledge_graph[entity_id]["facts"].update(facts)
    _knowledge_graph[entity_id]["claims"].append(claim_text[:100])
    _knowledge_graph[entity_id]["count"] += 1
    # Keep only last 10 claims per entity
    _knowledge_graph[entity_id]["claims"] = _knowledge_graph[entity_id]["claims"][-10:]


def get_knowledge_graph_stats() -> dict:
    """Return stats about the local knowledge graph."""
    return {
        "entities":    len(_knowledge_graph),
        "total_facts": sum(len(v["facts"]) for v in _knowledge_graph.values()),
        "top_entities": sorted(
            [{"id": k, "count": v["count"]} for k, v in _knowledge_graph.items()],
            key=lambda x: -x["count"]
        )[:10],
    }


# ── Multi-hop reasoning (item 112) ───────────────────────────

def _multi_hop_verify(entity_id: str, claim_text: str) -> Optional[str]:
    """
    Basic multi-hop: check if entity's known facts contradict the claim.
    E.g. if claim says "X is president of Y" but Wikidata says X is from Z.
    Returns a contradiction note or None.
    """
    if entity_id not in _knowledge_graph:
        return None
    facts = _knowledge_graph[entity_id].get("facts", {})
    claim_lower = claim_text.lower()
    for prop, value in facts.items():
        if value.lower() in claim_lower:
            return None  # consistent
    # No direct contradiction found — inconclusive
    return None


# ── Main verification function ────────────────────────────────

def verify_entities(text: str) -> list:
    """
    Verify named entities in the claim against Wikidata.
    Uses dslim/bert-large-NER for extraction, Wikidata for verification.

    Returns list of dicts:
      {"entity", "type", "found", "wikidata_id", "description", "facts", "flag"}
    """
    entities = extract_entities(text)
    results  = []

    # Verify persons + orgs + locations
    candidates = []
    for name in entities["persons"][:2]:
        candidates.append((name, "PER"))
    for name in entities["orgs"][:2]:
        candidates.append((name, "ORG"))
    for name in entities["locations"][:1]:
        candidates.append((name, "LOC"))

    for name, etype in candidates:
        if len(name) < 3:
            continue
        entity = _search_entity(name)
        if entity:
            facts = _get_entity_facts(entity["id"])
            _update_knowledge_graph(entity["id"], facts, text)
            contradiction = _multi_hop_verify(entity["id"], text)
            results.append({
                "entity":      name,
                "type":        etype,
                "found":       True,
                "wikidata_id": entity["id"],
                "description": entity["description"][:120] if entity["description"] else "",
                "facts":       dict(list(facts.items())[:5]),  # top 5 facts
                "flag":        "possible_contradiction" if contradiction else None,
            })
        else:
            results.append({
                "entity":      name,
                "type":        etype,
                "found":       False,
                "wikidata_id": None,
                "description": "Not found in Wikidata",
                "facts":       {},
                "flag":        "unverified_entity",
            })

    return results


def get_entity_risk_score(verifications: list) -> float:
    """
    Returns 0.0–1.0 risk score based on entity verification.
    Higher = more suspicious (unverified entities or contradictions).
    """
    if not verifications:
        return 0.0
    risk = 0.0
    for v in verifications:
        if not v["found"]:
            risk += 1.0
        elif v.get("flag") == "possible_contradiction":
            risk += 0.5
    return round(min(risk / len(verifications), 1.0), 2)
