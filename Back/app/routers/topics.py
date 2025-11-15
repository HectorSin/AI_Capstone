from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas

router = APIRouter(
    tags=["Topics"],
    prefix="/topics",
)


@router.post(
    "/",
    response_model=schemas.Topic,
    status_code=status.HTTP_201_CREATED,
    summary="토픽 생성",
    description="새로운 토픽을 생성합니다. 관리자/내부용 API로 사용자 연결은 포함되지 않습니다.",
)
async def create_topic(
    topic_in: schemas.TopicCreate,
    db: AsyncSession = Depends(auth.get_db),
):
    topic = await crud.create_topic(db=db, topic=topic_in)
    return topic


@router.get(
    "/",
    response_model=List[schemas.Topic],
    summary="모든 토픽 목록 조회",
    description="시스템에 등록된 모든 토픽 목록을 조회합니다.",
)
async def list_topics(
    db: AsyncSession = Depends(auth.get_db),
):
    topics = await crud.list_all_topics(db=db)
    return topics


@router.get(
    "/{topic_id}",
    response_model=schemas.Topic,
    summary="토픽 상세 조회",
    description="특정 토픽의 상세 정보를 조회합니다.",
)
async def get_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(auth.get_db),
):
    topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    return topic


@router.post(
    "/select",
    response_model=schemas.SelectTopicResponse,
    summary="토픽 선택",
    description="로그인한 사용자가 특정 토픽을 선택합니다.",
)
async def select_topic(
    payload: schemas.SelectTopicRequest,
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    try:
        link = await crud.upsert_user_topic(
            db,
            user_id=current_user.id,
            topic_id=payload.topic_id,
        )
    except ValueError as e:
        if str(e) == "topic_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        raise

    return schemas.SelectTopicResponse(
        user_id=current_user.id,
        topic_id=payload.topic_id,
    )


@router.get(
    "/preferred",
    response_model=List[schemas.PreferredTopic],
    summary="사용자 선호 토픽 조회",
    description="user_id로 해당 사용자가 선택한 선호 토픽의 ID와 이름 목록을 조회합니다.",
)
async def get_preferred_topics(
    user_id: UUID,
    db: AsyncSession = Depends(auth.get_db),
):
    topics = await crud.list_topics_for_user(db=db, user_id=user_id)
    return [schemas.PreferredTopic(topic_id=t.id, name=t.name) for t in topics]


@router.get(
    "/{topic_id}/articles",
    response_model=schemas.ArticleFeedResponse,
    summary="특정 토픽의 Article 목록"
)
async def get_topic_articles(
    topic_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(auth.get_db),
):
    """
    특정 토픽의 Article 목록 조회 (Topic Profile용)

    - 인증 불필요
    - 페이지네이션 지원
    - 날짜 내림차순
    """
    from sqlalchemy import select, func
    from app.database import models

    # Topic 존재 여부 확인
    topic = await crud.get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    # Article 조회
    articles = await crud.get_articles_by_topic(
        db=db,
        topic_id=topic_id,
        skip=skip,
        limit=limit
    )

    # FeedItem으로 변환
    feed_items = []
    for article in articles:
        if article.topic:
            feed_item = schemas.ArticleFeedItem.from_article(article, article.topic)
            feed_items.append(feed_item)

    # 전체 개수
    total_stmt = select(func.count(models.Article.id)).where(
        models.Article.topic_id == topic_id
    )
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
    "/by-name/{topic_name}/articles",
    response_model=schemas.ArticleFeedResponse,
    summary="Topic 이름으로 Article 목록 조회"
)
async def get_topic_articles_by_name(
    topic_name: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(auth.get_db),
):
    """
    Topic 이름(keyword)으로 Article 목록 조회 (Keyword Profile 페이지용)

    - 인증 불필요
    - Topic 이름(GOOGLE, META 등)으로 검색
    - 페이지네이션 지원
    - 날짜 내림차순
    """
    from sqlalchemy import select, func
    from app.database import models

    # Topic 이름으로 조회
    topic = await crud.get_topic_by_name(db=db, topic_name=topic_name)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_name}' not found"
        )

    # Article 조회
    articles = await crud.get_articles_by_topic(
        db=db,
        topic_id=topic.id,
        skip=skip,
        limit=limit
    )

    # FeedItem으로 변환
    feed_items = []
    for article in articles:
        if article.topic:
            feed_item = schemas.ArticleFeedItem.from_article(article, article.topic)
            feed_items.append(feed_item)

    # 전체 개수
    total_stmt = select(func.count(models.Article.id)).where(
        models.Article.topic_id == topic.id
    )
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    return schemas.ArticleFeedResponse(
        items=feed_items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + len(feed_items)) < total
    )
