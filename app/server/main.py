from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

# Import your new non-CrewAI pipeline
from scripts.run_medquery import run_medquery  # ← CHANGED THIS LINE

app = FastAPI(title="MedQuery Mock Server", version="0.1.0")

# Static assets and reports serving
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

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
    idx = _STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"message": "MedQuery Mock Server Running. Frontend not found at /static/index.html"}


# === Mock Endpoints (unchanged) ===
MOCK_IQVIA: Dict[str, Dict[str, Any]] = {
    "COPD": {"market_size_usd": 1200000000, "competitor_count": 18},
    "Asthma": {"market_size_usd": 900000000, "competitor_count": 14},
    "ILD": {"market_size_usd": 300000000, "competitor_count": 6},
    "Idiopathic Pulmonary Fibrosis": {"market_size_usd": 350000000, "competitor_count": 7},
    "Tuberculosis": {"market_size_usd": 800000000, "competitor_count": 10},
    "Non-Small Cell Lung Cancer": {"market_size_usd": 1100000000, "competitor_count": 22},
    "Multiple Myeloma": {"market_size_usd": 600000000, "competitor_count": 15},
}

MOCK_EXIM: Dict[str, Dict[str, Any]] = {
    "COPD": {"api_exports_tonnes": 4.2, "api_imports_tonnes": 6.8},
    "Asthma": {"api_exports_tonnes": 3.1, "api_imports_tonnes": 2.7},
    "ILD": {"api_exports_tonnes": 0.5, "api_imports_tonnes": 1.3},
}

MOCK_USPTO: Dict[str, Dict[str, Any]] = {
    "COPD": {"patent_filings_last_5y": 520, "key_patents_expiring_in_years": 5},
    "Asthma": {"patent_filings_last_5y": 410, "key_patents_expiring_in_years": 4},
    "ILD": {"patent_filings_last_5y": 160, "key_patents_expiring_in_years": 2},
}


@app.post("/mock/iqvia")
def mock_iqvia(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_IQVIA.get(d, {"market_size_usd": 150000000, "competitor_count": 5})
    return {"disease": d, "country": payload.country, **data}


@app.post("/mock/exim")
def mock_exim(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_EXIM.get(d, {"api_exports_tonnes": 0.0, "api_imports_tonnes": 0.0})
    return {"disease": d, "country": payload.country, **data}


@app.post("/mock/uspto")
def mock_uspto(payload: DiseaseRequest) -> Dict[str, Any]:
    d = payload.disease.strip()
    data = MOCK_USPTO.get(d, {"patent_filings_last_5y": 40, "key_patents_expiring_in_years": 1})
    return {"disease": d, "country": payload.country, **data}


# === New API Endpoint Using Your Modern Pipeline ===
@app.post("/api/run_query")
def api_run_query(payload: QueryRequest) -> Any:
    """Run the full NVIDIA Bio-powered analysis"""
    try:
        # Call your new run_medquery function directly
        result = run_medquery(payload.question)
        
        # Add report URL for frontend
        pdf_path = result.get("report_pdf")
        if pdf_path and isinstance(pdf_path, str):
            name = Path(pdf_path).name
            result["report_url"] = f"/reports/{name}"
        
        return result
    except Exception as e:
        logging.exception("run_medquery failed")
        return JSONResponse(
            content={"error": f"Analysis failed: {str(e)}"},
            status_code=500
        )
