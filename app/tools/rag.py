import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join("app", "rag", "chroma_db"))


def _pdf_to_text(path: str) -> str:
    if fitz is None:
        return ""
    text = []
    with fitz.open(path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)


def ingest(paths: List[str]) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set for embeddings")

    texts = []
    for p in paths:
        if p.lower().endswith(".pdf"):
            content = _pdf_to_text(p)
            if content:
                texts.append((p, content))
        elif p.lower().endswith((".txt", ".md")):
            loader = TextLoader(p, encoding="utf-8")
            docs = loader.load()
            for d in docs:
                texts.append((p, d.page_content))

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = []
    for src, content in texts:
        for chunk in splitter.split_text(content):
            docs.append({"page_content": chunk, "metadata": {"source": src}})

    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    vs = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)
    # Clear existing and re-add
    try:
        vs.delete_collection()
    except Exception:
        pass
    vs = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)
    vs.add_texts([d["page_content"] for d in docs], metadatas=[d["metadata"] for d in docs])
    vs.persist()
    return {"chunks_indexed": len(docs), "chroma_dir": CHROMA_DIR}


def query(question: str, k: int = 5) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set for embeddings")
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    vs = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)
    sims = vs.similarity_search(question, k=k)
    out = []
    for d in sims:
        out.append({"text": d.page_content, "source": d.metadata.get("source")})
    return {"query": question, "results": out}
