import requests
from typing import Dict, Any
from urllib.parse import quote_plus

BASE = "https://clinicaltrials.gov/api/v2/studies"


def trials_stats_for_disease_in_india(disease: str) -> Dict[str, Any]:
    # Fetch page 1 with modest page size
    q = quote_plus(disease)
    url = f"{BASE}?query.term={q}&pageSize=100"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        studies = data.get("studies", [])
        # Filter by location country = India, and phases 2 or 3
        def in_india(st: Dict[str, Any]) -> bool:
            locs = (
                st.get("protocolSection", {})
                .get("contactsLocationsModule", {})
                .get("locations", [])
            )
            for loc in locs:
                addr = loc.get("location", {}).get("address", {})
                if str(addr.get("country", "")).lower() == "india":
                    return True
            return False

        def phase(st: Dict[str, Any]) -> str:
            ph = (
                st.get("protocolSection", {})
                .get("designModule", {})
                .get("phases", [])
            )
            return ",".join(ph)

        total = 0
        p2 = 0
        p3 = 0
        examples = []
        for st in studies:
            if not in_india(st):
                continue
            total += 1
            phs = phase(st).lower()
            if "phase 2" in phs:
                p2 += 1
            if "phase 3" in phs:
                p3 += 1
            if len(examples) < 5:
                examples.append({
                    "nctId": st.get("protocolSection", {}).get("identificationModule", {}).get("nctId"),
                    "title": st.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle"),
                    "phases": phs,
                })
        return {
            "disease": disease,
            "total_trials_india": total,
            "phase2_india": p2,
            "phase3_india": p3,
            "examples": examples,
        }
    except Exception as e:
        return {
            "disease": disease,
            "error": str(e),
            "total_trials_india": 0,
            "phase2_india": 0,
            "phase3_india": 0,
            "examples": [],
        }
