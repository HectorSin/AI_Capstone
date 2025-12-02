from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database.database import engine, Base, AsyncSessionLocal
from app.database.redis_client import redis_client
from app.config import settings
from app.database import models  # 모델 import 추가 - 테이블 생성을 위해 필요
from app.routers import users, auth, cache, topics, ai_jobs, articles, podcasts
from app.routers.admin import dashboard as admin_dashboard, topics as admin_topics, podcasts as admin_podcasts
from app import crud, schemas
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# 이미지 저장 디렉토리 설정
IMAGES_DIR = Path("/app/database/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# DB 테이블 생성을 위한 코드
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 초기 토픽 데이터 생성
async def seed_initial_topics():
    """서버 시작 시 기본 토픽 데이터를 생성합니다."""
    initial_topics = [
        {"name": "GOOGLE", "summary": "구글 - 검색 엔진, 클라우드, AI 기술 선도 기업"},
        {"name": "AMAZON", "summary": "아마존 - 전자상거래, AWS 클라우드 서비스"},
        {"name": "OPENAI", "summary": "오픈AI - ChatGPT, GPT 모델 개발"},
        {"name": "META", "summary": "메타 - Facebook, Instagram, VR/AR 기술"},
        {"name": "ANTHROPIC", "summary": "앤트로픽 - Claude AI 개발"},
        {"name": "PERPLEXITY", "summary": "퍼플렉시티 - AI 기반 검색 엔진"},
        {"name": "TESLA", "summary": "테슬라 - 전기차, 자율주행, 청정에너지"},
        {"name": "MICROSOFT", "summary": "마이크로소프트 - Windows, Azure, Office 제품군"},
    ]

    async with AsyncSessionLocal() as db:
        # 기존 토픽 목록을 한 번만 조회
        try:
            existing_topics = await crud.list_all_topics(db)
            existing_names = {t.name for t in existing_topics}
        except Exception as e:
            logger.error(f"기존 토픽 목록 조회 실패: {e}")
            existing_names = set()

        created_count = 0
        failed_count = 0

        # 각 토픽을 개별적으로 처리 (하나가 실패해도 나머지는 계속 시도)
        for topic_data in initial_topics:
            try:
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
                    logger.info(f"✓ 토픽 생성 성공: {topic_data['name']}")
                    created_count += 1
                    existing_names.add(topic_data["name"])  # 생성된 토픽을 set에 추가
                else:
                    logger.debug(f"○ 토픽 이미 존재: {topic_data['name']}")
            except Exception as e:
                logger.error(f"✗ 토픽 생성 실패: {topic_data['name']} - {e}")
                failed_count += 1

        logger.info(f"초기 토픽 데이터 생성 완료 (새로 생성: {created_count}개, 실패: {failed_count}개, 기존: {len(existing_names) - created_count}개)")

# FastAPI 앱 생성
app = FastAPI(
    title="AI Podcast Generator API",
    description="AI가 URL을 분석하여 팟캐스트를 생성하는 API",
    version="1.0.0",
    debug=settings.debug,
    redirect_slashes=False  # trailing slash 자동 리디렉트 비활성화
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

# API 라우터 포함
# ==========================================================
# 기존 라우터
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cache.router, prefix="/cache", tags=["Cache & Redis"])
app.include_router(topics.router, tags=["Topics"])
app.include_router(ai_jobs.router, prefix="/ai_jobs", tags=["AI Jobs"])
app.include_router(articles.router, tags=["Articles"])  # Phase 5: Article 피드 API
app.include_router(podcasts.router)

# 관리자 페이지용 API 라우터
# ----------------------------------------------------------
admin_router = APIRouter()
admin_router.include_router(admin_dashboard.router, prefix="/dashboard", tags=["Admin Dashboard"])
admin_router.include_router(admin_topics.router, prefix="/topics", tags=["Admin Topics"])
admin_router.include_router(admin_podcasts.router, prefix="/podcasts", tags=["Admin Podcasts"])

app.include_router(admin_router, prefix="/api/v1/admin")
# ==========================================================

# 정적 파일 제공 (이미지)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


@app.get("/")
def read_root():
    return {"message": "Welcome to our API server!"}
