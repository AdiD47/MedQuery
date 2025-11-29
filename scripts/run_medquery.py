"""Unified launcher for MedQuery demo.

Usage (from project root):
    python scripts/run_medquery.py [--no-ingest] [--port 8000]

What it does:
 - Verifies required packages are installed.
 - Loads .env.
 - Starts FastAPI mock server (IQVIA/EXIM/USPTO) on chosen port.
 - Optionally runs RAG ingest if GOOGLE_API_KEY is set and there are internal files.
 - Launches Streamlit UI.

Press Ctrl+C in this terminal to terminate child processes.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import subprocess
import signal
import threading
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def ensure_env():
    from dotenv import load_dotenv  # type: ignore
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("[warn] .env not found. Create one to enable full features.")
    load_dotenv()


def check_dependencies():
    required_imports = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "crewai",
        "langchain_google_genai",
        "chromadb",
        "pydantic",
        "requests",
    ]
    missing = []
    for name in required_imports:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    if missing:
        print("[error] Missing packages:", ", ".join(missing))
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)


def start_mock_server(port: int) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "uvicorn", "app.server.main:app", "--port", str(port), "--reload"]
    print("[info] Starting mock server:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc


def wait_for_health(port: int, timeout: float = 30.0):
    url = f"http://127.0.0.1:{port}/health"
    print(f"[info] Waiting for mock server health at {url}")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.ok:
                print("[info] Mock server healthy.")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("[warn] Health check timeout; continuing anyway.")
    return False


def maybe_ingest(no_ingest: bool):
    if no_ingest:
        print("[info] Skipping ingest (flag --no-ingest).")
        return
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        print("[info] GOOGLE_API_KEY not set; skipping RAG ingest.")
        return
    internal_dir = ROOT / "data" / "internal"
    if not internal_dir.exists():
        print("[info] internal directory missing; skipping ingest.")
        return
    files = list(internal_dir.glob("*.txt")) + list(internal_dir.glob("*.md")) + list(internal_dir.glob("*.pdf"))
    if not files:
        print("[info] No internal files found; skipping ingest.")
        return
    cmd = [sys.executable, "app/rag/ingest.py"]
    print("[info] Running ingest:", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[warn] Ingest failed: {e}")


def launch_streamlit(port: int) -> subprocess.Popen:
    # Pass mock server port via env if user changed it
    env = os.environ.copy()
    env.setdefault("MOCK_SERVER_URL", f"http://127.0.0.1:{port}")
    cmd = ["streamlit", "run", "app/ui/ui_app.py"]
    print("[info] Launching Streamlit UI:", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env)
    return proc


def stream_output(prefix: str, proc: subprocess.Popen):
    if proc.stdout is None:
        return
    for line in proc.stdout:
        print(f"[{prefix}] {line.rstrip()}")


def main():
    parser = argparse.ArgumentParser(description="Run MedQuery demo with one command")
    parser.add_argument("--port", type=int, default=8000, help="Port for mock server")
    parser.add_argument("--no-ingest", action="store_true", help="Skip RAG ingest step")
    args = parser.parse_args()

    check_dependencies()
    ensure_env()

    server_proc = start_mock_server(args.port)
    t = threading.Thread(target=stream_output, args=("uvicorn", server_proc), daemon=True)
    t.start()

    wait_for_health(args.port)
    maybe_ingest(args.no_ingest)
    ui_proc = launch_streamlit(args.port)

    print("\n[info] All components launched.")
    print("[info] Streamlit should open in your browser (or check terminal).")
    print("[info] Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(2)
            if server_proc.poll() is not None:
                print("[error] Mock server exited; terminating UI.")
                break
    except KeyboardInterrupt:
        print("\n[info] Shutting down...")
    finally:
        for p in [ui_proc, server_proc]:
            if p and p.poll() is None:
                try:
                    if os.name == "nt":
                        p.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                    p.terminate()
                except Exception:
                    pass
        time.sleep(1)
        print("[info] Done.")


if __name__ == "__main__":
    main()
