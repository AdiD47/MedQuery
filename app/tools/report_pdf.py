from fpdf import FPDF
from typing import Dict, Any, List, Optional
import os
import re

class SimplePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "MedQuery Report", 0, 1, "C")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def _clean_text(text: str) -> str:
    """Replace or remove Unicode characters that Arial/Latin-1 can't handle"""
    # Replace common problematic chars
    text = text.replace("—", "-")   # em dash → hyphen
    text = text.replace("–", "-")   # en dash → hyphen
    text = text.replace("“", '"')   # smart quotes
    text = text.replace("”", '"')
    text = text.replace("‘", "'")
    text = text.replace("’", "'")
    text = text.replace("…", "...") # ellipsis
    text = text.replace("•", "-")   # bullet → hyphen
    # Remove any remaining non-Latin-1 chars
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def _add_table(pdf: FPDF, title: str, rows: List[Dict[str, Any]], columns: List[str]):
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, _clean_text(title), 0, 1)
    pdf.set_font("Arial", size=9)
    col_w = max(30, int(pdf.w / max(1, len(columns)) - 10))
    # header
    for c in columns:
        pdf.cell(col_w, 7, _clean_text(str(c)), 1)
    pdf.ln()
    # rows
    for r in rows:
        for c in columns:
            val = _clean_text(str(r.get(c, ""))[:32])
            pdf.cell(col_w, 7, val, 1)
        pdf.ln()
    pdf.ln(4)

def generate_report(
    title: str,
    question: str,
    summary: str,
    disease_rankings: List[Dict[str, Any]],
    iqvia_table: List[Dict[str, Any]],
    patent_table: List[Dict[str, Any]],
    trials_table: List[Dict[str, Any]],
    internal_refs: Optional[List[Dict[str, Any]]] = None,
    out_dir: str = "reports",
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    pdf = SimplePDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, _clean_text(title))
    pdf.ln(2)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, _clean_text(f"Question: {question}"))
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, _clean_text("Executive Summary"), 0, 1)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, _clean_text(summary))
    pdf.ln(4)
    if disease_rankings:
        _add_table(pdf, "Disease Rankings", disease_rankings, list(disease_rankings[0].keys()))
    if iqvia_table:
        _add_table(pdf, "Market & Competition (IQVIA Mock)", iqvia_table, list(iqvia_table[0].keys()))
    if patent_table:
        _add_table(pdf, "Patent Landscape (USPTO Mock)", patent_table, list(patent_table[0].keys()))
    if trials_table:
        _add_table(pdf, "Clinical Trials in India (Real)", trials_table, list(trials_table[0].keys()))
    if internal_refs:
        _add_table(pdf, "Internal Knowledge References", internal_refs, list(internal_refs[0].keys()))
    path = os.path.join(out_dir, f"report-{abs(hash(question)) % 10**8}.pdf")
    pdf.output(path)
    return path
