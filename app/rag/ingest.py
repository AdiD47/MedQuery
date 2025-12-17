import os
from glob import glob
# from app.tools.rag 
import ingest
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    paths = []
    paths += glob(os.path.join("data", "internal", "*.pdf"))
    paths += glob(os.path.join("data", "internal", "*.txt"))
    paths += glob(os.path.join("data", "internal", "*.md"))
    if not paths:
        print("No files found in data/internal; creating embeddings anyway (empty index)")
    res = ingest(paths)
    print("Ingested:", res)
