from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import Topic as TopicSchema, Article as ArticleSchema, User
from app.auth import get_current_user
from typing import List, Optional
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[TopicSchema], summary="토픽 목록 조회")
async def get_topics_list(
    name: Optional[str] = Query(None, description="토픽 이름으로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Topic)
    if name:
        query = query.filter(Topic.name.ilike(f"%{name}%"))
    
    topics = query.offset(skip).limit(limit).all()
    return topics

@router.get("/{topic_id}", response_model=TopicSchema, summary="토픽 상세 정보 조회")
async def get_topic_details(
    topic_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Fetch related articles for the topic
    # Note: The TopicSchema might need to be updated to include articles if not already.
    # For now, we return the topic itself.
    return topic
