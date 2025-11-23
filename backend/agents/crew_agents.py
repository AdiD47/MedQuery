"""
CrewAI Agent Definitions for Master-Worker Architecture
"""
import os
import sys
import json
from typing import Any, Dict

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# Make backend root importable to reach mock_apis.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mock_apis import get_iqvia_data, get_exim_data, get_patent_data

# Initialize Gemini LLM
def get_llm():
    """Get configured Gemini LLM - return model name for CrewAI via LiteLLM"""
    return "gemini/gemini-1.5-pro"

# Define Tools using CrewAI's tool decorator
@tool("Search Clinical Trials")
def search_clinical_trials_tool(disease: str) -> str:
    """Return placeholder clinical trials data for a disease."""
    return json.dumps({
        "source": "clinicaltrials.gov",
        "disease": disease,
        "trials": [],
        "note": "Stubbed clinical trials search. Integrate real API as needed."
    })

@tool("Get Market Data")
def iqvia_market_tool(disease: str) -> str:
    """Return mock IQVIA market data."""
    return json.dumps(get_iqvia_data(disease))

@tool("Get Trade Data")
def exim_trade_tool(disease: str) -> str:
    """Return mock EXIM trade data."""
    return json.dumps(get_exim_data(disease))

@tool("Get Patent Data")
def patent_landscape_tool(disease: str) -> str:
    """Return mock patent landscape data."""
    return json.dumps(get_patent_data(disease))

@tool("Search Web")
def web_search_tool(query: str) -> str:
    """Return placeholder web search results."""
    return json.dumps({
        "source": "web",
        "query": query,
        "results": [],
        "note": "Web search not connected. Plug in Tavily/Bing/SerpAPI."
    })

@tool("Search Internal Docs")
def internal_knowledge_tool(query: str) -> str:
    """Return placeholder internal knowledge search."""
    return json.dumps({
        "source": "internal_docs",
        "query": query,
        "hits": [],
        "note": "No internal index configured."
    })

def create_master_agent():
    """Create the Master Orchestrator Agent"""
    return Agent(
        role="Master Research Orchestrator",
        goal="Analyze complex pharmaceutical research queries and orchestrate a team of specialized agents to gather comprehensive insights",
        backstory=("You are a senior pharmaceutical strategist with deep expertise in market analysis, "
                   "clinical research, and competitive intelligence. You excel at breaking down complex questions "
                   "into actionable research tasks and synthesizing findings from multiple sources into strategic insights."),
        verbose=True,
        allow_delegation=True,
        llm=get_llm()
    )

def create_clinical_trials_agent():
    """Create Clinical Trials Research Agent"""
    return Agent(
        role="Clinical Trials Intelligence Specialist",
        goal="Search and analyze clinical trial data from ClinicalTrials.gov to identify R&D activity and competition",
        backstory=("You are an expert in clinical research with access to live clinical trial databases. "
                   "You analyze trial phases, enrollment status, and geographic distribution to assess competitive landscape."),
        verbose=True,
        allow_delegation=False,
        tools=[search_clinical_trials_tool],
        llm=get_llm()
    )

def create_market_intelligence_agent():
    """Create IQVIA Market Intelligence Agent"""
    return Agent(
        role="Market Intelligence Analyst",
        goal="Retrieve and analyze pharmaceutical market data including market size, growth rates, and competitor positioning",
        backstory=("You are a pharmaceutical market analyst with access to IQVIA market data. "
                   "You provide insights on market dynamics, key players, and competitive intensity."),
        verbose=True,
        allow_delegation=False,
        tools=[iqvia_market_tool],
        llm=get_llm()
    )

def create_trade_intelligence_agent():
    """Create EXIM Trade Intelligence Agent"""
    return Agent(
        role="Trade Intelligence Analyst",
        goal="Analyze pharmaceutical import-export data to understand supply chain dynamics and market dependencies",
        backstory=("You are a trade analyst specializing in pharmaceutical supply chains. "
                   "You analyze import/export trends to identify market gaps and opportunities."),
        verbose=True,
        allow_delegation=False,
        tools=[exim_trade_tool],
        llm=get_llm()
    )

