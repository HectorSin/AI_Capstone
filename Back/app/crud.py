import re
import secrets

from datetime import date, time
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import models
from app import schemas
from app.constants import (
    DEFAULT_NOTIFICATION_HOUR,
    DEFAULT_NOTIFICATION_MINUTE,
    DEFAULT_NOTIFICATION_DAYS,
    DEFAULT_NOTIFICATION_ALLOWED,
    DEFAULT_NOTIFICATION_TIME_ENABLED,
    DEFAULT_NOTIFICATION_PROMPTED,
    MAX_NICKNAME_LENGTH,
    MAX_NICKNAME_SUFFIX_ATTEMPTS,
    FALLBACK_NICKNAME_HEX_LENGTH,
)


# ==========================================================
# User helpers
# ==========================================================
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_admin_user_by_email(db: AsyncSession, email: str) -> Optional[models.AdminUser]:
    stmt = select(models.AdminUser).where(models.AdminUser.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_admin_user_by_id(db: AsyncSession, admin_user_id: UUID) -> Optional[models.AdminUser]:
    stmt = select(models.AdminUser).where(models.AdminUser.id == admin_user_id)
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
def _create_default_notification_preference(user_id: Optional[UUID] = None) -> models.NotificationPreference:
    """기본 알림 설정 객체를 생성합니다."""
    return models.NotificationPreference(
        user_id=user_id,
        allowed=DEFAULT_NOTIFICATION_ALLOWED,
        time_enabled=DEFAULT_NOTIFICATION_TIME_ENABLED,
        send_time=time(hour=DEFAULT_NOTIFICATION_HOUR, minute=DEFAULT_NOTIFICATION_MINUTE),
        days_of_week=DEFAULT_NOTIFICATION_DAYS.copy(),
        prompted=DEFAULT_NOTIFICATION_PROMPTED,
    )


def _sanitize_nickname(nickname: str) -> str:
    candidate = re.sub(r"\s+", "_", nickname.strip())
    candidate = re.sub(r"[^A-Za-z0-9_.-]", "", candidate)
    return candidate or f"user_{secrets.token_hex(4)}"


async def generate_unique_nickname(db: AsyncSession, desired_nickname: str) -> str:
    base = _sanitize_nickname(desired_nickname)[:MAX_NICKNAME_LENGTH]
    suffix = 0

    while suffix < MAX_NICKNAME_SUFFIX_ATTEMPTS:
        candidate = base if suffix == 0 else f"{base}_{suffix}"
        stmt = select(models.User.id).where(models.User.nickname == candidate)
        result = await db.execute(stmt)
        if result.scalars().first() is None:
            return candidate
        suffix += 1

    # 최종 fallback - 충돌이 계속되면 랜덤 닉네임 사용
    return f"user_{secrets.token_hex(FALLBACK_NICKNAME_HEX_LENGTH)}"


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
    difficulty_level: models.DifficultyLevel = models.DifficultyLevel.intermediate,
) -> models.User:
    preference = _create_default_notification_preference()

    user = models.User(
        email=email,
        nickname=nickname,
        plan=models.PlanType.free,
        difficulty_level=difficulty_level,
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
    return user


async def create_social_user(
    db: AsyncSession,
    *,
    email: str,
    nickname: str,
    provider: models.SocialProviderType,
    social_id: str,
) -> models.User:
    preference = _create_default_notification_preference()

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


async def create_admin_user(db: AsyncSession, email: str, password_hash: str) -> models.AdminUser:
    admin_user = models.AdminUser(
        email=email,
        password_hash=password_hash,
    )
    db.add(admin_user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise exc

    await db.refresh(admin_user)
    return admin_user


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

    preference = _create_default_notification_preference(user_id=user_id)
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


async def update_user(
    db: AsyncSession,
    user: models.User,
    update_data: dict,
) -> models.User:
    """사용자 정보 업데이트"""
    for key, value in update_data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


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
            selectinload(models.Topic.articles),
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
            selectinload(models.Topic.articles),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_topic(db: AsyncSession, topic: schemas.TopicCreate) -> models.Topic:
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

    await db.commit()

    # sources를 제대로 로드하기 위해 다시 조회
    return await get_topic_by_id(db=db, topic_id=topic_obj.id)


async def list_all_topics(db: AsyncSession) -> List[models.Topic]:
    stmt = (
        select(models.Topic)
        .options(
            selectinload(models.Topic.sources),
            selectinload(models.Topic.articles),
        )
        .order_by(models.Topic.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique())


async def update_topic(
    db: AsyncSession,
    topic_id: UUID,
    topic_update: schemas.TopicBase
) -> Optional[models.Topic]:
    """토픽 정보를 업데이트합니다."""
    # 기존 토픽 조회
    topic = await get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        return None

    # 업데이트할 필드 적용
    topic.name = topic_update.name
    topic.type = models.TopicType[topic_update.type.name]
    topic.summary = topic_update.summary
    topic.image_uri = topic_update.image_uri
    topic.keywords = topic_update.keywords or []

    await db.commit()
    await db.refresh(topic)

    # sources와 articles를 포함하여 다시 조회
    return await get_topic_by_id(db=db, topic_id=topic_id)


async def delete_topic(
    db: AsyncSession,
    topic_id: UUID
) -> bool:
    """토픽을 삭제합니다."""
    topic = await get_topic_by_id(db=db, topic_id=topic_id)
    if not topic:
        return False

    await db.delete(topic)
    await db.commit()
    return True


# ==========================================================
# User-Topic selection helpers
# ==========================================================
async def upsert_user_topic(
    db: AsyncSession,
    *,
    user_id: UUID,
    topic_id: UUID,
) -> models.UserTopic:
    # 토픽 존재 확인
    topic = await get_topic_by_id(db, topic_id)
    if topic is None:
        raise ValueError("topic_not_found")

    # 기존 링크 조회
    stmt = select(models.UserTopic).where(
        models.UserTopic.user_id == user_id,
        models.UserTopic.topic_id == topic_id,
    )
    result = await db.execute(stmt)
    link = result.scalars().first()

    if link is None:
        link = models.UserTopic(user_id=user_id, topic_id=topic_id)
        db.add(link)
    # 이미 존재하는 경우는 업데이트할 필드가 없으므로 그대로 반환

    await db.commit()
    return link


# ==========================================================
# Article helpers (Phase 5 - Feed API)
# ==========================================================
async def get_all_articles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    order_by_date: bool = True
) -> List[models.Article]:
    """
    모든 Article을 조회 (페이지네이션 지원)

    Args:
        db: Database session
        skip: 건너뛸 개수
        limit: 가져올 최대 개수
        order_by_date: True면 date DESC, False면 created_at DESC

    Returns:
        Article 목록
    """
    from sqlalchemy import desc

    stmt = select(models.Article).options(
        selectinload(models.Article.topic)
    )

    if order_by_date:
        stmt = stmt.order_by(desc(models.Article.date))
    else:
        stmt = stmt.order_by(desc(models.Article.created_at))

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_articles_by_user_topics(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> List[models.Article]:
    """
    사용자가 구독한 토픽들의 Article 조회

    Args:
        db: Database session
        user_id: 사용자 UUID
        skip: 건너뛸 개수
        limit: 가져올 최대 개수

    Returns:
        Article 목록 (날짜 내림차순)
    """
    from sqlalchemy import desc

    # 사용자가 구독한 토픽 ID 목록 조회
    user_topics_stmt = (
        select(models.UserTopic.topic_id)
        .where(models.UserTopic.user_id == user_id)
    )
    user_topics_result = await db.execute(user_topics_stmt)
    topic_ids = [row[0] for row in user_topics_result.all()]

    if not topic_ids:
        return []

    # 해당 토픽들의 Article 조회
    stmt = (
        select(models.Article)
        .options(selectinload(models.Article.topic))
        .where(models.Article.topic_id.in_(topic_ids))
        .order_by(desc(models.Article.date))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_articles_with_audio_for_topics(
    db: AsyncSession,
    topic_ids: List[UUID],
    start_date: date,
    end_date: date,
) -> List[Tuple[models.Article, models.Topic]]:
    """
    지정한 토픽들의 기사 중 날짜 범위에 속하며 오디오가 포함된 데이터를 조회합니다.
    """
    if not topic_ids:
        return []

    stmt = (
        select(models.Article, models.Topic)
        .join(models.Topic, models.Article.topic_id == models.Topic.id)
        .where(
            models.Article.topic_id.in_(topic_ids),
            models.Article.date >= start_date,
            models.Article.date <= end_date,
            models.Article.status == 'completed',
        )
        .order_by(models.Article.date.desc(), models.Article.created_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.all())


async def get_articles_by_topic(
    db: AsyncSession,
    topic_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> List[models.Article]:
    """
    특정 토픽의 Article 조회

    Args:
        db: Database session
        topic_id: 토픽 UUID
        skip: 건너뛸 개수
        limit: 가져올 최대 개수

    Returns:
        Article 목록 (날짜 내림차순)
    """
    from sqlalchemy import desc

    stmt = (
        select(models.Article)
        .options(selectinload(models.Article.topic))
        .where(models.Article.topic_id == topic_id)
        .order_by(desc(models.Article.date))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_article_by_id(
    db: AsyncSession,
    article_id: UUID
) -> Optional[models.Article]:
    """
    Article ID로 개별 Article 조회 (Article 상세 페이지용)

    Args:
        db: Database session
        article_id: Article UUID

    Returns:
        Article 또는 None
    """
    stmt = (
        select(models.Article)
        .options(selectinload(models.Article.topic))
        .where(models.Article.id == article_id)
    )

    result = await db.execute(stmt)
    return result.scalars().first()


async def get_topic_by_name(
    db: AsyncSession,
    topic_name: str
) -> Optional[models.Topic]:
    """
    Topic 이름으로 Topic 조회 (Topic Profile 페이지용)

    Args:
        db: Database session
        topic_name: Topic 이름 (예: "GOOGLE", "META")

    Returns:
        Topic 또는 None
    """
    stmt = (
        select(models.Topic)
        .where(models.Topic.name == topic_name)
        .options(
            selectinload(models.Topic.sources),
            selectinload(models.Topic.articles),
        )
    )

    result = await db.execute(stmt)
    return result.scalars().first()
