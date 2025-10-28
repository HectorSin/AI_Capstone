import re
import secrets

from datetime import time
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
# Helper utilities
# ==========================================================
def _sanitize_nickname(nickname: str) -> str:
    candidate = re.sub(r"\s+", "_", nickname.strip())
    candidate = re.sub(r"[^A-Za-z0-9_.-]", "", candidate)
    return candidate or f"user_{secrets.token_hex(4)}"


async def generate_unique_nickname(db: AsyncSession, desired_nickname: str) -> str:
    base = _sanitize_nickname(desired_nickname)[:30]
    suffix = 0

    while suffix < 100:
        candidate = base if suffix == 0 else f"{base}_{suffix}"
        stmt = select(models.User.id).where(models.User.nickname == candidate)
        result = await db.execute(stmt)
        if result.scalars().first() is None:
            return candidate
        suffix += 1

    # 최종 fallback - 충돌이 계속되면 랜덤 닉네임 사용
    return f"user_{secrets.token_hex(6)}"


async def get_user_by_nickname(db: AsyncSession, nickname: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.nickname == nickname)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_social(
    db: AsyncSession,
    *,
    provider: models.SocialProviderType,
    social_id: str,
) -> Optional[models.User]:
    stmt = select(models.User).where(
        models.User.social_provider == provider,
        models.User.social_id == social_id,
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_local_user(
    db: AsyncSession,
    *,
    email: str,
    nickname: str,
    password_hash: str,
) -> models.User:
    preference = models.NotificationPreference(
        allowed=False,
        time_enabled=False,
        send_time=time(hour=7, minute=0),
        days_of_week=[0, 1, 2, 3, 4],
        prompted=False,
    )

    user = models.User(
        email=email,
        nickname=nickname,
        plan=models.PlanType.free,
        social_provider=models.SocialProviderType.none,
        social_id=None,
        password_hash=password_hash,
        notification_preference=preference,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise exc

    await db.refresh(user)
    await db.refresh(user)
    return user


async def create_social_user(
    db: AsyncSession,
    *,
    email: str,
    nickname: str,
    provider: models.SocialProviderType,
    social_id: str,
) -> models.User:
    preference = models.NotificationPreference(
        allowed=False,
        time_enabled=False,
        send_time=time(hour=7, minute=0),
        days_of_week=[0, 1, 2, 3, 4],
        prompted=False,
    )

    user = models.User(
        email=email,
        nickname=nickname,
        plan=models.PlanType.free,
        social_provider=provider,
        social_id=social_id,
        password_hash=None,
        notification_preference=preference,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise exc

    await db.refresh(user)
    return user


async def update_user_password(
    db: AsyncSession,
    *,
    user: models.User,
    password_hash: str,
) -> models.User:
    user.password_hash = password_hash
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_notification_preference(
    db: AsyncSession,
    user_id: UUID,
) -> Optional[models.NotificationPreference]:
    stmt = select(models.NotificationPreference).where(models.NotificationPreference.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def ensure_notification_preference(
    db: AsyncSession,
    user_id: UUID,
) -> models.NotificationPreference:
    preference = await get_notification_preference(db, user_id)
    if preference:
        return preference

    preference = models.NotificationPreference(
        user_id=user_id,
        allowed=False,
        time_enabled=False,
        send_time=time(hour=7, minute=0),
        days_of_week=[0, 1, 2, 3, 4],
        prompted=False,
    )
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    return preference


async def update_notification_preference(
    db: AsyncSession,
    preference: models.NotificationPreference,
    *,
    allowed: bool,
    time_enabled: bool,
    send_time_value: Optional[time],
    days_of_week: Sequence[int],
    prompted: bool,
) -> models.NotificationPreference:
    preference.allowed = allowed
    preference.time_enabled = time_enabled
    preference.send_time = send_time_value
    preference.days_of_week = list(days_of_week)
    preference.prompted = prompted

    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    return preference


async def delete_user(db: AsyncSession, user: models.User) -> None:
    await db.delete(user)
    await db.commit()


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
