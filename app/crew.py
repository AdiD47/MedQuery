import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from app.tools.web_search import tavily_search, extract_candidate_diseases
from app.tools.iqvia_client import iqvia_get, exim_get
from app.tools.uspto_client import uspto_mock
from app.tools.clinicaltrials_client import trials_stats_for_disease_in_india
from app.tools.rag import query as rag_query
from app.tools.report_pdf import generate_report

# NVIDIA Biomedical AI-Q (keep if you want to retain this optional integration)
from app.tools.nvidia_bio_aiq import (
    is_configured as nvidia_is_configured,
    analyze_question as nvidia_analyze,
    rank_diseases as nvidia_rank,
)

# Replace Google Gemini with NVIDIA NIM LLM
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()


def _normalize(values: List[float]) -> List[float]:
    if not values:
        return values
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
    """Structured answer. Uses NVIDIA analysis if provided."""
    api_key = os.getenv("NVIDIA_API_KEY")  # Now uses NVIDIA key

    def _heuristic() -> str:
        lines = ["## Executive Summary (Heuristic)", f"Question: {question}"]
        top = ranked[:3]
        if top:
            lines.append("\n### Top Candidates")
            for row in top:
                lines.append(
                    f"- {row['disease']} (score={row['score']:.2f}, competitors={row['competitor_count']}, "
                    f"trialsP2={row['phase2_india']}, trialsP3={row['phase3_india']})"
                )
        lines.append("\n### NVIDIA Analysis")
        lines.append(nvidia_preface.get("analysis", "N/A") if nvidia_preface else "N/A")
        lines.append("\n### Rationale")
        lines.append(
            "Score approximates burden (market size) minus competition (competitors + trials). Higher score => more attractive."
        )
        if internal_refs:
            lines.append("\n### Internal Notes (Snippets)")
            for ref in internal_refs[:3]:
                lines.append(f"- {ref['disease']}: {ref['snippet']}…")
        lines.append("\n### Next Questions")
        lines.append("- Validate prevalence")
        lines.append("- Analyze regulatory timelines")
        return "\n".join(lines)

    if not api_key:
        return _heuristic()

    # Build contextual CSV for the LLM
    rows_csv = "\n".join(
        [
            "disease,score,market_size_usd,competitors,phase2_india,phase3_india,patent_filings_last_5y,key_patents_expiring_in_years,trials_total_india"
        ]
        + [
            f"{r['disease']},{r['score']:.3f},{r.get('market_size_usd',0)},{r.get('competitor_count',0)},"
            f"{r.get('phase2_india',0)},{r.get('phase3_india',0)},{r.get('patent_filings_last_5y',0)},"
            f"{r.get('key_patents_expiring_in_years',0)},{r.get('trials_total_india',0)}"
            for r in ranked
        ]
    )

    # Citations
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

    # Use environment variable for model selection (recommended for flexibility)
    model_name = os.getenv("NVIDIA_CHAT_MODEL", "nvidia/nemotron-4-340b-reward")  # Strong reasoning model; alternatives below

    try:
        llm = ChatNVIDIA(
            model=model_name,
            temperature=0.2,
            max_tokens=4096,  # Adjust as needed; Nemotron models support large contexts
        )

        prompt = (
            "You are an expert pharma strategy analyst. Provide a structured and concise markdown answer.\n"
            "Sections:\n"
            "1. **Executive Summary**\n"
            "2. **Ranking Rationale**\n"
            "3. **Key Metrics Table**\n"
            "4. **Signals & Gaps**\n"
            "5. **Next Recommended Actions**\n"
            "6. **Citations**\n"
            "\nContext CSV:\n" + rows_csv + "\n"
            + ("\nNVIDIA Biomedical AI-Q Analysis:\n" + nvidia_analysis + "\n" if nvidia_analysis else "")
            + ("\nWeb Sources:\n" + "\n".join(web_citations) + "\n" if web_citations else "")
            + ("\nInternal References:\n" + "\n".join(internal_citations) + "\n" if internal_citations else "")
            + "\nKeep it < 500 words. Be precise.\n"
        )

        resp = llm.invoke(prompt)
        return getattr(resp, "content", str(resp))

    except Exception:
        return _heuristic()


