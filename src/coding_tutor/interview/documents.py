"""Session-only extraction for JD and resume uploads."""
from __future__ import annotations

from io import BytesIO

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DOCUMENT_CHARS = 100_000


class DocumentError(ValueError):
    pass


def extract_document(name: str, data: bytes) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError("The uploaded file must be 5 MB or smaller.")
    suffix = name.rsplit(".", 1)[-1].casefold() if "." in name else ""
    try:
        if suffix == "txt":
            text = data.decode("utf-8-sig")
        elif suffix == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == "docx":
            from docx import Document

            document = Document(BytesIO(data))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            raise DocumentError("Use a PDF, DOCX, or TXT file.")
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("The document could not be read. It may be encrypted or damaged.") from exc
    text = text.strip()
    if not text:
        raise DocumentError("No selectable text was found. Scanned documents need OCR first.")
    return text[:MAX_DOCUMENT_CHARS]
