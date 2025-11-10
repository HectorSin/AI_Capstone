from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base, AsyncSessionLocal
from app.database.redis_client import redis_client
from app.config import settings
from app.database import models  # 모델 import 추가 - 테이블 생성을 위해 필요
from app.routers import users, auth, cache, topics, ai_jobs
from app import crud, schemas
import logging

# 로깅 설정
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# DB 테이블 생성을 위한 코드
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 초기 토픽 데이터 생성
async def seed_initial_topics():
    """서버 시작 시 기본 토픽 데이터를 생성합니다."""
    initial_topics = [
        {"name": "GOOGLE", "summary": "구글"},
        {"name": "AMAZON", "summary": "아마존"},
        {"name": "OPENAI", "summary": "오픈AI"},
        {"name": "META", "summary": "메타"},
        {"name": "ANTHROPIC", "summary": "앤트로픽"},
        {"name": "PERPLEXITY", "summary": "퍼플렉시티"},
        {"name": "GROK", "summary": "그록"},
        {"name": "MICROSOFT", "summary": "마이크로소프트"},
    ]

    async with AsyncSessionLocal() as db:
        try:
            for topic_data in initial_topics:
                # 이미 존재하는지 확인
                existing_topics = await crud.list_all_topics(db)
                existing_names = {t.name for t in existing_topics}

                if topic_data["name"] not in existing_names:
                    topic_create = schemas.TopicCreate(
                        name=topic_data["name"],
                        type=schemas.TopicType.company,
                        summary=topic_data["summary"],
                        image_uri="https://via.placeholder.com/150",  # 임시 이미지
                        keywords=[],
                        sources=[]
                    )
                    await crud.create_topic(db, topic_create)
                    logger.info(f"토픽 생성: {topic_data['name']}")

            await db.commit()
            logger.info("초기 토픽 데이터 생성 완료")
        except Exception as e:
            await db.rollback()
            logger.error(f"초기 토픽 데이터 생성 실패: {e}")

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

    # 초기 토픽 데이터 생성
    await seed_initial_topics()

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

# ai_jobs 라우터 포함
app.include_router(
    ai_jobs.router,
    prefix="/ai_jobs",
    tags=["AI Jobs"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to our API server!"}
