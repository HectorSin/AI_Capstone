"""
뉴스 수집 모듈

Perplexity API를 사용하여 기술 뉴스를 수집하는 클래스
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ValidationError

from .prompt_generator import PromptGenerator
from .data_validator import DataValidator


class Article(BaseModel):
    """기사 데이터 모델"""
    news_url: str
    title: str
    text: str
    date: str


class NewsData(BaseModel):
    """뉴스 데이터 모델"""
    category: str
    articles: List[Article]


class NewsCollector:
    """뉴스 수집 클래스"""
    
    def __init__(self, api_key: str, config_path: str = "config/company_config.json"):
        """
        NewsCollector 초기화
        
        Args:
            api_key (str): Perplexity API 키
            config_path (str): 회사 설정 파일 경로
        """
        if not api_key:
            raise ValueError("Perplexity API 키가 필요합니다.")
        
        self.api_key = api_key
        self.config_path = config_path
        self.prompt_generator = PromptGenerator(config_path)
        self.validator = DataValidator()
        
        # API 엔드포인트 설정
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def collect_news_by_category(self, category: str, search_recency: str = "week") -> Dict[str, Any]:
        """
        지정된 카테고리에 대한 뉴스 기사를 수집하는 메서드
        
        Args:
            category (str): 뉴스 카테고리 (예: "GOOGLE", "META", "OPENAI" 등)
            search_recency (str): 검색 기간 필터 ("day", "week", "month")
        
        Returns:
            Dict[str, Any]: 카테고리와 기사 목록이 포함된 딕셔너리 또는 에러 정보
        """
        try:
            # 회사 정보 및 프롬프트 생성
            company_info = self.prompt_generator.get_company_info(category)
            source_preferences = self.prompt_generator.get_source_preferences()
            prompt = self.prompt_generator.create_tech_news_prompt(
                category, company_info, source_preferences
            )
            
            # API 요청 페이로드 구성
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "search_domain_filter": company_info["sources"],
                "search_recency_filter": search_recency,
                "return_citations": True,
                "max_tokens": 4000
            }
            
            # API 호출
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # 응답에서 컨텐츠 추출
            response_data = response.json()
            content = response_data["choices"][0]['message']['content']
            
            # JSON 파싱 및 검증
            try:
                raw_data = json.loads(content)
                news_data = NewsData(**raw_data)
                validated_data = self.validator.validate_news_data(news_data.model_dump())
                return validated_data
                
            except json.JSONDecodeError:
                return {
                    "error": "JSON 파싱 실패", 
                    "raw_content": content,
                    "category": category
                }
            except ValidationError as ve:
                return {
                    "error": "스키마 검증 실패", 
                    "details": str(ve),
                    "category": category
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API 요청 실패: {str(e)}",
                "category": category
            }
        except KeyError as e:
            return {
                "error": f"응답 형식 오류: {str(e)}",
                "category": category
            }
        except Exception as e:
            return {
                "error": f"예상치 못한 오류: {str(e)}",
                "category": category
            }
    
    def collect_multiple_categories(self, categories: List[str], search_recency: str = "week") -> Dict[str, Any]:
        """
        여러 카테고리의 뉴스를 수집하는 메서드
        
        Args:
            categories (List[str]): 수집할 카테고리 목록
            search_recency (str): 검색 기간 필터
        
        Returns:
            Dict[str, Any]: 카테고리별 뉴스 수집 결과
        """
        results = {}
        
        for category in categories:
            print(f"{category} 카테고리 뉴스 수집 중...")
            result = self.collect_news_by_category(category, search_recency)
            results[category] = result
            
            if "error" in result:
                print(f"{category} 수집 실패: {result['error']}")
            else:
                print(f"{category} 수집 완료: {len(result.get('articles', []))}개 기사")
        
        return results
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "data/output") -> Dict[str, str]:
        """
        수집 결과를 파일로 저장하는 메서드
        
        Args:
            results (Dict[str, Any]): 수집 결과
            output_dir (str): 출력 디렉토리
        
        Returns:
            Dict[str, str]: 저장된 파일 경로들
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = {}
        
        for category, data in results.items():
            if "error" not in data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{category}_news_{timestamp}.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                saved_files[category] = filepath
                print(f"{category} 결과 저장: {filepath}")
        
        return saved_files
