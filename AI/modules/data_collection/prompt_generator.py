"""
프롬프트 생성 모듈

회사별 설정을 기반으로 기술 뉴스 수집용 프롬프트를 생성하는 클래스
"""

import json
import os
from typing import Dict, List, Any


class PromptGenerator:
    """프롬프트 생성 클래스"""
    
    def __init__(self, config_path: str = "config/company_config.json"):
        """
        PromptGenerator 초기화
        
        Args:
            config_path (str): 회사 설정 파일 경로
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일을 로드하는 메서드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"설정 파일 JSON 파싱 오류: {e}")
    
    def get_company_info(self, category: str) -> Dict[str, Any]:
        """
        카테고리에 맞는 회사 정보 반환 (JSON 파일에서 읽기, 별칭 지원)
        
        Args:
            category (str): 카테고리명
        
        Returns:
            Dict[str, Any]: 회사 정보 (guideline, sources)
        """
        category_upper = category.upper()
        companies = self.config["companies"]
        default_sources = self.config["default_sources"]
        
        # 1. 정확한 회사명 매치 확인
        if category_upper in companies:
            return companies[category_upper]
        
        # 2. 별칭(aliases)으로 매치 확인
        for company, info in companies.items():
            if "aliases" in info and category_upper in info["aliases"]:
                return info
        
        # 3. 여러 회사가 포함된 경우 처리 (부분 매치)
        matched_info = {"guideline": "", "sources": []}
        for company, info in companies.items():
            if company in category_upper:
                matched_info["guideline"] += f"• {company}: {info['guideline']}\n"
                matched_info["sources"].extend(info["sources"])
        
        if matched_info["guideline"]:
            return matched_info
        
        # 4. 매치되는 회사가 없으면 기본값
        return {
            "guideline": f"• {category}: Focus on latest technical developments, research breakthroughs, product releases, and innovation announcements",
            "sources": default_sources
        }
    
    def get_source_preferences(self) -> str:
        """
        소스 선호도 문자열 반환 (JSON 파일에서 읽기)
        
        Returns:
            str: 소스 선호도 정보
        """
        source_categories = self.config.get("source_categories", {})
        
        sources_text = ""
        for i, (category, sources) in enumerate(source_categories.items(), 1):
            # sources가 리스트이므로 문자열로 변환
            sources_str = ", ".join(sources)
            sources_text += f"{i}. {category.replace('_', ' ').title()}: {sources_str}\n"
        
        return sources_text.strip()
    
    def create_tech_news_prompt(self, category: str, company_info: Dict[str, Any], source_preferences: str) -> str:
        """
        기술 뉴스 수집을 위한 프롬프트 생성
        
        Args:
            category (str): 카테고리명
            company_info (Dict[str, Any]): 회사 정보
            source_preferences (str): 소스 선호도 정보
        
        Returns:
            str: 생성된 프롬프트
        """
        
        prompt = f"""
        You are a technology news curator and translator specializing in cutting-edge tech developments.

        Find ALL AVAILABLE latest technology-focused news about "{category}" from recent sources (within 24 hours). Collect as many relevant articles as possible without any numerical limit.

        CONTENT FOCUS:
        • Technical breakthroughs: new AI models, research papers, product launches, API releases
        • Innovation announcements: infrastructure changes, technical partnerships, open-source releases
        • Research developments: academic papers, experimental results, technical demonstrations

        EXCLUSIONS:
        • Business/financial news, stock prices, funding rounds, acquisitions
        • Legal issues, lawsuits, regulatory news, HR/personnel changes
        • Marketing campaigns, user statistics, general company announcements
        • Opinion pieces, analysis without new technical information

        CATEGORY-SPECIFIC GUIDELINES:
        {company_info["guideline"]}

        PREFERRED SOURCES:
        {", ".join(company_info["sources"])}

        SOURCE PREFERENCES:
        {source_preferences}

        URL ACCESSIBILITY REQUIREMENT:
        • ONLY include articles with publicly accessible URLs
        • Exclude paywalled content, subscription-required sites, or restricted access pages
        • Verify that URLs lead to actual article content, not login pages or error pages
        • Prioritize open-access sources and free technical publications

        OUTPUT FORMAT:
        Return ONLY valid JSON with Korean translations:

        {{
            "category": "{category}",
            "articles": [
                {{
                    "news_url": "direct article URL (must be publicly accessible)",
                    "title": "Korean translated title (keep technical terms in English when appropriate)",
                    "text": "Korean summary 200+ characters focusing on technical significance and implications",
                    "date": "actual publication date (YYYY-MM-DD)"
                }}
            ]
        }}

        QUALITY STANDARDS:
        • Collect maximum number of relevant articles available
        • Verify technical accuracy and avoid sensationalized content
        • Prioritize official sources over secondary reporting
        • Double-check URL accessibility before inclusion
        • If no recent technical news found, return empty articles array

        CRITICAL: Output must be valid JSON only. No explanations, markdown, or additional text.
        """
        return prompt
