import json
from typing import Any, Dict
from dotenv import load_dotenv

from langchain.tools import Tool
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools.web_search import tavily_search, extract_candidate_diseases
from app.tools.iqvia_client import iqvia_get, exim_get
from app.tools.uspto_client import uspto_mock
from app.tools.clinicaltrials_client import trials_stats_for_disease_in_india
from app.tools.rag import query as rag_query
from app.tools.report_pdf import generate_report

from app.crew import run_query as deterministic_run

load_dotenv()

# Wrap multi-arg tools to single-string JSON inputs to satisfy Tool interface

def _web_search(q: str) -> str:
    res = tavily_search(q)
    res["candidates"] = extract_candidate_diseases(res)
    return json.dumps(res)


def _iqvia(json_in: str) -> str:
    data = json.loads(json_in)
    d = data.get("disease", "")
    return json.dumps(iqvia_get(d))


def _exim(json_in: str) -> str:
    data = json.loads(json_in)
    d = data.get("disease", "")
    return json.dumps(exim_get(d))


def _uspto(json_in: str) -> str:
    data = json.loads(json_in)
    d = data.get("disease", "")
    return json.dumps(uspto_mock(d))


def _trials(json_in: str) -> str:
    data = json.loads(json_in)
    d = data.get("disease", "")
    return json.dumps(trials_stats_for_disease_in_india(d))


def _rag(json_in: str) -> str:
    data = json.loads(json_in)
    q = data.get("query", "")
    return json.dumps(rag_query(q))


def _report(json_in: str) -> str:
    data = json.loads(json_in)
    path = generate_report(**data)
    return json.dumps({"report_path": path})


def build_crew() -> Crew:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2)

    tools = [
        Tool(name="web_search", func=_web_search, description="Search the web and extract candidate diseases"),
        Tool(name="iqvia", func=_iqvia, description='Get market size & competitor count. Input JSON: {"disease":"..."}'),
        Tool(name="exim", func=_exim, description='Get API exports/imports. Input JSON: {"disease":"..."}'),
        Tool(name="uspto", func=_uspto, description='Get patent landscape. Input JSON: {"disease":"..."}'),
        Tool(name="trials", func=_trials, description='Get Phase 2/3 trial counts in India. Input JSON: {"disease":"..."}'),
        Tool(name="rag_query", func=_rag, description='Query internal knowledge. Input JSON: {"query":"..."}'),
        Tool(name="report", func=_report, description='Generate PDF report. Provide fields as JSON to report generator'),
    ]

    master = Agent(
        role="Master Orchestrator",
        goal=(
            "Decompose complex pharma questions into steps and coordinate tools to "
            "identify diseases with low competition and high patient burden in India."
        ),
        backstory=(
            "You are a strategic analyst. You search the web, gather market, patent, trials, "
            "and internal insights, and synthesize actionable recommendations."
        ),
        verbose=True,
        allow_delegation=False,
        tools=tools,
        llm=llm,
    )

    task = Task(
        description=(
            "Given a user question, do the following: 1) use web_search to list candidate respiratory diseases; "
            "2) for each disease, call iqvia, exim, uspto, trials; 3) query rag_query for past research; "
            "4) rank diseases prioritizing low competition (fewer competitors and fewer phase 2/3 trials) and high burden (proxy: market size); "
            "5) write a concise summary; 6) call report to generate a PDF with tables and the summary."
        ),
        agent=master,
        expected_output=(
            "A JSON object with keys: candidates, ranked (array with metrics and score), summary, report_pdf"
        ),
    )

    return Crew(agents=[master], tasks=[task])


def run_with_crew(question: str) -> Dict[str, Any]:
    try:
        crew = build_crew()
        out = crew.kickoff(inputs={"question": question})
        # The LLM may output plain text; if it's JSON we parse; otherwise fall back
        try:
            return json.loads(str(out))
        except Exception:
            return {"raw": str(out)}
    except Exception:
        # Fallback to deterministic pipeline
        return deterministic_run(question)
