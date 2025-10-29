"""
AI 서비스 베이스 클래스
모든 AI 서비스의 공통 인터페이스를 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIServiceConfig:
    """AI 서비스 설정을 담는 데이터 클래스"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.extra_config = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """추가 설정값을 가져옵니다."""
        return self.extra_config.get(key, default)


class AIService(ABC):
    """모든 AI 서비스의 베이스 클래스"""
    
    def __init__(self, config: AIServiceConfig):
        self.config = config
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        AI 서비스를 호출하여 결과를 생성합니다.
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 매개변수
        
        Returns:
            생성된 결과 딕셔너리
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """
        설정이 유효한지 검증합니다.
        
        Returns:
            설정 유효 여부
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        서비스 메타데이터를 반환합니다.
        
        Returns:
            서비스 메타데이터
        """
        return {
            "service_name": self.__class__.__name__,
            "config_loaded": self.config.api_key is not None,
        }

