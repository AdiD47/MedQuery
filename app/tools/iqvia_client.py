import os
import requests
from typing import Dict, Any, List

MOCK_URL = os.getenv("MOCK_SERVER_URL", "http://127.0.0.1:8000")


def iqvia_get(disease: str, country: str = "India") -> Dict[str, Any]:
    url = f"{MOCK_URL}/mock/iqvia"
    resp = requests.post(url, json={"disease": disease, "country": country}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def iqvia_bulk(diseases: List[str], country: str = "India") -> Dict[str, Any]:
    url = f"{MOCK_URL}/mock/iqvia/bulk"
    resp = requests.post(url, json={"diseases": diseases, "country": country}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def exim_get(disease: str, country: str = "India") -> Dict[str, Any]:
    url = f"{MOCK_URL}/mock/exim"
    resp = requests.post(url, json={"disease": disease, "country": country}, timeout=20)
    resp.raise_for_status()
    return resp.json()
