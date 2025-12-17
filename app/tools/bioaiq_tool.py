import os
import requests
from typing import Dict, Any


def bioaiq_analyze(query: str) -> str:
    """
    Calls the NVIDIA Biomedical AI-Q Research Agent endpoint to perform deep biomedical analysis.
    
    Args:
        query (str): The biomedical or pharma strategy question to analyze.
                     Example: "What are the top emerging opportunities in idiopathic pulmonary fibrosis in India?"
    
    Returns:
        str: The AI-Q generated response (rich biomedical insight, mechanisms, burden, pipeline, etc.)
    """
    url = os.getenv("NVIDIA_BIOAIQ_URL")
    key = os.getenv("NVIDIA_BIOAIQ_API_KEY")

    if not url or not key:
        return (
            "NVIDIA Biomedical AI-Q is not configured.\n"
            "Please set these in your .env file:\n"
            "NVIDIA_BIOAIQ_URL=https://ai.api.nvidia.com/v1/gr/meta/bioaiq-research-agent\n"
            "NVIDIA_BIOAIQ_API_KEY=nvapi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        )

    payload = {
        "input": query,
        "options": {
            "max_output_tokens": 4096,  # Increased for richer reports
            "temperature": 0.3
        }
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()

        # Standard output key from NVIDIA BioAI-Q blueprint
        output = data.get("output_text") or data.get("text") or str(data)
        return output.strip()

    except requests.exceptions.HTTPError as http_err:
        return f"BioAI-Q HTTP Error: {http_err} - {response.text}"
    except requests.exceptions.ConnectionError:
        return "Connection failed to NVIDIA BioAI-Q endpoint. Check URL and network."
    except requests.exceptions.Timeout:
        return "BioAI-Q request timed out. Try again."
    except Exception as e:
        return f"BioAI-Q unexpected error: {str(e)}"


def is_bioaiq_configured() -> bool:
    """Helper to check if BioAI-Q is ready to use"""
    return bool(os.getenv("NVIDIA_BIOAIQ_URL") and os.getenv("NVIDIA_BIOAIQ_API_KEY"))