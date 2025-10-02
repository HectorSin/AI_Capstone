"""
오디오 관리 모듈

오디오 파일 생성 및 관리 워크플로우를 담당하는 클래스
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from .tts_processor import TTSProcessor


class AudioManager:
    """오디오 관리 클래스"""
    
    def __init__(self, google_credentials_path: Optional[str] = None):
        """
        AudioManager 초기화
        
        Args:
            google_credentials_path (Optional[str]): Google Cloud 서비스 계정 키 파일 경로
        """
        self.tts_processor = TTSProcessor(google_credentials_path)
    
    def create_audio_workflow(self, script_file_path: str, category: str, 
                            output_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        팟캐스트 대본에서 음성 파일까지 전체 오디오 워크플로우를 실행하는 메서드
        
        Args:
            script_file_path (str): 대본 파일 경로
            category (str): 카테고리명
            output_dir (Optional[str]): 출력 디렉토리 (기본값: 자동 생성)
        
        Returns:
            Optional[Dict[str, Any]]: 생성된 오디오 파일 정보
        """
        print("🎵 오디오 워크플로우 시작!")
        print(f"📂 카테고리: {category}")
        print(f"📄 대본 파일: {script_file_path}")
        print("-" * 50)
        
        # 출력 디렉토리 설정
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            safe_category = category.replace("/", "_").replace(" ", "_")
            output_dir = f"data/output/{safe_category}_{timestamp}/audio"
        
        # 오디오 파일 생성
        print("🎙️ 팟캐스트 음성 파일 생성 중...")
        audio_file = self.tts_processor.generate_podcast_audio(script_file_path, output_dir)
        
        if not audio_file:
            print("❌ 오디오 파일 생성에 실패했습니다.")
            return None
        
        # 파일 정보 수집
        file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
        
        result = {
            "category": category,
            "audio_file": audio_file,
            "file_size_mb": round(file_size, 2),
            "created_at": datetime.now().isoformat(),
            "output_dir": output_dir
        }
        
        print(f"✅ 오디오 워크플로우 완료!")
        print(f"🎵 음성 파일: {audio_file}")
        print(f"📊 파일 크기: {result['file_size_mb']} MB")
        
        return result
    
    def is_tts_available(self) -> bool:
        """
        TTS 기능 사용 가능 여부 확인
        
        Returns:
            bool: TTS 사용 가능 여부
        """
        return self.tts_processor.tts_client is not None
    
    def get_tts_status(self) -> Dict[str, Any]:
        """
        TTS 시스템 상태 정보 반환
        
        Returns:
            Dict[str, Any]: TTS 상태 정보
        """
        return {
            "tts_available": self.is_tts_available(),
            "google_tts_available": self.tts_processor.tts_client is not None,
            "libraries_installed": True  # 이 부분은 실제로는 라이브러리 설치 상태를 확인해야 함
        }
