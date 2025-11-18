"""
팟캐스트 생성 서비스
Perplexity, Gemini, Clova를 통합하여 팟캐스트를 생성합니다.
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List
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
        
        # 저장 경로 설정 (Docker 볼륨 마운트 경로)
        # TODO: 이런 경로 싹다 .env에 저장해주세요 & docker-compose.yml에 있을수도 있으니 둘다 체크해서 단 1개만 쓰고 될 수 있으면 .env에서만 관리해주세요
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

    def _load_topic_last_id(self, topic: str) -> int:
        """토픽별 마지막 ID 로드"""
        try:
            topic_dir = os.path.join(self.base_storage_path, topic)
            id_file = os.path.join(topic_dir, "last_id.txt")
            if os.path.exists(id_file):
                with open(id_file, 'r') as f:
                    last_id = int(f.read().strip())
                logger.info(f"토픽 '{topic}' 마지막 ID 로드: {last_id}")
                return last_id
            else:
                logger.info(f"토픽 '{topic}' ID 카운터 초기화: 0")
                return 0
        except Exception as e:
            logger.error(f"토픽 '{topic}' ID 로드 실패: {e}")
            return 0

    def _save_topic_last_id(self, topic: str, last_id: int):
        """토픽별 마지막 ID 저장"""
        try:
            topic_dir = os.path.join(self.base_storage_path, topic)
            os.makedirs(topic_dir, exist_ok=True)
            id_file = os.path.join(topic_dir, "last_id.txt")
            with open(id_file, 'w') as f:
                f.write(str(last_id))
            logger.info(f"토픽 '{topic}' 마지막 ID 저장: {last_id}")
        except Exception as e:
            logger.error(f"토픽 '{topic}' ID 저장 실패: {e}")
    
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
    
    def _save_crawled_data(self, podcast_id: str, crawled_data: Dict[str, Any]) -> str:
        """크롤링된 데이터 저장"""
        podcast_dir = self._create_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "01_crawled_data.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(crawled_data, f, ensure_ascii=False, indent=2)
            logger.info(f"크롤링 데이터 저장: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"크롤링 데이터 저장 실패: {e}")
            raise
    
    def _save_article(self, podcast_id: str, article: Dict[str, Any]) -> str:
        """생성된 문서 저장"""
        podcast_dir = self._get_podcast_directory(podcast_id)
        file_path = os.path.join(podcast_dir, "02_article.json")
        
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
        file_path = os.path.join(podcast_dir, "03_script.json")
        
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
        file_path = os.path.join(podcast_dir, "04_audio.json")
        
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
                    "crawling": {"status": "pending", "started_at": None, "completed_at": None},
                    "article_generation": {"status": "pending", "started_at": None, "completed_at": None},
                    "script_generation": {"status": "pending", "started_at": None, "completed_at": None},
                    "audio_generation": {"status": "pending", "started_at": None, "completed_at": None}
                }
            }
            self._save_metadata(podcast_id, metadata)
            
            # 1. Perplexity로 데이터 크롤링
            logger.info("Step 1: 데이터 크롤링 (Perplexity)")
            metadata["steps"]["crawling"]["status"] = "running"
            metadata["steps"]["crawling"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            crawled_data = await self.perplexity.crawl_topic(topic, keywords)
            # 오류 가드: 크롤링 실패 시 중단
            if isinstance(crawled_data, dict) and crawled_data.get("error"):
                metadata["steps"]["crawling"]["status"] = "failed"
                metadata["steps"]["crawling"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = crawled_data
                self._save_metadata(podcast_id, metadata)
                # 실패 상황도 기록
                try:
                    self._save_crawled_data(podcast_id, crawled_data)
                except Exception:
                    pass
                raise RuntimeError(f"Crawling failed: {crawled_data}")
            # 오류 가드: 기사 배열 비었을 때도 중단
            try:
                articles = crawled_data.get("data", {}).get("articles", [])
                if isinstance(articles, list) and len(articles) == 0:
                    empty_err = {"error": "NO_ARTICLES", "details": {"message": "크롤링 결과가 비어 있습니다."}}
                    metadata["steps"]["crawling"]["status"] = "failed"
                    metadata["steps"]["crawling"]["completed_at"] = datetime.now().isoformat()
                    metadata["status"] = "failed"
                    metadata["error"] = empty_err
                    self._save_metadata(podcast_id, metadata)
                    try:
                        self._save_crawled_data(podcast_id, empty_err)
                    except Exception:
                        pass
                    raise RuntimeError("Crawling returned empty articles")
            except Exception:
                pass
            self._save_crawled_data(podcast_id, crawled_data)
            
            metadata["steps"]["crawling"]["status"] = "completed"
            metadata["steps"]["crawling"]["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 2. Gemini로 문서 생성
            logger.info("Step 2: 문서 생성 (Gemini)")
            metadata["steps"]["article_generation"]["status"] = "running"
            metadata["steps"]["article_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            article = await self.gemini.generate_article(
                title=topic,
                articles=crawled_data.get("data", {}).get("articles", [])
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
            
            # 3. Gemini로 대본 생성
            logger.info("Step 3: 대본 생성 (Gemini)")
            metadata["steps"]["script_generation"]["status"] = "running"
            metadata["steps"]["script_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 기본 화자 구성: 남/여 2인
            script = await self.gemini.generate_script(
                article_title=topic,
                article_content=article.get("data", {}).get("content", "")
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
            
            # 4. Clova로 TTS 생성
            logger.info("Step 4: 음성 생성 (Clova)")
            metadata["steps"]["audio_generation"]["status"] = "running"
            metadata["steps"]["audio_generation"]["started_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            audio = await self.clova.generate_podcast_audio(
                script=script.get("data", {}),
                output_dir=self._get_podcast_directory(podcast_id),
                filename=f"04_audio.mp3",
                speaker_voices={"man": "jinho", "woman": "nara"}
            )
            # 오류 가드: 오디오 생성 실패 시 중단
            if isinstance(audio, dict) and audio.get("error"):
                metadata["steps"]["audio_generation"]["status"] = "failed"
                metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
                metadata["status"] = "failed"
                metadata["error"] = audio
                self._save_metadata(podcast_id, metadata)
                try:
                    self._save_audio(podcast_id, audio)
                except Exception:
                    pass
                raise RuntimeError(f"Audio generation failed: {audio}")
            self._save_audio(podcast_id, audio)
            
            metadata["steps"]["audio_generation"]["status"] = "completed"
            metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            self._save_metadata(podcast_id, metadata)
            
            # 결과 정리
            result = {
                "podcast_id": podcast_id,
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
                "status": "completed",
                "storage_path": self._get_podcast_directory(podcast_id)
            }
            
            logger.info(f"팟캐스트 생성 완료: {podcast_id}")
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

    async def create_podcasts_for_topic(
        self,
        topic: str,
        keywords: list = None, # TODO: 해당 변수 왜 가져오고 사용하는지 체크 필요!
        processed_urls: set = None
    ) -> List[Dict[str, Any]]:
        """
        토픽에 대해 여러 개의 팟캐스트 생성 (각 기사마다 난이도별로)

        Args:
            topic: 팟캐스트 주제
            keywords: 관련 키워드 목록
            processed_urls: 이미 처리된 URL 목록 (중복 방지용)

        Returns:
            List of article data:
            [
                {
                    'title': str,
                    'date': str,
                    'source_url': str,
                    'status': 'completed' | 'failed',
                    'crawled_data': {...},
                    'article_data': {...},
                    'script_data': {...},
                    'audio_data': {...},
                    'storage_path': str,
                    'error_message': str | None
                },
                ...
            ]
        """
        # TODO: 모든 변수 선언 주석 작성해주세요!
        results = []
        processed_urls = processed_urls or set()

        try:
            # 1. Perplexity로 링크 수집
            # TODO: 모든 로거 지워주세요 -> DB & Storage 구분 작업 필요해요 -> 어느 경로에 무슨 파일이 저장될지 정하기
            logger.info(f"토픽 '{topic}'에 대한 기사 크롤링 시작")
            # TODO: 퍼플렉시티의 결과물 원본도 저장 해주세요
            crawled_links = await self.perplexity.crawl_topic(topic, keywords) # TODO: Beautiful Soup랑 Perplexity summary를 보완해서 모델 다시 짜주세요

            logger.info(f"Perplexity 응답 타입: {type(crawled_links)}")
            logger.info(f"Perplexity 응답 keys: {crawled_links.keys() if isinstance(crawled_links, dict) else 'Not a dict'}")

            if isinstance(crawled_links, dict) and crawled_links.get("error"):
                logger.error(f"Perplexity 크롤링 실패: {crawled_links}")
                return []

            data = crawled_links.get("data", {})
            logger.info(f"data 타입: {type(data)}, data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")

            articles = data.get("articles", []) if isinstance(data, dict) else []
            logger.info(f"Perplexity에서 {len(articles)}개 기사 링크 수집")

            if articles and len(articles) > 0:
                logger.info(f"첫 번째 기사 샘플: {articles[0] if articles else 'None'}")

            if not articles:
                logger.warning("크롤링된 기사가 없습니다")
                return []

            # 2. 토픽별 마지막 ID 로드
            topic_last_id = self._load_topic_last_id(topic)
            current_article_id = topic_last_id

            # 3. 각 기사마다 독립적으로 처리
            crawler = WebCrawlerService()

            for idx, article_meta in enumerate(articles):
                news_url = article_meta.get('url', '') or article_meta.get('news_url', '')  # Perplexity는 'url', 이전 코드는 'news_url' 사용
                article_title = article_meta.get('title', 'Untitled')
                article_date = article_meta.get('date', datetime.now().strftime('%Y-%m-%d'))

                # 2-1. 중복 URL 체크
                if news_url in processed_urls:
                    logger.info(f"중복 URL 건너뛰기: {news_url}")
                    continue

                if not news_url:
                    logger.warning(f"Article {idx}: URL이 없습니다")
                    continue

                processed_urls.add(news_url)

                # 초기 변수 설정
                storage_path = None
                crawled = None
                article_data = None
                script_data = None
                audio_data = {}
                error_message = None
                article_status = 'processing'

                try:
                    # 2-2. storage_path 설정 및 디렉토리 생성 (토픽별 연속 ID 사용)
                    storage_path = os.path.join(self.base_storage_path, topic, f"article_{current_article_id}")
                    os.makedirs(storage_path, exist_ok=True)
                    logger.info(f"Article {current_article_id} (idx:{idx}) 처리 시작: {article_title[:50]}...")

                    # 메타데이터 생성 및 저장 (기존 create_podcast 방식)
                    metadata = {
                        "article_id": f"article_{current_article_id}",
                        "topic": topic,
                        "title": article_title,
                        "date": article_date,
                        "source_url": news_url,
                        "created_at": datetime.now().isoformat(),
                        "status": "processing",
                        "steps": {
                            "crawling": {"status": "pending", "started_at": None, "completed_at": None},
                            "article_generation": {"status": "pending", "started_at": None, "completed_at": None},
                            "script_generation": {"status": "pending", "started_at": None, "completed_at": None},
                            "audio_generation": {"status": "pending", "started_at": None, "completed_at": None}
                        }
                    }

                    # 메타데이터 파일 저장
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    # 2-3. BeautifulSoup으로 전체 원문 크롤링
                    logger.info(f"Article {idx}: Step 1 - 크롤링 시작")
                    metadata["steps"]["crawling"]["status"] = "running"
                    metadata["steps"]["crawling"]["started_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    crawled = await crawler.crawl_article(news_url)

                    # 크롤링 데이터 저장 (성공/실패 여부와 관계없이 저장)
                    with open(os.path.join(storage_path, "01_crawled_data.json"), 'w', encoding='utf-8') as f:
                        json.dump(crawled, f, ensure_ascii=False, indent=2)
                    
                    # TODO: 중복된거 저장 안되게 해주시고 지금 너무 복잡해요, 단순화 해주세요 <- 현재 상태 에러 생기면 찾기 힘들어요

                    if not crawled['success']:
                        logger.error(f"Article {idx} 크롤링 실패: {crawled['error']}")
                        metadata["steps"]["crawling"]["status"] = "failed"
                        metadata["steps"]["crawling"]["completed_at"] = datetime.now().isoformat()
                        metadata["status"] = "failed"
                        metadata["error"] = f"크롤링 실패: {crawled['error']}"
                        with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        error_message = f"크롤링 실패: {crawled['error']}"
                        article_status = 'failed'
                        raise Exception(error_message)

                    metadata["steps"]["crawling"]["status"] = "completed"
                    metadata["steps"]["crawling"]["completed_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    # 2-4. Gemini로 난이도별 원문 요약 (1번의 호출로 3개 난이도)
                    # TODO: 로거......
                    logger.info(f"Article {idx}: Step 2 - 난이도별 문서 생성 중...")
                    metadata["steps"]["article_generation"]["status"] = "running" # TODO: 관리자 페이지용 API 만드셔서 거기에 넣어주세요
                    metadata["steps"]["article_generation"]["started_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    article_data = await self.gemini.generate_articles_all_difficulties(
                        title=article_title,
                        raw_content=crawled['content']
                    )

                    # 문서 데이터 저장 (성공/실패 여부와 관계없이 저장)
                    with open(os.path.join(storage_path, "02_article_data.json"), 'w', encoding='utf-8') as f:
                        json.dump(article_data, f, ensure_ascii=False, indent=2)

                    if isinstance(article_data, dict) and article_data.get("error"):
                        logger.error(f"Article {idx} 문서 생성 실패: {article_data}")
                        metadata["steps"]["article_generation"]["status"] = "failed"
                        metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
                        metadata["status"] = "failed"
                        metadata["error"] = f"문서 생성 실패: {article_data.get('error')}"
                        with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        error_message = f"문서 생성 실패: {article_data.get('error')}"
                        article_status = 'failed'
                        raise Exception(error_message)

                    metadata["steps"]["article_generation"]["status"] = "completed"
                    metadata["steps"]["article_generation"]["completed_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    # 2-5. Gemini로 난이도별 대본 생성 (1번의 호출로 3개 난이도)
                    logger.info(f"Article {idx}: Step 3 - 난이도별 대본 생성 중...")
                    metadata["steps"]["script_generation"]["status"] = "running"
                    metadata["steps"]["script_generation"]["started_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    # TODO: 쓸데없는 로거 코드 메타데이터 다 지워주세요

                    script_data = await self.gemini.generate_scripts_all_difficulties(
                        article_title=article_title,
                        article_data=article_data
                    )

                    # 대본 데이터 저장 (성공/실패 여부와 관계없이 저장)
                    with open(os.path.join(storage_path, "03_script_data.json"), 'w', encoding='utf-8') as f:
                        json.dump(script_data, f, ensure_ascii=False, indent=2)

                    if isinstance(script_data, dict) and script_data.get("error"):
                        logger.error(f"Article {idx} 대본 생성 실패: {script_data}")
                        metadata["steps"]["script_generation"]["status"] = "failed"
                        metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
                        metadata["status"] = "failed"
                        metadata["error"] = f"대본 생성 실패: {script_data.get('error')}"
                        with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        error_message = f"대본 생성 실패: {script_data.get('error')}"
                        article_status = 'failed'
                        raise Exception(error_message)

                    metadata["steps"]["script_generation"]["status"] = "completed"
                    metadata["steps"]["script_generation"]["completed_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    # 2-6. Clova로 난이도별 TTS 생성 (3개)
                    logger.info(f"Article {idx}: Step 4 - 난이도별 TTS 생성 중...")
                    metadata["steps"]["audio_generation"]["status"] = "running"
                    metadata["steps"]["audio_generation"]["started_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    for difficulty in ['beginner', 'intermediate', 'advanced']:
                        script_for_difficulty = script_data.get(difficulty, {})

                        if not script_for_difficulty:
                            logger.warning(f"Article {idx}: {difficulty} 대본이 없습니다")
                            continue
                        
                        # TODO: 비동기 없애주세요
                        audio_result = await self.clova.generate_podcast_audio(
                            script=script_for_difficulty,
                            output_dir=storage_path,
                            filename=f"{difficulty}.mp3",
                            speaker_voices={"man": "jinho", "woman": "nara"}
                        )

                        if isinstance(audio_result, dict) and not audio_result.get("error"):
                            audio_data[difficulty] = audio_result.get('data', {})
                            logger.info(f"Article {idx}: {difficulty} TTS 생성 완료")
                        else:
                            logger.error(f"Article {idx} {difficulty} TTS 생성 실패: {audio_result}")

                    # 오디오 데이터 저장 (일부 실패해도 성공한 것은 저장)
                    with open(os.path.join(storage_path, "04_audio_data.json"), 'w', encoding='utf-8') as f:
                        json.dump(audio_data, f, ensure_ascii=False, indent=2)

                    metadata["steps"]["audio_generation"]["status"] = "completed"
                    metadata["steps"]["audio_generation"]["completed_at"] = datetime.now().isoformat()
                    metadata["status"] = "completed"
                    metadata["completed_at"] = datetime.now().isoformat()
                    with open(os.path.join(storage_path, "00_metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    article_status = 'completed'
                    logger.info(f"Article {current_article_id} (idx:{idx}) 처리 완료: {article_title[:50]}...")


                except Exception as e:
                    logger.error(f"Article {idx} 처리 중 오류: {e}", exc_info=True)

                    # 예외 발생 시에도 메타데이터 업데이트 (실패 상태로)
                    if storage_path and os.path.exists(storage_path):
                        try:
                            metadata_path = os.path.join(storage_path, "00_metadata.json")
                            if os.path.exists(metadata_path):
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                metadata["status"] = "failed"
                                metadata["error"] = str(e)
                                metadata["failed_at"] = datetime.now().isoformat()
                                with open(metadata_path, 'w', encoding='utf-8') as f:
                                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                        except Exception as meta_error:
                            logger.error(f"메타데이터 업데이트 실패: {meta_error}")

                    article_status = 'failed'
                    error_message = str(e)

                # 2-7. 결과 저장 (성공/실패 여부와 관계없이)
                results.append({
                    'title': article_title,
                    'date': article_date,
                    'source_url': news_url,
                    'status': article_status,
                    'crawled_data': {
                        'url': crawled['url'],
                        'title': crawled['title'],
                        'content': crawled['content'],
                        'content_length': crawled['content_length']
                    } if crawled and crawled.get('success') else None,
                    'article_data': article_data if article_data and not article_data.get('error') else None,
                    'script_data': script_data if script_data and not script_data.get('error') else None,
                    'audio_data': audio_data if audio_data else {},
                    'storage_path': storage_path,
                    'error_message': error_message
                })

                # 2-8. ID 증가 (다음 기사를 위해)
                current_article_id += 1

            # 4. 토픽별 마지막 ID 저장
            self._save_topic_last_id(topic, current_article_id)

            logger.info(f"토픽 '{topic}' 처리 완료: 총 {len(results)}개 (성공: {sum(1 for r in results if r['status'] == 'completed')}개)")
            return results

        except Exception as e:
            logger.error(f"create_podcasts_for_topic 실패: {e}", exc_info=True)
            return results


# 전역 인스턴스
podcast_service = PodcastService()

