"""
Perplexity AI 서비스
Perplexity API를 사용하여 데이터 크롤링 및 정보 수집
"""
import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
from pydantic import BaseModel, ValidationError
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from .base import AIService, AIServiceConfig
from .config_manager import ConfigManager, CompanyInfoManager, PromptManager

logger = logging.getLogger(__name__)


class Article(BaseModel):
    """기사 데이터 모델 (Pydantic)"""
    news_url: str
    title: str
    text: str
    date: str


class NewsData(BaseModel):
    """뉴스 데이터 모델 (Pydantic)"""
    category: str
    articles: List[Article]


class PerplexityService(AIService):
    """Perplexity AI 서비스 구현체"""
    
    API_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, config: AIServiceConfig):
        super().__init__(config)
        self.api_key = config.api_key
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager()
        self.company_manager = CompanyInfoManager(self.config_manager)
        self.prompt_manager = PromptManager(self.config_manager)
        
        # LangChain JSON Output Parser 초기화
        self.json_parser = JsonOutputParser(pydantic_object=NewsData)
    
    async def validate_config(self) -> bool:
        """설정이 유효한지 검증합니다."""
        if not self.api_key:
            logger.error("Perplexity API 키가 설정되지 않았습니다.")
            return False
        return True
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Perplexity API를 사용하여 정보를 생성합니다.
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 매개변수 (model, temperature 등)
        
        Returns:
            Perplexity API 응답
        """
        if not await self.validate_config():
            return {"error": "Perplexity API 설정이 유효하지 않습니다."}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "model": kwargs.get("model", "sonar"),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", 4000),
            "return_citations": kwargs.get("return_citations", True)
        }

        max_retries = kwargs.get("max_retries", 3)
        backoff_base = kwargs.get("backoff_base", 1.5)

        for attempt in range(1, max_retries + 1):
            try:
                timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=60.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(self.API_URL, headers=headers, json=payload)
                    # 재시도 가치가 있는 상태코드 처리
                    if response.status_code in (429, 500, 502, 503, 504):
                        raise httpx.HTTPStatusError("Server busy", request=response.request, response=response)
                    response.raise_for_status()

                    response_data = response.json()
                    content = response_data["choices"][0]['message']['content']

                    return {
                        "service": "perplexity",
                        "status": "success",
                        "data": {
                            "content": content,
                            "citations": response_data.get("citations", [])
                        }
                    }
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.HTTPStatusError) as e:
                logger.warning(f"Perplexity 시도 {attempt}/{max_retries} 실패: {type(e).__name__}: {e}")
                if attempt == max_retries:
                    logger.error("Perplexity 최대 재시도 초과")
                    return {"error": f"API 요청 실패: {type(e).__name__}: {str(e)}"}
                # 지수 백오프
                delay = backoff_base ** attempt
                await asyncio.sleep(delay)
            except KeyError as e:
                logger.error(f"응답 형식 오류: {e}")
                return {"error": f"응답 형식 오류: {str(e)}"}
    
    async def crawl_topic(self, topic: str, keywords: list = None) -> Dict[str, Any]:
        """
        특정 토픽에 대한 정보를 크롤링합니다.

        Args:
            topic: 크롤링할 토픽
            keywords: 관련 키워드 목록

        Returns:
            크롤링된 정보
        """
        logger.info(f"토픽 크롤링 시작: {topic}")

        # API 키 확인
        if not self.api_key or len(self.api_key) < 10:
            logger.error(f"Perplexity API 키가 유효하지 않음: {self.api_key[:10] if self.api_key else 'None'}...")
            return {"error": "Perplexity API 키가 설정되지 않았거나 유효하지 않습니다."}
        
        try:
            # 설정 관리자를 통해 회사 정보와 프롬프트 생성
            company_info = self.company_manager.get_company_info(topic)
            source_preferences = self.company_manager.get_source_preferences()
            prompt = self.prompt_manager.create_tech_news_prompt(topic, company_info, source_preferences)
            
            # API 요청 페이로드 구성
            payload = {
                "model": "sonar",  # 노트북에서 사용한 모델
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "search_domain_filter": company_info["sources"],
                "search_recency_filter": "week",  # 노트북과 동일
                "return_citations": True,
                "max_tokens": 4000
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            max_retries = 3
            backoff_base = 1.5
            for attempt in range(1, max_retries + 1):
                try:
                    timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=60.0)
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(self.API_URL, headers=headers, json=payload)
                        if response.status_code in (429, 500, 502, 503, 504):
                            raise httpx.HTTPStatusError("Server busy", request=response.request, response=response)
                        response.raise_for_status()

                        response_data = response.json()
                        content = response_data["choices"][0]['message']['content']

                        logger.info(f"Perplexity 원본 응답 (처음 500자): {content[:500]}")

                        # JSON 마크다운 블록 제거
                        if content.startswith("```json"):
                            content = content.replace("```json", "").replace("```", "").strip()
                            logger.info("JSON 마크다운 블록 제거")

                        # 필드 매핑: Perplexity 응답을 우리 모델에 맞게 변환
                        try:
                            raw_data = json.loads(content)
                            logger.info(f"JSON 파싱 성공, keys: {raw_data.keys()}")

                            # url -> news_url, content -> text 변환
                            if "articles" in raw_data:
                                for article in raw_data["articles"]:
                                    if "url" in article and "news_url" not in article:
                                        article["news_url"] = article.pop("url")
                                    if "content" in article and "text" not in article:
                                        article["text"] = article.pop("content")
                                logger.info(f"필드 매핑 완료: url->news_url, content->text (기사 {len(raw_data['articles'])}개)")

                            # 매핑된 데이터를 JSON 문자열로 변환
                            mapped_content = json.dumps(raw_data)
                        except json.JSONDecodeError as je:
                            logger.error(f"JSON 파싱 실패: {je}")
                            return {
                                "error": "JSON 파싱 실패",
                                "raw_content": content[:1000]
                            }

                        # LangChain JSON Output Parser 사용
                        try:
                            parsed_data = self.json_parser.parse(mapped_content)
                            logger.info(f"LangChain 파싱 성공, 타입: {type(parsed_data)}")
                            # 기사 비어있음 처리
                            try:
                                article_count = len(parsed_data.articles) if hasattr(parsed_data, 'articles') else 0
                                logger.info(f"파싱된 기사 개수: {article_count}")
                                if not parsed_data or article_count == 0:
                                    logger.warning("크롤링 결과에 기사가 없음")
                                    return {
                                        "error": "NO_ARTICLES",
                                        "details": {
                                            "message": "크롤링 결과에 유효한 기사 항목이 없습니다.",
                                        },
                                    }
                            except Exception as check_error:
                                logger.error(f"기사 개수 확인 중 오류: {check_error}")
                                pass
                            # Pydantic 객체를 딕셔너리로 변환
                            if hasattr(parsed_data, 'model_dump'):
                                data_dict = parsed_data.model_dump()
                            elif hasattr(parsed_data, 'dict'):
                                data_dict = parsed_data.dict()
                            else:
                                data_dict = parsed_data
                            return {
                                "service": "perplexity",
                                "status": "success",
                                "data": data_dict
                            }
                        except Exception as e:
                            logger.error(f"LangChain JSON 파싱 실패: {e}")
                            logger.error(f"파싱 실패한 원본 내용 (처음 1000자): {content[:1000]}")
                            # 폴백: 수동 파싱 시도
                            try:
                                logger.info("폴백 파싱 시도 중...")
                                if content.startswith("```json"):
                                    content = content.replace("```json", "").replace("```", "").strip()
                                    logger.info("JSON 마크다운 블록 제거")

                                raw_data = json.loads(content)
                                logger.info(f"JSON 파싱 성공, keys: {raw_data.keys()}")

                                # Perplexity 응답 필드명을 우리 모델에 맞게 변환
                                # url -> news_url, content -> text
                                if "articles" in raw_data:
                                    for article in raw_data["articles"]:
                                        if "url" in article and "news_url" not in article:
                                            article["news_url"] = article.pop("url")
                                        if "content" in article and "text" not in article:
                                            article["text"] = article.pop("content")
                                    logger.info(f"필드 매핑 완료: url->news_url, content->text")

                                news_data = NewsData(**raw_data)
                                logger.info(f"Pydantic 변환 성공, 기사 개수: {len(news_data.articles)}")
                                if len(news_data.articles) == 0:
                                    return {
                                        "error": "NO_ARTICLES",
                                        "details": {
                                            "message": "크롤링 결과에 유효한 기사 항목이 없습니다.",
                                        },
                                    }
                                return {
                                    "service": "perplexity",
                                    "status": "success",
                                    "data": news_data.model_dump()
                                }
                            except Exception as fallback_error:
                                logger.error(f"폴백 파싱도 실패: {fallback_error}")
                                return {
                                    "error": "JSON 파싱 실패",
                                    "raw_content": content,
                                    "langchain_error": str(e),
                                    "fallback_error": str(fallback_error)
                                }
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.HTTPStatusError) as e:
                    logger.warning(f"Perplexity 크롤링 시도 {attempt}/{max_retries} 실패: {type(e).__name__}: {e}")
                    if attempt == max_retries:
                        raise
                    delay = backoff_base ** attempt
                    await asyncio.sleep(delay)
                    
        except FileNotFoundError as e:
            logger.error(f"설정 파일을 찾을 수 없습니다: {e}")
            return {"error": "설정 파일을 찾을 수 없습니다"}
        except httpx.HTTPError as e:
            # HTTP 계열 예외에 대해 최대한 상세한 정보 로깅
            err_type = type(e).__name__
            err_msg = str(e) or repr(e)
            logger.error(f"HTTP 오류: {err_type}: {err_msg}")
            status_code = None
            response_text = None
            request_url = None
            if getattr(e, 'request', None) is not None:
                try:
                    request_url = str(e.request.url)
                    logger.error(f"요청 URL: {request_url}")
                except Exception:
                    pass
            if getattr(e, 'response', None) is not None:
                try:
                    status_code = e.response.status_code
                    response_text = e.response.text
                    logger.error(f"응답 상태 코드: {status_code}")
                    logger.error(f"응답 내용: {response_text}")
                except Exception:
                    pass
            return {
                "error": "HTTP 오류",
                "details": {
                    "type": err_type,
                    "message": err_msg,
                    "status_code": status_code,
                    "request_url": request_url,
                    "response_text": response_text,
                },
            }
        except Exception as e:
            logger.error(f"토픽 크롤링 실패: {e}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return {"error": f"토픽 크롤링 실패: {str(e)}"}
    
    async def search_articles(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        검색 쿼리에 대한 기사들을 검색합니다.
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 개수
        
        Returns:
            검색된 기사 목록
        """
        logger.info(f"기사 검색: {query}")
        
        prompt = f"Search recent articles about: {query}"
        
        return await self.generate(prompt)