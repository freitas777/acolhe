from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

MAX_TEXTO_ARQUIVO = 5000


def extrair_texto(ext: str, data: bytes) -> str | None:
    ext = (ext or "").lower().lstrip(".")
    texto = None
    try:
        if ext == "txt":
            texto = _ler_texto(data)
        elif ext == "pdf":
            texto = _extrair_pdf(data)
        elif ext == "docx":
            texto = _extrair_docx(data)
        elif ext == "pptx":
            texto = _extrair_pptx(data)
    except Exception as exc:
        logger.warning("Falha ao extrair texto de .%s: %s", ext, exc)
        return None

    texto = (texto or "").strip()
    if not texto:
        return None

    if len(texto) > MAX_TEXTO_ARQUIVO:
        texto = texto[:MAX_TEXTO_ARQUIVO] + "\n...[texto truncado]"

    return texto


def _ler_texto(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _extrair_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    partes = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            partes.append(t.strip())
    return "\n\n".join(partes)


def _extrair_docx(data: bytes) -> str:
    import docx

    documento = docx.Document(io.BytesIO(data))
    paragrafos = [p.text for p in documento.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragrafos)


def _extrair_pptx(data: bytes) -> str:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(data))
    partes = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape.text:
                partes.append(shape.text.strip())
    return "\n".join(partes)