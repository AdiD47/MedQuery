from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import logging
import time
import asyncio
import json
from functools import lru_cache

from app.crew import run_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedQuery Intelligence Platform",
    version="1.0.0",
    description="Multi-agent biomedical intelligence system for disease opportunity analysis"
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=600
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Static assets and reports serving for the HTML frontend
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

try:
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Static directory: {_STATIC_DIR}")
    logger.info(f"Reports directory: {_REPORTS_DIR}")
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.mount("/reports", StaticFiles(directory=str(_REPORTS_DIR)), name="reports")
except Exception as e:
    logger.error(f"Failed to mount static directories: {e}")
    raise


class DiseaseRequest(BaseModel):
    disease: str
    country: Optional[str] = "India"


class DiseaseListRequest(BaseModel):
    diseases: List[str]
    country: Optional[str] = "India"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500, description="Research question about disease opportunities")
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        # Basic sanitization
        v = v.strip()
        if len(v.split()) < 3:
            raise ValueError('Question must contain at least 3 words')
        return v


class RankedDisease(BaseModel):
    disease: str
    score: float
    market_size_usd: int
    competitor_count: int
    phase2_india: int
    phase3_india: int
    trials_total_india: int
    patent_filings_last_5y: Optional[int] = 0
    key_patents_expiring_in_years: Optional[int] = 0


class QueryResponse(BaseModel):
    ranked: List[RankedDisease]
    summary: str
    report_url: Optional[str]
    processing_time_ms: int
    status: str = "success"


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


@app.post("/api/run_query", response_model=None)
async def api_run_query(payload: QueryRequest, request: Request) -> Any:
    """Run the end-to-end multi-agent analysis and return structured JSON result.
    
    Returns disease ranking, executive summary, and PDF report URL.
    Gracefully handles errors with structured JSON responses.
    
    Args:
        payload: QueryRequest containing the research question
        
    Returns:
        JSON with ranked diseases, summary, report URL, and processing time
    """
    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    
    try:
        logger.info(f"Processing query from {client_host}: '{payload.question[:100]}'")
        
        # Validate environment
        import os
        if not os.getenv("GOOGLE_API_KEY"):
            logger.warning("GOOGLE_API_KEY not set - using fallback mode")
        
        # Run analysis
        res = run_query(payload.question)
        
        # Process PDF path
        pdf_path = res.get("report_pdf")
        if isinstance(pdf_path, str) and Path(pdf_path).exists():
            name = Path(pdf_path).name
            res["report_url"] = f"/reports/{name}"
            logger.info(f"Generated report: {name}")
        else:
            res["report_url"] = None
            logger.warning("No PDF report generated")
        
        # Add processing time
        processing_time = int((time.time() - start_time) * 1000)
        res["processing_time_ms"] = processing_time
        res["status"] = "success"
        
        logger.info(f"Query completed in {processing_time}ms")
        return res
        
    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error: {e}")
        return JSONResponse(
            {"error": f"Invalid input: {str(e)}", "status": "validation_error"},
            status_code=400
        )
    except TimeoutError as e:
        logger.error(f"Timeout error: {e}")
        return JSONResponse(
            {"error": "Analysis timed out. Please try again with a simpler query.", "status": "timeout"},
            status_code=408
        )
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception("Unexpected error in run_query")
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return JSONResponse(
            {
                "error": f"Analysis failed: {error_msg}",
                "status": "error",
                "processing_time_ms": int((time.time() - start_time) * 1000)
            },
            status_code=200  # Return 200 to avoid frontend error handling issues
        )
