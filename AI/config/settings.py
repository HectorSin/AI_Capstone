"""
AI 시스템 설정 파일

환경변수와 기본 설정을 관리하는 모듈
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Back 디렉토리의 .env 파일 로드
back_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Back', '.env')
load_dotenv(back_env_path)


class AISettings:
    """AI 시스템 설정 클래스"""
    
    # API 키 설정
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # 파일 경로 설정
    CONFIG_PATH: str = os.getenv("AI_CONFIG_PATH", os.path.join(os.path.dirname(__file__), "company_config.json"))
    OUTPUT_DIR: str = os.getenv("AI_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "output"))
    TEMP_DIR: str = os.getenv("AI_TEMP_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "temp"))
    
    # 모델 설정
    LLM_MODEL: str = os.getenv("AI_LLM_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("AI_LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("AI_LLM_MAX_TOKENS", "4000"))
    
    # TTS 설정
    TTS_VOICE_MALE: str = os.getenv("AI_TTS_VOICE_MALE", "ko-KR-Standard-A")
    TTS_VOICE_FEMALE: str = os.getenv("AI_TTS_VOICE_FEMALE", "ko-KR-Standard-C")
    TTS_SPEAKING_RATE: float = float(os.getenv("AI_TTS_SPEAKING_RATE", "1.0"))
    TTS_PITCH: float = float(os.getenv("AI_TTS_PITCH", "0.0"))
    
    # 검색 설정
    DEFAULT_SEARCH_RECENCY: str = os.getenv("AI_SEARCH_RECENCY", "week")
    MAX_ARTICLES_PER_CATEGORY: int = int(os.getenv("AI_MAX_ARTICLES", "10"))
    
    # 호스트 설정
    DEFAULT_HOST1: str = os.getenv("AI_HOST1_NAME", "김테크")
    DEFAULT_HOST2: str = os.getenv("AI_HOST2_NAME", "박AI")
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("AI_LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("AI_LOG_FILE")
    
    @classmethod
    def validate_settings(cls) -> dict:
        """
        설정 유효성 검증
        
        Returns:
            dict: 검증 결과
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 필수 API 키 검증
        if not cls.PERPLEXITY_API_KEY:
            validation_result["errors"].append("PERPLEXITY_API_KEY가 설정되지 않았습니다.")
            validation_result["valid"] = False
        
        # 선택적 API 키 경고
        if not cls.GOOGLE_API_KEY:
            validation_result["warnings"].append("GOOGLE_API_KEY가 설정되지 않았습니다. LLM 기능이 제한됩니다.")
        
        if not cls.GOOGLE_APPLICATION_CREDENTIALS:
            validation_result["warnings"].append("GOOGLE_APPLICATION_CREDENTIALS가 설정되지 않았습니다. TTS 기능이 제한됩니다.")
        
        # 파일 경로 검증
        if not os.path.exists(cls.CONFIG_PATH):
            validation_result["errors"].append(f"설정 파일을 찾을 수 없습니다: {cls.CONFIG_PATH}")
            validation_result["valid"] = False
        
        return validation_result
    
    @classmethod
    def get_status_summary(cls) -> str:
        """
        설정 상태 요약 문자열 반환
        
        Returns:
            str: 설정 상태 요약
        """
        validation = cls.validate_settings()
        
        if validation["valid"]:
            status = "설정 완료"
        else:
            status = "설정 오류"
        
        summary = f"AI 시스템 설정 상태: {status}\n"
        
        if validation["errors"]:
            summary += "오류:\n"
            for error in validation["errors"]:
                summary += f"  - {error}\n"
        
        if validation["warnings"]:
            summary += "경고:\n"
            for warning in validation["warnings"]:
                summary += f"  - {warning}\n"
        
        return summary
