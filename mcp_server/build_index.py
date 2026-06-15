"""
build_index.py — ONE-TIME setup for live Foundry IQ grounding.
==============================================================
Creates the Azure AI Search index, loads the regulatory control corpus (from
control_library.py), and adds a semantic configuration named "default" so
foundry_grounding.py can retrieve cited regulation text in EXTRACTIVE mode
(semantic ranker, no LLM required).

Run this ONCE, from the mcp_server/ folder, after the search service exists:

    export AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
    export AZURE_SEARCH_ADMIN_KEY=<your search ADMIN key>   # build needs write access
    export AZURE_SEARCH_INDEX=palis-reg-index
    python3 build_index.py

Expected output:
    [index] PUT palis-reg-index -> 201   (or 204 if it already existed)
    [docs]  uploaded 8 documents -> 200

Then point the server at the index and turn live grounding on:
    export AZURE_SEARCH_API_KEY=<query key (preferred) or admin key>
    export AZURE_SEARCH_INDEX=palis-reg-index
    export PALIS_MOCK_MODE=false
    python3 server.py

Uses only the Python standard library (urllib) — no extra installs.
Reads all credentials from env vars; never hard-code keys here.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from control_library import CONTROLS

ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
ADMIN_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY")
INDEX = os.environ.get("AZURE_SEARCH_INDEX", "palis-reg-index")
API = "2024-07-01"  # stable API version; semantic configuration is GA here


def _req(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "api-key": ADMIN_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8")}
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def main() -> None:
    if not (ENDPOINT and ADMIN_KEY):
        sys.exit("ERROR: set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_ADMIN_KEY first.")

    # 1) Create (or update) the index with a semantic configuration named "default".
    index_def = {
        "name": INDEX,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "title", "type": "Edm.String", "searchable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "framework", "type": "Edm.String", "searchable": True, "filterable": True},
            {"name": "citation", "type": "Edm.String", "searchable": True},
            {"name": "source_url", "type": "Edm.String"},
        ],
        "semantic": {
            "configurations": [
                {
                    "name": "default",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "prioritizedContentFields": [{"fieldName": "content"}],
                        "prioritizedKeywordsFields": [{"fieldName": "citation"}],
                    },
                }
            ]
        },
    }
    status, resp = _req("PUT", f"{ENDPOINT}/indexes/{INDEX}?api-version={API}", index_def)
    print(f"[index] PUT {INDEX} -> {status}")
    if status >= 400 or status == 0:
        sys.exit(f"Index create/update failed: {resp}")

    # 2) Upload one document per control — the regulatory corpus retrieval grounds on.
    docs = []
    for c in CONTROLS.values():
        docs.append({
            "@search.action": "mergeOrUpload",
            "id": c.id,
            "title": f"{c.framework} {c.citation} — {c.title}",
            "content": f"{c.requirement} (Keywords: {c.citation_anchor})",
            "framework": c.framework,
            "citation": c.citation,
            "source_url": c.source_url,
        })
    status, resp = _req("POST", f"{ENDPOINT}/indexes/{INDEX}/docs/index?api-version={API}",
                        {"value": docs})
    print(f"[docs]  uploaded {len(docs)} documents -> {status}")
    if status >= 400 or status == 0:
        sys.exit(f"Document upload failed: {resp}")

    print("\n✅ Index built. Turn on live grounding:")
    print("   export AZURE_SEARCH_API_KEY=<query or admin key>")
    print(f"   export AZURE_SEARCH_INDEX={INDEX}")
    print("   export PALIS_MOCK_MODE=false")
    print("   python3 server.py")
    print("\nThen in the Inspector, run map_to_controls on an agent and confirm")
    print('   "grounding_mode": "foundry_iq_extractive"  (not "fallback").')


if __name__ == "__main__":
    main()
