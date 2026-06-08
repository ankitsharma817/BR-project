"""Unit tests for file service text extraction."""
import io
import pytest

from api.services.file_service import extract_text
from api.utils.security import hash_file


def test_extract_txt():
    content = b"Hello World. This is a test requirement."
    result = extract_text(content, "test.txt")
    assert "Hello World" in result


def test_extract_unsupported_type_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        extract_text(b"data", "file.xlsx")
    assert exc.value.status_code == 422


def test_hash_file_consistent():
    content = b"the same content every time"
    h1 = hash_file(content)
    h2 = hash_file(content)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_file_different_content():
    h1 = hash_file(b"content A")
    h2 = hash_file(b"content B")
    assert h1 != h2


def test_extract_txt_utf8():
    content = "Ünïcödé requirement: système must support UTF-8.".encode("utf-8")
    result = extract_text(content, "req.txt")
    assert "UTF-8" in result
