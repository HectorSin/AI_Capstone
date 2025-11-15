"""
Article 피드 API 라우터
프론트엔드 FeedItem 구조와 호환되는 API 제공
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database.database import get_db
from app.auth import get_current_user
from app.database import models
from app import schemas, crud

router = APIRouter(
    prefix="/articles",
    tags=["Articles"]
)


@router.get(
    "/feed",
    response_model=schemas.ArticleFeedResponse,
    summary="전체 Article 피드 (Home용)"
)
async def get_article_feed(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(20, ge=1, le=100, description="가져올 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    모든 Article을 날짜 내림차순으로 조회 (Home 피드용)

    - 인증 불필요
    - 페이지네이션 지원
    - Topic 정보 포함
    """
    articles = await crud.get_all_articles(db=db, skip=skip, limit=limit)

    # Article을 FeedItem으로 변환
    feed_items = []
    for article in articles:
        if article.topic:  # Topic이 로드되었는지 확인
            feed_item = schemas.ArticleFeedItem.from_article(article, article.topic)
            feed_items.append(feed_item)

    # 전체 개수 조회 (페이지네이션용)
    total_stmt = select(func.count(models.Article.id))
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    return schemas.ArticleFeedResponse(
        items=feed_items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(feed_items)) < total
    )


@router.get(
    "/subscribed",
    response_model=schemas.ArticleFeedResponse,
    summary="구독 토픽 Article 피드 (Subscribe 탭용)"
)
async def get_subscribed_articles(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(20, ge=1, le=100, description="가져올 개수"),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자가 구독한 토픽들의 Article 조회 (Subscribe 탭용)

    - 인증 필수
    - 사용자가 구독한 토픽의 Article만 반환
    - 날짜 내림차순
    """
    articles = await crud.get_articles_by_user_topics(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    # Article을 FeedItem으로 변환
    feed_items = []
    for article in articles:
        if article.topic:
            feed_item = schemas.ArticleFeedItem.from_article(article, article.topic)
            feed_items.append(feed_item)

    # 구독 토픽의 전체 Article 개수
    user_topics_stmt = select(models.UserTopic.topic_id).where(
        models.UserTopic.user_id == current_user.id
    )
    user_topics_result = await db.execute(user_topics_stmt)
    topic_ids = [row[0] for row in user_topics_result.all()]

    if topic_ids:
        total_stmt = select(func.count(models.Article.id)).where(
            models.Article.topic_id.in_(topic_ids)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
    else:
        total = 0

    return schemas.ArticleFeedResponse(
        items=feed_items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(feed_items)) < total
    )


@router.get(
    "/{article_id}",
    response_model=schemas.ArticleFeedItem,
    summary="Article 상세 조회"
)
async def get_article_detail(
    article_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Article ID로 개별 Article 조회 (Article 상세 페이지용)

    - 인증 불필요
    - Topic 정보 포함
    - 404 에러 처리
    """
    article = await crud.get_article_by_id(db=db, article_id=article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    if not article.topic:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Article topic not found"
        )

    return schemas.ArticleFeedItem.from_article(article, article.topic)