# Rest of the file remains unchanged
def run_query(question: str) -> Dict[str, Any]:
    """Main execution pipeline, now NVIDIA-first."""

    # --- NVIDIA BIOMEDICAL AI-Q PREFACE ---
    nvidia_preface = None
    if nvidia_is_configured():
        try:
            nvidia_preface = nvidia_analyze(question)
        except Exception as e:
            nvidia_preface = {"analysis": f"NVIDIA error: {str(e)}"}

    # --- 1. Web search → candidate diseases ---
    search = tavily_search(
        "respiratory diseases high patient burden India competitive landscape"
    )
    candidates = extract_candidate_diseases(search)
    if not candidates:
        candidates = ["COPD", "Asthma", "ILD"]

    # --- 2. Optional NVIDIA ranking override ---
    nvidia_ranked = None
    if nvidia_is_configured():
        try:
            rnk = nvidia_rank(candidates, country="India")
            if isinstance(rnk, dict) and rnk.get("ranked"):
                order = [
                    row.get("disease")
                    for row in rnk.get("ranked", [])
                    if row.get("disease") in candidates
                ]

                # stable merge
                new_candidates = []
                for d in order:
                    if d not in new_candidates:
                        new_candidates.append(d)
                for d in candidates:
                    if d not in new_candidates:
                        new_candidates.append(d)

                candidates = new_candidates
                nvidia_ranked = rnk.get("ranked")

        except Exception as e:
            nvidia_ranked = [{"error": str(e)}]

    # --- 3. Competition / trials / patents ---
    rows: List[Dict[str, Any]] = []
    for d in candidates:
        iqvia = iqvia_get(d)
        exim = exim_get(d)
        patents = uspto_mock(d)
        trials = trials_stats_for_disease_in_india(d)

        rows.append(
            {
                "disease": d,
                "market_size_usd": iqvia.get("market_size_usd", 0),
                "competitor_count": iqvia.get("competitor_count", 0),
                "api_exports_tonnes": exim.get("api_exports_tonnes", 0.0),
                "api_imports_tonnes": exim.get("api_imports_tonnes", 0.0),
                "patent_filings_last_5y": patents.get("patent_filings_last_5y", 0),
                "key_patents_expiring_in_years": patents.get("key_patents_expiring_in_years", 0),
                "phase2_india": trials.get("phase2_india", 0),
                "phase3_india": trials.get("phase3_india", 0),
                "trials_total_india": trials.get("total_trials_india", 0),
            }
        )

    # --- 4. Score = burden (market) – competition (competitors + trials) ---
    ms = _normalize([r["market_size_usd"] for r in rows])
    comp = _normalize([r["competitor_count"] + r["phase2_india"] + r["phase3_india"] for r in rows])
    scores = [m - c for m, c in zip(ms, comp)]
    for r, s in zip(rows, scores):
        r["score"] = s

    rows_sorted = sorted(rows, key=lambda x: x["score"], reverse=True)

    # --- 5. RAG internal knowledge ---
    internal_refs: List[Dict[str, Any]] = []
    try:
        for d in rows_sorted[:3]:
            q = f"past research on {d['disease']}"
            res = rag_query(q).get("results", [])
            for hit in res[:2]:
                internal_refs.append(
                    {"disease": d["disease"], "snippet": hit["text"][:140], "source": hit["source"]}
                )
    except Exception:
        pass  # optional

    # --- 6. Full synthesis (now using ChatNVIDIA) ---
    summary = _structured_summary(
        question,
        rows_sorted,
        search,
        internal_refs,
        nvidia_preface,
    )

    # --- 7. PDF table preparation ---
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

    return {
        "question": question,
        "candidates": candidates,
        "ranked": rows_sorted,
        "summary": summary,
        "report_pdf": pdf_path,
        "nvidia_ranked": nvidia_ranked,
    }
