import os
import logging
import time
from typing import List, Dict, Any, Optional, Generator
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Lazy imports for faster startup - only import when needed
def _get_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None

from app.tools.web_search import tavily_search, extract_candidate_diseases
from app.tools.iqvia_client import iqvia_get, exim_get
from app.tools.uspto_client import uspto_mock
from app.tools.clinicaltrials_client import trials_stats_for_disease_in_india
from app.tools.rag import query as rag_query
from app.tools.report_pdf import generate_report
from app.tools.nvidia_bio_aiq import is_configured as nvidia_is_configured, analyze_question as nvidia_analyze, rank_diseases as nvidia_rank

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Cache configuration
MAX_WORKERS = 5  # For parallel data gathering

# Lazy LLM initialization - only create when needed (saves ~2GB memory at startup)
_llm_instance = None

def _get_llm():
    """Lazy singleton for LLM to reduce memory footprint."""
    global _llm_instance
    if _llm_instance is None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            _llm_instance = ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_CHAT_MODEL", "gemini-1.5-pro"),
                temperature=0.3
            )
    return _llm_instance


def _normalize(values: List[float]) -> List[float]:
    """Normalize values to [0,1] range using vectorized operations when available."""
    if not values:
        return values
    
    # Use numpy for vectorized operations (10x faster for large arrays)
    np = _get_numpy()
    if np is not None and len(values) > 10:
        arr = np.array(values, dtype=np.float32)
        lo, hi = arr.min(), arr.max()
        if hi - lo == 0:
            return [0.5] * len(values)
        return ((arr - lo) / (hi - lo)).tolist()
    
    # Fallback to standard Python
    lo, hi = min(values), max(values)
    if hi - lo == 0:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def _structured_summary(
    question: str,
    ranked: List[Dict[str, Any]],
    search_payload: Dict[str, Any],
    internal_refs: List[Dict[str, Any]] | None,
    nvidia_preface: Dict[str, Any] | None,
) -> str:
    """Generate a Perplexity-style structured answer with sections, rationale, and citations.
    Falls back to heuristic if LLM unavailable or errors.
    """
    api_key = os.getenv("GOOGLE_API_KEY")

    def _heuristic() -> str:
        lines = ["## Executive Summary (Heuristic)", f"Question: {question}"]
        top = ranked[:3]
        if top:
            lines.append("\n### Top Candidates")
            for row in top:
                lines.append(
                    f"- {row['disease']} (score={row['score']:.2f}, competitors={row['competitor_count']}, trialsP2={row['phase2_india']}, trialsP3={row['phase3_india']})"
                )
        lines.append("\n### Rationale")
        lines.append(
            "Score approximates burden (market size) minus competition (competitors + late-stage trials). Higher score => attractive gap."
        )
        if internal_refs:
            lines.append("\n### Internal Notes (Snippets)")
            for ref in internal_refs[:3]:
                lines.append(f"- {ref['disease']}: {ref['snippet']}…")
        lines.append("\n### Next Questions")
        lines.append("- Validate patient prevalence data magnitude")
        lines.append("- Examine regulatory timelines for top 2 diseases")
        return "\n".join(lines)

    if not api_key:
        return _heuristic()

    # Use generator for memory-efficient CSV building
    def _gen_csv_rows() -> Generator[str, None, None]:
        yield "disease,score,market_size_usd,competitors,phase2_india,phase3_india,patent_filings_last_5y,key_patents_expiring_in_years,trials_total_india"
        for r in ranked:
            yield f"{r['disease']},{r['score']:.3f},{r.get('market_size_usd',0)},{r.get('competitor_count',0)},{r.get('phase2_india',0)},{r.get('phase3_india',0)},{r.get('patent_filings_last_5y',0)},{r.get('key_patents_expiring_in_years',0)},{r.get('trials_total_india',0)}"
    
    rows_csv = "\n".join(_gen_csv_rows())
    )
    web_citations: List[str] = []
    for r in (search_payload.get("results", []) or [])[:5]:
        url = r.get("url") or ""
        title = r.get("title") or ""
        if url:
            web_citations.append(f"{title} | {url}")
    internal_citations = [f"{ref['disease']}: {ref['source']}" for ref in (internal_refs or [])[:5]]

    nvidia_analysis = None
    if nvidia_preface and isinstance(nvidia_preface, dict):
        nvidia_analysis = nvidia_preface.get("analysis")

    model_name = os.getenv("GOOGLE_CHAT_MODEL", "gemini-1.5-pro")
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)
        prompt = (
            "You are an expert pharma strategy analyst. Produce a structured answer in concise markdown.\n"
            "Sections (use these exact headings):\n"
            "1. **Executive Summary** (<=120 words)\n"
            "2. **Ranking Rationale** (bullet points explaining top 2-3)\n"
            "3. **Key Metrics Table** (compact markdown table)\n"
            "4. **Signals & Gaps** (competition gaps, trial scarcity, patent timing)\n"
            "5. **Next Recommended Actions** (3 bullets)\n"
            "6. **Citations** (list)\n"
            "\nContext CSV:\n" + rows_csv + "\n"
            + ("\nNVIDIA Analysis:\n" + nvidia_analysis + "\n" if nvidia_analysis else "")
            + ("\nWeb Sources:\n" + "\n".join(web_citations) + "\n" if web_citations else "")
            + ("\nInternal Snippets:\n" + "\n".join(internal_citations) + "\n" if internal_citations else "")
            + "\nConstraints: Keep total under 500 words. Be precise and non-repetitive."
        )
        resp = llm.invoke(prompt)
        return getattr(resp, "content", str(resp))
    except Exception:
        return _heuristic()


