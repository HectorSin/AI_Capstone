from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import Article as ArticleSchema
from app.auth import get_current_admin_user
from app.database import models
from typing import List

router = APIRouter()

@router.get("/stats", summary="기본 통계 조회")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession을 사용한 비동기 쿼리
    total_topics_result = await db.execute(select(func.count(Topic.id)))
    total_topics = total_topics_result.scalar() or 0

    total_articles_result = await db.execute(select(func.count(Article.id)))
    total_articles = total_articles_result.scalar() or 0

    # completed 상태의 Article 개수로 podcasts 대체
    completed_articles_result = await db.execute(
        select(func.count(Article.id)).where(Article.status == 'completed')
    )
    total_completed_articles = completed_articles_result.scalar() or 0

    return {
        "total_topics": total_topics,
        "total_articles": total_articles,
        "total_completed_articles": total_completed_articles,
    }

@router.get("/recent-articles", response_model=List[ArticleSchema], summary="최근 Article 조회")
async def get_recent_articles(
    limit: int = Query(5, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession을 사용한 비동기 쿼리
    stmt = select(Article).order_by(Article.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    recent_articles = result.scalars().all()
    return recent_articles

@router.get("/articles", response_model=List[ArticleSchema], summary="전체 Article 조회")
async def get_all_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession을 사용한 비동기 쿼리
    stmt = select(Article).order_by(Article.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return articles
