"""PDF parsing, chunking, and lightweight retrieval suitable for serverless use."""
import os
from pypdf import PdfReader

MAX_MB = 10
_embedder = None


def extract_pdf_text(source) -> str:
    """Extract text from a PDF path or a binary file-like object."""
    if isinstance(source, (str, os.PathLike)) and os.path.getsize(source) > MAX_MB * 1024 * 1024:
        raise ValueError(f"PDF larger than {MAX_MB} MB.")
    text = "\n".join((p.extract_text() or "") for p in PdfReader(source).pages).strip()
    if not text:
        raise ValueError("No extractable text (scanned PDF?).")
    return text


def chunk(text: str, size: int = 400, overlap: int = 50):
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(len(words), 1), step)]


def retrieve(text: str, query: str, k: int = 5) -> str:
    """Return the top-k chunks most relevant to the query (all text if short)."""
    chunks = chunk(text)
    if len(chunks) <= k:
        return "\n\n".join(chunks)
    query_words = {word.casefold() for word in (query or "").split()}
    ranked = sorted(
        chunks,
        key=lambda item: sum(word.casefold() in query_words for word in item.split()),
        reverse=True,
    )
    return "\n\n".join(ranked[:k])
