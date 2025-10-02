"""
데이터 검증 모듈

수집된 뉴스 데이터의 유효성을 검증하는 클래스
"""

from typing import Dict, List, Any
import re
from urllib.parse import urlparse


class DataValidator:
    """데이터 검증 클래스"""
    
    def __init__(self):
        """DataValidator 초기화"""
        self.min_text_length = 100
        self.max_title_length = 200
        self.max_text_length = 2000
    
    def validate_url(self, url: str) -> bool:
        """
        URL 유효성 검증
        
        Args:
            url (str): 검증할 URL
        
        Returns:
            bool: 유효한 URL인지 여부
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def validate_date(self, date_str: str) -> bool:
        """
        날짜 형식 검증 (YYYY-MM-DD)
        
        Args:
            date_str (str): 검증할 날짜 문자열
        
        Returns:
            bool: 유효한 날짜 형식인지 여부
        """
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(date_pattern, date_str))
    
    def validate_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        개별 기사 데이터 검증 및 정제
        
        Args:
            article (Dict[str, Any]): 검증할 기사 데이터
        
        Returns:
            Dict[str, Any]: 검증 및 정제된 기사 데이터
        """
        errors = []
        
        # URL 검증
        if not self.validate_url(article.get('news_url', '')):
            errors.append("유효하지 않은 URL")
        
        # 제목 검증
        title = article.get('title', '').strip()
        if not title:
            errors.append("제목이 비어있음")
        elif len(title) > self.max_title_length:
            errors.append(f"제목이 너무 깁니다 ({len(title)}/{self.max_title_length})")
        
        # 본문 검증
        text = article.get('text', '').strip()
        if len(text) < self.min_text_length:
            errors.append(f"본문이 너무 짧습니다 ({len(text)}/{self.min_text_length})")
        elif len(text) > self.max_text_length:
            # 본문이 너무 길면 자르기
            text = text[:self.max_text_length] + "..."
            article['text'] = text
        
        # 날짜 검증
        if not self.validate_date(article.get('date', '')):
            errors.append("유효하지 않은 날짜 형식")
        
        # 에러가 있으면 에러 정보 반환
        if errors:
            return {
                "valid": False,
                "errors": errors,
                "original_article": article
            }
        
        # 정제된 데이터 반환
        return {
            "valid": True,
            "article": {
                "news_url": article['news_url'],
                "title": title,
                "text": text,
                "date": article['date']
            }
        }
    
    def validate_news_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        뉴스 데이터 전체 검증 및 정제
        
        Args:
            data (Dict[str, Any]): 검증할 뉴스 데이터
        
        Returns:
            Dict[str, Any]: 검증 및 정제된 뉴스 데이터
        """
        validated_articles = []
        invalid_articles = []
        
        # 카테고리 검증
        category = data.get('category', '').strip()
        if not category:
            return {
                "error": "카테고리가 비어있습니다",
                "original_data": data
            }
        
        # 기사 목록 검증
        articles = data.get('articles', [])
        if not isinstance(articles, list):
            return {
                "error": "기사 목록이 올바르지 않습니다",
                "original_data": data
            }
        
        # 각 기사 검증
        for i, article in enumerate(articles):
            if not isinstance(article, dict):
                invalid_articles.append({
                    "index": i,
                    "error": "기사 데이터 형식이 올바르지 않음"
                })
                continue
            
            validation_result = self.validate_article(article)
            if validation_result["valid"]:
                validated_articles.append(validation_result["article"])
            else:
                invalid_articles.append({
                    "index": i,
                    "errors": validation_result["errors"],
                    "article": article
                })
        
        # 결과 반환
        result = {
            "category": category,
            "articles": validated_articles,
            "total_articles": len(validated_articles),
            "validation_info": {
                "total_input_articles": len(articles),
                "valid_articles": len(validated_articles),
                "invalid_articles": len(invalid_articles),
                "invalid_details": invalid_articles
            }
        }
        
        return result
    
    def get_validation_summary(self, data: Dict[str, Any]) -> str:
        """
        검증 결과 요약 문자열 생성
        
        Args:
            data (Dict[str, Any]): 검증된 데이터
        
        Returns:
            str: 검증 결과 요약
        """
        if "error" in data:
            return f"검증 실패: {data['error']}"
        
        info = data.get("validation_info", {})
        return (
            f"검증 완료: {info.get('valid_articles', 0)}/{info.get('total_input_articles', 0)}개 기사 유효 "
            f"(무효: {info.get('invalid_articles', 0)}개)"
        )
