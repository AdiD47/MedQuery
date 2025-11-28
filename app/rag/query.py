from app.tools.rag import query

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "past research on ILD"
    print(query(q))
