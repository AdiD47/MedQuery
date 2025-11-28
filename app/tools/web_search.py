import os
import requests
from typing import Dict, Any, List

TAVILY_URL = "https://api.tavily.com/search"


def tavily_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        # Fallback minimal response
        return {
            "provider": "fallback",
            "query": query,
            "summary": (
                "No Tavily key configured. Provide qualitative web hints via manual follow-up."
            ),
            "results": [],
        }
    try:
        resp = requests.post(
            TAVILY_URL,
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "search_depth": "basic",
                "include_images": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"provider": "tavily", **data}
    except Exception as e:
        return {"provider": "tavily", "error": str(e), "query": query, "results": []}


def extract_candidate_diseases(search_payload: Dict[str, Any]) -> List[str]:
    # Very light heuristic; the Master Agent can refine via LLM
    text = " ".join([
        search_payload.get("answer", ""),
        " ".join([r.get("content", "") for r in search_payload.get("results", [])]),
        search_payload.get("summary", ""),
    ])
    candidates = []
    for kw in ["COPD", "Asthma", "ILD", "IPF", "Bronchiectasis"]:
        if kw.lower() in text.lower():
            candidates.append(kw if kw != "IPF" else "ILD")
    # de-dup and limit
    out = []
    for d in candidates:
        if d not in out:
            out.append(d)
    return out[:5]
