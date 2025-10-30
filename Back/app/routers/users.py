from datetime import time as dt_time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas

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
        social_provider=schemas.SocialProviderType(user.social_provider.value),
        social_id=user.social_id,
        notification_time=user.notification_time,
        created_at=user.created_at,
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
