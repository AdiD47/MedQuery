import os
import requests
from typing import Dict, Any

MOCK_URL = os.getenv("MOCK_SERVER_URL", "http://127.0.0.1:8000")


def uspto_mock(disease: str, country: str = "India") -> Dict[str, Any]:
    url = f"{MOCK_URL}/mock/uspto"
    resp = requests.post(url, json={"disease": disease, "country": country}, timeout=20)
    resp.raise_for_status()
    return resp.json()
