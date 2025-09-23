from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 실제 DB 접속 정보 (사용자명, 비밀번호, 호스트, DB이름)
DATABASE_URL = "postgresql+asyncpg://postgres:kkang15634@127.0.0.1:5432/my_project_db"

# 비동기 엔진 생성
engine = create_async_engine(DATABASE_URL, echo=True)

# 비동기 세션 생성
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# 모델 클래스들이 상속받을 기본 클래스
Base = declarative_base()