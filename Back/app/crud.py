from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models
import schemas

# --- User CRUD ---
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    db_user = models.User(
        email=user.email,
        nickname=user.nickname,
        social_id=user.social_id,
        provider=user.provider
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- AnalysisTopic CRUD ---
async def create_topic_for_user(db: AsyncSession, topic: schemas.AnalysisTopicCreate, user_id: int):
    db_topic = models.AnalysisTopic(**topic.dict(), user_id=user_id)
    db.add(db_topic)
    await db.commit()
    await db.refresh(db_topic)
    return db_topic