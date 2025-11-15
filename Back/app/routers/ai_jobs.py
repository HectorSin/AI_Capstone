"""
AI 작업 관리를 위한 API 엔드포인트
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db, AsyncSessionLocal
from app.database import models
from app import schemas
from app.auth import get_current_user
from app.services.topic_service import TopicService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/debug/perplexity", summary="Perplexity API 직접 테스트")
async def test_perplexity_direct():
    """Perplexity API를 직접 호출하여 테스트합니다."""
    from app.services.podcast_service import podcast_service
    from app.config import settings

    # API 키 확인
    api_key_status = "OK" if settings.perplexity_api_key and len(settings.perplexity_api_key) > 10 else "MISSING"

    try:
        # Perplexity 직접 호출
        result = await podcast_service.perplexity.crawl_topic("GOOGLE", ["AI"])

        return {
            "api_key_status": api_key_status,
            "api_key_prefix": settings.perplexity_api_key[:10] if settings.perplexity_api_key else None,
            "perplexity_result_type": str(type(result)),
            "perplexity_result_keys": list(result.keys()) if isinstance(result, dict) else None,
            "has_error": result.get("error") if isinstance(result, dict) else None,
            "has_data": "data" in result if isinstance(result, dict) else None,
            "data_type": str(type(result.get("data"))) if isinstance(result, dict) and "data" in result else None,
            "full_result": result
        }
    except Exception as e:
        return {
            "api_key_status": api_key_status,
            "error": str(e),
            "error_type": type(e).__name__
        }

# AI 팟캐스트 생성
# 1. 팟캐스트 생성 요청 POST -> perplexity 활용 데이터 크롤링 -> Gemini 활용 문서 생성 -> Gemini 활용 대본 생성 -> Clova 활용 TTS 생성 -> 팟캐스트 생성 완료

@router.post("/test", response_model=schemas.PodcastBatchCreateResponse, summary="AI 팟캐스트 생성 (테스트용)")
async def create_ai_podcast_test(
    podcast_data: schemas.PodcastCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    AI 팟캐스트를 생성합니다. (인증 없이 테스트용)

    테스트용 특징:
    - JSON 파일 저장 (검증용)
    - DB에는 저장하지 않음
    - 인증 불필요

    프로세스:
    1. Topic 찾기 또는 생성
    2. Perplexity로 기사 링크 수집
    3. 각 기사마다:
       - BeautifulSoup으로 원문 크롤링
       - Gemini로 난이도별 문서 생성 (beginner/intermediate/advanced)
       - Gemini로 난이도별 대본 생성
       - Clova로 난이도별 TTS 생성 (3개 오디오 파일)
    4. JSON 파일로 저장 (DB 저장 안 함)
    """
    from app.services.podcast_service import podcast_service

    try:
        # 1. Topic 찾기 또는 생성
        topic_id = await TopicService.get_or_create_topic(
            db=db,
            topic_name=podcast_data.topic,
            keywords=podcast_data.keywords
        )

        # 2. DB에서 이미 처리된 URL 조회 (중복 방지)
        from sqlalchemy import select
        stmt = select(models.Article.source_url).where(
            models.Article.topic_id == topic_id,
            models.Article.source_url.isnot(None)
        )
        result = await db.execute(stmt)
        existing_urls = set(row[0] for row in result.all())

        # 3. 여러 팟캐스트 생성 (JSON 파일 저장됨)
        articles_data = await podcast_service.create_podcasts_for_topic(
            topic=podcast_data.topic,
            keywords=podcast_data.keywords,
            processed_urls=existing_urls
        )

        logger.info(f"테스트용 API: {len(articles_data)}개 Article 생성 완료 (JSON 파일로 저장됨, DB 저장 안 함)")

        # 4. 응답 생성 (DB 저장 없이 바로 응답)
        successful = sum(1 for a in articles_data if a['status'] == 'completed')
        failed = sum(1 for a in articles_data if a['status'] == 'failed')

        article_responses = []
        for a in articles_data:
            audio_data = a.get('audio_data', {})

            # 테스트용이므로 article_id는 임시 UUID 사용
            from uuid import uuid4
            article_responses.append(
                schemas.ArticlePodcastResponse(
                    article_id=uuid4(),  # 임시 ID (DB에 저장 안 함)
                    title=a['title'],
                    date=a['date'],
                    source_url=a.get('source_url'),
                    status=a['status'],
                    audio_beginner=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('beginner', {}).get('audio_file'),
                        duration=audio_data.get('beginner', {}).get('duration')
                    ) if audio_data.get('beginner') else None,
                    audio_intermediate=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('intermediate', {}).get('audio_file'),
                        duration=audio_data.get('intermediate', {}).get('duration')
                    ) if audio_data.get('intermediate') else None,
                    audio_advanced=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('advanced', {}).get('audio_file'),
                        duration=audio_data.get('advanced', {}).get('duration')
                    ) if audio_data.get('advanced') else None,
                    error_message=a.get('error_message')
                )
            )

        return schemas.PodcastBatchCreateResponse(
            topic=podcast_data.topic,
            topic_id=topic_id,
            keywords=podcast_data.keywords or [],
            total_crawled=len(articles_data),
            successful=successful,
            failed=failed,
            processing=0,
            articles=article_responses,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"AI 팟캐스트 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=schemas.PodcastBatchCreateResponse, summary="AI 팟캐스트 생성 (배치)")
async def create_ai_podcast(
    podcast_data: schemas.PodcastCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 팟캐스트를 생성합니다. (여러 기사를 각각 난이도별로 생성)

    프로세스:
    1. Topic 찾기 또는 생성
    2. Perplexity로 기사 링크 수집
    3. 각 기사마다:
       - BeautifulSoup으로 원문 크롤링
       - Gemini로 난이도별 문서 생성 (beginner/intermediate/advanced)
       - Gemini로 난이도별 대본 생성
       - Clova로 난이도별 TTS 생성 (3개 오디오 파일)
    4. DB에 Article 레코드 저장
    """
    from app.services.podcast_service import podcast_service

    try:
        # 1. Topic 찾기 또는 생성
        topic_id = await TopicService.get_or_create_topic(
            db=db,
            topic_name=podcast_data.topic,
            keywords=podcast_data.keywords
        )

        # 2. DB에서 이미 처리된 URL 조회 (중복 방지)
        from sqlalchemy import select
        stmt = select(models.Article.source_url).where(
            models.Article.topic_id == topic_id,
            models.Article.source_url.isnot(None)
        )
        result = await db.execute(stmt)
        existing_urls = set(row[0] for row in result.all())

        # 3. 여러 팟캐스트 생성
        articles_data = await podcast_service.create_podcasts_for_topic(
            topic=podcast_data.topic,
            keywords=podcast_data.keywords,
            processed_urls=existing_urls
        )

        # 4. DB에 저장
        db_articles = []
        for article_data in articles_data:
            try:
                # date 파싱
                article_date_str = article_data.get('date', datetime.now().strftime('%Y-%m-%d'))
                try:
                    article_date = datetime.strptime(article_date_str, '%Y-%m-%d').date()
                except:
                    article_date = datetime.now().date()

                db_article = models.Article(
                    topic_id=topic_id,
                    title=article_data['title'],
                    date=article_date,
                    source_url=article_data.get('source_url'),
                    status=article_data['status'],
                    crawled_data=article_data.get('crawled_data'),
                    article_data=article_data.get('article_data'),
                    script_data=article_data.get('script_data'),
                    audio_data=article_data.get('audio_data'),
                    storage_path=article_data.get('storage_path'),
                    error_message=article_data.get('error_message'),
                    completed_at=datetime.now() if article_data['status'] == 'completed' else None
                )
                db.add(db_article)
                db_articles.append(db_article)
            except Exception as e:
                logger.error(f"Article DB 저장 실패: {e}")
                continue

        await db.commit()

        # 5. 각 article refresh하여 ID 가져오기
        for article in db_articles:
            await db.refresh(article)

        # 6. 응답 생성
        successful = sum(1 for a in articles_data if a['status'] == 'completed')
        failed = sum(1 for a in articles_data if a['status'] == 'failed')

        article_responses = []
        for i, a in enumerate(articles_data):
            if i >= len(db_articles):
                continue

            audio_data = a.get('audio_data', {})
            article_responses.append(
                schemas.ArticlePodcastResponse(
                    article_id=db_articles[i].id,
                    title=a['title'],
                    date=a['date'],
                    source_url=a.get('source_url'),
                    status=a['status'],
                    audio_beginner=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('beginner', {}).get('audio_file'),
                        duration=audio_data.get('beginner', {}).get('duration')
                    ) if audio_data.get('beginner') else None,
                    audio_intermediate=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('intermediate', {}).get('audio_file'),
                        duration=audio_data.get('intermediate', {}).get('duration')
                    ) if audio_data.get('intermediate') else None,
                    audio_advanced=schemas.DifficultyAudioInfo(
                        audio_file=audio_data.get('advanced', {}).get('audio_file'),
                        duration=audio_data.get('advanced', {}).get('duration')
                    ) if audio_data.get('advanced') else None,
                    error_message=a.get('error_message')
                )
            )

        return schemas.PodcastBatchCreateResponse(
            topic=podcast_data.topic,
            topic_id=topic_id,
            keywords=podcast_data.keywords or [],
            total_crawled=len(articles_data),
            successful=successful,
            failed=failed,
            processing=0,
            articles=article_responses,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"AI 팟캐스트 생성 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/", response_model=AIJob, summary="AI 작업 생성")
# async def create_ai_job(
#     job_data: AIJobCreate,
#     background_tasks: BackgroundTasks,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     새로운 AI 작업을 생성합니다.
#     """
#     try:
#         # 사용자 ID 설정
#         job_data.user_id = current_user.user_id
        
#         # AI 작업 서비스 생성
#         job_service = AIJobService(db)
        
#         # 작업 생성
#         job = await job_service.create_job(job_data)
        
#         # 백그라운드에서 새 세션으로 작업 시작
#         async def start_job_bg(job_id: int):
#             async with AsyncSessionLocal() as session:
#                 from app.services.ai_job_service import AIJobService as _Svc
#                 svc = _Svc(session)
#                 await svc.start_job(job_id)

#         background_tasks.add_task(start_job_bg, job.job_id)
        
#         logger.info(f"AI 작업 생성됨: {job.job_id} by user {current_user.user_id}")
#         # 응답을 명시적으로 직렬화하여 필수 필드 보장
#         return {
#             "job_id": int(job.job_id) if job.job_id is not None else 0,
#             "job_type": job.job_type.value if hasattr(job.job_type, "value") else str(job.job_type),
#             "user_id": int(job.user_id),
#             "topic_id": job.topic_id,
#             "input_data": job.input_data or {},
#             "priority": int(job.priority or 0),
#             "status": job.status.value if hasattr(job.status, "value") else str(job.status),
#             "progress": int(job.progress or 0),
#             "result_data": job.result_data,
#             "error_message": job.error_message,
#             "created_at": job.created_at,
#             "updated_at": job.updated_at,
#             "started_at": job.started_at,
#             "completed_at": job.completed_at,
#         }
        
#     except Exception as e:
#         logger.error(f"AI 작업 생성 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/{job_id}", response_model=AIJob, summary="AI 작업 조회")
# async def get_ai_job(
#     job_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     특정 AI 작업의 상세 정보를 조회합니다.
#     """
#     try:
#         job_service = AIJobService(db)
#         job = await job_service.get_job(job_id)
        
#         if not job:
#             raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
#         # 사용자 권한 확인
#         if job.user_id != current_user.user_id:
#             raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
#         return job
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"AI 작업 조회 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/", response_model=List[AIJob], summary="AI 작업 목록 조회")
# async def get_ai_jobs(
#     status: Optional[JobStatus] = Query(None, description="상태 필터"),
#     job_type: Optional[JobType] = Query(None, description="작업 타입 필터"),
#     limit: int = Query(50, ge=1, le=100, description="조회 개수 제한"),
#     offset: int = Query(0, ge=0, description="오프셋"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     사용자의 AI 작업 목록을 조회합니다.
#     """
#     try:
#         job_service = AIJobService(db)
#         jobs = await job_service.get_user_jobs(
#             user_id=current_user.user_id,
#             status=status,
#             job_type=job_type,
#             limit=limit,
#             offset=offset
#         )
        
#         return jobs
        
#     except Exception as e:
#         logger.error(f"AI 작업 목록 조회 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.put("/{job_id}", response_model=AIJob, summary="AI 작업 상태 업데이트")
# async def update_ai_job(
#     job_id: int,
#     job_update: AIJobUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     AI 작업의 상태를 업데이트합니다.
#     """
#     try:
#         job_service = AIJobService(db)
        
#         # 작업 존재 및 권한 확인
#         job = await job_service.get_job(job_id)
#         if not job:
#             raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
#         if job.user_id != current_user.user_id:
#             raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
#         # 상태 업데이트
#         updated_job = await job_service.update_job_status(
#             job_id=job_id,
#             status=job_update.status,
#             progress=job_update.progress,
#             result_data=job_update.result_data,
#             error_message=job_update.error_message
#         )
        
#         return updated_job
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"AI 작업 상태 업데이트 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/{job_id}/cancel", summary="AI 작업 취소")
# async def cancel_ai_job(
#     job_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     AI 작업을 취소합니다.
#     """
#     try:
#         job_service = AIJobService(db)
        
#         # 작업 존재 및 권한 확인
#         job = await job_service.get_job(job_id)
#         if not job:
#             raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
#         if job.user_id != current_user.user_id:
#             raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
#         # 작업 취소
#         success = await job_service.cancel_job(job_id)
        
#         if not success:
#             raise HTTPException(status_code=400, detail="작업을 취소할 수 없습니다")
        
#         return {"message": "작업이 취소되었습니다"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"AI 작업 취소 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/{job_id}/logs", summary="AI 작업 로그 조회")
# async def get_ai_job_logs(
#     job_id: int,
#     limit: int = Query(100, ge=1, le=1000, description="조회 개수 제한"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     AI 작업의 로그를 조회합니다.
#     """
#     try:
#         job_service = AIJobService(db)
        
#         # 작업 존재 및 권한 확인
#         job = await job_service.get_job(job_id)
#         if not job:
#             raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
#         if job.user_id != current_user.user_id:
#             raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
#         # 로그 조회
#         logs = await job_service.get_job_logs(job_id, limit)
        
#         return logs
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"AI 작업 로그 조회 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# """Airflow 관련 엔드포인트는 미사용으로 제거되었습니다."""
