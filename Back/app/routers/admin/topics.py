from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import TopicAdmin, Article as ArticleSchema
from app.auth import get_current_admin_user
from app.database import models
from typing import List, Optional
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[TopicAdmin], summary="토픽 목록 조회")
async def get_topics_list(
    name: Optional[str] = Query(None, description="토픽 이름으로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    query = db.query(Topic)
    if name:
        query = query.filter(Topic.name.ilike(f"%{name}%"))

    topics = query.offset(skip).limit(limit).all()
    return topics

@router.get("/{topic_id}", response_model=TopicAdmin, summary="토픽 상세 정보 조회")
async def get_topic_details(
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic


@router.get("/{topic_id}/articles", response_model=List[ArticleSchema], summary="토픽별 아티클 목록 조회")
async def get_topic_articles(
    topic_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """특정 토픽의 아티클 목록을 조회합니다."""
    # 토픽 존재 확인
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 해당 토픽의 아티클 조회 (최신순)
    articles = db.query(Article).filter(
        Article.topic_id == topic_id
    ).order_by(
        Article.created_at.desc()
    ).offset(skip).limit(limit).all()

    return articles
