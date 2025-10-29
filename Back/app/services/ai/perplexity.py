"""
Perplexity AI 서비스
Perplexity API를 사용하여 데이터 크롤링 및 정보 수집
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

from .base import AIService, AIServiceConfig
from .config_manager import ConfigManager, CompanyInfoManager, PromptManager

logger = logging.getLogger(__name__)


class Article:
    """기사 데이터 모델"""
    def __init__(self, news_url: str, title: str, text: str, date: str):
        self.news_url = news_url
        self.title = title
        self.text = text
        self.date = date


class NewsData:
    """뉴스 데이터 모델"""
    def __init__(self, category: str, articles: List[Article]):
        self.category = category
        self.articles = articles


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
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": kwargs.get("model", "sonar"),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", 4000),
            "return_citations": kwargs.get("return_citations", True)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.API_URL, headers=headers, json=payload)
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
                
        except httpx.HTTPError as e:
            logger.error(f"Perplexity API 요청 실패: {e}")
            return {"error": f"API 요청 실패: {str(e)}"}
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
        
        try:
            # 설정 관리자를 통해 회사 정보와 프롬프트 생성
            company_info = self.company_manager.get_company_info(topic)
            source_preferences = self.company_manager.get_source_preferences()
            prompt = self.prompt_manager.create_tech_news_prompt(topic, company_info, source_preferences)
            
            # API 요청 페이로드 구성
            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "search_domain_filter": company_info["sources"],
                "search_recency_filter": "week",  # 일주일 내의 기사만
                "return_citations": True,
                "max_tokens": 4000
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.API_URL, headers=headers, json=payload)
                response.raise_for_status()
                
                response_data = response.json()
                content = response_data["choices"][0]['message']['content']
                
                # JSON 파싱 시도
                try:
                    raw_data = json.loads(content)
                    return {
                        "service": "perplexity",
                        "status": "success",
                        "data": raw_data
                    }
                except json.JSONDecodeError:
                    logger.error("JSON 파싱 실패")
                    return {
                        "error": "JSON 파싱 실패",
                        "raw_content": content
                    }
                    
        except FileNotFoundError as e:
            logger.error(f"설정 파일을 찾을 수 없습니다: {e}")
            return {"error": "설정 파일을 찾을 수 없습니다"}
        except Exception as e:
            logger.error(f"토픽 크롤링 실패: {e}")
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