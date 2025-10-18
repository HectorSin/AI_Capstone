from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import models
from app import schemas


# ==========================================================
# User helpers
# ==========================================================
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        email=user.email,
        nickname=user.nickname,
        plan=models.PlanType[user.plan.name],
        social_provider=models.SocialProviderType[user.social_provider.name],
        social_id=user.social_id,
        notification_time=user.notification_time,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# ==========================================================
# Topic helpers
# ==========================================================
async def create_topic_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    topic: schemas.TopicCreate,
) -> models.Topic:
    topic_obj = models.Topic(
        name=topic.name,
        type=models.TopicType[topic.type.name],
        summary=topic.summary,
        image_uri=topic.image_uri,
        keywords=topic.keywords or [],
    )
    db.add(topic_obj)
    await db.flush()

    for source in topic.sources:
        db.add(
            models.TopicSource(
                topic_id=topic_obj.id,
                source_name=source.source_name,
                source_url=str(source.source_url),
                is_active=source.is_active,
            )
        )

    db.add(models.UserTopic(user_id=user_id, topic_id=topic_obj.id))
    await db.commit()

    await db.refresh(
        topic_obj,
        attribute_names=["sources", "articles", "users"],
    )
    return topic_obj


async def list_topics_for_user(db: AsyncSession, user_id: UUID) -> List[models.Topic]:
    stmt = (
        select(models.Topic)
        .join(models.UserTopic, models.UserTopic.topic_id == models.Topic.id)
        .where(models.UserTopic.user_id == user_id)
        .options(
            selectinload(models.Topic.sources),
            selectinload(models.Topic.articles)
            .selectinload(models.Article.podcast_script),
            selectinload(models.Topic.articles)
            .selectinload(models.Article.podcast),
            selectinload(models.Topic.users),
        )
        .order_by(models.Topic.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique())


async def get_topic_by_id(db: AsyncSession, topic_id: UUID) -> Optional[models.Topic]:
    stmt = (
        select(models.Topic)
        .where(models.Topic.id == topic_id)
        .options(
            selectinload(models.Topic.sources),
            selectinload(models.Topic.articles)
            .selectinload(models.Article.podcast_script),
            selectinload(models.Topic.articles)
            .selectinload(models.Article.podcast),
            selectinload(models.Topic.users),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()
