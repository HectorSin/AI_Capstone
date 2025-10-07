"""
AI 팟캐스트 생성 시스템 설정

환경변수와 설정을 관리하는 클래스
"""

import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class AISettings:
    """AI 시스템 설정 클래스"""
    
    # API 키 설정
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    NAVER_CLOVA_CLIENT_ID = os.getenv("NAVER_CLOVA_CLIENT_ID", "")
    NAVER_CLOVA_CLIENT_SECRET = os.getenv("NAVER_CLOVA_CLIENT_SECRET", "")
    
    # 파일 경로 설정
    CONFIG_PATH = os.getenv("AI_CONFIG_PATH", "config/company_config.json")
    OUTPUT_DIR = os.getenv("AI_OUTPUT_DIR", "data/output")
    TEMP_DIR = os.getenv("AI_TEMP_DIR", "data/temp")
    
    # AI 모델 설정
    LLM_MODEL = os.getenv("AI_LLM_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE = float(os.getenv("AI_LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("AI_LLM_MAX_TOKENS", "4000"))
    
    # TTS 설정
    TTS_VOICE_MALE = os.getenv("AI_TTS_VOICE_MALE", "jinho")
    TTS_VOICE_FEMALE = os.getenv("AI_TTS_VOICE_FEMALE", "nara")
    
    # 검색 설정
    SEARCH_RECENCY = os.getenv("AI_SEARCH_RECENCY", "week")
    MAX_ARTICLES = int(os.getenv("AI_MAX_ARTICLES", "10"))
    
    # 호스트 설정
    HOST1_NAME = os.getenv("AI_HOST1_NAME", "김테크")
    HOST2_NAME = os.getenv("AI_HOST2_NAME", "박AI")
    
    # 파일 크기 제한
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    @classmethod
    def validate_settings(cls) -> Dict[str, Any]:
        """
        설정 유효성 검증
        
        Returns:
            Dict[str, Any]: 검증 결과
        """
        errors = []
        warnings = []
        
        # 필수 API 키 검증
        if not cls.PERPLEXITY_API_KEY:
            errors.append("PERPLEXITY_API_KEY가 설정되지 않았습니다.")
        
        # 선택적 API 키 경고
        if not cls.GOOGLE_API_KEY:
            warnings.append("GOOGLE_API_KEY가 설정되지 않았습니다. LLM 기능이 제한됩니다.")
        
        if not cls.NAVER_CLOVA_CLIENT_ID or not cls.NAVER_CLOVA_CLIENT_SECRET:
            warnings.append("네이버 클로바 TTS API 키가 설정되지 않았습니다. 오디오 생성이 제한됩니다.")
        
        # 파일 경로 검증
        if not os.path.exists(cls.CONFIG_PATH):
            errors.append(f"설정 파일을 찾을 수 없습니다: {cls.CONFIG_PATH}")
        
        # 출력 디렉토리 생성
        try:
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
        except Exception as e:
            errors.append(f"디렉토리 생성 실패: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def get_required_env_vars(cls) -> List[str]:
        """
        필수 환경변수 목록 반환
        
        Returns:
            List[str]: 필수 환경변수 목록
        """
        return [
            "PERPLEXITY_API_KEY"
        ]
    
    @classmethod
    def get_optional_env_vars(cls) -> List[str]:
        """
        선택적 환경변수 목록 반환
        
        Returns:
            List[str]: 선택적 환경변수 목록
        """
        return [
            "GOOGLE_API_KEY",
            "NAVER_CLOVA_CLIENT_ID",
            "NAVER_CLOVA_CLIENT_SECRET",
            "AI_CONFIG_PATH",
            "AI_OUTPUT_DIR",
            "AI_TEMP_DIR",
            "AI_LLM_MODEL",
            "AI_LLM_TEMPERATURE",
            "AI_LLM_MAX_TOKENS",
            "AI_TTS_VOICE_MALE",
            "AI_TTS_VOICE_FEMALE",
            "AI_SEARCH_RECENCY",
            "AI_MAX_ARTICLES",
            "AI_HOST1_NAME",
            "AI_HOST2_NAME",
            "MAX_FILE_SIZE"
        ]
    
    @classmethod
    def get_all_env_vars(cls) -> Dict[str, str]:
        """
        모든 환경변수 값 반환
        
        Returns:
            Dict[str, str]: 환경변수 딕셔너리
        """
        return {
            "PERPLEXITY_API_KEY": cls.PERPLEXITY_API_KEY,
            "GOOGLE_API_KEY": cls.GOOGLE_API_KEY,
            "NAVER_CLOVA_CLIENT_ID": cls.NAVER_CLOVA_CLIENT_ID,
            "NAVER_CLOVA_CLIENT_SECRET": cls.NAVER_CLOVA_CLIENT_SECRET,
            "AI_CONFIG_PATH": cls.CONFIG_PATH,
            "AI_OUTPUT_DIR": cls.OUTPUT_DIR,
            "AI_TEMP_DIR": cls.TEMP_DIR,
            "AI_LLM_MODEL": cls.LLM_MODEL,
            "AI_LLM_TEMPERATURE": str(cls.LLM_TEMPERATURE),
            "AI_LLM_MAX_TOKENS": str(cls.LLM_MAX_TOKENS),
            "AI_TTS_VOICE_MALE": cls.TTS_VOICE_MALE,
            "AI_TTS_VOICE_FEMALE": cls.TTS_VOICE_FEMALE,
            "AI_SEARCH_RECENCY": cls.SEARCH_RECENCY,
            "AI_MAX_ARTICLES": str(cls.MAX_ARTICLES),
            "AI_HOST1_NAME": cls.HOST1_NAME,
            "AI_HOST2_NAME": cls.HOST2_NAME,
            "MAX_FILE_SIZE": str(cls.MAX_FILE_SIZE)
        }
    
    @classmethod
    def print_settings(cls):
        """설정 정보 출력"""
        print("AI 팟캐스트 생성 시스템 설정")
        print("=" * 50)
        
        all_vars = cls.get_all_env_vars()
        required_vars = cls.get_required_env_vars()
        optional_vars = cls.get_optional_env_vars()
        
        print("필수 설정:")
        for var in required_vars:
            value = all_vars.get(var, "")
            status = "✓" if value else "✗"
            print(f"  {status} {var}: {'설정됨' if value else '미설정'}")
        
        print("\n선택적 설정:")
        for var in optional_vars:
            value = all_vars.get(var, "")
            status = "✓" if value else "○"
            print(f"  {status} {var}: {value if value else '기본값 사용'}")
        
        print("\n파일 경로:")
        print(f"  설정 파일: {cls.CONFIG_PATH}")
        print(f"  출력 디렉토리: {cls.OUTPUT_DIR}")
        print(f"  임시 디렉토리: {cls.TEMP_DIR}")