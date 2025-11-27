"""
팟캐스트 생성 서비스
Perplexity, Gemini, Clova를 통합하여 팟캐스트를 생성합니다.
"""
import logging
import os
import json
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import threading

from app.services.ai import (
    PerplexityService,
    GeminiService,
    ClovaService,
    AIServiceConfig
)
from app.services.crawler_service import WebCrawlerService
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
        self.crawler = WebCrawlerService()
        
        # 저장 경로 설정 (Docker 볼륨 마운트 경로)
        self.base_storage_path = "/app/podcasts"
        self._ensure_storage_directory()
        
        # ID 카운터 초기화
        self._id_counter = 0
        self._id_lock = threading.Lock()
        self._load_last_id()
    
    def _load_last_id(self):
        """마지막 ID를 로드하여 연속성 보장"""
        try:
            id_file = os.path.join(self.base_storage_path, "last_id.txt")
            if os.path.exists(id_file):
                with open(id_file, 'r') as f:
                    self._id_counter = int(f.read().strip())
                logger.info(f"마지막 ID 로드: {self._id_counter}")
            else:
                self._id_counter = 0
                logger.info("ID 카운터 초기화: 0")
        except Exception as e:
            logger.error(f"ID 로드 실패: {e}")
            self._id_counter = 0
    
    def _save_last_id(self):
        """현재 ID를 저장"""
        try:
            id_file = os.path.join(self.base_storage_path, "last_id.txt")
            with open(id_file, 'w') as f:
                f.write(str(self._id_counter))
        except Exception as e:
            logger.error(f"ID 저장 실패: {e}")
    
    def _generate_podcast_id(self) -> str:
        """새로운 팟캐스트 ID 생성 (5자리 숫자)"""
        with self._id_lock:
            self._id_counter += 1
            podcast_id = f"{self._id_counter:05d}"  # 5자리로 패딩
            self._save_last_id()
            logger.info(f"새 팟캐스트 ID 생성: {podcast_id}")
            return podcast_id
    
    def _ensure_storage_directory(self):
        """저장 디렉토리가 존재하는지 확인하고 생성"""
        try:
            if not os.path.exists(self.base_storage_path):
                os.makedirs(self.base_storage_path, mode=0o755, exist_ok=True)
                logger.info(f"저장 디렉토리 생성: {self.base_storage_path}")
            else:
                logger.info(f"저장 디렉토리 이미 존재: {self.base_storage_path}")
        except Exception as e:
            logger.error(f"저장 디렉토리 생성 실패: {e}")
            # 실패해도 계속 진행하도록 예외를 다시 발생시키지 않음
    
    def _get_podcast_directory(self, podcast_id: str) -> str:
        """팟캐스트별 디렉토리 경로 반환"""
        return os.path.join(self.base_storage_path, podcast_id)
    
    def _create_podcast_directory(self, podcast_id: str) -> str:
        """팟캐스트별 디렉토리 생성"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        try:
            # 부모 디렉토리도 함께 생성
            os.makedirs(podcast_dir, mode=0o755, exist_ok=True)
            logger.info(f"팟캐스트 디렉토리 생성: {podcast_dir}")
            return podcast_dir
        except Exception as e:
            logger.error(f"팟캐스트 디렉토리 생성 실패: {e}")
            # 디렉토리 생성 실패 시에도 계속 진행
            return podcast_dir
    
    def _save_perplexity_urls(self, podcast_id: str, perplexity_data: Dict[str, Any]) -> str:
        """Perplexity에서 수집한 URL 데이터 저장"""
        podcast_dir = self._create_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "01_perplexity_urls.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(perplexity_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Perplexity URL 데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Perplexity URL 데이터 저장 실패: {e}")
            raise

    def _save_crawled_data(self, podcast_id: str, crawled_data: Dict[str, Any]) -> str:
        """BeautifulSoup으로 크롤링된 원문 데이터 저장"""
        podcast_dir = self._create_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "02_crawled_data.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(crawled_data, f, ensure_ascii=False, indent=2)
            logger.info(f"크롤링 원문 데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"크롤링 원문 데이터 저장 실패: {e}")
            raise
    
    def _save_article(self, podcast_id: str, article: Dict[str, Any]) -> str:
        """생성된 문서 저장"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "03_article.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=2)
            logger.info(f"문서 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            raise
    
    def _save_script(self, podcast_id: str, script: Dict[str, Any]) -> str:
        """생성된 대본 저장"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "04_script.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            logger.info(f"대본 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"대본 저장 실패: {e}")
            raise
    
    def _save_audio(self, podcast_id: str, audio: Dict[str, Any]) -> str:
        """생성된 음성 파일 정보 저장"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "05_audio.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(audio, f, ensure_ascii=False, indent=2)
            logger.info(f"음성 정보 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"음성 정보 저장 실패: {e}")
            raise
    
    def _save_metadata(self, podcast_id: str, metadata: Dict[str, Any]) -> str:
        """팟캐스트 메타데이터 저장"""
        # 디렉토리 생성 보장
        podcast_dir = self._create_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "00_metadata.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"메타데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
            raise
    
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
            # 팟캐스트 ID 생성 (5자리 숫자)
            podcast_id = self._generate_podcast_id()
            logger.info(f"팟캐스트 생성 시작: {topic} (ID: {podcast_id})")
            
            # 메타데이터 생성 및 저장
            metadata = {
                "podcast_id": podcast_id,
                "topic": topic,
                "keywords": keywords or [],
                "created_at": datetime.now().isoformat(),
                "status": "processing",
                "steps": {
                    "perplexity_crawling": {"status": "pending", "started_at": None, "completed_at": None},
                    "beautifulsoup_crawling": {"status": "pending", "started_at": None, "completed_at": None},
                    "article_generation": {"status": "pending", "started_at": None, "completed_at": None},
                    "script_generation": {"status": "pending", "started_at": None, "completed_at": None},
                    "audio_generation": {"status": "pending", "started_at": None, "completed_at": None}
                }
            }
            self._save_metadata(podcast_id, metadata)
            
            # 1. Perplexity로 URL 수집
            logger.info("Step 1: URL 수집 (Perplexity)")
            metadata["steps"]["perplexity_crawling"]["status"] = "running"
            metadata["steps"]["perplexity_crawling"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            perplexity_data = await self.perplexity.crawl_topic(topic, keywords)
            # 오류 가드: 크롤링 실패 시 중단
            if isinstance(perplexity_data, dict) and perplexity_data.get("error"):
                metadata["steps"]["perplexity_crawling"]["status"] = "failed"
                metadata["steps"]["perplexity_crawling"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = perplexity_data
                self._save_metadata(podcast_id, metadata)
                # 실패 상황도 기록
                try:
                    self._save_perplexity_urls(podcast_id, perplexity_data)
                except Exception:
                    pass
                raise RuntimeError(f"Perplexity crawling failed: {perplexity_data}")
            # 오류 가드: 기사 배열 비었을 때도 중단
            try:
                articles = perplexity_data.get("data", {}).get("articles", [])
                if isinstance(articles, list) and len(articles) == 0:
                    empty_err = {"error": "NO_ARTICLES", "details": {"message": "크롤링 결과가 비어 있습니다."}}
                    metadata["steps"]["perplexity_crawling"]["status"] = "failed"
                    metadata["steps"]["perplexity_crawling"]["completed_at"] = datetime.now().isoformat()
                    metadata["status"] = "failed"
                    metadata["error"] = empty_err
                    self._save_metadata(podcast_id, metadata)
                    try:
                        self._save_perplexity_urls(podcast_id, empty_err)
                    except Exception:
                        pass
                    raise RuntimeError("Perplexity returned empty articles")
            except Exception:
                pass
            self._save_perplexity_urls(podcast_id, perplexity_data)

            metadata["steps"]["perplexity_crawling"]["status"] = "completed"
            metadata["steps"]["perplexity_crawling"]["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 2. BeautifulSoup으로 원문 크롤링 (모든 URL)
            logger.info("Step 2: 원문 크롤링 (BeautifulSoup)")
            metadata["steps"]["beautifulsoup_crawling"]["status"] = "running"
            metadata["steps"]["beautifulsoup_crawling"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # Perplexity에서 가져온 모든 기사 URL에 대해 크롤링
            articles = perplexity_data.get("data", {}).get("articles", [])
            if not articles or len(articles) == 0:
                raise RuntimeError("No articles to crawl")

            crawled_articles = []
            for idx, article in enumerate(articles):
                article_url = article.get("news_url") or article.get("url", "")
                if not article_url:
                    logger.warning(f"Article {idx} has no URL, skipping")
                    continue

                logger.info(f"크롤링 중 ({idx+1}/{len(articles)}): {article_url}")
                crawled_content = await self.crawler.crawl_article(article_url)

                if crawled_content.get("success"):
                    crawled_articles.append({
                        "url": article_url,
                        "title": crawled_content.get("title", ""),
                        "content": crawled_content.get("content", ""),
                        "content_length": crawled_content.get("content_length", 0),
                        "perplexity_metadata": {
                            "title": article.get("title", ""),
                            "text": article.get("text", ""),
                            "date": article.get("date", "")
                        }
                    })
                    logger.info(f"크롤링 성공: {article_url} ({crawled_content.get('content_length', 0)} 자)")
                else:
                    logger.warning(f"크롤링 실패: {article_url} - {crawled_content.get('error')}")

            # 최소 1개 이상의 기사가 크롤링되어야 함
            if len(crawled_articles) == 0:
                error_data = {"error": "NO_CRAWLED_ARTICLES", "details": {"message": "모든 기사 크롤링 실패"}}
                metadata["steps"]["beautifulsoup_crawling"]["status"] = "failed"
                metadata["steps"]["beautifulsoup_crawling"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = error_data
                self._save_metadata(podcast_id, metadata)
                try:
                    self._save_crawled_data(podcast_id, error_data)
                except Exception:
                    pass
                raise RuntimeError("All articles failed to crawl")

            # 크롤링된 모든 기사 저장
            crawled_data = {
                "total_crawled": len(crawled_articles),
                "articles": crawled_articles
            }
            self._save_crawled_data(podcast_id, crawled_data)

            metadata["steps"]["beautifulsoup_crawling"]["status"] = "completed"
            metadata["steps"]["beautifulsoup_crawling"]["completed_at"] = datetime.now().isoformat()
            metadata["steps"]["beautifulsoup_crawling"]["crawled_count"] = len(crawled_articles)
            self._save_metadata(podcast_id, metadata)
            
            # 3. Gemini로 난이도별 문서 생성
            logger.info("Step 3: 난이도별 문서 생성 (Gemini)")
            metadata["steps"]["article_generation"]["status"] = "running"
            metadata["steps"]["article_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # BeautifulSoup으로 크롤링된 기사들을 Gemini에 전달
            # 반환: {beginner: {...}, intermediate: {...}, advanced: {...}}
            article = await self.gemini.generate_article(
                title=topic,
                articles=crawled_articles  # BeautifulSoup 크롤링 데이터 사용
            )
            # 오류 가드: 문서 생성 실패 시 중단
            if isinstance(article, dict) and article.get("error"):
                metadata["steps"]["article_generation"]["status"] = "failed"
                metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = article
                self._save_metadata(podcast_id, metadata)
                try:
                    self._save_article(podcast_id, article)
                except Exception:
                    pass
                raise RuntimeError(f"Article generation failed: {article}")
            self._save_article(podcast_id, article)

            metadata["steps"]["article_generation"]["status"] = "completed"
            metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 4. Gemini로 난이도별 대본 생성
            logger.info("Step 4: 난이도별 대본 생성 (Gemini)")
            metadata["steps"]["script_generation"]["status"] = "running"
            metadata["steps"]["script_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 난이도별 문서 데이터를 전달
            # 반환: {beginner: {intro, turns, outro}, intermediate: {...}, advanced: {...}}
            script = await self.gemini.generate_script(
                article_title=topic,
                article_data=article.get("data", {})  # 난이도별 문서 데이터
            )
            # 오류 가드: 대본 생성 실패 시 중단
            if isinstance(script, dict) and script.get("error"):
                metadata["steps"]["script_generation"]["status"] = "failed"
                metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = script
                self._save_metadata(podcast_id, metadata)
                try:
                    self._save_script(podcast_id, script)
                except Exception:
                    pass
                raise RuntimeError(f"Script generation failed: {script}")
            self._save_script(podcast_id, script)

            metadata["steps"]["script_generation"]["status"] = "completed"
            metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 5. Clova로 난이도별 TTS 생성
            logger.info("Step 5: 난이도별 음성 생성 (Clova)")
            metadata["steps"]["audio_generation"]["status"] = "running"
            metadata["steps"]["audio_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 난이도별 대본 데이터
            script_data = script.get("data", {})
            audio_results = {}

            # 세 가지 난이도 각각 TTS 생성
            for difficulty in ["beginner", "intermediate", "advanced"]:
                difficulty_script = script_data.get(difficulty, {})
                if not difficulty_script:
                    logger.warning(f"{difficulty} 대본이 없습니다. 건너뜁니다.")
                    continue

                logger.info(f"{difficulty} 난이도 TTS 생성 중...")
                audio = await self.clova.generate_podcast_audio(
                    script=difficulty_script,
                    output_dir=self._get_podcast_directory(podcast_id),
                    filename=f"05_audio_{difficulty}.mp3",
                    speaker_voices={"man": "jinho", "woman": "nara"}
                )

                # 오류 가드: 오디오 생성 실패 시 경고만 하고 계속 진행
                if isinstance(audio, dict) and audio.get("error"):
                    logger.error(f"{difficulty} TTS 생성 실패: {audio}")
                    audio_results[difficulty] = {"error": audio.get("error")}
                else:
                    audio_results[difficulty] = audio.get("data", {})
                    logger.info(f"{difficulty} TTS 생성 완료")

            # 최소 1개 이상의 오디오가 생성되어야 함
            success_count = sum(1 for v in audio_results.values() if not v.get("error"))
            if success_count == 0:
                error_data = {"error": "ALL_AUDIO_FAILED", "details": audio_results}
                metadata["steps"]["audio_generation"]["status"] = "failed"
                metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = error_data
                self._save_metadata(podcast_id, metadata)
                try:
                    self._save_audio(podcast_id, error_data)
                except Exception:
                    pass
                raise RuntimeError(f"All audio generation failed: {error_data}")

            # 난이도별 오디오 정보 저장
            self._save_audio(podcast_id, {"service": "clova", "status": "success", "data": audio_results})

            metadata["steps"]["audio_generation"]["status"] = "completed"
            metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
            metadata["steps"]["audio_generation"]["generated_count"] = success_count
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 결과 정리 (난이도별 데이터)
            result = {
                "podcast_id": podcast_id,
                "topic": topic,
                "keywords": keywords or [],
                "article": article.get("data", {}),  # {beginner: {...}, intermediate: {...}, advanced: {...}}
                "script": script.get("data", {}),    # {beginner: {...}, intermediate: {...}, advanced: {...}}
                "audio": audio_results,              # {beginner: {...}, intermediate: {...}, advanced: {...}}
                "status": "completed",
                "storage_path": self._get_podcast_directory(podcast_id)
            }

            logger.info(f"난이도별 팟캐스트 생성 완료: {podcast_id}")
            return result
            
        except Exception as e:
            logger.error(f"팟캐스트 생성 실패: {e}")
            # 실패 시에도 메타데이터 업데이트
            if 'podcast_id' in locals():
                metadata["status"] = "failed"
                metadata["error"] = str(e)
                metadata["failed_at"] = datetime.now().isoformat()
                self._save_metadata(podcast_id, metadata)
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
