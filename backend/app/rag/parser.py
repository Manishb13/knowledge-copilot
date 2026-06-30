from pathlib import Path
from typing import Optional


def _parse_pdf(file_path: Path) -> list[dict]:
    """
    Parse a PDF using PyMuPDF (fitz) as primary.
    Falls back to pdfplumber if PyMuPDF fails or returns no content.
    Returns a list of dicts: {text, page_number}.
    """
    pages = []

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text and text.strip():
                pages.append({
                    "text": text.strip(),
                    "page_number": page_num + 1,
                })
        doc.close()

        if pages:
            return pages
    except Exception:
        pass

    try:
        import pdfplumber

        with pdfplumber.open(str(file_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "text": text.strip(),
                        "page_number": page_num + 1,
                    })
        return pages
    except Exception as exc:
        raise RuntimeError(f"Both PDF parsers failed. Last error: {exc}") from exc


def _parse_docx(file_path: Path) -> list[dict]:
    """
    Parse a DOCX file using python-docx.
    Returns a list of dicts: {text, page_number}.
    Page number is not available for DOCX so it defaults to None.
    """
    from docx import Document

    doc = Document(str(file_path))
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]

    if not paragraphs:
        return []

    full_text = "\n".join(paragraphs)
    return [{"text": full_text, "page_number": None}]


def _parse_txt(file_path: Path) -> list[dict]:
    """
    Parse a plain-text file natively.
    Returns a list of dicts: {text, page_number}.
    """
    encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
    content = None

    for encoding in encodings:
        try:
            content = file_path.read_text(encoding=encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if content is None:
        raise RuntimeError("Could not decode text file with any supported encoding")

    text = content.strip()
    if not text:
        return []

    return [{"text": text, "page_number": None}]


def _parse_markdown(file_path: Path) -> list[dict]:
    """
    Parse a Markdown file natively.
    Returns a list of dicts: {text, page_number}.
    """
    return _parse_txt(file_path)


def parse_document(file_path: Path, original_filename: str) -> list[dict]:
    """
    Dispatch to the correct parser based on file extension.
    Returns a list of page dicts: {text: str, page_number: int | None}.
    """
    suffix = Path(original_filename).suffix.lower()

    parsers = {
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
        ".txt": _parse_txt,
        ".md": _parse_markdown,
    }

    parser = parsers.get(suffix)
    if parser is None:
        raise ValueError(f"Unsupported file type: '{suffix}'")

    return parser(file_path)
