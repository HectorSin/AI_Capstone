"""
AI 서비스 설정 관리 모듈
"""
import json
import os
from typing import Dict, Any, List


class ConfigManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "configs")
        self.config_dir = config_dir
    
    def load_config(self, filename: str) -> Dict[str, Any]:
        """설정 파일을 로드합니다."""
        file_path = os.path.join(self.config_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {e}")
    
    def get_company_config(self) -> Dict[str, Any]:
        """회사 설정을 반환합니다."""
        return self.load_config("company_config.json")
    
    def get_prompt_templates(self) -> Dict[str, Any]:
        """프롬프트 템플릿을 반환합니다."""
        return self.load_config("prompt_templates.json")


class CompanyInfoManager:
    """회사 정보 관리 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def get_company_info(self, category: str) -> Dict[str, Any]:
        """카테고리에 맞는 회사 정보 반환 (JSON 파일에서 읽기, 별칭 지원)"""
        config = self.config_manager.get_company_config()
        category_upper = category.upper()
        companies = config["companies"]
        default_sources = config["default_sources"]
        
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
        """소스 선호도 문자열 반환 (JSON 파일에서 읽기)"""
        config = self.config_manager.get_company_config()
        source_categories = config.get("source_categories", {})
        
        sources_text = ""
        for i, (category, sources) in enumerate(source_categories.items(), 1):
            # sources가 리스트이므로 문자열로 변환
            sources_str = ", ".join(sources)
            sources_text += f"{i}. {category.replace('_', ' ').title()}: {sources_str}\n"
        
        return sources_text.strip()


class PromptManager:
    """프롬프트 관리 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def create_tech_news_prompt(self, category: str, company_info: Dict[str, Any], source_preferences: str) -> str:
        """기술 뉴스 수집을 위한 프롬프트 생성"""
        
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
    
    def create_summary_prompt(self, topic: str, content: str) -> str:
        """요약을 위한 프롬프트 생성"""
        return f"""
        다음 내용을 한국어로 요약해주세요:
        
        주제: {topic}
        내용: {content}
        
        요약 요구사항:
        - 핵심 내용을 200자 이내로 요약
        - 기술적 의미와 시사점 중심으로 작성
        - 전문 용어는 영어로 유지
        """
    
    def create_script_prompt(self, article_title: str, article_content: str) -> str:
        """팟캐스트 대본 생성을 위한 프롬프트 생성"""
        return f"""
        다음 기사 내용을 바탕으로 팟캐스트 대본을 작성해주세요:
        
        기사 제목: {article_title}
        기사 내용: {article_content}
        
        대본 작성 요구사항:
        - 자연스러운 대화체로 작성
        - 도입부, 본문, 마무리로 구성
        - 청취자가 이해하기 쉽게 설명
        - 약 3-5분 분량 (500-800자)
        - 전문 용어는 쉽게 풀어서 설명
        """
