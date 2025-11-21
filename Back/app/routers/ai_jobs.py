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
from app.auth import get_current_user, get_current_admin_user
from app.services.topic_service import TopicService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/debug/perplexity", summary="Perplexity API 직접 테스트")
async def test_perplexity_direct(topic: str = "GOOGLE"):
    """Perplexity API를 직접 호출하여 테스트합니다."""
    from app.services.podcast_service import podcast_service
    from app.config import settings
    import httpx

    # API 키 확인
    api_key_status = "OK" if settings.perplexity_api_key and len(settings.perplexity_api_key) > 10 else "MISSING"

    try:
        # 1. Perplexity 직접 호출
        result = await podcast_service.perplexity.crawl_topic(topic, ["AI"])

        # 2. 원본 Perplexity API 호출 (파싱 없이)
        from app.services.ai.config_manager import ConfigManager, CompanyInfoManager, PromptManager
        config_manager = ConfigManager()
        company_manager = CompanyInfoManager(config_manager)
        prompt_manager = PromptManager(config_manager)

        company_info = company_manager.get_company_info(topic)
        source_preferences = company_manager.get_source_preferences()
        prompt = prompt_manager.create_tech_news_prompt(topic, company_info, source_preferences)

        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "search_domain_filter": company_info["sources"],
            "search_recency_filter": "week",
            "return_citations": True,
            "max_tokens": 4000
        }

        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            raw_response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )
            raw_content = raw_response.json()["choices"][0]['message']['content']

        return {
            "api_key_status": api_key_status,
            "api_key_prefix": settings.perplexity_api_key[:10] if settings.perplexity_api_key else None,
            "parsed_result": result,
            "raw_perplexity_response": raw_content[:2000],  # 처음 2000자
            "prompt_preview": prompt[:500]  # 프롬프트 미리보기
        }
    except Exception as e:
        import traceback
        return {
            "api_key_status": api_key_status,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

# AI 팟캐스트 생성
# 1. 팟캐스트 생성 요청 POST -> perplexity 활용 데이터 크롤링 -> Gemini 활용 문서 생성 -> Gemini 활용 대본 생성 -> Clova 활용 TTS 생성 -> 팟캐스트 생성 완료

# TODO: 현재 만들어진 코드를 보니 /test는 필요 없어 보입니다. 우선 주석처리한 후 테스트 5단계 진행해보시고 이상 없으면 제거 해주세요!
@router.post("/test", response_model=schemas.PodcastBatchCreateResponse, summary="AI 팟캐스트 생성 (테스트용)")
async def create_ai_podcast_test(  # TODO: 비동기 처리
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

        # 3. 여러 팟캐스트 생성 (JSON 파일 저장됨) & Perplexity 크롤링 포함
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

            # TODO: 지금 테스트 API인데 DB에 데이터가 저장되는 로직이 들어가 있는건가요? 있다면 빼주세요 & UUID 왜 있는거죠? 필요 없는거면 지워주세요
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
    # TODO: 테스트 후 관리자 인증 활성화
    # current_admin: models.AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 팟캐스트를 생성합니다. (여러 기사를 각각 난이도별로 생성)

    **임시**: 관리자 인증 비활성화 (테스트용)

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

                # Extract summary and content from article_data or crawled_data
                summary = ""
                content = ""
                
                # Try to get from article_data first (intermediate level as default)
                if article_data.get('article_data'):
                    intermediate_article = article_data['article_data'].get('intermediate', {})
                    summary = intermediate_article.get('summary', '')
                    content = intermediate_article.get('content', '')
                
                # Fallback to crawled_data if article_data doesn't have content
                if not content and article_data.get('crawled_data'):
                    crawled = article_data['crawled_data']
                    summary = crawled.get('title', article_data['title'])[:500]  # Limit summary length
                    content = crawled.get('text', '')[:5000]  # Limit content length
                
                # Final fallback to title if still empty
                if not summary:
                    summary = article_data['title']
                if not content:
                    content = f"Article: {article_data['title']}"
                
                db_article = models.Article(
                    topic_id=topic_id,
                    title=article_data['title'],
                    summary=summary,
                    content=content,
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
                logger.error(f"Article DB 저장 실패: {e}", exc_info=True)
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


@router.post("/test/info-graphic", summary="인포그래픽 생성 (테스트)")
async def create_infographic_test(request: schemas.InfographicRequest):
    """
    테스트용 API로 정해진 location에 pdf 파일 생성
    input: 대본
    output: 인포그래픽 PDF 파일 경로
    
    과정:
    LLM [인포그래픽에 들어갈 json 데이터 생성] -> HTML로 변환 -> PDF로 변환
    """
    from app.services.infographic_service import infographic_service
    import os
    from datetime import datetime
    
    try:
        # 1. LLM을 통한 데이터 생성
        logger.info("Generating infographic data from script...")
        infographic_data = await infographic_service.generate_infographic_json(request.script)
        
        # 2. HTML 변환
        logger.info("Converting data to HTML...")
        html_content = infographic_service.generate_html(infographic_data)
        
        # 3. PDF 생성
        # 저장 경로 설정 (환경 변수에서 로드)
        output_dir = settings.infographic_output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"infographic_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        logger.info(f"Generating PDF at {output_path}...")
        success = infographic_service.generate_pdf(html_content, output_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="PDF generation failed")
            
        return {
            "status": "success",
            "message": "Infographic generated successfully",
            "file_path": os.path.abspath(output_path),
            "data": infographic_data
        }
        
    except Exception as e:
        logger.error(f"Infographic generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/info-graphic", summary="인포그래픽 생성 (DB 기반)")
async def create_infographic_from_article(
    request: schemas.InfographicFromArticleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    DB에 저장된 Article의 script_data를 사용하여 인포그래픽 생성
    
    팟캐스트 생성 시 Perplexity로 수집된 데이터가 DB에 저장되어 있으며,
    해당 데이터를 활용하여 인포그래픽을 생성합니다.
    
    input: article_id, difficulty_level (optional)
    output: 인포그래픽 PDF 파일 경로
    
    과정:
    1. DB에서 Article 조회
    2. script_data에서 해당 난이도의 대본 추출
    3. LLM [인포그래픽에 들어갈 json 데이터 생성] -> HTML로 변환 -> PDF로 변환
    """
    from app.services.infographic_service import infographic_service
    from sqlalchemy import select
    import os
    from datetime import datetime
    
    try:
        # 1. DB에서 Article 조회
        logger.info(f"Fetching article {request.article_id} from database...")
        stmt = select(models.Article).where(models.Article.id == request.article_id)
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise HTTPException(
                status_code=404, 
                detail=f"Article with id {request.article_id} not found"
            )
        
        # 2. script_data 확인
        if not article.script_data:
            raise HTTPException(
                status_code=400,
                detail="Article does not have script data. Please generate podcast first."
            )
        
        # 3. 난이도별 대본 추출
        difficulty = request.difficulty_level.value
        script_for_difficulty = article.script_data.get(difficulty)
        
        # Fallback: 요청한 난이도가 없으면 intermediate -> beginner -> advanced 순으로 시도
        if not script_for_difficulty:
            logger.warning(f"Difficulty '{difficulty}' not found, trying fallback...")
            for fallback_level in ["intermediate", "beginner", "advanced"]:
                script_for_difficulty = article.script_data.get(fallback_level)
                if script_for_difficulty:
                    logger.info(f"Using fallback difficulty: {fallback_level}")
                    difficulty = fallback_level
                    break
        
        if not script_for_difficulty:
            raise HTTPException(
                status_code=400,
                detail="No valid script data found in any difficulty level"
            )
        
        # 4. 대본 텍스트 추출 (content 필드 또는 dialogues 조합)
        script_text = script_for_difficulty.get("content", "")
        
        # content가 없으면 dialogues에서 조합
        if not script_text and script_for_difficulty.get("dialogues"):
            dialogues = script_for_difficulty.get("dialogues", [])
            script_text = "\n\n".join([
                f"{d.get('speaker', 'Unknown')}: {d.get('text', '')}"
                for d in dialogues
            ])
        
        if not script_text:
            raise HTTPException(
                status_code=400,
                detail=f"Script content is empty for difficulty '{difficulty}'"
            )
        
        logger.info(f"Extracted script (length: {len(script_text)}) from difficulty: {difficulty}")
        
        # 5. LLM을 통한 인포그래픽 데이터 생성
        logger.info("Generating infographic data from script...")
        infographic_data = await infographic_service.generate_infographic_json(script_text)
        
        # 6. HTML 변환
        logger.info("Converting data to HTML...")
        html_content = infographic_service.generate_html(infographic_data)
        
        # 7. PDF 생성
        output_dir = settings.infographic_output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"infographic_{article.id}_{difficulty}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        logger.info(f"Generating PDF at {output_path}...")
        success = infographic_service.generate_pdf(html_content, output_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="PDF generation failed")
            
        return {
            "status": "success",
            "message": "Infographic generated successfully from database",
            "article_id": str(article.id),
            "article_title": article.title,
            "difficulty_level": difficulty,
            "file_path": os.path.abspath(output_path),
            "data": infographic_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Infographic generation from article failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

