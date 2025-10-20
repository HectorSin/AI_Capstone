from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth, crud, schemas

router = APIRouter(
    tags=["Users"],
)

@router.get("/me", response_model=schemas.User)
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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_users_me(
    current_user=Depends(auth.get_current_user),
    db: AsyncSession = Depends(auth.get_db),
):
    user = await crud.get_user_by_id(db, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await crud.delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
