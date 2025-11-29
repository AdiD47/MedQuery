import os
import requests
from typing import Dict, Any, List

"""
NVIDIA Biomedical AI-Q Research Agent – Integration Stub

This module integrates with an external NVIDIA Biomedical AI-Q endpoint.
It expects a REST API compatible with the Developer Blueprint, such as a
FastAPI/Helm-deployed service fronting NVIDIA NIM or Triton Inference Server.

Env vars:
- NVIDIA_BIOAIQ_URL: Base URL of the AI-Q service (e.g., http://localhost:8081)
- NVIDIA_BIOAIQ_API_KEY: Bearer token if required

Endpoints (expected):
- POST {BASE}/aiq/analyze: {"question": str, "context": str, "entities": [str]} -> {"analysis": str, "citations": [..]}
- POST {BASE}/aiq/extract_entities: {"text": str} -> {"entities": [..]}
- POST {BASE}/aiq/rank_diseases: {"diseases": [str], "country": str} -> {"ranked": [{..}]}

.
"""

BASE = os.getenv("NVIDIA_BIOAIQ_URL")
API_KEY = os.getenv("NVIDIA_BIOAIQ_API_KEY")


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def is_configured() -> bool:
    return bool(BASE)


def extract_entities(text: str) -> Dict[str, Any]:
    if not BASE:
        return {"configured": False, "entities": []}
    try:
        r = requests.post(f"{BASE}/aiq/extract_entities", json={"text": text}, headers=_headers(), timeout=45)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "entities": []}


def analyze_question(question: str, context: str = "", entities: List[str] | None = None) -> Dict[str, Any]:
    if not BASE:
        return {"configured": False, "analysis": "", "citations": []}
    try:
        payload = {"question": question, "context": context, "entities": entities or []}
        r = requests.post(f"{BASE}/aiq/analyze", json=payload, headers=_headers(), timeout=90)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "analysis": "", "citations": []}


def rank_diseases(diseases: List[str], country: str = "India") -> Dict[str, Any]:
    if not BASE:
        return {"configured": False, "ranked": []}
    try:
        r = requests.post(f"{BASE}/aiq/rank_diseases", json={"diseases": diseases, "country": country}, headers=_headers(), timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "ranked": []}
