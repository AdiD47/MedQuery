import os
import sys

# Add the project root to Python path so 'app' module can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from tavily import TavilyClient

from app.tools.iqvia_client import iqvia_get
from app.tools.uspto_client import uspto_mock
from app.tools.clinicaltrials_client import trials_stats_for_disease_in_india
from app.tools.rag import query as rag_query
from app.tools.report_pdf import generate_report
from app.tools.nvidia_bio_aiq import bioaiq_analyze, is_bioaiq_configured

# OpenFold3 integration (optional)
try:
    from app.tools.openfold3 import openfold3_predict
    OPENFOLD3_AVAILABLE = True
except ImportError:
    OPENFOLD3_AVAILABLE = False

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# NVIDIA LLM fallback
fallback_model = os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.1-70b-instruct")

if not os.getenv("NVIDIA_API_KEY"):
    print("Warning: NVIDIA_API_KEY not set — ChatNVIDIA may be limited.")
    llm = None  # Fallback gracefully
else:
    llm = ChatNVIDIA(
        model=fallback_model,
        temperature=0.2,
        max_completion_tokens=8192,
    )

# Lazy initialization of Tavily client to avoid connection errors at import time
tavily = None
def get_tavily_client():
    global tavily
    if tavily is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if api_key:
            tavily = TavilyClient(api_key=api_key)
    return tavily

def search_and_extract_candidates(question: str) -> List[str]:
    search_query = f"{question} India 2025 high burden low competition biosimilar patent cliff orphan rare"
    
    # Get Tavily client (may be None if not configured)
    client = get_tavily_client()
    
    # Fallback candidates if Tavily is not available or fails
    fallback_candidates = [
        "Idiopathic Pulmonary Fibrosis",
        "Chronic Obstructive Pulmonary Disease", 
        "Tuberculosis",
        "Non-Small Cell Lung Cancer",
        "Multiple Myeloma",
        "Asthma"
    ]
    
    if client is None:
        print("No Tavily API key configured — using fallback candidates")
        return fallback_candidates
    
    try:
        results = client.search(query=search_query, max_results=15, include_raw_content=True)
    except Exception as e:
        print(f"Tavily search failed ({e}) — using fallback candidates")
        return fallback_candidates

    if llm is None:
        print("No LLM available — using fallback candidates")
        return fallback_candidates

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a pharma strategy analyst in emerging markets."),
        ("human", """
Question: {question}
Web Results: {results}
Return ONLY a JSON list of 6–10 full disease names with high opportunity in India.
""")
    ])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "question": question,
            "results": json.dumps([{"title": r["title"], "content": r["content"][:500]} for r in results.get("results", [])], indent=2)
        })
        candidates = json.loads(response.content.strip())
        if not isinstance(candidates, list):
            raise ValueError
    except Exception as e:
        print(f"Candidate extraction failed ({e}) → using fallback")
        candidates = fallback_candidates
    return candidates