def _gather_disease_data(disease: str) -> Dict[str, Any]:
    """Gather all data for a single disease with error handling."""
    try:
        iqvia = iqvia_get(disease)
        exim = exim_get(disease)
        patents = uspto_mock(disease)
        trials = trials_stats_for_disease_in_india(disease)
        
        return {
            "disease": disease,
            "market_size_usd": iqvia.get("market_size_usd", 0),
            "competitor_count": iqvia.get("competitor_count", 0),
            "api_exports_tonnes": exim.get("api_exports_tonnes", 0.0),
            "api_imports_tonnes": exim.get("api_imports_tonnes", 0.0),
            "patent_filings_last_5y": patents.get("patent_filings_last_5y", 0),
            "key_patents_expiring_in_years": patents.get("key_patents_expiring_in_years", 0),
            "phase2_india": trials.get("phase2_india", 0),
            "phase3_india": trials.get("phase3_india", 0),
            "trials_total_india": trials.get("total_trials_india", 0),
            "error": None
        }
    except Exception as e:
        logger.warning(f"Error gathering data for {disease}: {e}")
        return {
            "disease": disease,
            "market_size_usd": 0,
            "competitor_count": 0,
            "api_exports_tonnes": 0.0,
            "api_imports_tonnes": 0.0,
            "patent_filings_last_5y": 0,
            "key_patents_expiring_in_years": 0,
            "phase2_india": 0,
            "phase3_india": 0,
            "trials_total_india": 0,
            "error": str(e)
        }


