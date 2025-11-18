"""
Google Gemini AI 서비스
LangChain의 ChatGoogleGenerativeAI를 사용하여 문서 생성 및 대본 작성
"""
import logging
import json
from typing import Dict, Any, Optional, List

from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from .base import AIService, AIServiceConfig
from .config_manager import ConfigManager, PromptManager

logger = logging.getLogger(__name__)


class ArticleSection(BaseModel):
    heading: str
    body: str


class ArticleOutput(BaseModel):
    title: str
    summary: str
    sections: List[ArticleSection]
    sources: List[str]
    word_count: int


class ScriptTurn(BaseModel):
    speaker: str  # "man" | "woman" 등 프롬프트에서 지정한 키
    text: str


class ScriptOutput(BaseModel):
    intro: str
    turns: List[ScriptTurn]
    outro: str


class GeminiService(AIService):
    """Google Gemini AI 서비스 구현체 (LangChain 통합)"""
    
    def __init__(self, config: AIServiceConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model_name = config.get("model", "gemini-2.5-pro")
        self.prompt_manager = PromptManager(ConfigManager())
        self.parser = JsonOutputParser(pydantic_object=ArticleOutput)
        # LangChain Chat Model 준비
        self.chat_model = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            api_key=self.api_key,
        )
    
    async def validate_config(self) -> bool:
        """설정이 유효한지 검증합니다."""
        if not self.api_key:
            logger.error("Gemini API 키가 설정되지 않았습니다.")
            return False
        return True
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Gemini API를 사용하여 텍스트를 생성합니다.
        """
        logger.info("Gemini 요청 시작 (LangChain)")
        try:
            # 비구조화 텍스트 응답
            resp = await self.chat_model.ainvoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            return {"service": "gemini", "status": "success", "data": {"content": text, "model": self.model_name}}
        except Exception as e:
            logger.error(f"Gemini 오류: {e}")
            return {"error": f"Gemini 오류: {str(e)}"}
    
    async def generate_article(self, title: str, content: str = "", sources: List[str] = None, articles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perplexity 기사 목록을 바탕으로 구조화된 JSON 기사 생성
        - JsonOutputParser(Pydantic)로 안전 파싱
        """
        logger.info(f"문서 생성 시작: {title}")

        # Perplexity 결과가 구조화되어 있으므로 articles 우선 사용
        articles_list = articles or []
        prompt = self.prompt_manager.create_article_prompt(topic=title, articles=articles_list)

        try:
            # 구조화 출력 체인: 모델에 ArticleOutput 스키마를 부여
            structured_model = self.chat_model.with_structured_output(ArticleOutput)
            parsed = await structured_model.ainvoke(self.prompt_manager.create_article_prompt(topic=title, articles=articles_list))
            data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed

            # 스크립트 생성을 위해 결합된 본문 문자열 제공
            try:
                combined_content = data.get("summary", "") + "\n\n" + "\n\n".join(
                    [s.get("body", "") for s in data.get("sections", [])]
                )
            except Exception:
                combined_content = data.get("summary", "")

            return {
                "service": "gemini",
                "status": "success",
                "data": {**data, "content": combined_content},
            }
        except Exception as e:
            logger.error(f"문서 생성 실패: {e}")
            return {"error": f"문서 생성 실패: {str(e)}"}
    
    async def generate_script(self, article_title: str, article_content: str) -> Dict[str, Any]:
        """
        기사 내용을 바탕으로 팟캐스트 대본을 생성합니다.
        
        Args:
            article_title: 기사 제목
            article_content: 기사 내용
        
        Returns:
            생성된 대본
        """
        logger.info(f"대본 생성 시작: {article_title}")
        try:
            # 스피커는 기본 ["man", "woman"]로 설정. 필요 시 상위에서 전달 가능하도록 오버로드 준비
            speakers = ["man", "woman"]
            prompt = self.prompt_manager.create_script_prompt(article_title, article_content, speakers)

            # 구조화 출력으로 안전하게 JSON 생성
            structured_model = self.chat_model.with_structured_output(ScriptOutput)
            parsed = await structured_model.ainvoke(prompt)
            data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed

            # content 필드에 턴들을 합쳐 스크립트 원문도 제공
            joined = data.get("intro", "") + "\n\n" + "\n\n".join(
                [f"[{t.get('speaker','')}] {t.get('text','')}" for t in data.get("turns", [])]
            ) + "\n\n" + data.get("outro", "")

            return {
                "service": "gemini",
                "status": "success",
                "data": {**data, "content": joined},
            }
        except Exception as e:
            logger.error(f"대본 생성 실패: {e}")
            return {"error": f"대본 생성 실패: {str(e)}"}
    
    async def summarize_text(self, text: str) -> Dict[str, Any]:
        """
        텍스트를 요약합니다.

        Args:
            text: 요약할 텍스트

        Returns:
            요약된 텍스트
        """
        # TODO: 실제 요약 로직 구현
        logger.info(f"텍스트 요약 시작: {text[:50]}...")

        prompt = f"Summarize the following text:\n{text}"

        return await self.generate(prompt)

    async def generate_articles_all_difficulties(
        self,
        title: str,
        raw_content: str
    ) -> Dict[str, Any]:
        """
        크롤링된 원문을 한 번의 Gemini 호출로 3가지 난이도로 모두 생성

        Args:
            title: 기사 제목
            raw_content: 크롤링된 원문

        Returns:
            {
                'summary': '1-2문장 피드용 공통 요약',
                'beginner': { 'content': '쉬운 요약 전문...' },
                'intermediate': { 'content': '중간 요약 전문...' },
                'advanced': { 'content': '고급 요약 전문...' }
            }
        """
        logger.info(f"난이도별 문서 생성 시작: {title}")

        prompt = f"""
다음 기사를 3가지 난이도로 요약해주세요.

**기사 제목**: {title}

**원문**:
{raw_content[:5000]}  # 너무 길면 잘라서 전달

**요구사항**:
1. **summary**: 피드용 1-2문장 짧은 요약 (공통)
2. **beginner**: 초급 - 쉬운 단어, 기술 용어 최소화 및 설명 포함, 비유와 예시 활용
3. **intermediate**: 중급 - 적절한 기술 용어, 개념 설명과 실제 적용 균형
4. **advanced**: 고급 - 전문 용어 적극 사용, 기술적 세부사항 포함, 심층 분석

**출력 형식** (JSON):
{{
    "summary": "1-2문장 피드용 공통 요약",
    "beginner": {{
        "content": "쉬운 요약 전문..."
    }},
    "intermediate": {{
        "content": "중간 요약 전문..."
    }},
    "advanced": {{
        "content": "고급 요약 전문..."
    }}
}}
"""

        try:
            resp = await self.chat_model.ainvoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)

            # JSON 마크다운 블록 제거
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            # JSON 파싱
            data = json.loads(text)

            logger.info(f"난이도별 문서 생성 완료: {title}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"난이도별 문서 JSON 파싱 실패: {e}")
            logger.error(f"응답 내용: {text[:500]}")
            return {"error": f"JSON 파싱 실패: {str(e)}"}
        except Exception as e:
            logger.error(f"난이도별 문서 생성 실패: {e}")
            return {"error": f"난이도별 문서 생성 실패: {str(e)}"}

    async def generate_scripts_all_difficulties(
        self,
        article_title: str,
        article_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        한 번의 Gemini 호출로 3가지 난이도의 대본 모두 생성

        Args:
            article_title: 기사 제목
            article_data: {
                'beginner': { 'content': '...' },
                'intermediate': { 'content': '...' },
                'advanced': { 'content': '...' }
            }

        Returns:
            {
                'beginner': { 'intro': '...', 'turns': [...], 'outro': '...' },
                'intermediate': { 'intro': '...', 'turns': [...], 'outro': '...' },
                'advanced': { 'intro': '...', 'turns': [...], 'outro': '...' }
            }
        """
        logger.info(f"난이도별 대본 생성 시작: {article_title}")

        beginner_content = article_data.get('beginner', {}).get('content', '')
        intermediate_content = article_data.get('intermediate', {}).get('content', '')
        advanced_content = article_data.get('advanced', {}).get('content', '')
        # TODO: 지금 프롬프트 단에서 자료 2000자 제한하고 있어요, 싹다 prompt_templates.json으로 옮겨주세요
        # TODO: langchain output parser 써주세요
        prompt = f"""
다음 3가지 난이도의 문서를 각각 팟캐스트 대본으로 만들어주세요.

**기사 제목**: {article_title}

**초급 문서**:
{beginner_content[:2000]}

**중급 문서**:
{intermediate_content[:2000]}

**고급 문서**:
{advanced_content[:2000]}

**대본 형식**:
- 스피커: "man"과 "woman" 두 명이 대화하는 형식
- 구조: intro (도입부) → turns (대화 턴들) → outro (마무리)
- 각 난이도에 맞게 언어 수준 조정

**출력 형식** (JSON):
{{
    "beginner": {{
        "intro": "도입부...",
        "turns": [
            {{"speaker": "man", "text": "..."}},
            {{"speaker": "woman", "text": "..."}}
        ],
        "outro": "마무리..."
    }},
    "intermediate": {{
        "intro": "도입부...",
        "turns": [...],
        "outro": "마무리..."
    }},
    "advanced": {{
        "intro": "도입부...",
        "turns": [...],
        "outro": "마무리..."
    }}
}}
"""

        try:
            resp = await self.chat_model.ainvoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            # TODO: json output parser로 쓰기 <- 제 기존 코드 봐주세요
            # JSON 마크다운 블록 제거
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            # JSON 파싱
            data = json.loads(text)

            logger.info(f"난이도별 대본 생성 완료: {article_title}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"난이도별 대본 JSON 파싱 실패: {e}")
            logger.error(f"응답 내용: {text[:500]}")
            return {"error": f"JSON 파싱 실패: {str(e)}"}
        except Exception as e:
            logger.error(f"난이도별 대본 생성 실패: {e}")
            return {"error": f"난이도별 대본 생성 실패: {str(e)}"}

