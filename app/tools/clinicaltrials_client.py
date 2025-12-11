import requests
import logging
from typing import Dict, Any
from urllib.parse import quote_plus
from functools import lru_cache

BASE = "https://clinicaltrials.gov/api/v2/studies"
TIMEOUT = 30
MAX_RETRIES = 2

logger = logging.getLogger(__name__)


@lru_cache(maxsize=100)
def trials_stats_for_disease_in_india(disease: str) -> Dict[str, Any]:
    """
    Fetch clinical trial statistics for a disease in India.
    
    Args:
        disease: Disease name to search for
        
    Returns:
        Dictionary with trial counts and examples
    """
    # Fetch page 1 with modest page size
    q = quote_plus(disease)
    url = f"{BASE}?query.term={q}&pageSize=100"
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Fetching trials for {disease} (attempt {attempt + 1}/{MAX_RETRIES})")
            r = requests.get(url, timeout=TIMEOUT)
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
            # phases may be None or contain non-strings; normalize safely
            if not ph or not isinstance(ph, (list, tuple)):
                return ""
            safe = [str(x) for x in ph if x is not None]
            return ",".join(safe)

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
            logger.info(f"Found {total} trials in India for {disease} (P2: {p2}, P3: {p3})")
            return {
                "disease": disease,
                "total_trials_india": total,
                "phase2_india": p2,
                "phase3_india": p3,
                "examples": examples,
            }
            
        except requests.Timeout:
            logger.warning(f"Timeout fetching trials for {disease} (attempt {attempt + 1})")
            if attempt == MAX_RETRIES - 1:
                raise
        except requests.RequestException as e:
            logger.warning(f"Request error for {disease}: {e} (attempt {attempt + 1})")
            if attempt == MAX_RETRIES - 1:
                raise
        except Exception as e:
            logger.error(f"Unexpected error for {disease}: {e}")
            raise
    
    # If all retries failed
    return {
        "disease": disease,
        "error": "Max retries exceeded",
        "total_trials_india": 0,
        "phase2_india": 0,
        "phase3_india": 0,
        "examples": [],
    }
