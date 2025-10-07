from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 환경 변수에서 DB 접속 정보 가져오기
DATABASE_URL = settings.database_url

# 비동기 엔진 생성
engine = create_async_engine(DATABASE_URL, echo=settings.debug)

# 비동기 세션 생성
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# 모델 클래스들이 상속받을 기본 클래스
Base = declarative_base()

# 데이터베이스 세션 의존성 함수
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()