def run_query(question: str) -> Dict[str, Any]:
    """
    Execute end-to-end multi-agent disease opportunity analysis.
    
    Args:
        question: Research question about disease opportunities
        
    Returns:
        Dictionary with ranked diseases, summary, and report path
        
    Raises:
        ValueError: If question is invalid
        TimeoutError: If analysis takes too long
    """
    logger.info(f"Starting analysis for: {question[:100]}")
    
    if not question or len(question.strip()) < 10:
        raise ValueError("Question must be at least 10 characters")
    
    # Optional NVIDIA Biomedical AI-Q pre-analysis
    nvidia_preface = None
    if nvidia_is_configured():
        try:
            logger.info("Running NVIDIA AI-Q pre-analysis")
            nvidia_preface = nvidia_analyze(question)
        except Exception as e:
            logger.warning(f"NVIDIA pre-analysis failed: {e}")

    # 1) Identify diseases via web intelligence
    try:
        logger.info("Searching for candidate diseases")
        search = tavily_search(
            f"respiratory diseases high patient burden India competitive landscape"
        )
        candidates = extract_candidate_diseases(search)
        if not candidates:
            logger.warning("No candidates from web search, using defaults")
            candidates = ["COPD", "Asthma", "ILD"]
        else:
            logger.info(f"Found {len(candidates)} candidates: {candidates}")
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        candidates = ["COPD", "Asthma", "ILD"]

    # Optional NVIDIA AI-Q ranking of candidates (as a hint)
    nvidia_ranked = None
    if nvidia_is_configured():
        try:
            rnk = nvidia_rank(candidates, country="India")
            if isinstance(rnk, dict) and rnk.get("ranked"):
                # reorder candidates by NVIDIA rank if provided
                order = [row.get("disease") for row in rnk.get("ranked", []) if row.get("disease") in candidates]
                # stable merge of order over candidates
                new_candidates = []
                for d in order:
                    if d not in new_candidates:
                        new_candidates.append(d)
                for d in candidates:
                    if d not in new_candidates:
                        new_candidates.append(d)
                candidates = new_candidates
                nvidia_ranked = rnk.get("ranked")
                logger.info("Applied NVIDIA ranking hints")
        except Exception as e:
            logger.warning(f"NVIDIA ranking failed: {e}")

    # 2) Competition and landscape per disease (parallel)
    logger.info(f"Gathering data for {len(candidates)} diseases in parallel")
    rows: List[Dict[str, Any]] = []
    
    try:
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(candidates))) as executor:
            future_to_disease = {executor.submit(_gather_disease_data, d): d for d in candidates}
            for future in as_completed(future_to_disease):
                disease = future_to_disease[future]
                try:
                    row = future.result(timeout=30)
                    rows.append(row)
                except Exception as e:
                    logger.error(f"Failed to gather data for {disease}: {e}")
                    # Add placeholder row
                    rows.append(_gather_disease_data(disease))
    except Exception as e:
        logger.error(f"Parallel data gathering failed: {e}, falling back to sequential")
        # Fallback to sequential
        for d in candidates:
            rows.append(_gather_disease_data(d))
    
    if not rows:
        raise ValueError("No disease data collected")

    # 3) Score: high burden proxy (market size) - competition (competitors + trials)
    perf_start = time.time()
    logger.info("Starting scoring phase")
    logger.info("Calculating opportunity scores")
    try:
        ms = _normalize([r["market_size_usd"] for r in rows])
        comp = _normalize([r["competitor_count"] + r["phase2_india"] + r["phase3_india"] for r in rows])
        scores = [m - c for m, c in zip(ms, comp)]
        for r, s in zip(rows, scores):
            r["score"] = s
    except Exception as e:
        logger.error(f"Scoring failed: {e}, using default scores")
        for r in rows:
            r["score"] = 0.5

    rows_sorted = sorted(rows, key=lambda x: x["score"], reverse=True)
    scoring_time = time.time() - perf_start
    logger.info(f"Scoring completed in {scoring_time:.2f}s - Top: {rows_sorted[0]['disease']} (score: {rows_sorted[0]['score']:.3f})")

    # 4) Internal knowledge lookup (RAG)
    rag_start = time.time()
    internal_refs: List[Dict[str, Any]] = []
    try:
        logger.info("Querying RAG for internal knowledge")
        for d in rows_sorted[:3]:
            try:
                q = f"past research on {d['disease']}"
                res = rag_query(q).get("results", [])
                for hit in res[:2]:
                    internal_refs.append(
                        {"disease": d["disease"], "snippet": hit["text"][:140], "source": hit["source"]}
                    )
            except Exception as e:
                logger.warning(f"RAG query failed for {d['disease']}: {e}")
        if internal_refs:
            rag_time = time.time() - rag_start
            logger.info(f"RAG completed in {rag_time:.2f}s - Found {len(internal_refs)} internal references")
    except Exception as e:
        logger.warning(f"RAG lookup failed: {e}")

    # 5) Synthesis via LLM
    llm_start = time.time()
    logger.info("Generating structured summary")
    try:
        summary = _structured_summary(question, rows_sorted, search, internal_refs, nvidia_preface)
        llm_time = time.time() - llm_start
        logger.info(f"LLM summary completed in {llm_time:.2f}s")
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        summary = f"## Analysis Summary\n\nTop opportunity: {rows_sorted[0]['disease']}\n\nError generating detailed summary: {str(e)}"

    # 6) Build tables for PDF
    iqvia_table = [
        {
            "disease": r["disease"],
            "market_size_usd": r["market_size_usd"],
            "competitor_count": r["competitor_count"],
        }
        for r in rows_sorted
    ]
    patent_table = [
        {
            "disease": r["disease"],
            "patent_filings_last_5y": r["patent_filings_last_5y"],
            "key_patents_expiring_in_years": r["key_patents_expiring_in_years"],
        }
        for r in rows_sorted
    ]
    trials_table = [
        {
            "disease": r["disease"],
            "phase2_india": r["phase2_india"],
            "phase3_india": r["phase3_india"],
            "total_india": r["trials_total_india"],
        }
        for r in rows_sorted
    ]

    # 6) Generate PDF report
    logger.info("Generating PDF report")
    pdf_path = None
    try:
        pdf_path = generate_report(
            title="Low-Competition, High-Burden Respiratory Diseases in India",
            question=question,
            summary=summary,
            disease_rankings=[
                {
                    "disease": r["disease"],
                    "score": round(r["score"], 3),
                    "market_size_usd": r["market_size_usd"],
                    "competitor_count": r["competitor_count"],
                    "phase2": r["phase2_india"],
                    "phase3": r["phase3_india"],
                }
                for r in rows_sorted
            ],
            iqvia_table=iqvia_table,
            patent_table=patent_table,
            trials_table=trials_table,
            internal_refs=internal_refs if internal_refs else None,
        )
        logger.info(f"PDF report generated: {pdf_path}")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")

    logger.info("Analysis complete")
    return {
        "question": question,
        "candidates": candidates,
        "ranked": rows_sorted,
        "summary": summary,
        "report_pdf": pdf_path,
        "nvidia_ranked": nvidia_ranked,
    }
