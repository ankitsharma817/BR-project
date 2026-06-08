"""
Core matching pipeline:
  1. Extract requirements from document text
  2. Generate embeddings for BR and proposal requirements
  3. Compute cosine similarity + reranker scores
  4. Aggregate into per-category and overall scores
  5. Generate LLM explanations via Qwen
  6. Identify risks & recommendations
"""
import re
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from ..models.br import BRRequirement
from ..models.proposal import Proposal, ProposalRequirement
from ..models.matching import MatchingResult, RequirementMatching, MatchAnalysis, MatchHistory
from ..utils.constants import (
    RequirementCategory, RequirementPriority, MatchLabel,
    SCORE_THRESHOLDS, CATEGORY_WEIGHTS, RERANK_TOP_K,
)
from .embedding_service import generate_embeddings, batch_cosine_similarities, rerank

_llm_pipeline = None


def _get_llm():
    global _llm_pipeline
    if _llm_pipeline is None:
        from transformers import pipeline
        from ..config import settings
        _llm_pipeline = pipeline(
            "text-generation",
            model=settings.LLM_MODEL,
            model_kwargs={"torch_dtype": "float16"},
            device_map="auto",
        )
    return _llm_pipeline


# ---------------------------------------------------------------------------
# Requirement extraction
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS = {
    RequirementCategory.SECURITY: ["security", "authentication", "auth", "oauth", "encryption", "ssl", "tls", "jwt", "saml", "compliance", "gdpr", "audit"],
    RequirementCategory.TECHNICAL: ["database", "api", "architecture", "cloud", "server", "docker", "kubernetes", "redis", "postgresql", "microservice", "rest", "graphql"],
    RequirementCategory.TIMELINE: ["month", "week", "day", "deadline", "delivery", "timeline", "schedule", "duration", "milestone"],
    RequirementCategory.RESOURCE: ["team", "developer", "engineer", "staff", "support", "sla", "uptime", "availability", "maintenance"],
    RequirementCategory.COMPLIANCE: ["iso", "soc", "hipaa", "pci", "regulation", "certif", "standard", "gdpr", "compliant"],
    RequirementCategory.DELIVERABLES: ["deliver", "document", "report", "source code", "training", "handover", "warranty", "license"],
}


def _classify_category(text: str) -> str:
    lower = text.lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return cat.value
    return RequirementCategory.FUNCTIONAL.value


def _classify_priority(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["must", "critical", "mandatory", "required", "shall"]):
        return RequirementPriority.CRITICAL.value
    if any(w in lower for w in ["should", "high", "important", "essential"]):
        return RequirementPriority.HIGH.value
    if any(w in lower for w in ["may", "optional", "preferred", "nice"]):
        return RequirementPriority.LOW.value
    return RequirementPriority.MEDIUM.value


