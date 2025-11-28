from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(title="MedQuery Mock Server", version="0.1.0")


class DiseaseRequest(BaseModel):
    disease: str
    country: Optional[str] = "India"


class DiseaseListRequest(BaseModel):
    diseases: List[str]
    country: Optional[str] = "India"


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# Deterministic mock data for demo
MOCK_IQVIA: Dict[str, Dict[str, Any]] = {
    "COPD": {
        "market_size_usd": 1200000000,
        "competitor_count": 18,
        "top_competitors": ["GSK", "Novartis", "Cipla", "Sun Pharma"],
    },
    "Asthma": {
        "market_size_usd": 900000000,
        "competitor_count": 14,
        "top_competitors": ["GSK", "AstraZeneca", "Hikal"],
    },
    "ILD": {
        "market_size_usd": 300000000,
        "competitor_count": 6,
        "top_competitors": ["Roche", "Boehringer Ingelheim"],
    },
}

MOCK_EXIM: Dict[str, Dict[str, Any]] = {
    "COPD": {"api_exports_tonnes": 4.2, "api_imports_tonnes": 6.8},
    "Asthma": {"api_exports_tonnes": 3.1, "api_imports_tonnes": 2.7},
    "ILD": {"api_exports_tonnes": 0.5, "api_imports_tonnes": 1.3},
}

MOCK_USPTO: Dict[str, Dict[str, Any]] = {
    "COPD": {
        "patent_filings_last_5y": 520,
        "key_patents_expiring_in_years": 5,
        "highlights": ["Biologics in late-stage", "Device combos"],
    },
    "Asthma": {
        "patent_filings_last_5y": 410,
        "key_patents_expiring_in_years": 4,
        "highlights": ["Inhaled corticosteroids", "Long-acting beta agonists"],
    },
    "ILD": {
        "patent_filings_last_5y": 160,
        "key_patents_expiring_in_years": 2,
        "highlights": ["Antifibrotics", "Repurposed small molecules"],
    },
}


@app.post("/mock/iqvia")
def mock_iqvia(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_IQVIA.get(d, {
        "market_size_usd": 150000000,
        "competitor_count": 5,
        "top_competitors": ["GenericCo"],
    })
    return {"disease": d, "country": payload.country, **data}


@app.post("/mock/iqvia/bulk")
def mock_iqvia_bulk(payload: DiseaseListRequest) -> Dict[str, Any]:
    out = []
    for d in payload.diseases:
        item = MOCK_IQVIA.get(d, {
            "market_size_usd": 150000000,
            "competitor_count": 5,
            "top_competitors": ["GenericCo"],
        })
        out.append({"disease": d, **item})
    return {"country": payload.country, "results": out}


@app.post("/mock/exim")
def mock_exim(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_EXIM.get(d, {"api_exports_tonnes": 0.0, "api_imports_tonnes": 0.0})
    return {"disease": d, "country": payload.country, **data}


@app.post("/mock/uspto")
def mock_uspto(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_USPTO.get(d, {
        "patent_filings_last_5y": 40,
        "key_patents_expiring_in_years": 1,
        "highlights": ["Limited filings"],
    })
    return {"disease": d, "country": payload.country, **data}
