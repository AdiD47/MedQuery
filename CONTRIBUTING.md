# Contributing

Thanks for considering contributing to MedQuery!

## Development setup
- Python 3.10+
- Create a virtualenv and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Copy `.env.example` to `.env` and fill values.

## Running
- Mock server:
```bash
uvicorn app.server.main:app --reload --port 8000
```
- RAG ingestion:
```bash
python app/rag/ingest.py
```
- UI:
```bash
streamlit run app/ui/app.py
```

## Pull requests
- Keep changes focused and small.
- Include minimal docs updates when needed.
- Ensure CI passes.

## Code style
- Prefer clear, small functions.
- Avoid inline comments unless clarifying non-obvious logic.
