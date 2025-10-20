from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app import auth

router = APIRouter(
    tags=["Users"],
)

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    # get_current_user 함수가 토큰을 검증하고 user 객체를 반환해줍니다.
    return current_user