def extract_requirements(text: str) -> list[dict]:
    """Split text into requirement sentences and classify them."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    requirements = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20:
            continue
        requirements.append({
            "text": sent,
            "category": _classify_category(sent),
            "priority": _classify_priority(sent),
        })
    return requirements[:200]  # cap at 200


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------

def _label_score(score: float) -> str:
    if score >= SCORE_THRESHOLDS[MatchLabel.STRONG_MATCH]:
        return MatchLabel.STRONG_MATCH.value
    if score >= SCORE_THRESHOLDS[MatchLabel.PARTIAL_MATCH]:
        return MatchLabel.PARTIAL_MATCH.value
    if score >= SCORE_THRESHOLDS[MatchLabel.GAP_IDENTIFIED]:
        return MatchLabel.GAP_IDENTIFIED.value
    return MatchLabel.MISSING.value


def _generate_explanation(br_text: str, proposal_text: Optional[str], score: float) -> str:
    if not proposal_text:
        return f"No matching content found in the proposal for this requirement. Score: {score:.0%}."
    label = _label_score(score)
    if label == MatchLabel.STRONG_MATCH.value:
        return f"Strong match ({score:.0%}): The proposal directly addresses this requirement."
    if label == MatchLabel.PARTIAL_MATCH.value:
        return f"Partial match ({score:.0%}): The proposal partially covers this requirement but may lack specifics."
    if label == MatchLabel.GAP_IDENTIFIED.value:
        return f"Gap identified ({score:.0%}): The proposal mentions related content but doesn't clearly fulfill this requirement."
    return f"Missing ({score:.0%}): This requirement does not appear to be addressed in the proposal."


def _llm_explanation(br_text: str, proposal_text: str, score: float) -> str:
    """Use Qwen LLM for richer explanation (called only when LLM available)."""
    try:
        llm = _get_llm()
        prompt = (
            f"[INST] Explain in 2 sentences why the following proposal feature matches or doesn't match the requirement.\n"
            f"Requirement: {br_text}\n"
            f"Proposal: {proposal_text}\n"
            f"Match score: {score:.0%} [/INST]"
        )
        result = llm(prompt, max_new_tokens=100, do_sample=False)[0]["generated_text"]
        # Strip prompt from output
        return result.replace(prompt, "").strip()
    except Exception:
        return _generate_explanation(br_text, proposal_text, score)


# ---------------------------------------------------------------------------
# Main matching pipeline
# ---------------------------------------------------------------------------

def run_matching(
    db: Session,
    proposal: Proposal,
    br_requirements: list[BRRequirement],
    use_llm: bool = False,
    triggered_by: Optional[uuid.UUID] = None,
) -> MatchingResult:
    """
    Full matching pipeline. Returns a persisted MatchingResult.
    """
    proposal_reqs = proposal.requirements
    if not proposal_reqs:
        raise ValueError("Proposal has no extracted requirements")
    if not br_requirements:
        raise ValueError("BR project has no requirements")

    # Generate/retrieve embeddings
    br_texts = [r.text for r in br_requirements]
    prop_texts = [r.text for r in proposal_reqs]

    br_embs = [r.embedding if r.embedding else None for r in br_requirements]
    prop_embs = [r.embedding if r.embedding else None for r in proposal_reqs]

    # Generate missing embeddings
    br_missing_idx = [i for i, e in enumerate(br_embs) if e is None]
    prop_missing_idx = [i for i, e in enumerate(prop_embs) if e is None]

    if br_missing_idx:
        new_embs = generate_embeddings([br_texts[i] for i in br_missing_idx])
        for idx, emb in zip(br_missing_idx, new_embs):
            br_embs[idx] = emb
            br_requirements[idx].embedding = emb
    if prop_missing_idx:
        new_embs = generate_embeddings([prop_texts[i] for i in prop_missing_idx])
        for idx, emb in zip(prop_missing_idx, new_embs):
            prop_embs[idx] = emb
            proposal_reqs[idx].embedding = emb

    db.commit()

    # Per-requirement matching
    requirement_matchings = []
    category_scores: dict[str, list[float]] = {cat.value: [] for cat in RequirementCategory}

    for br_req, br_emb in zip(br_requirements, br_embs):
        if not br_emb:
            continue
        sims = batch_cosine_similarities(br_emb, [e for e in prop_embs if e])
        top_k = min(RERANK_TOP_K, len(sims))
        top_indices = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]

        best_score = 0.0
        best_prop_req = None

        if top_indices:
            top_prop_texts = [prop_texts[i] for i in top_indices]
            reranker_scores = rerank(br_req.text, top_prop_texts)
            # Blend embedding + reranker
            blended = [0.4 * sims[top_indices[i]] + 0.6 * reranker_scores[i] for i in range(len(top_indices))]
            best_local_idx = max(range(len(blended)), key=lambda i: blended[i])
            best_score = blended[best_local_idx]
            best_prop_req = proposal_reqs[top_indices[best_local_idx]]

        label = _label_score(best_score)
        explanation = (
            _llm_explanation(br_req.text, best_prop_req.text, best_score)
            if use_llm and best_prop_req
            else _generate_explanation(br_req.text, best_prop_req.text if best_prop_req else None, best_score)
        )

        rm = RequirementMatching(
            br_requirement_id=br_req.id,
            proposal_requirement_id=best_prop_req.id if best_prop_req else None,
            score=round(best_score, 4),
            label=label,
            explanation=explanation,
            embedding_score=round(sims[top_indices[0]], 4) if top_indices else 0.0,
        )
        requirement_matchings.append(rm)
        category_scores[br_req.category].append(best_score)

    # Category aggregation (weighted average)
    cat_avgs = {}
    for cat, scores in category_scores.items():
        cat_avgs[cat] = float(sum(scores) / len(scores)) if scores else None

    # Overall weighted score
    total_weight = 0.0
    weighted_sum = 0.0
    for cat_enum, weight in CATEGORY_WEIGHTS.items():
        avg = cat_avgs.get(cat_enum.value)
        if avg is not None:
            weighted_sum += avg * weight
            total_weight += weight
    overall_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

    # Persist or update MatchingResult
    existing = db.query(MatchingResult).filter(MatchingResult.proposal_id == proposal.id).first()
    if existing:
        # Archive to history
        history = MatchHistory(
            result_id=existing.id,
            overall_score=existing.overall_score,
            scores_snapshot={
                "functional": existing.functional_score,
                "technical": existing.technical_score,
                "compliance": existing.compliance_score,
                "security": existing.security_score,
                "timeline": existing.timeline_score,
                "resource": existing.resource_score,
                "deliverables": existing.deliverables_score,
            },
            version=existing.version,
            triggered_by=triggered_by,
        )
        db.add(history)
        db.delete(existing)
        db.flush()

    result = MatchingResult(
        proposal_id=proposal.id,
        overall_score=overall_score,
        functional_score=cat_avgs.get(RequirementCategory.FUNCTIONAL.value),
        technical_score=cat_avgs.get(RequirementCategory.TECHNICAL.value),
        compliance_score=cat_avgs.get(RequirementCategory.COMPLIANCE.value),
        security_score=cat_avgs.get(RequirementCategory.SECURITY.value),
        timeline_score=cat_avgs.get(RequirementCategory.TIMELINE.value),
        resource_score=cat_avgs.get(RequirementCategory.RESOURCE.value),
        deliverables_score=cat_avgs.get(RequirementCategory.DELIVERABLES.value),
        executive_summary=_build_summary(proposal.vendor_name, overall_score, cat_avgs),
        version=(existing.version + 1) if existing else 1,
    )
    db.add(result)
    db.flush()

    for rm in requirement_matchings:
        rm.result_id = result.id
        db.add(rm)

    # Build analysis
    analysis = _build_analysis(result.id, requirement_matchings, cat_avgs, br_requirements)
    db.add(analysis)

    proposal.status = "matched"
    db.commit()
    db.refresh(result)
    return result


def _build_summary(vendor_name: str, overall_score: float, cat_avgs: dict) -> str:
    pct = overall_score * 100
    strongest = max(cat_avgs, key=lambda k: cat_avgs[k] or 0)
    weakest = min(cat_avgs, key=lambda k: cat_avgs[k] or 1)
    return (
        f"{vendor_name} achieved an overall match score of {pct:.1f}%. "
        f"Strongest alignment in {strongest} ({(cat_avgs[strongest] or 0)*100:.1f}%). "
        f"Area requiring attention: {weakest} ({(cat_avgs[weakest] or 0)*100:.1f}%)."
    )


def _build_analysis(
    result_id: uuid.UUID,
    matchings: list[RequirementMatching],
    cat_avgs: dict,
    br_requirements: list[BRRequirement],
) -> MatchAnalysis:
    risks = []
    recommendations = []
    strengths = []
    gaps = []

    for cat, avg in cat_avgs.items():
        if avg is None:
            continue
        if avg >= 0.80:
            strengths.append(f"Strong {cat} alignment ({avg*100:.1f}%)")
        elif avg < 0.50:
            risks.append({"level": "high", "description": f"Low {cat} coverage ({avg*100:.1f}%)", "category": cat})
            recommendations.append({"priority": "HIGH", "action": f"Request detailed {cat} clarification from vendor", "reason": f"Score only {avg*100:.1f}%"})
        elif avg < 0.70:
            risks.append({"level": "medium", "description": f"Partial {cat} coverage ({avg*100:.1f}%)", "category": cat})
            recommendations.append({"priority": "MEDIUM", "action": f"Verify {cat} specifics with vendor", "reason": f"Score {avg*100:.1f}%"})

    for rm in matchings:
        br_req = next((r for r in br_requirements if str(r.id) == str(rm.br_requirement_id)), None)
        if not br_req:
            continue
        if rm.label in (MatchLabel.MISSING.value, MatchLabel.GAP_IDENTIFIED.value):
            gaps.append(f"{br_req.category.upper()}: {br_req.text[:120]}")

    return MatchAnalysis(
        result_id=result_id,
        risks=risks,
        recommendations=recommendations,
        strengths=strengths,
        gaps=gaps,
    )