def create_patent_intelligence_agent():
    """Create Patent Landscape Agent"""
    return Agent(
        role="Patent Intelligence Specialist",
        goal="Analyze patent landscapes to identify IP barriers, expiring patents, and generic opportunities",
        backstory=("You are a patent analyst with expertise in pharmaceutical intellectual property. "
                   "You identify patent cliffs, active filings, and freedom-to-operate opportunities."),
        verbose=True,
        allow_delegation=False,
        tools=[patent_landscape_tool],
        llm=get_llm()
    )

def create_web_intelligence_agent():
    """Create Web Intelligence Agent"""
    return Agent(
        role="Web Intelligence Analyst",
        goal="Search the web for the latest news, publications, and competitive signals",
        backstory="You track recent developments and external signals relevant to the research query.",
        verbose=True,
        allow_delegation=False,
        tools=[web_search_tool],
        llm=get_llm()
    )

def create_internal_knowledge_agent():
    """Create Internal Knowledge Agent"""
    return Agent(
        role="Internal Knowledge Analyst",
        goal="Search internal reports and documents for prior research and insights",
        backstory="You surface relevant internal knowledge to avoid reinventing the wheel.",
        verbose=True,
        allow_delegation=False,
        tools=[internal_knowledge_tool],
        llm=get_llm()
    )

def create_synthesis_agent():
    """Create Synthesis Agent"""
    return Agent(
        role="Synthesis & Strategy Analyst",
        goal="Synthesize all findings into an executive summary with actionable recommendations",
        backstory="You combine multi-source insights into a concise, decision-ready output.",
        verbose=True,
        allow_delegation=False,
        llm=get_llm()
    )

def create_research_crew(query: str):
    """
    Build a Crew with master + specialists and define a simple sequential workflow.
    Returns a Crew instance that supports .kickoff() / .kickoff_async().
    """
    master = create_master_agent()
    clinical = create_clinical_trials_agent()
    market = create_market_intelligence_agent()
    trade = create_trade_intelligence_agent()
    patent = create_patent_intelligence_agent()
    web = create_web_intelligence_agent()
    internal = create_internal_knowledge_agent()
    synth = create_synthesis_agent()

    scope_task = Task(
        description=f"Understand and refine the research question: '{query}'. "
                    f"Break it down into sub-questions and outline a plan.",
        expected_output="A clear research plan with sub-questions and data needs.",
        agent=master
    )

    clinical_task = Task(
        description="Investigate clinical trial activity relevant to the disease. Use the clinical trials tool.",
        expected_output="Summary of trial phases, geographies, and key sponsors.",
        agent=clinical
    )

    market_task = Task(
        description="Analyze market size, growth, and competitors. Use the IQVIA market tool.",
        expected_output="Market overview with key players and growth rates.",
        agent=market
    )

    trade_task = Task(
        description="Analyze import/export trends for related products. Use the EXIM trade tool.",
        expected_output="Trade flows and supply chain dependencies.",
        agent=trade
    )

    patent_task = Task(
        description="Assess the patent landscape and patent cliffs. Use the patent tool.",
        expected_output="Key patents, expiry timelines, and FTO considerations.",
        agent=patent
    )

    web_task = Task(
        description="Search the web for recent developments and news.",
        expected_output="Bullet list of notable recent events with sources.",
        agent=web
    )

    internal_task = Task(
        description="Search internal knowledge for prior work related to the query.",
        expected_output="Relevant internal docs and summarized insights.",
        agent=internal
    )

    synth_task = Task(
        description="Synthesize all findings into an executive summary with recommendations.",
        expected_output="Executive summary, key findings, and next steps.",
        agent=synth
    )

    crew = Crew(
        agents=[master, clinical, market, trade, patent, web, internal, synth],
        tasks=[scope_task, clinical_task, market_task, trade_task, patent_task, web_task, internal_task, synth_task],
        process=Process.sequential,
        verbose=True
    )
    return crew
