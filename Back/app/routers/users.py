from datetime import time as dt_time
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas
from app.database import models

router = APIRouter(
    tags=["Users"],
)

@router.get(
    "/me",
    response_model=schemas.User,
    summary="내 프로필 조회",
    description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
)
async def read_users_me(
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    user = await crud.get_user_by_id(db, current_user.id)
    if user is None:
        return current_user
    return schemas.User(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        plan=schemas.PlanType(user.plan.value),
        difficulty_level=schemas.DifficultyLevel(user.difficulty_level.value),
        social_provider=schemas.SocialProviderType(user.social_provider.value),
        social_id=user.social_id,
        notification_time=user.notification_time,
        created_at=user.created_at,
        topics=[],
    )


@router.put(
    "/me",
    response_model=schemas.User,
    summary="내 프로필 수정",
    description="현재 로그인한 사용자의 프로필 정보(닉네임, 난이도 등)를 수정합니다.",
)
async def update_users_me(
    user_update: schemas.UserUpdate,
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    user = await crud.get_user_by_id(db, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 닉네임 변경 시 중복 확인
    if user_update.nickname and user_update.nickname != user.nickname:
        existing_nickname = await crud.get_user_by_nickname(db, nickname=user_update.nickname)
        if existing_nickname:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname is already in use.")

    # 업데이트할 데이터 준비
    update_data = {}

    if user_update.nickname is not None:
        update_data["nickname"] = user_update.nickname
    if user_update.difficulty_level is not None:
        update_data["difficulty_level"] = models.DifficultyLevel[user_update.difficulty_level.name]
    if user_update.plan is not None:
        update_data["plan"] = models.PlanType[user_update.plan.name]

    updated_user = await crud.update_user(db, user, update_data)

    return schemas.User(
        id=updated_user.id,
        email=updated_user.email,
        nickname=updated_user.nickname,
        plan=schemas.PlanType(updated_user.plan.value),
        difficulty_level=schemas.DifficultyLevel(updated_user.difficulty_level.value),
        social_provider=schemas.SocialProviderType(updated_user.social_provider.value),
        social_id=updated_user.social_id,
        notification_time=updated_user.notification_time,
        created_at=updated_user.created_at,
        topics=[],
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴",
    description="현재 로그인한 사용자의 계정을 삭제합니다.",
)
async def delete_users_me(
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    user = await crud.get_user_by_id(db, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await crud.delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _serialize_preference(pref) -> schemas.NotificationPreference:
    send_time = pref.send_time
    hour: Optional[int] = send_time.hour if send_time else None
    minute: Optional[int] = send_time.minute if send_time else None
    return schemas.NotificationPreference(
        id=pref.id,
        allowed=pref.allowed,
        time_enabled=pref.time_enabled,
        hour=hour,
        minute=minute,
        days_of_week=pref.days_of_week or [],
        prompted=pref.prompted,
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )


@router.get(
    "/me/notification-preference",
    response_model=schemas.NotificationPreference,
    summary="내 알림 설정 조회",
    description="현재 로그인한 사용자의 알림 수신 설정을 조회합니다.",
)
async def get_notification_preference(
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    pref = await crud.ensure_notification_preference(db, current_user.id)
    return _serialize_preference(pref)


@router.put(
    "/me/notification-preference",
    response_model=schemas.NotificationPreference,
    summary="내 알림 설정 수정",
    description="현재 로그인한 사용자의 알림 수신 설정을 업데이트합니다.",
)
async def update_notification_preference(
    payload: schemas.NotificationPreferenceUpdate,
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    pref = await crud.ensure_notification_preference(db, current_user.id)

    if payload.time_enabled:
        if payload.hour is None or payload.minute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hour and minute are required when time_enabled is true",
            )
        send_time_value = dt_time(hour=payload.hour, minute=payload.minute)
    else:
        send_time_value = None

    if payload.time_enabled and not payload.days_of_week:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="days_of_week cannot be empty when time_enabled is true",
        )

    sanitized_days = sorted({int(day) for day in payload.days_of_week})

    updated = await crud.update_notification_preference(
        db,
        pref,
        allowed=payload.allowed,
        time_enabled=payload.time_enabled,
        send_time_value=send_time_value,
        days_of_week=sanitized_days,
        prompted=payload.prompted,
    )

    return _serialize_preference(updated)


# ==========================================================
# 토픽 구독 관리
# ==========================================================
@router.get(
    "/me/topics",
    response_model=List[schemas.Topic],
    summary="내가 구독 중인 토픽 목록 조회",
    description="현재 로그인한 사용자가 구독 중인 모든 토픽 목록을 조회합니다.",
)
async def get_my_topics(
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    topics = await crud.list_topics_for_user(db, user_id=current_user.id)
    return topics


@router.post(
    "/me/topics/{topic_id}",
    response_model=schemas.UserTopicLink,
    status_code=status.HTTP_201_CREATED,
    summary="토픽 구독 추가",
    description="현재 로그인한 사용자의 구독 목록에 새로운 토픽을 추가합니다.",
)
async def add_topic_to_user(
    topic_id: UUID,
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    # 토픽 존재 여부 확인
    topic = await crud.get_topic_by_id(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    try:
        link = await crud.upsert_user_topic(db, user_id=current_user.id, topic_id=topic_id)
    except ValueError as e:
        if str(e) == "topic_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        raise

    return schemas.UserTopicLink(
        user_id=current_user.id,
        topic_id=topic_id,
        created_at=link.created_at,
    )


@router.delete(
    "/me/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="토픽 구독 취소",
    description="현재 로그인한 사용자의 구독 목록에서 토픽을 제거합니다.",
)
async def remove_topic_from_user(
    topic_id: UUID,
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    # UserTopic 링크 조회
    from sqlalchemy import select, delete
    stmt = select(models.UserTopic).where(
        models.UserTopic.user_id == current_user.id,
        models.UserTopic.topic_id == topic_id,
    )
    result = await db.execute(stmt)
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic subscription not found")

    # 링크 삭제
    delete_stmt = delete(models.UserTopic).where(
        models.UserTopic.user_id == current_user.id,
        models.UserTopic.topic_id == topic_id,
    )
    await db.execute(delete_stmt)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
