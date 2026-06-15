"""
foundry_grounding.py
--------------------
The Foundry IQ / Azure AI Search grounding layer (the REQUIRED Microsoft IQ layer).

VERIFIED DESIGN (Microsoft Learn, June 2026):
  - Foundry IQ runs on Azure AI Search agentic retrieval. For an AGENT that reasons
    over results (Palis), Microsoft recommends EXTRACTIVE output, not answer
    synthesis: "extractive data returns raw content that agents can reason over...
    Reserve answer synthesis for standalone apps." (Foundry IQ FAQ)
  - Extractive retrieval needs NO Azure OpenAI model. An LLM is only required for
    query planning / answer synthesis / web sources. For non-web sources it is
    optional in 2026-05-01-preview and unsupported in the 2026-04-01 GA API.
    => This is why Palis does not need the gated gpt-4o-mini. Citations come from
       the retrieval layer: "References are extracted and retained for citation."
  - Requires: Azure AI Search Basic tier+ (semantic ranker), a search index built
    from references/regulatory-sources.md, in a region that supports agentic
    retrieval (West US 2 is supported).

This module keeps a hard MOCK fallback so the demo NEVER depends on a live call.
Set these env vars to go live (never commit them; use .env / Key Vault):
    PALIS_MOCK_MODE=false
    AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
    AZURE_SEARCH_INDEX=palis-reg-index
    AZURE_SEARCH_API_KEY=<query key, not admin key, for least privilege>

HONEST CLAIM for README/demo: "Foundry IQ grounding via Azure AI Search semantic
retrieval in extractive mode." Do NOT claim answer synthesis or LLM query planning
unless those are actually wired (they are deliberately not, and need not be).
"""

import json
import os
import urllib.request
import urllib.error

# Bundled grounded snippets — used in MOCK_MODE and as a safety net if a live call
# fails. In production the same text is RETRIEVED (with a reference) rather than bundled.
_MOCK_SNIPPETS = {
    "P11_AUDIT_TRAIL": "Part 11 requires secure, computer-generated, time-stamped audit "
                       "trails that independently record operator actions creating, "
                       "modifying, or deleting electronic records.",
    "P11_ACCESS_LIMIT": "Limit system access to authorized individuals.",
    "P11_ESIGN": "Signed electronic records must show signature information, and each "
                 "electronic signature must be unique to one individual.",
    "HIPAA_MIN_NECESSARY": "The HIPAA minimum necessary standard limits PHI use and "
                           "disclosure to the least needed for the intended purpose.",
    "HIPAA_ACCESS_CONTROL": "Implement technical policies permitting ePHI access only to "
                            "authorized persons or software.",
    "HIPAA_AUDIT_CONTROLS": "Implement mechanisms to record and examine activity in "
                            "systems containing ePHI.",
    "GDPR_ART9": "Health data is a special category; re-identifiable data is not "
                 "de-identified and remains subject to Article 9 protections.",
    "GCP_DELEGATION": "Study tasks may be performed only by qualified, delegated "
                      "individuals; records must be attributable and accurate.",
}


def _live_retrieve(citation_anchor: str) -> dict | None:
    """
    Query Azure AI Search with semantic ranking and return the top extractive caption
    plus its source reference. Uses the STABLE search API + semantic queryType — the
    semantic ranker returns verbatim captions ("extracted verbatim from text in the
    search document"), which is exactly the grounded, citable text Palis needs and
    requires no LLM.

    Returns {"grounded_text", "reference"} or None on any failure (caller falls back
    to the mock snippet so a finding is never left ungrounded on camera).

    NOTE: request/response shapes follow the documented semantic-query API. Verify the
    api-version and your index's field names against your service before the live demo.
    """
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    index = os.environ.get("AZURE_SEARCH_INDEX")
    api_key = os.environ.get("AZURE_SEARCH_API_KEY")
    if not (endpoint and index and api_key):
        return None

    url = f"{endpoint}/indexes/{index}/docs/search?api-version=2024-07-01"
    body = {
        "search": citation_anchor,
        "queryType": "semantic",
        "semanticConfiguration": os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIG", "default"),
        "captions": "extractive",
        "answers": "extractive|count-1",
        "top": 3,
        "select": "title,content,source_url",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    # Prefer a semantic answer; else the top document's semantic caption.
    answers = data.get("@search.answers") or []
    if answers:
        top = answers[0]
        return {"grounded_text": top.get("text", "").strip(),
                "reference": "Azure AI Search (semantic answer)"}
    results = data.get("value") or []
    if results:
        doc = results[0]
        caps = doc.get("@search.captions") or []
        text = (caps[0].get("text") if caps else doc.get("content", "")).strip()
        return {"grounded_text": text,
                "reference": doc.get("source_url") or doc.get("title") or "Azure AI Search"}
    return None


def retrieve_grounding(control_id: str, citation_anchor: str, mock_mode: bool) -> dict:
    """
    Return {"grounded_text", "reference", "grounding_mode"} for a control.
    mock_mode -> bundled snippet. Live -> Azure AI Search extractive retrieval, with a
    safe fallback to the bundled snippet if the call returns nothing (never ungrounded).
    """
    if mock_mode:
        return {"grounded_text": _MOCK_SNIPPETS.get(control_id, ""),
                "reference": "bundled (mock mode)",
                "grounding_mode": "mock"}

    live = _live_retrieve(citation_anchor)
    if live and live.get("grounded_text"):
        live["grounding_mode"] = "foundry_iq_extractive"
        return live
    # Safety net: degrade to the bundled snippet rather than assert nothing.
    return {"grounded_text": _MOCK_SNIPPETS.get(control_id, ""),
            "reference": "bundled (live retrieval unavailable)",
            "grounding_mode": "fallback"}
