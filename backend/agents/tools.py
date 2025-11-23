"""
Custom tools for AI agents
"""
import os
import requests
from typing import Optional
import json
from langchain.tools import tool

# Import mock data
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mock_apis import get_iqvia_data, get_exim_data, get_patent_data


@tool("Search Clinical Trials")
def search_clinical_trials(disease: str) -> str:
    """
    Search ClinicalTrials.gov for trials related to a disease.
    Useful for finding ongoing Phase 2 and Phase 3 clinical trials in India.
    Input should be a disease name like 'COPD', 'Asthma', 'ILD', etc.
    Returns JSON data about clinical trials.
    """
    phase = None
    try:
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        
        # Build query
        query_parts = [disease]
        if phase:
            query_parts.append(phase)
        
        params = {
            "query.term": " ".join(query_parts),
            "filter.geo": "distance(India,500mi)",
            "pageSize": 20,
            "format": "json"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        studies = data.get("studies", [])
        
        # Extract relevant information
        trial_info = []
        for study in studies[:10]:  # Limit to 10 results
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            
            trial_info.append({
                "nct_id": identification.get("nctId", "N/A"),
                "title": identification.get("briefTitle", "N/A"),
                "status": status.get("overallStatus", "N/A"),
                "phase": design.get("phases", ["N/A"]),
                "enrollment": status.get("enrollmentInfo", {}).get("count", 0)
            })
        
        result = {
            "disease": disease,
            "total_trials": len(studies),
            "displayed_trials": len(trial_info),
            "trials": trial_info
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "disease": disease,
            "trials": []
        })


@tool("Get IQVIA Market Data")
def get_iqvia_market_data(disease: str) -> str:
    """
    Get pharmaceutical market data including market size, growth rate, and competitor information.
    Useful for understanding market dynamics and competitive intensity.
    Input should be a disease name like 'COPD', 'Asthma', 'ILD', etc.
    Returns JSON with market metrics.
    """
    data = get_iqvia_data(disease)
    return json.dumps(data, indent=2)


@tool("Get Export-Import Trade Data")
def get_exim_trade_data(disease: str) -> str:
    """
    Get pharmaceutical export-import trade data for India.
    Useful for understanding supply chain dynamics and market dependencies.
    Input should be a disease name like 'COPD', 'Asthma', 'ILD', etc.
    Returns JSON with trade metrics.
    """
    data = get_exim_data(disease)
    return json.dumps(data, indent=2)


@tool("Get Patent Landscape")
def get_patent_landscape(disease: str) -> str:
    """
    Get patent landscape analysis including active patents, expiring patents, and generic opportunities.
    Useful for identifying IP barriers and freedom-to-operate opportunities.
    Input should be a disease name like 'COPD', 'Asthma', 'ILD', etc.
    Returns JSON with patent information.
    """
    data = get_patent_data(disease)
    return json.dumps(data, indent=2)


@tool("Search Medical Literature")
def search_web_tavily(query: str) -> str:
    """
    Search medical literature, WHO reports, and health publications using Tavily AI.
    Useful for finding disease burden data, epidemiological information, and patient statistics.
    Input should be a search query like 'respiratory diseases high patient burden India'.
    Returns JSON with search results from authoritative sources.
    """
    try:
        from tavily import TavilyClient
        
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return json.dumps({
                "error": "Tavily API key not found",
                "results": []
            })
        
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["who.int", "nih.gov", "thelancet.com", "bmj.com"]
        )
        
        # Extract relevant info
        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:500]  # First 500 chars
            })
        
        return json.dumps({
            "query": query,
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "query": query,
            "results": []
        })


@tool("Search Internal Knowledge Base")
def search_internal_knowledge(query: str) -> str:
    """
    Search internal company documents, research reports, and strategic memos.
    Useful for finding past research, ongoing initiatives, and strategic alignment.
    Input should be a search query mentioning a disease or therapeutic area.
    Returns relevant information from internal documents.
    """
    try:
        # This will be implemented with ChromaDB RAG
        # For now, return mock response
        mock_responses = {
            "COPD": "Internal research shows COPD is a strategic priority area with ongoing R&D initiatives in novel bronchodilators.",
            "ILD": "Recent internal memo highlighted ILD as an underserved market with high unmet need. Limited competition noted.",
            "Asthma": "Asthma program is well-established. Focus is on next-gen inhalers and biologics for severe asthma.",
            "Tuberculosis": "TB program aligned with government partnerships. Focus on drug-resistant TB formulations.",
            "Pneumonia": "Pneumonia vaccines under development. Market analysis shows strong demand in pediatric segment."
        }
        
        # Simple keyword matching for demo
        for disease, response in mock_responses.items():
            if disease.lower() in query.lower():
                return json.dumps({
                    "query": query,
                    "found": True,
                    "content": response,
                    "source": "Internal Knowledge Base"
                }, indent=2)
        
        return json.dumps({
            "query": query,
            "found": False,
            "content": "No relevant internal documents found.",
            "source": "Internal Knowledge Base"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "query": query,
            "found": False
        })
