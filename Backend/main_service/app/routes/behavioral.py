from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.models.behavioral import BehavioralQuestion

router = APIRouter(prefix="/behavioral", tags=["Behavioral Interviews"])

@router.get("/questions")
def get_behavioral_questions(limit: int = 20, db: Session = Depends(get_db)):
    """Fetch behavioral questions from the database."""
    questions = db.query(BehavioralQuestion).order_by(func.random()).limit(limit).all()
    return questions
