import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is first on sys.path so that the package
# `app` (folder) is found before any sibling `app.py` files.
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.crew import run_query

load_dotenv()

st.set_page_config(page_title="MedQuery – Multi-Agent Demo", layout="wide")
st.title("MedQuery – Multi-Agent Med Intelligence")

st.markdown("This demo finds respiratory diseases with low competition but high burden in India.")

question = st.text_input(
    "Your question",
    value="Which respiratory diseases show low competition but high patient burden in India?",
)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Run Analysis", use_container_width=True):
        with st.spinner("Running multi-agent analysis..."):
            try:
                result = run_query(question)
                st.success("Completed")

                ranked = result.get("ranked", [])
                if ranked:
                    import pandas as pd
                    st.subheader("Disease Ranking")
                    df = pd.DataFrame([
                        {
                            "Disease": r["disease"],
                            "Score": round(r["score"], 3),
                            "Market USD": r["market_size_usd"],
                            "Competitors": r["competitor_count"],
                            "P2 India": r["phase2_india"],
                            "P3 India": r["phase3_india"],
                            "Trials India": r["trials_total_india"],
                        }
                        for r in ranked
                    ])
                    st.dataframe(df, use_container_width=True)

                st.subheader("Executive Summary")
                st.write(result.get("summary", ""))

                pdf_path = result.get("report_pdf")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF Report",
                            data=f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                        )
            except Exception as e:
                st.error(f"Error: {e}")

with col2:
    st.info("1) Start mock server: `uvicorn app.server.main:app --reload --port 8000`")
with col3:
    st.info("2) (Optional) Ingest RAG: `python app/rag/ingest.py`")
