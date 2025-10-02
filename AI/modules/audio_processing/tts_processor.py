"""
TTS (Text-to-Speech) 처리 모듈

텍스트를 음성으로 변환하고 팟캐스트 음성을 생성하는 클래스
네이버 클로바 TTS API를 사용합니다.
"""

import os
import re
import requests
import base64
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from pydub import AudioSegment
    from pydub.effects import normalize
    PYTHON_TTS_AVAILABLE = True
except ImportError:
    PYTHON_TTS_AVAILABLE = False
    print("⚠️ pydub 라이브러리가 설치되지 않았습니다.")


class TTSProcessor:
    """TTS 처리 클래스 - 네이버 클로바 TTS API 사용"""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        TTSProcessor 초기화
        
        Args:
            client_id (str): 네이버 클로바 TTS 클라이언트 ID
            client_secret (str): 네이버 클로바 TTS 클라이언트 시크릿
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
        
        if not client_id or not client_secret:
            print("❌ 네이버 클로바 TTS API 키가 설정되지 않았습니다.")
            self.tts_available = False
        else:
            self.tts_available = True
            print("✅ 네이버 클로바 TTS 클라이언트 초기화 완료")
    
    def text_to_speech(self, text: str, speaker: str = "nara", 
                      output_file: Optional[str] = None) -> Optional[str]:
        """
        텍스트를 음성으로 변환하는 메서드 (네이버 클로바 TTS)
        
        Args:
            text (str): 변환할 텍스트
            speaker (str): 음성 선택 (nara, jinho, shinji, mijin, jihun)
            output_file (Optional[str]): 출력 파일 경로 (기본값: 자동 생성)
        
        Returns:
            Optional[str]: 생성된 음성 파일 경로
        """
        if not self.tts_available:
            print("❌ TTS 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 네이버 클로바 TTS API 요청
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.client_id,
                "X-NCP-APIGW-API-KEY": self.client_secret,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # 요청 데이터
            data = {
                "speaker": speaker,
                "speed": 0,
                "text": text
            }
            
            # API 요청
            response = requests.post(self.api_url, headers=headers, data=data)
            response.raise_for_status()
            
            # 파일 저장
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"temp_audio_{timestamp}.mp3"
            
            with open(output_file, "wb") as out:
                out.write(response.content)
            
            print(f"🎵 음성 파일 생성 완료: {output_file}")
            return output_file
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 네이버 클로바 TTS API 요청 실패: {e}")
            return None
        except Exception as e:
            print(f"❌ TTS 변환 중 오류 발생: {e}")
            return None
    
    def parse_podcast_script(self, script_content: str) -> List[Dict[str, str]]:
        """
        팟캐스트 대본을 파싱하여 대화별로 분리하는 메서드
        
        Args:
            script_content (str): 팟캐스트 대본 내용
        
        Returns:
            List[Dict[str, str]]: 대화 리스트 [{"speaker": "김테크", "text": "대사 내용"}, ...]
        """
        
        # 대본에서 실제 대화 부분만 추출
        lines = script_content.split('\n')
        dialogues = []
        
        # 대화 패턴 찾기 (진행자: 대사)
        dialogue_pattern = r'^(김테크|박AI):\s*(.+)$'
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**') and not line.startswith('---'):
                match = re.match(dialogue_pattern, line)
                if match:
                    speaker = match.group(1)
                    text = match.group(2).strip()
                    if text:
                        dialogues.append({
                            "speaker": speaker,
                            "text": text
                        })
        
        print(f"📝 총 {len(dialogues)}개의 대화를 찾았습니다.")
        return dialogues
    
    def generate_podcast_audio(self, script_file_path: str, output_dir: str) -> Optional[str]:
        """
        팟캐스트 대본을 음성 파일로 변환하는 메서드
        
        Args:
            script_file_path (str): 대본 파일 경로
            output_dir (str): 출력 디렉토리
        
        Returns:
            Optional[str]: 최종 음성 파일 경로
        """
        if not self.tts_available:
            print("❌ TTS 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 대본 파일 읽기
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 대본 파싱
            dialogues = self.parse_podcast_script(script_content)
            
            if not dialogues:
                print("❌ 대화를 찾을 수 없습니다.")
                return None
            
            # 출력 디렉토리 설정
            os.makedirs(output_dir, exist_ok=True)
            
            # 음성 파일들 저장할 리스트
            audio_files = []
            
            # 각 대화를 음성으로 변환
            for i, dialogue in enumerate(dialogues):
                speaker = dialogue["speaker"]
                text = dialogue["text"]
                
                # 진행자별 음성 선택 (네이버 클로바 TTS 음성)
                if speaker == "김테크":
                    voice_speaker = "jinho"  # 남성 음성
                else:  # 박AI
                    voice_speaker = "nara"   # 여성 음성
                
                # 임시 파일명
                temp_file = os.path.join(output_dir, f"temp_{i:03d}_{speaker}.mp3")
                
                print(f"🎤 {speaker}: {text[:50]}...")
                
                # TTS 변환
                audio_file = self.text_to_speech(text, voice_speaker, temp_file)
                if audio_file:
                    audio_files.append(audio_file)
            
            if not audio_files:
                print("❌ 음성 파일 생성에 실패했습니다.")
                return None
            
            # 음성 파일들 병합
            print("🔗 음성 파일들을 병합 중...")
            final_audio = self.merge_audio_files(audio_files, output_dir)
            
            # 임시 파일들 삭제
            for temp_file in audio_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            print(f"✅ 팟캐스트 음성 파일 생성 완료: {final_audio}")
            return final_audio
            
        except Exception as e:
            print(f"❌ 팟캐스트 음성 생성 중 오류 발생: {e}")
            return None
    
    def merge_audio_files(self, audio_files: List[str], output_dir: str) -> Optional[str]:
        """
        여러 음성 파일을 하나로 병합하는 메서드
        
        Args:
            audio_files (List[str]): 병합할 음성 파일 경로들
            output_dir (str): 출력 디렉토리
        
        Returns:
            Optional[str]: 병합된 음성 파일 경로
        """
        if not PYTHON_TTS_AVAILABLE:
            print("❌ pydub 라이브러리가 필요합니다.")
            return None
        
        try:
            # 첫 번째 파일을 기준으로 시작
            combined = AudioSegment.from_mp3(audio_files[0])
            
            # 나머지 파일들을 순차적으로 병합
            for audio_file in audio_files[1:]:
                audio = AudioSegment.from_mp3(audio_file)
                # 0.5초 간격 추가
                combined += AudioSegment.silent(duration=500) + audio
            
            # 음성 정규화
            combined = normalize(combined)
            
            # 최종 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"팟캐스트_{timestamp}.mp3")
            
            combined.export(output_file, format="mp3")
            
            print(f"🎵 음성 파일 병합 완료: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ 음성 파일 병합 중 오류 발생: {e}")
            return None