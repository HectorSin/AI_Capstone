from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app import schemas
from app import auth

router = APIRouter(
    tags=["Authentication"],
)

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(auth.get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(db: AsyncSession = Depends(auth.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # 소셜 로그인에서는 form_data 대신 소셜 토큰을 받아 유저를 확인하는 로직이 필요합니다.
    # 여기서는 이메일(username) 기반의 기본 예시를 보여줍니다.
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = auth.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}