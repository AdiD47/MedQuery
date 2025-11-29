from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.crew import run_query

app = FastAPI(title="MedQuery Mock Server", version="0.1.0")

# Static assets and reports serving for the HTML frontend
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
# Ensure directories exist before mounting
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.mount("/reports", StaticFiles(directory=str(_REPORTS_DIR)), name="reports")


class DiseaseRequest(BaseModel):
    disease: str
    country: Optional[str] = "India"


class DiseaseListRequest(BaseModel):
    diseases: List[str]
    country: Optional[str] = "India"


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> Any:
    # Serve the HTML frontend
    idx = _STATIC_DIR / "index.html"
    return FileResponse(str(idx))


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


@app.post("/api/run_query")
def api_run_query(payload: QueryRequest) -> Dict[str, Any]:
    """Run the end-to-end analysis and return JSON result.
    Also include a public report URL for the generated PDF.
    """
    res = run_query(payload.question)
    pdf_path = res.get("report_pdf")
    try:
        if isinstance(pdf_path, str):
            name = Path(pdf_path).name
            res["report_url"] = f"/reports/{name}"
    except Exception:
        pass
    return res
