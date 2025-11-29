# MedQuery – Multi-Agent Med Intelligence 

This project demonstrates a Master Agent orchestrating specialist agents to answer complex pharma strategy questions like:

“Which respiratory diseases show low competition but high patient burden in India?”

It uses CrewAI for orchestration, a real ClinicalTrials.gov API, a RAG agent over internal docs via ChromaDB, Tavily for live web search, and a FastAPI mock server for proprietary data (IQVIA/EXIM/USPTO).

## Stack
- CrewAI (agents, tasks, collaboration)
- LLM: Google Gemini 1.5 Pro via `langchain-google-genai`
- UI: Streamlit
- Mock APIs: FastAPI (IQVIA/EXIM/USPTO)
- Live Search: Tavily API
- RAG: ChromaDB + Google embeddings
- Reports: fpdf2

## Setup
1. Python 3.10+ recommended
2. Create and activate venv
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```
3. Install deps
```powershell
pip install -r requirements.txt
```
4. Configure env
- Copy `.env.example` to `.env` and fill `GOOGLE_API_KEY` and (optional) `TAVILY_API_KEY`.
 - Optional: configure NVIDIA Biomedical AI-Q by setting `NVIDIA_BIOAIQ_URL` and `NVIDIA_BIOAIQ_API_KEY` if your blueprint service is deployed.

## Run the mock server
```powershell
uvicorn app.server.main:app --reload --port 8000
```

## Ingest internal knowledge (RAG)
Put your PDFs or `.txt` files into `data/internal/`. For the demo we include `internal_notes.txt`.
```powershell
python app/rag/ingest.py
```

## Run the Streamlit UI
```powershell
streamlit run app/ui/app.py
```
Open the link shown in terminal. Enter a question (e.g., the respiratory example) and click Run.

## Notes
- ClinicalTrials.gov API is real and requires no key.
- Tavily is optional; without a key, the app falls back to a minimal generic search summary.
- The mock server returns deterministic data.
 - NVIDIA Biomedical AI-Q integration is optional; if configured, its analysis is prepended to the summary and candidate ordering can be influenced.

