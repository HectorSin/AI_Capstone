"""
팟캐스트 생성 서비스
Perplexity, Gemini, Clova를 통합하여 팟캐스트를 생성합니다.
"""
import logging
import os
import json
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, date
import threading

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai import (
    PerplexityService,
    GeminiService,
    ClovaService,
    AIServiceConfig
)
from app.services.crawler_service import WebCrawlerService
from app.config import settings
from app.database.models import Article
from app import crud

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

    def _get_next_article_number(self, topic_name: str) -> int:
        """토픽별 다음 Article 번호 반환"""
        topic_dir = os.path.join(self.base_storage_path, topic_name)
        last_id_file = os.path.join(topic_dir, "last_id.txt")

        try:
            if os.path.exists(last_id_file):
                with open(last_id_file, 'r') as f:
                    last_id = int(f.read().strip())
                return last_id + 1
            else:
                return 0
        except Exception as e:
            logger.error(f"Article ID 로드 실패: {e}")
            return 0

    def _save_article_number(self, topic_name: str, article_number: int):
        """토픽별 Article 번호 저장"""
        topic_dir = os.path.join(self.base_storage_path, topic_name)
        os.makedirs(topic_dir, mode=0o755, exist_ok=True)
        last_id_file = os.path.join(topic_dir, "last_id.txt")

        try:
            with open(last_id_file, 'w') as f:
                f.write(str(article_number))
        except Exception as e:
            logger.error(f"Article ID 저장 실패: {e}")

    def _get_article_directory(self, topic_name: str, article_number: int) -> str:
        """Article별 디렉토리 경로 반환"""
        return os.path.join(self.base_storage_path, topic_name, f"article_{article_number}")

    def _create_article_directory(self, topic_name: str, article_number: int) -> str:
        """Article별 디렉토리 생성"""
        article_dir = self._get_article_directory(topic_name, article_number)
        try:
            os.makedirs(article_dir, mode=0o755, exist_ok=True)
            logger.info(f"Article 디렉토리 생성: {article_dir}")
            return article_dir
        except Exception as e:
            logger.error(f"Article 디렉토리 생성 실패: {e}")
            return article_dir
    
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

    def _save_crawled_data(self, dir_or_id: str, crawled_data: Dict[str, Any] = None, is_article_dir: bool = False) -> str:
        """BeautifulSoup으로 크롤링된 원문 데이터 저장

        Args:
            dir_or_id: podcast_id (기존) 또는 article_dir (새로운)
            crawled_data: 크롤링 데이터 (기존 호출 시 필수)
            is_article_dir: True면 dir_or_id를 article_dir로 사용
        """
        if is_article_dir:
            # 새로운 방식: article_dir 직접 사용
            file_path = os.path.join(dir_or_id, "crawled_data.json")
        else:
            # 기존 방식: podcast_id 사용
            podcast_dir = self._create_podcast_directory(dir_or_id)
            file_path = os.path.join(podcast_dir, "02_crawled_data.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(crawled_data, f, ensure_ascii=False, indent=2)
            logger.info(f"크롤링 원문 데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"크롤링 원문 데이터 저장 실패: {e}")
            raise
    
    def _save_article_file(self, article_dir: str, article_data: Dict[str, Any]) -> str:
        """생성된 문서 저장 (article_dir에 직접 저장)"""
        file_path = os.path.join(article_dir, "article.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            logger.info(f"문서 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            raise

    def _save_script_file(self, article_dir: str, script_data: Dict[str, Any]) -> str:
        """생성된 대본 저장 (article_dir에 직접 저장)"""
        file_path = os.path.join(article_dir, "script.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            logger.info(f"대본 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"대본 저장 실패: {e}")
            raise

    # 기존 함수들 (하위 호환성)
    def _save_article(self, podcast_id: str, article_index: int, article: Dict[str, Any]) -> str:
        """생성된 문서 저장 (기사별 개별 파일) - 기존 방식"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        articles_dir = os.path.join(podcast_dir, "03_articles")
        os.makedirs(articles_dir, mode=0o755, exist_ok=True)

        file_path = os.path.join(articles_dir, f"article_{article_index}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=2)
            logger.info(f"문서 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            raise

    def _save_script(self, podcast_id: str, script_index: int, script: Dict[str, Any]) -> str:
        """생성된 대본 저장 (기사별 개별 파일) - 기존 방식"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        scripts_dir = os.path.join(podcast_dir, "04_scripts")
        os.makedirs(scripts_dir, mode=0o755, exist_ok=True)

        file_path = os.path.join(scripts_dir, f"script_{script_index}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            logger.info(f"대본 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"대본 저장 실패: {e}")
            raise

    def _save_audio_metadata(self, podcast_id: str, audio_index: int, audio: Dict[str, Any]) -> str:
        """생성된 음성 파일 메타데이터 저장 (기사별)"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        audios_dir = os.path.join(podcast_dir, "05_audios")
        os.makedirs(audios_dir, mode=0o755, exist_ok=True)

        file_path = os.path.join(audios_dir, f"audio_{audio_index}_metadata.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(audio, f, ensure_ascii=False, indent=2)
            logger.info(f"음성 메타데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"음성 메타데이터 저장 실패: {e}")
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
    
    async def create_podcast(self, topic: str, keywords: list = None, db: AsyncSession = None) -> Dict[str, Any]:
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
        if db is None:
            raise ValueError("Database session is required")

        try:
            # Topic 조회
            topic_obj = await crud.get_topic_by_name(db, topic)
            if not topic_obj:
                raise ValueError(f"Topic '{topic}' not found in database")

            # Topic 이름을 디렉토리명으로 사용 (띄어쓰기 없음)
            topic_dir_name = topic_obj.name

            # 팟캐스트 ID 생성 (5자리 숫자)
            podcast_id = self._generate_podcast_id()
            logger.info(f"팟캐스트 생성 시작: {topic} (ID: {podcast_id}, Topic: {topic_dir_name})")
            
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
            
            # 3. Gemini로 난이도별 문서 생성 (기사별 개별 처리)
            logger.info("Step 3: 난이도별 문서 생성 (Gemini) - 기사별 개별 처리")
            metadata["steps"]["article_generation"]["status"] = "running"
            metadata["steps"]["article_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 각 크롤링된 기사마다 개별적으로 문서 생성
            generated_articles = []
            db_articles = []  # DB Article 객체 리스트

            for idx, crawled_article in enumerate(crawled_articles):
                logger.info(f"기사 처리 중 ({idx+1}/{len(crawled_articles)}): {crawled_article.get('url', '')}")

                # Article 번호 생성
                article_number = self._get_next_article_number(topic_dir_name)
                logger.info(f"Article 번호: {article_number}")

                # DB Article 레코드 생성
                # Perplexity 제목 우선 사용 (한글), 없으면 크롤링된 제목
                perplexity_metadata = crawled_article.get("perplexity_metadata", {})
                perplexity_title = perplexity_metadata.get("title", "")
                crawled_title = crawled_article.get("title", "")
                article_title = perplexity_title or crawled_title or f"Article {article_number}"

                # Perplexity에서 가져온 실제 기사 날짜 사용, 없으면 오늘 날짜
                article_date_str = perplexity_metadata.get("date", "")
                try:
                    # YYYY-MM-DD 형식의 날짜 문자열을 date 객체로 변환
                    article_date = datetime.strptime(article_date_str, "%Y-%m-%d").date() if article_date_str else date.today()
                except (ValueError, TypeError):
                    logger.warning(f"Invalid date format: {article_date_str}, using today's date")
                    article_date = date.today()

                db_article = Article(
                    topic_id=topic_obj.id,
                    title=article_title,
                    date=article_date,
                    source_url=crawled_article.get("url"),
                    status='processing'
                )
                db.add(db_article)
                await db.flush()  # article.id 생성
                db_articles.append(db_article)
                logger.info(f"DB Article 생성: {db_article.id}")

                # 스토리지 경로 설정
                article_dir = self._get_article_directory(topic_dir_name, article_number)
                self._create_article_directory(topic_dir_name, article_number)
                db_article.storage_path = article_dir

                # Article 번호 저장
                self._save_article_number(topic_dir_name, article_number)

                # 크롤링 데이터 저장 (파일)
                self._save_crawled_data(article_dir, crawled_article, is_article_dir=True)

                # DB에 crawled_data 저장 (commit은 나중에)
                db_article.crawled_data = crawled_article

                # 문서 생성
                article = await self.gemini.generate_article(
                    title=topic,
                    article=crawled_article
                )

                # 오류 가드: 문서 생성 실패 시
                if isinstance(article, dict) and article.get("error"):
                    logger.error(f"문서 {idx} 생성 실패: {article}")
                    db_article.status = 'failed'
                    db_article.error_message = str(article.get("error"))
                    generated_articles.append({"error": article.get("error"), "url": crawled_article.get("url")})
                else:
                    # 성공한 문서 저장
                    article_data = article.get("data", {})
                    self._save_article_file(article_dir, article_data)  # 새로운 방식으로 저장

                    # DB에 article_data 저장
                    db_article.article_data = article_data

                    # 한글 제목으로 업데이트 (Gemini가 생성한 제목 사용)
                    # article_data에서 한글 제목 추출 (beginner, intermediate, advanced 중 하나)
                    korean_title = None
                    for difficulty in ["intermediate", "beginner", "advanced"]:
                        if difficulty in article_data and "title" in article_data[difficulty]:
                            korean_title = article_data[difficulty]["title"]
                            break

                    if korean_title:
                        db_article.title = korean_title
                        logger.info(f"제목 업데이트: {korean_title}")

                    generated_articles.append(article)
                    logger.info(f"문서 {idx} 생성 완료")

            # 최소 1개 이상의 문서가 생성되어야 함
            success_count = sum(1 for a in generated_articles if not (isinstance(a, dict) and a.get("error")))
            if success_count == 0:
                error_data = {"error": "ALL_ARTICLES_FAILED", "details": generated_articles}
                metadata["steps"]["article_generation"]["status"] = "failed"
                metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = error_data
                self._save_metadata(podcast_id, metadata)
                raise RuntimeError(f"All article generation failed: {error_data}")

            metadata["steps"]["article_generation"]["status"] = "completed"
            metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
            metadata["steps"]["article_generation"]["generated_count"] = success_count
            self._save_metadata(podcast_id, metadata)
            
            # 4. Gemini로 난이도별 대본 생성 (기사별 개별 처리)
            logger.info("Step 4: 난이도별 대본 생성 (Gemini) - 기사별 개별 처리")
            metadata["steps"]["script_generation"]["status"] = "running"
            metadata["steps"]["script_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 성공한 문서들에 대해서만 대본 생성
            generated_scripts = []
            for idx, article in enumerate(generated_articles):
                # 오류가 있는 문서는 건너뛰기
                if isinstance(article, dict) and article.get("error"):
                    logger.warning(f"문서 {idx}에 오류가 있어 대본 생성을 건너뜁니다.")
                    generated_scripts.append({"error": "ARTICLE_FAILED", "article_error": article.get("error")})
                    continue

                logger.info(f"대본 생성 중 ({idx+1}/{len(generated_articles)})")

                script = await self.gemini.generate_script(
                    article_title=topic,
                    article_data=article.get("data", {})  # 난이도별 문서 데이터
                )

                # 오류 가드: 대본 생성 실패 시
                if isinstance(script, dict) and script.get("error"):
                    logger.error(f"대본 {idx} 생성 실패: {script}")
                    db_articles[idx].status = 'failed'
                    db_articles[idx].error_message = str(script.get("error"))
                    generated_scripts.append({"error": script.get("error")})
                else:
                    # 성공한 대본 저장
                    script_data = script.get("data", {})
                    article_output_dir = db_articles[idx].storage_path
                    self._save_script_file(article_output_dir, script_data)  # 새로운 방식으로 저장
                    # DB에 script_data 저장
                    db_articles[idx].script_data = script_data
                    generated_scripts.append(script)
                    logger.info(f"대본 {idx} 생성 완료")

            # 최소 1개 이상의 대본이 생성되어야 함
            script_success_count = sum(1 for s in generated_scripts if not (isinstance(s, dict) and s.get("error")))
            if script_success_count == 0:
                error_data = {"error": "ALL_SCRIPTS_FAILED", "details": generated_scripts}
                metadata["steps"]["script_generation"]["status"] = "failed"
                metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = error_data
                self._save_metadata(podcast_id, metadata)
                raise RuntimeError(f"All script generation failed: {error_data}")

            metadata["steps"]["script_generation"]["status"] = "completed"
            metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
            metadata["steps"]["script_generation"]["generated_count"] = script_success_count
            self._save_metadata(podcast_id, metadata)
            
            # 5. Clova로 난이도별 TTS 생성 (기사별 개별 처리)
            logger.info("Step 5: 난이도별 음성 생성 (Clova) - 기사별 개별 처리")
            metadata["steps"]["audio_generation"]["status"] = "running"
            metadata["steps"]["audio_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 성공한 대본들에 대해서만 오디오 생성
            generated_audios = []
            total_audio_count = 0

            for idx, script in enumerate(generated_scripts):
                # 오류가 있는 대본은 건너뛰기
                if isinstance(script, dict) and script.get("error"):
                    logger.warning(f"대본 {idx}에 오류가 있어 오디오 생성을 건너뜁니다.")
                    generated_audios.append({"error": "SCRIPT_FAILED", "script_error": script.get("error")})
                    continue

                logger.info(f"오디오 생성 중 ({idx+1}/{len(generated_scripts)})")

                # 해당 Article 디렉토리 가져오기
                article_output_dir = db_articles[idx].storage_path

                # 난이도별 대본 데이터
                script_data = script.get("data", {})
                audio_results = {}

                # 세 가지 난이도 각각 TTS 생성
                for difficulty in ["beginner", "intermediate", "advanced"]:
                    difficulty_script = script_data.get(difficulty, {})
                    if not difficulty_script:
                        logger.warning(f"기사 {idx} - {difficulty} 대본이 없습니다. 건너뜁니다.")
                        continue

                    logger.info(f"기사 {idx} - {difficulty} 난이도 TTS 생성 중...")
                    audio = await self.clova.generate_podcast_audio(
                        script=difficulty_script,
                        output_dir=article_output_dir,
                        filename=f"{difficulty}.mp3",
                        speaker_voices={"man": "jinho", "woman": "nara"}
                    )

                    # 오류 가드: 오디오 생성 실패 시 경고만 하고 계속 진행
                    if isinstance(audio, dict) and audio.get("error"):
                        logger.error(f"기사 {idx} - {difficulty} TTS 생성 실패: {audio}")
                        audio_results[difficulty] = {"error": audio.get("error")}
                    else:
                        audio_results[difficulty] = audio.get("data", {})
                        total_audio_count += 1
                        logger.info(f"기사 {idx} - {difficulty} TTS 생성 완료")

                # 이 기사의 오디오 정보 저장 (파일)
                self._save_audio_metadata(podcast_id, idx, {"service": "clova", "status": "success", "data": audio_results})
                generated_audios.append({"service": "clova", "status": "success", "data": audio_results})

                # DB에 audio_data 저장 및 완료 처리
                db_articles[idx].audio_data = audio_results
                db_articles[idx].status = 'completed'
                db_articles[idx].completed_at = datetime.now()
                logger.info(f"기사 {idx} 처리 완료")

            # 최소 1개 이상의 오디오가 생성되어야 함
            if total_audio_count == 0:
                error_data = {"error": "ALL_AUDIO_FAILED", "details": generated_audios}
                metadata["steps"]["audio_generation"]["status"] = "failed"
                metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = error_data
                self._save_metadata(podcast_id, metadata)
                raise RuntimeError(f"All audio generation failed: {error_data}")

            metadata["steps"]["audio_generation"]["status"] = "completed"
            metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
            metadata["steps"]["audio_generation"]["generated_count"] = total_audio_count
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)

            # 모든 처리가 끝난 후 DB에 한 번에 저장
            await db.commit()
            logger.info(f"모든 기사 DB 저장 완료 (총 {len(db_articles)}개)")

            # 결과 정리 (기사별 개별 데이터)
            result = {
                "podcast_id": podcast_id,
                "topic": topic,
                "keywords": keywords or [],
                "articles": generated_articles,  # 기사별 문서 리스트
                "scripts": generated_scripts,    # 기사별 대본 리스트
                "audios": generated_audios,      # 기사별 오디오 리스트
                "status": "completed",
                "storage_path": self._get_podcast_directory(podcast_id),
                "summary": {
                    "total_articles": len(crawled_articles),
                    "successful_articles": success_count,
                    "successful_scripts": script_success_count,
                    "total_audio_files": total_audio_count
                }
            }

            logger.info(f"기사별 팟캐스트 생성 완료: {podcast_id} (기사 {len(crawled_articles)}개, 오디오 {total_audio_count}개)")
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
