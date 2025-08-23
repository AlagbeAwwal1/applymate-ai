from pathlib import Path
from typing import Optional
def extract_text_from_file(path: str) -> str:
    p = Path(path)
    text = ""
    try:
        if p.suffix.lower() in ['.docx']:
            from docx import Document
            d = Document(str(p))
            text = "\n".join([para.text for para in d.paragraphs])
        elif p.suffix.lower() in ['.pdf']:
            from pdfminer.high_level import extract_text
            text = extract_text(str(p))
        else:
            text = ""
    except Exception:
        text = ""
    return text or ""
