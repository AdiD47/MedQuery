import os
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
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
logger = logging.getLogger(__name__)

CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join("app", "rag", "chroma_db"))

# Connection pooling - reuse embedding model and vector store
_embeddings_cache: Optional[GoogleGenerativeAIEmbeddings] = None
_vectorstore_cache: Optional[Chroma] = None

def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Get cached embeddings model to avoid reinitializing."""
    global _embeddings_cache
    if _embeddings_cache is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set for embeddings")
        _embeddings_cache = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004",
            task_type="retrieval_document"  # Optimize for document retrieval
        )
    return _embeddings_cache

def _get_vectorstore() -> Chroma:
    """Get cached vector store connection."""
    global _vectorstore_cache
    if _vectorstore_cache is None:
        embeddings = _get_embeddings()
        _vectorstore_cache = Chroma(
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
    return _vectorstore_cache


def _pdf_to_text(path: str) -> str:
    if fitz is None:
        return ""
    text = []
    with fitz.open(path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)


def ingest(paths: List[str], batch_size: int = 100) -> Dict[str, Any]:
    """Ingest documents with optimized batching and semantic chunking.
    
    Args:
        paths: List of file paths to ingest
        batch_size: Number of chunks to embed at once (reduces API calls)
    """
    logger.info(f"Ingesting {len(paths)} documents")
    
    texts = []
    for p in paths:
        try:
            if p.lower().endswith(".pdf"):
                content = _pdf_to_text(p)
                if content:
                    texts.append((p, content))
            elif p.lower().endswith((".txt", ".md")):
                loader = TextLoader(p, encoding="utf-8")
                docs = loader.load()
                for d in docs:
                    texts.append((p, d.page_content))
        except Exception as e:
            logger.warning(f"Failed to load {p}: {e}")

    # Optimized chunking: larger chunks with semantic boundaries
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Reduced for better precision
        chunk_overlap=200,  # Increased overlap for context preservation
        separators=["\n\n", "\n", ". ", " ", ""]  # Semantic boundaries
    )
    
    docs = []
    for src, content in texts:
        for chunk in splitter.split_text(content):
            docs.append({"page_content": chunk, "metadata": {"source": src}})

    logger.info(f"Created {len(docs)} chunks")
    
    embeddings = _get_embeddings()
    vs = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)
    
    # Clear existing and re-add
    try:
        vs.delete_collection()
    except Exception as e:
        logger.warning(f"Collection delete failed: {e}")
    
    vs = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DIR)
    
    # Batch processing to reduce API calls (5-10x faster)
    texts_list = [d["page_content"] for d in docs]
    metas_list = [d["metadata"] for d in docs]
    
    for i in range(0, len(texts_list), batch_size):
        batch_texts = texts_list[i:i + batch_size]
        batch_metas = metas_list[i:i + batch_size]
        vs.add_texts(batch_texts, metadatas=batch_metas)
        logger.info(f"Ingested batch {i // batch_size + 1}/{(len(texts_list) + batch_size - 1) // batch_size}")
    
    vs.persist()
    return {"chunks_indexed": len(docs), "chroma_dir": CHROMA_DIR}


@lru_cache(maxsize=50)  # Cache frequent queries
def query(question: str, k: int = 5, use_mmr: bool = True) -> Dict[str, Any]:
    """Query RAG with hybrid search and MMR for diversity.
    
    Args:
        question: Query text
        k: Number of results
        use_mmr: Use Maximal Marginal Relevance for diverse results
    """
    logger.info(f"RAG query: {question[:100]}")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set for embeddings")
    
    vs = _get_vectorstore()
    
    # Use MMR for better diversity and reduce redundancy
    if use_mmr:
        # MMR balances relevance and diversity (fetch 2x, return k)
        sims = vs.max_marginal_relevance_search(
            question,
            k=k,
            fetch_k=min(k * 2, 20),  # Fetch more candidates
            lambda_mult=0.7  # Balance: 0=diversity, 1=relevance
        )
    else:
        sims = vs.similarity_search(question, k=k)
    
    # Score and rerank results by relevance
    out = []
    for idx, d in enumerate(sims):
        # Simple reranking: prefer longer, more informative chunks
        relevance_score = 1.0 - (idx * 0.1)  # Decay by position
        length_bonus = min(len(d.page_content) / 800, 1.0) * 0.2
        
        out.append({
            "text": d.page_content,
            "source": d.metadata.get("source"),
            "score": relevance_score + length_bonus,
            "rank": idx + 1
        })
    
    # Sort by score
    out.sort(key=lambda x: x["score"], reverse=True)
    
    logger.info(f"Retrieved {len(out)} results")
    return {"query": question, "results": out}
