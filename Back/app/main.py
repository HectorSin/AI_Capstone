from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base
from app.database.redis_client import redis_client
from app.config import settings
from app.routers import users, auth, cache, topics
import logging

# 로깅 설정
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# DB 테이블 생성을 위한 코드
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# FastAPI 앱 생성
app = FastAPI(
    title="AI Podcast Generator API",
    description="AI가 URL을 분석하여 팟캐스트를 생성하는 API",
    version="1.0.0",
    debug=settings.debug
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI 앱이 시작될 때 실행
@app.on_event("startup")
async def on_startup():
    logger.info("애플리케이션 시작 중...")
    
    # 데이터베이스 테이블 생성
    await create_tables()
    logger.info("데이터베이스 테이블 생성 완료")
    
    # Redis 연결 확인
    if redis_client.is_connected():
        logger.info("Redis 연결 성공")
    else:
        logger.warning("Redis 연결 실패 - 캐시 기능이 제한될 수 있습니다")
    
    logger.info("애플리케이션 시작 완료")

# FastAPI 앱이 종료될 때 실행
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("애플리케이션 종료 중...")
    logger.info("애플리케이션 종료 완료")

# users.py에 정의된 API들을 메인 앱에 포함
app.include_router(
    users.router,
    prefix="/users", # URL 경로 앞에 /users 를 붙여줌
    tags=["Users"],   # API 문서에서 'users' 그룹으로 묶어줌
)

# auth 라우터 포함
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# cache 라우터 포함
app.include_router(
    cache.router,
    prefix="/cache",
    tags=["Cache & Redis"],
)

# topics 라우터 포함
app.include_router(
    topics.router,
    tags=["Topics"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to our API server!"}
