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
