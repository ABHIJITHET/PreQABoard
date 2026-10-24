import os
import re

def _clean_text(t: str) -> str:
    t = (t or "").replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def extract_pdf_text(pdf_path: str, max_pages: int = None, max_chars: int = 250000) -> str:
    """
    Extract text from PDF.
    Returns "" if no text layer exists (scanned/image PDF) or extraction fails.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return ""

    # 1) pdfplumber (good for many PDFs)
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages
            if max_pages:
                pages = pages[:max_pages]
            for p in pages:
                tx = p.extract_text() or ""
                if tx.strip():
                    parts.append(tx)
        text = _clean_text("\n".join(parts))
        if len(text) >= 80:
            return text[:max_chars]
    except Exception:
        pass

    # 2) PyMuPDF (fitz) (often extracts where others fail)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        end = doc.page_count
        if max_pages:
            end = min(end, max_pages)
        parts = []
        for i in range(end):
            parts.append(doc.load_page(i).get_text("text") or "")
        doc.close()
        text = _clean_text("\n".join(parts))
        if len(text) >= 80:
            return text[:max_chars]
    except Exception:
        pass

    # 3) pypdf fallback
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        end = len(reader.pages)
        if max_pages:
            end = min(end, max_pages)
        parts = []
        for i in range(end):
            parts.append(reader.pages[i].extract_text() or "")
        text = _clean_text("\n".join(parts))
        if len(text) >= 80:
            return text[:max_chars]
        return text[:max_chars] if text else ""
    except Exception:
        return ""