from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.database import get_db
from app.database.models import Topic, Article
from app.schemas import Topic as TopicSchema, Article as ArticleSchema
from app.auth import get_current_admin_user
from app.database import models
from typing import List, Optional
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[TopicSchema], summary="토픽 목록 조회")
async def get_topics_list(
    name: Optional[str] = Query(None, description="토픽 이름으로 필터링"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession 비동기 쿼리로 수정
    stmt = select(Topic).order_by(Topic.created_at.desc())
    if name:
        stmt = stmt.where(Topic.name.ilike(f"%{name}%"))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    topics = result.scalars().all()
    return topics

@router.get("/{topic_id}", response_model=TopicSchema, summary="토픽 상세 정보 조회")
async def get_topic_details(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    # AsyncSession 비동기 쿼리로 수정
    stmt = select(Topic).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    topic = result.scalars().first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic


@router.get("/{topic_id}/articles", response_model=List[ArticleSchema], summary="토픽별 아티클 목록 조회")
async def get_topic_articles(
    topic_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin_user: models.AdminUser = Depends(get_current_admin_user)
):
    """특정 토픽의 아티클 목록을 조회합니다."""
    # 토픽 존재 확인
    stmt = select(Topic).where(Topic.id == topic_id)
    result = await db.execute(stmt)
    topic = result.scalars().first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 해당 토픽의 아티클 조회 (최신순)
    articles_stmt = select(Article).where(
        Article.topic_id == topic_id
    ).order_by(
        Article.created_at.desc()
    ).offset(skip).limit(limit)

    articles_result = await db.execute(articles_stmt)
    articles = articles_result.scalars().all()

    return articles
