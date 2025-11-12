from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from app.database.models import Topic, Article, Podcast
from app.schemas import Article as ArticleSchema, User
from app.auth import get_current_user
from typing import List

router = APIRouter()

@router.get("/stats", summary="기본 통계 조회")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_topics = db.query(func.count(Topic.id)).scalar()
    total_articles = db.query(func.count(Article.id)).scalar()
    total_podcasts = db.query(func.count(Podcast.id)).scalar()

    return {
        "total_topics": total_topics,
        "total_articles": total_articles,
        "total_podcasts": total_podcasts,
    }

@router.get("/recent-articles", response_model=List[ArticleSchema], summary="최근 Article 조회")
async def get_recent_articles(
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recent_articles = db.query(Article).order_by(Article.created_at.desc()).limit(limit).all()
    return recent_articles
