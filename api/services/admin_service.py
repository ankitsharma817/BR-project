from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.user import User
from ..models.br import BRProject
from ..models.proposal import Proposal
from ..models.matching import MatchingResult
from ..models.feedback import Feedback, AILearningLog
from ..models.audit import AuditLog


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> dict:
        return {
            "total_br_projects": self.db.query(BRProject).filter(BRProject.is_deleted == False).count(),
            "total_proposals": self.db.query(Proposal).filter(Proposal.is_deleted == False).count(),
            "total_matched": self.db.query(Proposal).filter(Proposal.status == "matched").count(),
            "total_users": self.db.query(User).filter(User.is_active == True).count(),
            "avg_match_score": self._avg_match_score(),
            "pending_processing": self.db.query(Proposal).filter(Proposal.status == "processing").count(),
            "total_feedback": self.db.query(Feedback).count(),
        }

    def _avg_match_score(self) -> float | None:
        result = self.db.query(func.avg(MatchingResult.overall_score)).scalar()
        return round(float(result), 4) if result else None

    def get_system_health(self) -> dict:
        health: dict = {"database": "ok", "gpu": "unknown", "redis": "unknown"}
        try:
            self.db.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception:
            health["database"] = "error"
        try:
            import redis as redis_lib
            from ..config import settings
            r = redis_lib.from_url(settings.REDIS_URL)
            r.ping()
            health["redis"] = "ok"
        except Exception:
            health["redis"] = "error"
        try:
            import torch
            health["gpu"] = "ok" if torch.cuda.is_available() else "cpu_only"
            if torch.cuda.is_available():
                health["gpu_name"] = torch.cuda.get_device_name(0)
                health["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
        except ImportError:
            health["gpu"] = "torch_not_installed"
        return health

    def get_recent_activities(self, limit: int = 20) -> list[dict]:
        logs = (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": str(log.id),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    def get_audit_logs(self, page: int = 1, page_size: int = 50) -> dict:
        q = self.db.query(AuditLog).order_by(AuditLog.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "items": [
                {
                    "id": str(l.id),
                    "action": l.action,
                    "user_id": str(l.user_id) if l.user_id else None,
                    "resource_type": l.resource_type,
                    "resource_id": l.resource_id,
                    "detail": l.detail,
                    "ip_address": l.ip_address,
                    "created_at": l.created_at.isoformat(),
                }
                for l in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    def get_ai_learning_stats(self) -> dict:
        logs = self.db.query(AILearningLog).all()
        if not logs:
            return {"total_corrections": 0, "avg_delta": None, "applied": 0, "pending": 0}
        avg_delta = sum(l.delta for l in logs) / len(logs)
        applied = sum(1 for l in logs if l.applied_to_model)
        return {
            "total_corrections": len(logs),
            "avg_delta": round(avg_delta, 4),
            "applied": applied,
            "pending": len(logs) - applied,
        }

    def log_audit(
        self,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_id=None,
        detail: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(entry)
        self.db.commit()