def fetch_structured_data(candidates: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for disease in candidates:
        rows.append({
            "disease": disease,
            "market_size_usd": iqvia_get(disease).get("market_size_usd", 0),
            "competitor_count": iqvia_get(disease).get("competitor_count", 0),
            "phase2_india": trials_stats_for_disease_in_india(disease).get("phase2_india", 0),
            "phase3_india": trials_stats_for_disease_in_india(disease).get("phase3_india", 0),
            "patent_filings_last_5y": uspto_mock(disease).get("patent_filings_last_5y", 0),
            "structural_insight": ""
        })
    return rows

def generate_bioaiq_deep_analysis(top_candidates: List[str]) -> str:
    if not is_bioaiq_configured():
        return "NVIDIA Biomedical AI-Q not configured — deep analysis skipped."

    query = f"""
Perform a comprehensive strategic analysis of these therapeutic opportunities in India:

{', '.join(top_candidates[:5])}

For each:
• Epidemiology and patient burden in India
• Key biological pathways and druggable targets
• Current standard of care and limitations
• Global and India clinical pipeline
• Major competitors and market share
• Patent landscape and LOE timelines
• Biosimilar or complex generic entry potential
• Reimbursement and market access
• Overall commercial attractiveness

Rank them and recommend top priorities.
"""

    print("Calling NVIDIA Biomedical AI-Q for deep insights...")
    return bioaiq_analyze(query)

def add_structural_insight(ranked: List[Dict]) -> str:
    if not OPENFOLD3_AVAILABLE or not ranked:
        return "Structural analysis not available."

    top_disease = ranked[0]["disease"]
    target_map = {
        "Idiopathic Pulmonary Fibrosis": {"protein": "TGF-β1", "sequence": "MPPSGLRLLPLLLPLLWLLVLTPGRPAAGLSTCKTIDMELVKRKRIEAIRGQILSKLRLASPPSQGEVPPGPLPEAVLALYNSTRDRVAGESAEPEPEPEADYYAKEVTRVLMVETHNEIYDKFKQSTHSIYMFFNTSELREAVPEPVLLSRAELRLLRLKLKVEQHVELYQKYSNNSWRYLSNRLLAPSDSPEWLSFDVTGVVRQWLSRGGEIEGFRLSAHCSCDSRDNTLQVDINGFTTGRRGDLATIHGMNRPFLLLMATPLERAQHLQSSRHRRALDTNYCFSSTEKNCCVRQLYIDFRKDLGWKWIHEPKGYHANFCLGPCPYIWSLDTQYSKVLALYNQHNPGASAAPCCVPQALEPLPIVYYVGRKPKVEQLSNMIVRSCKCS"},
        "Non-Small Cell Lung Cancer": {"protein": "EGFR", "sequence": "MRPSGTAGAALLALLAALCPASRALEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEVVLGNLEITYVQRNYDLSFLKTIQEVAGYVLIALNTVERIPLENLQIIRGNMYYENSYALAVLSNYDANKTGLKELPMRNLQEILHGAVRFSNNPALCNVESIQWRDIVSSDFLSNMSMDFQNHLGSCQKCDPSCPNGSCWGAGEENCQKLTKIICAQQCSGRCRGKSPSDCCHNQCAAGCTGPRESDCLVCRKFRDEATCKDTCPPLMLYNPTTYQMDVNPEGKYSFGATCVKKCPRNYVVTDHGSCVRACGADSYEMEEDGVRKCKKCEGPCRKVCNGIGIGEFKDSLSINATNIKHFKNCTSISGDLHILPVAFRGDSFTHTPPLDPQELDILKTVKEITGFLLIQAWPENRTDLHAFENLEIIRGRTKQHGQFSLAVVSLNITSLGLRSLKEISDGDVIISGNKNLCYANTINWKKLFGTSGQKTKIISNRGENSCKATGQVCHALCSPEGCWGPEPRDCVSCRNVSRGRECVDKCNLLEGEPREFVENSECIQCHPECLPQAMNITCTGRGPDNCIQCAHYIDGPHCVKTCPAGVMGENNTLVWKYADAGHVCHLCHPNCTYGCTGPGLEGCPTNGPKIPSIATGMVGALLLLLVVALGIGLFMRRRHIVRKRTLRRLLQERELVEPLTPSGEAPNQALLRILKETEFKKIKVLGSGAFGTVYKGLWIPEGEKVKIPVAIKELREATSPKANKEILDEAYVMASVDNPHVCRLLGICLTSTVQLITQLMPFGCLLDYVREHKDNIGSQYLLNWCVQIAKGMNYLEDRRLVHRDLAARNVLVKTPQHVKITDFGLAKLLGAEEKEYHAEGGKVPIKWMALESILHRIYTHQSDVWSYGVTVWELMTFGSKPYDGIPASEISSILEKGERLPQPPICTIDVYMIMVKCWMIDADSRPKFRELIIEFSKMARDPQRYLVIQGDERMHLPSPTDSNFYRALMDEEDMDDVVDADEYLIPQQGFFSSPSTSRTPLLSSLSATSNNSTVACIDRNGLQSCPIKEDSFLQRYSSDPTGALTEDSIDDTFLPVPEYINQSVPKRPAGSVQNPVYHNQPLNPAPSRDPHYQDPHSTAVGNPEYLNTVQPTCVNSTFDSPAHWAQKGSHQISLDNPDYQQDFFPKEAKPNGIFKGSTAENAEYLRVAPQSSEFIGA"},
    }

    target = target_map.get(top_disease)
    if not target:
        return f"No OpenFold3 target mapped for {top_disease}."

    print(f"Running OpenFold3 for {target['protein']} in {top_disease}...")
    try:
        result = openfold3_predict([{"type": "protein", "sequence": target["sequence"]}])
        avg_plddt = result.get("plddt_avg", 0)
        insight = f"OpenFold3: {target['protein']} structure predicted with avg pLDDT {avg_plddt:.1f}/100."
        ranked[0]["structural_insight"] = insight
        return insight
    except Exception as e:
        return f"OpenFold3 failed: {str(e)}"

def run_medquery(question: str = "Best high-burden, low-competition therapeutic opportunities in India for 2025"):
    print(f"\n{'='*80}")
    print(f"   MEDQUERY — NVIDIA BIO-POWERED PHARMA INTELLIGENCE")
    print(f"{'='*80}")
    print(f"Question: {question}\n")

    candidates = search_and_extract_candidates(question)
    print("Candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"  {i}. {c}")
    print()

    data_rows = fetch_structured_data(candidates)

    for row in data_rows:
        burden = row["market_size_usd"] / 1e9 if row["market_size_usd"] else 0
        competition = row["competitor_count"] + row["phase2_india"] + row["phase3_india"] + (row["patent_filings_last_5y"] / 8)
        row["score"] = max(0.0, burden - competition / 10)

    ranked = sorted(data_rows, key=lambda x: x["score"], reverse=True)

    structural_insight = add_structural_insight(ranked) if OPENFOLD3_AVAILABLE else "Structural analysis skipped."

    bioaiq_insight = generate_bioaiq_deep_analysis([r["disease"] for r in ranked])

    internal_refs = []
    for row in ranked[:4]:
        hits = rag_query(f"internal research {row['disease']} India biosimilar").get("results", [])[:2]
        for hit in hits:
            internal_refs.append({
                "disease": row["disease"],
                "snippet": hit["text"][:350],
                "source": hit.get("source", "Internal")
            })

    # Prepare tables for PDF
    iqvia_table = [
        {
            "disease": row["disease"],
            "market_size_usd": row["market_size_usd"],
            "competitor_count": row["competitor_count"],
        }
        for row in ranked
    ]

    patent_table = [
        {
            "disease": row["disease"],
            "patent_filings_last_5y": row["patent_filings_last_5y"],
        }
        for row in ranked
    ]

    trials_table = [
        {
            "disease": row["disease"],
            "phase2_india": row["phase2_india"],
            "phase3_india": row["phase3_india"],
        }
        for row in ranked
    ]

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Partner-level pharma strategy consultant."),
        ("human", """
Question: {question}

NVIDIA Biomedical AI-Q Analysis:
{bioaiq}

OpenFold3 Structural Insight:
{structure}

Ranked Opportunities:
{ranked}

Internal Intelligence:
{internal}

Generate a concise executive report in markdown.
""")
    ])

    # Generate summary using LLM or fallback to a simple template
    if llm is not None:
        chain = final_prompt | llm
        summary = chain.invoke({
            "question": question,
            "bioaiq": bioaiq_insight or "Not available",
            "structure": structural_insight,
            "ranked": json.dumps(ranked[:6], indent=2),
            "internal": json.dumps(internal_refs, indent=2),
        }).content
    else:
        # Fallback summary when LLM is not available
        print("No LLM available — generating basic summary")
        summary = f"""# MedQuery Analysis Report

## Query
{question}

## Top Ranked Opportunities
{json.dumps(ranked[:6], indent=2)}

## BioAIQ Insights
{bioaiq_insight or "Not available"}

## Structural Analysis
{structural_insight}

## Internal References
{json.dumps(internal_refs, indent=2) if internal_refs else "None available"}

*Note: This is a basic report generated without LLM summarization. Configure NVIDIA_API_KEY for enhanced analysis.*
"""

    pdf_path = generate_report(
        title="MedQuery — India Therapeutic Opportunity Report (2025)",
        question=question,
        summary=summary,
        disease_rankings=ranked,
        iqvia_table=iqvia_table,
        patent_table=patent_table,
        trials_table=trials_table,
        internal_refs=internal_refs or None,
    )

    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    print(summary)
    print(f"\nPDF saved: {pdf_path}")
    print("="*80)

    # Return dict for API
    return {
        "question": question,
        "summary": summary,
        "ranked": ranked,
        "internal_refs": internal_refs,
        "report_pdf": pdf_path
    }


if __name__ == "__main__":
    user_question = input("\nEnter your pharma strategy question: ").strip() or \
                    "Best high-burden, low-competition therapeutic opportunities in India for 2025"
    run_medquery(user_question)
