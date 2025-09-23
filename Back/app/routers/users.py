from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import database

router = APIRouter()

# DB 세션을 얻기 위한 함수
async def get_db():
    async with database.AsyncSessionLocal() as session:
        yield session

@router.post("/", response_model=schemas.User)
async def create_user_api(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)