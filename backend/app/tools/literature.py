"""External clinical-evidence sources (PubMed + published guidelines).

The record tools (`app.tools.records`) are the only source of PATIENT facts; this module
is the only source of EXTERNAL clinical evidence. Both carry an id the dentist can open:
record tools return record_ids, these return `PMID:########` or a guideline URL.

Nothing here interprets evidence — each function returns what the source said, verbatim
enough to be checked. A source that is unavailable says so (§22: report the unavailable
source, never invent a result).
"""
from typing import Any

import httpx

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 12.0

# Guideline bodies the advisor may scope a search to. Dental-first; `all` is an open search.
GUIDELINE_SITES = {
    "sdcep": "sdcep.org.uk",      # Scottish Dental Clinical Effectiveness Programme
    "ada": "ada.org",             # American Dental Association
    "nice": "nice.org.uk",        # NICE (UK)
    "cochrane": "cochranelibrary.com",
}


def _unavailable(source: str, reason: str) -> dict[str, Any]:
    """The shape every caller gets when a source cannot be reached (never a fabricated hit)."""
    return {"source": source, "available": False, "reason": reason, "results": []}


def search_pubmed(query: str, max_results: int = 4,
                  high_evidence_only: bool = True) -> dict[str, Any]:
    """Search PubMed via NCBI E-utilities. Returns {source, available, results:[citation...]}.

    high_evidence_only restricts to systematic reviews / clinical trials. That filter is
    narrow enough to return nothing for specific clinical questions, so an empty filtered
    result retries unfiltered rather than reporting "no evidence exists".
    """
    max_results = max(1, min(int(max_results or 4), 10))
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            ids = _esearch(client, query, max_results, high_evidence_only)
            broadened = False
            if not ids and high_evidence_only:
                ids = _esearch(client, query, max_results, False)
                broadened = bool(ids)
            if not ids:
                return {"source": "pubmed", "available": True, "query": query, "results": [],
                        "note": f"No PubMed record matched '{query}'."}
            results = _esummary(client, ids)
    except Exception as e:  # network/API failure -> unavailable, never invented (§22)
        return _unavailable("pubmed", f"PubMed API unavailable: {e}")

    out: dict[str, Any] = {"source": "pubmed", "available": True, "query": query,
                           "results": results}
    if broadened:
        out["note"] = ("No systematic review or trial matched; these are broader PubMed "
                       "records and are weaker evidence.")
    return out


def _esearch(client: httpx.Client, query: str, retmax: int, filtered: bool) -> list[str]:
    term = query
    if filtered:
        term = f"{query} AND (systematic review[Filter] OR clinical trial[Filter])"
    r = client.get(f"{EUTILS}/esearch.fcgi", params={
        "db": "pubmed", "term": term, "retmode": "json", "retmax": retmax})
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])


def _esummary(client: httpx.Client, ids: list[str]) -> list[dict[str, Any]]:
    r = client.get(f"{EUTILS}/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    r.raise_for_status()
    data = r.json().get("result", {})
    out = []
    for pmid in ids:
        item = data.get(pmid, {})
        if not item:
            continue
        out.append({
            "citation_id": f"PMID:{pmid}",
            "title": (item.get("title") or "").strip(),
            "journal": item.get("source", ""),
            "published": item.get("pubdate", ""),
            "publication_types": item.get("pubtype", []),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return out


def search_clinical_guidelines(query: str, site_filter: str = "all",
                               max_results: int = 4) -> dict[str, Any]:
    """Search published clinical guidelines (SDCEP, ADA, NICE, Cochrane) on the open web.

    Returns the source's own snippet and URL — the advisor quotes and links it; it never
    presents a snippet as a guideline's full recommendation.
    """
    max_results = max(1, min(int(max_results or 4), 10))
    try:
        from ddgs import DDGS  # optional dependency; absent -> source unavailable, not fatal
    except ImportError:
        return _unavailable("clinical_guidelines",
                            "guideline web search unavailable (ddgs not installed)")

    site = GUIDELINE_SITES.get((site_filter or "all").lower())
    term = f"{query} site:{site}" if site else f"{query} dental clinical guideline"
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(term, max_results=max_results))
    except Exception as e:  # rate limit / network -> unavailable, never invented (§22)
        return _unavailable("clinical_guidelines", f"guideline search unavailable: {e}")

    results = [{
        "citation_id": r.get("href", ""),
        "title": r.get("title", ""),
        "url": r.get("href", ""),
        "snippet": r.get("body", ""),
        "scope": site or "open web",
    } for r in raw if r.get("href")]

    if not results:
        return {"source": "clinical_guidelines", "available": True, "query": term, "results": [],
                "note": f"No guideline page matched '{term}'."}
    return {"source": "clinical_guidelines", "available": True, "query": term, "results": results}
