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
    """
    TODO: 주석 좀더 자세히 적어주세요 -> 어떤 데이터가 들어오는지 & 나가는지
    회사 정보 관리 클래스
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    # TODO: 변수명 통일 해주세요!
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
        # TODO: configs/prompt_templates.json에 해당 프롬프트 옮겨주세요
        prompt = f"""
        You are a technology news curator and translator specializing in cutting-edge tech developments.

        Find ALL AVAILABLE latest technology-focused news about "{category}" from recent sources (within the past week). Collect as many relevant articles as possible without any numerical limit.

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
        Return ONLY valid JSON. No explanations or markdown.

        JSON Schema:
        {{
            "articles": [
                {{
                    "url": "article URL",
                    "title": "기사 제목 (반드시 한글로 번역)",
                    "text": "article content",
                    "date": "YYYY-MM-DD"
                }}
            ]
        }}

        TRANSLATION REQUIREMENTS:
        • "title" field MUST be in Korean (한글)
        • Translate English titles to natural Korean
        • Keep technical terms in English if commonly used (e.g., AI, API, GitHub)
        • "text" field can remain in original language

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
    
    def create_script_prompt(self, article_title: str, article_content: str, speakers: List[str] = None, persona_description: str = None) -> str:
        """팟캐스트 대본 생성을 위한 프롬프트 생성 (화자 지정 및 JSON 출력)"""
        speakers = speakers or ["man", "woman"]
        speakers_text = ", ".join(speakers)
        # persona_description이 없으면 템플릿에서 불러와 speakers에 맞게 포매팅
        if persona_description is None:
            templates = self.config_manager.get_prompt_templates()
            persona_tpl = templates.get("script_prompt", {}).get("persona_description", "")
            # 호환 포맷: {speaker0}, {speaker1}
            try:
                persona_description = persona_tpl.replace("{speaker0}", speakers[0]).replace("{speaker1}", speakers[1] if len(speakers) > 1 else speakers[0])
            except Exception:
                persona_description = persona_tpl

        return f"""
        다음 기사 내용을 '재미있는 팟캐스트 토크쇼' 대본으로 재구성해주세요. 반드시 JSON만 출력하세요.

        기사 제목: {article_title}
        기사 내용: {article_content}

        화자 설정:
        - 총 인원: {len(speakers)}명
        - 화자 키: {speakers_text}
        - 화자 역할(페르소나): {persona_description}

        작성 요구사항:
        1.  **톤 앤 매너**: 딱딱한 정보 전달이 아닌, '생동감 있고 재치 있는(witty)' 수다(banter) 형식.
        2.  **도입부 (intro)**: 단순 인사 금지. 청취자의 흥미를 유발할 '강력한 훅(hook)' (예: 충격적인 사실, 공감 가는 질문, 개인적 경험)으로 시작.
        3.  **본문 (turns[])**:
            - 기사 내용을 단순히 요약하지 말고, 화자들이 기사에 대해 '서로의 의견을 묻고, 반응(reaction)하며, 때로는 가벼운 농담이나 개인적인 생각'을 덧붙이도록 구성.
            - '티키타카'가 잘 드러나야 함. 한 사람이 길게 말하기보다 짧은 턴을 주고받는 형식.
            - 어려운 용어는 '반드시' 청취자의 눈높이에서 비유나 예시를 들어 설명.
            - 청취자에게 말을 거는 듯한 '수사적 질문' (예: "다들 이런 경험 없으신가요?") 포함.
        4.  **마무리 (outro)**: 단순 요약/끝인사 금지. 핵심 메시지를 '한 문장으로 요약'하고, 청취자에게 '생각할 거리(food for thought)나 구체적인 행동 제안(Call to Action)' (예: "오늘 집에 가면서 OOO에 대해 한번 생각해보시는 건 어떨까요?")을 던져주세요.
        5.  **분량**: 3-5분 분량 (약 500-800 **단어**).
        6.  **기본 원칙**: 사실 기반, 과장/선정성 금지.

        출력:
        - 오직 JSON만 출력 (설명/마크다운 금지)
        - JSON 구조: {{ "intro": "...", "turns": [{{ "speaker": "...", "script": "..." }}], "outro": "..." }}
        - speaker 값은 [{speakers_text}] 중 하나여야 함.
        """

    def create_article_prompt(self, topic: str, articles: List[Dict[str, Any]]) -> str:
        """Perplexity 수집 기사 목록을 바탕으로 통합 기사 생성을 위한 프롬프트 생성"""
        # 기사 리스트를 프롬프트에 포함하기 위해 간단한 텍스트로 직렬화
        articles_text = "\n".join(
            [
                f"- URL: {a.get('news_url','')}\n  TITLE: {a.get('title','')}\n  DATE: {a.get('date','')}\n  TEXT: {a.get('text','')}"
                for a in (articles or [])
            ]
        )

        return f"""
        너는 최신 기술 뉴스를 한국어로 통합 정리하는 전문 기술 기자야.

        주제: {topic}

        입력 기사들:
        {articles_text}

        작성 지침:
        - 완전한 기사 한 편을 작성하되, 구조화된 JSON으로만 출력해.
        - 과장 없이 정확하게, 기술적 의미와 시사점을 중심으로 작성해.
        - 출처(URL)는 실제 기사 링크만 포함해. 접근 불가/로그인 필요 페이지는 제외.
        - 한국어로 작성하되, 고유 기술 용어는 영어를 유지해.
        - 본문 분량은 800~1200자 수준 권장.

        출력:
        - 오직 JSON만 출력(설명/마크다운 금지)
        """
