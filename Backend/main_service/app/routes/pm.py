from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.models.product_management import PMQuestion

router = APIRouter(prefix="/pm", tags=["Product Management Interviews"])

@router.get("/questions")
def get_pm_questions(limit: int = 20, db: Session = Depends(get_db)):
    """Fetch product management questions from the database."""
    questions = db.query(PMQuestion).order_by(func.random()).limit(limit).all()
    return questions
