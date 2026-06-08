import re
from pathlib import Path
from fastapi import HTTPException, UploadFile
from .constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PASSWORD_MIN_LENGTH = 8


def validate_email(email: str) -> str:
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=422, detail="Invalid email address")
    return email.lower()


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=422, detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=422, detail="Password must contain at least one digit"
        )


def validate_score(score: float, field: str = "score") -> float:
    if not 0.0 <= score <= 1.0:
        raise HTTPException(status_code=422, detail=f"{field} must be between 0.0 and 1.0")
    return score


async def validate_upload_file(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    content = await file.read()
    await file.seek(0)
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=422,
            detail=f"File size {size_mb:.1f}MB exceeds limit of {MAX_FILE_SIZE_MB}MB",
        )


def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
    if page < 1:
        raise HTTPException(status_code=422, detail="page must be >= 1")
    if not 1 <= page_size <= 100:
        raise HTTPException(status_code=422, detail="page_size must be between 1 and 100")
    return page, page_size
