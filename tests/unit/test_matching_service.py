"""Unit tests for matching utilities that don't need GPU/DB."""
import pytest

from api.services.matching_service import (
    extract_requirements,
    _classify_category,
    _classify_priority,
    _label_score,
    _generate_explanation,
)
from api.utils.constants import MatchLabel


# ── Requirement extraction ────────────────────────────────────────────────────

def test_extract_requirements_returns_list():
    text = (
        "The system must support 500 concurrent users. "
        "OAuth 2.0 authentication is required. "
        "Delivery must be within 6 months. "
        "The solution must use PostgreSQL database."
    )
    reqs = extract_requirements(text)
    assert isinstance(reqs, list)
    assert len(reqs) >= 1
    for r in reqs:
        assert "text" in r
        assert "category" in r
        assert "priority" in r


def test_extract_requirements_caps_at_200():
    long_text = "This is a valid requirement sentence. " * 300
    reqs = extract_requirements(long_text)
    assert len(reqs) <= 200


def test_extract_requirements_skips_short_lines():
    text = "Short.\nThis is a real requirement that must be met.\nOK."
    reqs = extract_requirements(text)
    for r in reqs:
        assert len(r["text"]) >= 20


# ── Category classification ───────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("OAuth 2.0 authentication required", "security"),
    ("The system must use PostgreSQL database", "technical"),
    ("Delivery within 6 months", "timeline"),
    ("ISO 27001 certification required", "compliance"),
    ("Team of 5 developers for support", "resource"),
    ("Source code handover upon completion", "deliverables"),
    ("The system must handle file uploads", "functional"),
])
def test_classify_category(text, expected):
    assert _classify_category(text) == expected


# ── Priority classification ───────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("The system must support 500 users", "critical"),
    ("The system shall comply with GDPR", "critical"),
    ("The solution should scale horizontally", "high"),
    ("Optional dark mode support", "low"),
    ("The system handles file uploads", "medium"),
])
def test_classify_priority(text, expected):
    assert _classify_priority(text) == expected


# ── Score labeling ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected_label", [
    (1.0, MatchLabel.STRONG_MATCH.value),
    (0.85, MatchLabel.STRONG_MATCH.value),
    (0.80, MatchLabel.STRONG_MATCH.value),
    (0.75, MatchLabel.PARTIAL_MATCH.value),
    (0.60, MatchLabel.PARTIAL_MATCH.value),
    (0.45, MatchLabel.GAP_IDENTIFIED.value),
    (0.30, MatchLabel.GAP_IDENTIFIED.value),
    (0.20, MatchLabel.MISSING.value),
    (0.0, MatchLabel.MISSING.value),
])
def test_label_score(score, expected_label):
    assert _label_score(score) == expected_label


# ── Explanation generation ────────────────────────────────────────────────────

def test_explanation_strong_match():
    text = _generate_explanation("Support 500 users", "Handles 1000+ users", 0.92)
    assert "Strong match" in text or "strong" in text.lower()
    assert "92%" in text or "0.92" in text.lower() or "92" in text


def test_explanation_missing():
    text = _generate_explanation("Must have OAuth 2.0", None, 0.1)
    assert "No matching" in text or "missing" in text.lower() or "Missing" in text


def test_explanation_contains_score():
    text = _generate_explanation("Some requirement", "Some proposal text", 0.65)
    assert "65%" in text or "65" in text
