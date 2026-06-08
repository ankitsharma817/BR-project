from enum import Enum


class RequirementCategory(str, Enum):
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    TIMELINE = "timeline"
    RESOURCE = "resource"
    DELIVERABLES = "deliverables"


class RequirementPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BRStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ProposalStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    MATCHED = "matched"
    FAILED = "failed"


class MatchLabel(str, Enum):
    STRONG_MATCH = "strong_match"       # 80-100%
    PARTIAL_MATCH = "partial_match"     # 60-79%
    GAP_IDENTIFIED = "gap_identified"   # 30-59%
    MISSING = "missing"                 # 0-29%


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeedbackType(str, Enum):
    SCORE_CORRECTION = "score_correction"
    REQUIREMENT_MISMATCH = "requirement_mismatch"
    GENERAL = "general"


SCORE_THRESHOLDS = {
    MatchLabel.STRONG_MATCH: 0.80,
    MatchLabel.PARTIAL_MATCH: 0.60,
    MatchLabel.GAP_IDENTIFIED: 0.30,
    MatchLabel.MISSING: 0.0,
}

CATEGORY_WEIGHTS = {
    RequirementCategory.FUNCTIONAL: 0.25,
    RequirementCategory.TECHNICAL: 0.20,
    RequirementCategory.COMPLIANCE: 0.15,
    RequirementCategory.SECURITY: 0.15,
    RequirementCategory.TIMELINE: 0.10,
    RequirementCategory.RESOURCE: 0.08,
    RequirementCategory.DELIVERABLES: 0.07,
}

MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
EMBEDDING_BATCH_SIZE = 64
RERANK_TOP_K = 20
CACHE_TTL_SECONDS = 300
