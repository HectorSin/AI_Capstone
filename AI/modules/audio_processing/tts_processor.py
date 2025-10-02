"""
TTS (Text-to-Speech) 처리 모듈

텍스트를 음성으로 변환하고 팟캐스트 음성을 생성하는 클래스
"""

import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from google.cloud import texttospeech
    from pydub import AudioSegment
    from pydub.effects import normalize
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("Google Cloud TTS 또는 pydub 라이브러리가 설치되지 않았습니다.")


class TTSProcessor:
    """TTS 처리 클래스"""
    
    def __init__(self, google_credentials_path: Optional[str] = None):
        """
        TTSProcessor 초기화
        
        Args:
            google_credentials_path (Optional[str]): Google Cloud 서비스 계정 키 파일 경로
        """
        self.tts_client = None
        
        if GOOGLE_TTS_AVAILABLE:
            if google_credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path
            
            try:
                self.tts_client = texttospeech.TextToSpeechClient()
                print("Google TTS 클라이언트 초기화 완료")
            except Exception as e:
                print(f"Google TTS 클라이언트 초기화 실패: {e}")
                print("Google Cloud 인증을 확인해주세요.")
        else:
            print("TTS 라이브러리가 설치되지 않았습니다.")
    
    def text_to_speech(self, text: str, voice_name: str = "ko-KR-Standard-A", 
                      output_file: Optional[str] = None) -> Optional[str]:
        """
        텍스트를 음성으로 변환하는 메서드
        
        Args:
            text (str): 변환할 텍스트
            voice_name (str): 사용할 음성 (기본값: 한국어 남성)
            output_file (Optional[str]): 출력 파일 경로 (기본값: 자동 생성)
        
        Returns:
            Optional[str]: 생성된 음성 파일 경로
        """
        if not self.tts_client:
            print("TTS 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 음성 설정
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # 음성 선택 (한국어)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.MALE if "A" in voice_name else texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # 오디오 설정
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,  # 말하기 속도
                pitch=0.0,  # 음높이
                volume_gain_db=0.0  # 볼륨
            )
            
            # TTS 요청
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 파일 저장
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"temp_audio_{timestamp}.mp3"
            
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            print(f"음성 파일 생성 완료: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"TTS 변환 중 오류 발생: {e}")
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
        
        print(f"총 {len(dialogues)}개의 대화를 찾았습니다.")
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
        if not self.tts_client:
            print("TTS 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 대본 파일 읽기
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 대본 파싱
            dialogues = self.parse_podcast_script(script_content)
            
            if not dialogues:
                print("대화를 찾을 수 없습니다.")
                return None
            
            # 출력 디렉토리 설정
            os.makedirs(output_dir, exist_ok=True)
            
            # 음성 파일들 저장할 리스트
            audio_files = []
            
            # 각 대화를 음성으로 변환
            for i, dialogue in enumerate(dialogues):
                speaker = dialogue["speaker"]
                text = dialogue["text"]
                
                # 진행자별 음성 선택
                if speaker == "김테크":
                    voice_name = "ko-KR-Standard-A"  # 남성 음성
                else:  # 박AI
                    voice_name = "ko-KR-Standard-C"  # 여성 음성
                
                # 임시 파일명
                temp_file = os.path.join(output_dir, f"temp_{i:03d}_{speaker}.mp3")
                
                print(f"🎤 {speaker}: {text[:50]}...")
                
                # TTS 변환
                audio_file = self.text_to_speech(text, voice_name, temp_file)
                if audio_file:
                    audio_files.append(audio_file)
            
            if not audio_files:
                print("음성 파일 생성에 실패했습니다.")
                return None
            
            # 음성 파일들 병합
            print("음성 파일들을 병합 중...")
            final_audio = self.merge_audio_files(audio_files, output_dir)
            
            # 임시 파일들 삭제
            for temp_file in audio_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            print(f"팟캐스트 음성 파일 생성 완료: {final_audio}")
            return final_audio
            
        except Exception as e:
            print(f"팟캐스트 음성 생성 중 오류 발생: {e}")
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
        if not GOOGLE_TTS_AVAILABLE:
            print("pydub 라이브러리가 필요합니다.")
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
            
            print(f"음성 파일 병합 완료: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"음성 파일 병합 중 오류 발생: {e}")
            return None
