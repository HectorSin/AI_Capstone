"""
팟캐스트 생성 서비스
Perplexity, Gemini, Clova를 통합하여 팟캐스트를 생성합니다.
"""
import logging
from typing import Dict, Any, Optional
import uuid

from app.services.ai import (
    PerplexityService,
    GeminiService,
    ClovaService,
    AIServiceConfig
)
from app.config import settings

logger = logging.getLogger(__name__)


class PodcastService:
    """팟캐스트 생성 통합 서비스"""
    
    def __init__(self):
        # AI 서비스 초기화
        self.perplexity = PerplexityService(
            AIServiceConfig(api_key=settings.perplexity_api_key)
        )
        self.gemini = GeminiService(
            AIServiceConfig(api_key=settings.google_api_key)
        )
        self.clova = ClovaService(
            AIServiceConfig(
                api_key="",  # Clova는 client_id, client_secret 사용
                client_id=settings.naver_clova_client_id,
                client_secret=settings.naver_clova_client_secret
            )
        )
    
    async def create_podcast(self, topic: str, keywords: list = None) -> Dict[str, Any]:
        """
        팟캐스트 생성 파이프라인
        1. Perplexity로 데이터 크롤링
        2. Gemini로 문서 생성
        3. Gemini로 대본 생성
        4. Clova로 TTS 생성
        
        Args:
            topic: 팟캐스트 주제
            keywords: 관련 키워드 목록
        
        Returns:
            생성된 팟캐스트 정보
        """
        try:
            logger.info(f"팟캐스트 생성 시작: {topic}")
            
            # 1. Perplexity로 데이터 크롤링
            logger.info("Step 1: 데이터 크롤링 (Perplexity)")
            crawled_data = await self.perplexity.crawl_topic(topic, keywords)
            
            # 2. Gemini로 문서 생성
            logger.info("Step 2: 문서 생성 (Gemini)")
            article = await self.gemini.generate_article(
                title=topic,
                content=crawled_data.get("data", {}).get("content", ""),
                sources=crawled_data.get("data", {}).get("sources", [])
            )
            
            # 3. Gemini로 대본 생성
            logger.info("Step 3: 대본 생성 (Gemini)")
            script = await self.gemini.generate_script(
                article_title=topic,
                article_content=article.get("data", {}).get("content", "")
            )
            
            # 4. Clova로 TTS 생성
            logger.info("Step 4: 음성 생성 (Clova)")
            audio = await self.clova.generate_podcast_audio(
                script=script.get("data", {}).get("content", "")
            )
            
            # 결과 정리
            result = {
                "podcast_id": str(uuid.uuid4()),
                "topic": topic,
                "keywords": keywords or [],
                "article": {
                    "title": topic,
                    "content": article.get("data", {}).get("content", "")
                },
                "script": script.get("data", {}).get("content", ""),
                "audio": {
                    "file": audio.get("data", {}).get("audio_file", ""),
                    "duration": audio.get("data", {}).get("duration", 0)
                },
                "status": "completed"
            }
            
            logger.info(f"팟캐스트 생성 완료: {result['podcast_id']}")
            return result
            
        except Exception as e:
            logger.error(f"팟캐스트 생성 실패: {e}")
            raise
    
    async def validate_all_services(self) -> Dict[str, bool]:
        """
        모든 AI 서비스의 설정 유효성을 검증합니다.
        
        Returns:
            각 서비스의 유효성 검증 결과
        """
        return {
            "perplexity": await self.perplexity.validate_config(),
            "gemini": await self.gemini.validate_config(),
            "clova": await self.clova.validate_config()
        }


# 전역 인스턴스
podcast_service = PodcastService()

