import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.feedback import Feedback, AILearningLog
from ..models.proposal import Proposal
from ..schemas.feedback import FeedbackCreate, FeedbackUpdate


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, proposal_id: uuid.UUID, user_id: uuid.UUID, data: FeedbackCreate) -> Feedback:
        proposal = self.db.get(Proposal, proposal_id)
        if not proposal or proposal.is_deleted:
            raise HTTPException(status_code=404, detail="Proposal not found")

        feedback = Feedback(
            proposal_id=proposal_id,
            user_id=user_id,
            feedback_type=data.feedback_type.value,
            rating=data.rating,
            comment=data.comment,
            corrected_score=data.corrected_score,
            original_score=data.original_score,
        )
        self.db.add(feedback)

        if data.corrected_score is not None and data.original_score is not None:
            delta = data.corrected_score - data.original_score
            log = AILearningLog(
                feedback_id=feedback.id,
                original_score=data.original_score,
                corrected_score=data.corrected_score,
                delta=delta,
            )
            self.db.add(log)

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def list_feedbacks(self, proposal_id: uuid.UUID) -> list[Feedback]:
        return self.db.query(Feedback).filter(Feedback.proposal_id == proposal_id).all()

    def get_feedback(self, feedback_id: uuid.UUID) -> Feedback:
        fb = self.db.get(Feedback, feedback_id)
        if not fb:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return fb

    def update_feedback(self, feedback_id: uuid.UUID, user_id: uuid.UUID, data: FeedbackUpdate) -> Feedback:
        fb = self.get_feedback(feedback_id)
        if str(fb.user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized to update this feedback")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(fb, field, value)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def mark_useful(self, feedback_id: uuid.UUID, useful: bool) -> Feedback:
        fb = self.get_feedback(feedback_id)
        fb.is_useful = useful
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def get_quality_metrics(self) -> dict:
        total = self.db.query(Feedback).count()
        useful = self.db.query(Feedback).filter(Feedback.is_useful == True).count()
        corrections = self.db.query(AILearningLog).count()
        avg_rating = self.db.query(Feedback).filter(Feedback.rating.isnot(None)).all()
        avg = sum(f.rating for f in avg_rating) / len(avg_rating) if avg_rating else None
        return {
            "total_feedback": total,
            "useful_feedback": useful,
            "total_corrections": corrections,
            "average_rating": round(avg, 2) if avg else None,
        }
