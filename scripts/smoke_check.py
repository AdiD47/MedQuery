import os
from app.server.main import app
from app.crew import run_query

if __name__ == "__main__":
    # Minimal smoke to ensure orchestration returns without NVIDIA/Gemini keys
    os.environ.setdefault("MOCK_SERVER_URL", "http://127.0.0.1:8000")
    print("Run a small query…")
    res = run_query("Which respiratory diseases show low competition but high patient burden in India?")
    print("Candidates:", res.get("candidates"))
    print("Summary (first 140 chars):", res.get("summary", "")[:140])
