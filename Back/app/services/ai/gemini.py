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


class DifficultyArticle(BaseModel):
    """난이도별 문서"""
    title: str
    sections: List[ArticleSection]
    sources: List[str]
    word_count: int


class ArticleOutput(BaseModel):
    """세 가지 난이도의 문서를 한 번에 생성"""
    beginner: DifficultyArticle
    intermediate: DifficultyArticle
    advanced: DifficultyArticle


class ScriptTurn(BaseModel):
    speaker: str  # "man" | "woman" 등 프롬프트에서 지정한 키
    text: str


class DifficultyScript(BaseModel):
    """난이도별 대본"""
    intro: str
    turns: List[ScriptTurn]
    outro: str


class ScriptOutput(BaseModel):
    """세 가지 난이도의 대본을 한 번에 생성"""
    beginner: DifficultyScript
    intermediate: DifficultyScript
    advanced: DifficultyScript


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
    
    async def generate_article(self, title: str, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        BeautifulSoup 크롤링 기사 1개를 바탕으로 세 가지 난이도의 문서를 한 번에 생성
        - with_structured_output(ArticleOutput)로 Pydantic 검증

        Args:
            title: 주제/토픽 제목
            article: 크롤링된 기사 1개 {url, title, content, content_length, perplexity_metadata}

        Returns:
            {
                "service": "gemini",
                "status": "success",
                "data": {
                    "beginner": {title, sections, sources, word_count},
                    "intermediate": {title, sections, sources, word_count},
                    "advanced": {title, sections, sources, word_count}
                }
            }
        """
        logger.info(f"난이도별 문서 생성 시작: {title} - {article.get('url', '')}")

        # 단일 기사로 프롬프트 생성
        prompt = self.prompt_manager.create_article_prompt(topic=title, article=article)

        try:
            # 구조화 출력 체인: 모델에 ArticleOutput 스키마 부여 (beginner/intermediate/advanced)
            structured_model = self.chat_model.with_structured_output(ArticleOutput)
            parsed = await structured_model.ainvoke(prompt)
            data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed

            return {
                "service": "gemini",
                "status": "success",
                "data": data,  # {beginner: {...}, intermediate: {...}, advanced: {...}}
            }
        except Exception as e:
            logger.error(f"난이도별 문서 생성 실패: {e}")
            return {"error": f"난이도별 문서 생성 실패: {str(e)}"}
    
    async def generate_script(self, article_title: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        난이도별 문서를 바탕으로 세 가지 난이도의 팟캐스트 대본을 한 번에 생성합니다.

        Args:
            article_title: 기사 제목
            article_data: 난이도별 문서 데이터 {beginner: {...}, intermediate: {...}, advanced: {...}}

        Returns:
            {
                "service": "gemini",
                "status": "success",
                "data": {
                    "beginner": {intro, turns, outro},
                    "intermediate": {intro, turns, outro},
                    "advanced": {intro, turns, outro}
                }
            }
        """
        logger.info(f"난이도별 대본 생성 시작: {article_title}")
        try:
            # 스피커는 기본 ["man", "woman"]로 설정
            speakers = ["man", "woman"]
            prompt = self.prompt_manager.create_script_prompt(article_title, article_data, speakers)

            # 구조화 출력으로 안전하게 JSON 생성 (beginner/intermediate/advanced)
            structured_model = self.chat_model.with_structured_output(ScriptOutput)
            parsed = await structured_model.ainvoke(prompt)
            data = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed

            return {
                "service": "gemini",
                "status": "success",
                "data": data,  # {beginner: {...}, intermediate: {...}, advanced: {...}}
            }
        except Exception as e:
            logger.error(f"난이도별 대본 생성 실패: {e}")
            return {"error": f"난이도별 대본 생성 실패: {str(e)}"}
    
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
