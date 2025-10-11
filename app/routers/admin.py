# app/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

from .. import models, schemas, database
from .users import get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])

# -----------------------------
# Dashboard Analytics Endpoints (No Changes)
# -----------------------------
@router.get("/summary-stats")
# ... (this function is unchanged)
def get_summary_stats(db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    total_users = db.query(models.User).count()
    total_queries = db.query(models.ChatHistory).count()
    health_topics = db.query(models.KnowledgeBase.intent).distinct().count()
    return {
        "total_users": total_users,
        "queries_handled": total_queries,
        "health_topics": health_topics
    }

@router.get("/query-trends")
# ... (this function is unchanged)
def get_query_trends(db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    trends = (
        db.query(
            func.date(models.ChatHistory.timestamp).label("date"),
            func.count(models.ChatHistory.id).label("count")
        )
        .filter(models.ChatHistory.timestamp >= seven_days_ago)
        .group_by(func.date(models.ChatHistory.timestamp))
        .order_by(func.date(models.ChatHistory.timestamp))
        .all()
    )
    return [{"date": str(date), "queries": count} for date, count in trends]

@router.get("/feedback-summary")
# ... (this function is unchanged)
def get_feedback_summary(db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    total_feedback = db.query(models.Feedback).count()
    if total_feedback == 0:
        return {"positive_feedback_percentage": 0}
    positive_feedback = db.query(models.Feedback).filter(models.Feedback.feedback == 1).count()
    percentage = (positive_feedback / total_feedback) * 100
    return {"positive_feedback_percentage": round(percentage, 2)}

@router.get("/unanswered-questions", response_model=list[schemas.UnansweredQuestionResponse])
# ... (this function is unchanged)
def get_unanswered_questions(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    questions = db.query(models.UnansweredQuestion).offset(skip).limit(limit).all()
    return questions

# -----------------------------
# Knowledge Base Management
# -----------------------------

## NEW ## - Endpoint to get a list of all unique intents for the filter dropdown
@router.get("/intents")
def get_all_intents(db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    intents = db.query(models.KnowledgeBase.intent).distinct().all()
    return [intent[0] for intent in intents]

## UPDATED ## - The /kb endpoint now accepts search and intent query parameters
@router.get("/kb", response_model=list[schemas.KBResponse])
def get_all_kb(
    db: Session = Depends(database.get_db), 
    admin=Depends(get_admin_user),
    search: Optional[str] = None,
    intent: Optional[str] = None
):
    """Retrieves knowledge base entries with optional search and filtering."""
    query = db.query(models.KnowledgeBase)
    
    if intent:
        query = query.filter(models.KnowledgeBase.intent == intent)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.KnowledgeBase.intent.ilike(search_term),
                models.KnowledgeBase.entity_value.ilike(search_term),
                models.KnowledgeBase.response_text.ilike(search_term)
            )
        )
        
    return query.all()

@router.post("/kb", response_model=schemas.KBResponse)
# ... (this function is unchanged)
def add_kb(entry: schemas.KBCreate, db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    new_entry = models.KnowledgeBase(intent=entry.intent, entity_value=entry.entity_value, response_text=entry.response_text)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

@router.put("/kb/{kb_id}", response_model=schemas.KBResponse)
# ... (this function is unchanged)
def update_kb(kb_id: int, entry: schemas.KBCreate, db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="KB entry not found")
    kb.intent = entry.intent
    kb.entity_value = entry.entity_value
    kb.response_text = entry.response_text
    db.commit()
    db.refresh(kb)
    return kb

@router.delete("/kb/{kb_id}")
# ... (this function is unchanged)
def delete_kb(kb_id: int, db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    kb = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="KB entry not found")
    db.delete(kb)
    db.commit()
    return {"message": "KB entry deleted"}

# -----------------------------
# Feedback & Usage Monitoring (No Changes)
# -----------------------------
@router.get("/feedback", response_model=list[schemas.FeedbackResponse])
# ... (this function is unchanged)
def get_feedback(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    return db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/usage")
# ... (this function is unchanged)
def usage_stats(db: Session = Depends(database.get_db), admin=Depends(get_admin_user)):
    stats = db.query(models.ChatHistory.intent, func.count(models.ChatHistory.id)).group_by(models.ChatHistory.intent).all()
    return [{"intent": intent, "count": count} for intent, count in stats]