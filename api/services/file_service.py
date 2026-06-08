import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..utils.security import hash_file


def _extract_pdf(content: bytes) -> str:
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract PDF: {e}")


def _extract_docx(content: bytes) -> str:
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract DOCX: {e}")


def extract_text(content: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(content)
    elif ext in (".docx", ".doc"):
        return _extract_docx(content)
    elif ext == ".txt":
        return content.decode("utf-8", errors="replace")
    raise HTTPException(status_code=422, detail=f"Unsupported file type: {ext}")


async def save_upload(file: UploadFile, subfolder: str) -> dict:
    content = await file.read()
    file_hash = hash_file(content)
    ext = Path(file.filename or "file").suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = Path(settings.UPLOAD_DIR) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / stored_name
    with open(dest_path, "wb") as f:
        f.write(content)
    return {
        "file_path": str(dest_path),
        "file_hash": file_hash,
        "file_size": len(content),
        "mime_type": file.content_type,
        "content": content,
    }


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
