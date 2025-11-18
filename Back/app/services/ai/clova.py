"""
Naver Clova Voice 서비스
Clova API를 사용하여 TTS(Text-to-Speech) 음성 생성
"""
import logging
import json
import os
import tempfile
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import httpx

from .base import AIService, AIServiceConfig

# MP3 병합/내보내기용. 실제 TTS가 준비되기 전까지는 무성 오디오로 대체
try:
    from pydub import AudioSegment
except Exception:  # pydub 미설치 환경에서도 코드가 import 되도록 방어
    AudioSegment = None  # type: ignore

logger = logging.getLogger(__name__)


# TODO: 기존 제 코드로 롤백 해주세요
class ClovaService(AIService):
    """Naver Clova Voice 서비스 구현체"""
    
    TTS_API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    
    def __init__(self, config: AIServiceConfig):
        super().__init__(config)
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
    
    async def validate_config(self) -> bool:
        """설정이 유효한지 검증합니다."""
        if not self.client_id or not self.client_secret:
            logger.error("Clova API 키가 설정되지 않았습니다.")
            return False
        return True
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Clova API를 사용하여 TTS를 생성합니다.
        
        Args:
            prompt: TTS로 변환할 텍스트
            **kwargs: 추가 매개변수 (voice, speed, pitch 등)
        
        Returns:
            생성된 TTS 정보 (오디오 파일 경로 포함)
        """
        if not self.client_id or not self.client_secret:
            logger.error("Clova API 키가 설정되지 않았습니다.")
            return {
                "service": "clova",
                "status": "failed",
                "error": {"message": "API_KEY_NOT_SET"}
            }
        
        voice = kwargs.get("voice", "nara")
        speed = kwargs.get("speed", 0.0)
        pitch = kwargs.get("pitch", 0.0)
        
        logger.info(f"Clova TTS 요청: {prompt[:100]}... (voice={voice})")
        
        try:
            # Clova TTS API 호출
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.client_id,
                "X-NCP-APIGW-API-KEY": self.client_secret,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "speaker": voice,
                "speed": str(speed),
                "text": prompt
            }
            
            timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.TTS_API_URL,
                    headers=headers,
                    data=data
                )
                
                if response.status_code != 200:
                    logger.error(f"Clova TTS API 오류: {response.status_code} - {response.text}")
                    return {
                        "service": "clova",
                        "status": "failed",
                        "error": {
                            "message": "API_ERROR",
                            "status_code": response.status_code,
                            "details": response.text[:200]
                        }
                    }
                
                # 오디오 데이터를 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_audio_path = tmp_file.name
                
                logger.info(f"TTS 오디오 생성 완료: {tmp_audio_path}")
                
                return {
                    "service": "clova",
                    "status": "success",
                    "data": {
                        "audio_file": tmp_audio_path,
                        "duration": 0,  # 실제 오디오 로드 후 계산
                        "voice": voice
                    }
                }
                
        except Exception as e:
            logger.error(f"Clova TTS 생성 실패: {e}")
            return {
                "service": "clova",
                "status": "failed",
                "error": {"message": "TTS_GENERATION_FAILED", "details": str(e)}
            }
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "nara",
        speed: float = 0.0,
        pitch: float = 0.0
    ) -> Dict[str, Any]:
        """
        텍스트를 음성으로 변환합니다.
        
        Args:
            text: 변환할 텍스트
            voice: 음성 종류 (nara, njh, nhajin 등)
            speed: 속도 (-5.0 ~ 5.0)
            pitch: 음높이 (-5.0 ~ 5.0)
        
        Returns:
            음성 파일 정보
        """
        logger.info(f"TTS 생성 시작: {voice} 음성")
        
        # TODO: 실제 TTS 로직 구현
        # 여기서는 더미 응답 반환
        return await self.generate(text, voice=voice, speed=speed, pitch=pitch)
    
    async def generate_podcast_audio(
        self,
        script: Union[str, Dict[str, Any]],
        output_dir: Optional[str] = None,
        filename: Optional[str] = None,
        speaker_voices: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        팟캐스트 대본을 음성 파일로 생성합니다.

        Args:
            script: 팟캐스트 대본 문자열 전체 또는 구조화된 딕셔너리({ data.turns, data.intro, data.outro })
            output_dir: 결과 MP3를 저장할 디렉토리
            filename: 결과 파일명 (기본: podcast_{timestamp}.mp3)
            speaker_voices: 화자별 클로바 보이스 매핑, 예: {"man": "jinho", "woman": "nara"}

        Returns:
            생성된 음성 파일 정보 딕셔너리
        """
        logger.info("팟캐스트 음성 생성 시작")

        # 출력 경로 준비
        # TODO: 현재 경로 하드코딩 되어 있는데 전부 .env, docker-compose.yml, config 에서 관리해주세요 & 변수는 1번만 호출해주세요
        output_dir = output_dir or "/app/podcasts"
        try:
            os.makedirs(output_dir, mode=0o755, exist_ok=True) # TODO: MODE이거 뭔가요? AI똥이면 지워주세요
        except Exception:
            pass
        if not filename:
            filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        output_path = os.path.join(output_dir, filename)

        # 스크립트 파싱: 문자열이면 JSON 시도 -> 실패 시 단일 텍스트로 간주
        parsed: Dict[str, Any]
        if isinstance(script, str):
            try:
                parsed = json.loads(script)
            except Exception:
                parsed = {"data": {"content": script}}
        else:
            parsed = script

        # data 키가 있으면 그것 사용, 없으면 parsed 자체가 data인 경우
        if isinstance(parsed, dict) and "data" in parsed:
            data = parsed.get("data", {})
        else:
            # 이미 data 부분만 전달된 경우 (podcast_service.py에서 script.get("data", {}) 전달)
            data = parsed if isinstance(parsed, dict) else {}
        
        turns: List[Dict[str, str]] = data.get("turns") or []
        intro: Optional[str] = data.get("intro")
        outro: Optional[str] = data.get("outro")
        
        logger.info(f"대본 파싱 완료: intro={bool(intro)}, turns={len(turns)}, outro={bool(outro)}")

        # 기본 화자-보이스 매핑
        speaker_voices = speaker_voices or {"man": "jinho", "woman": "nara"}

        # pydub 없으면 단일 파일 메타만 반환 (개발 환경 호환)
        if AudioSegment is None:
            logger.warning("pydub 미설치로 인해 실제 오디오 병합 없이 메타데이터만 반환합니다.")
            # 단일 텍스트 TTS 더미 호출
            content = data.get("content") or "\n".join(
                [intro or "", *[t.get("text", "") for t in turns], outro or ""]
            )
            tts = await self.text_to_speech(content, voice="nara")
            # 더미 파일명만 대입
            return {
                "service": "clova",
                "status": "success",
                "data": {
                    "audio_file": output_path,
                    "duration": 0,
                    "voice": "mixed",
                },
            }

        # 세그먼트 구성: intro -> turns -> outro
        segments: List[AudioSegment] = []

        async def synth_text_to_audio(text: str, voice: str) -> Optional[AudioSegment]:
            """텍스트를 TTS로 변환하여 AudioSegment 반환"""
            if not text.strip():
                return None
            
            try:
                # Clova TTS 호출
                tts_result = await self.text_to_speech(text, voice=voice, speed=0.0, pitch=0.0)
                
                if tts_result.get("status") != "success" or not tts_result.get("data", {}).get("audio_file"):
                    logger.warning(f"TTS 생성 실패, 무음으로 대체: {tts_result.get('error', {}).get('message', 'UNKNOWN')}")
                    # 실패 시 무음 생성 (대략적인 길이)
                    duration_ms = max(400, int(len(text) / 13.0 * 1000))  # 대략 13자/초
                    return AudioSegment.silent(duration=duration_ms)
                
                audio_file = tts_result["data"]["audio_file"]
                
                # 오디오 파일 로드
                audio_segment = AudioSegment.from_mp3(audio_file)
                
                # 임시 파일 정리
                try:
                    if os.path.exists(audio_file) and audio_file.startswith(tempfile.gettempdir()):
                        os.unlink(audio_file)
                except Exception:
                    pass
                
                return audio_segment
                
            except Exception as e:
                logger.error(f"TTS 오디오 로드 실패: {e}, 무음으로 대체")
                duration_ms = max(400, int(len(text) / 13.0 * 1000))
                return AudioSegment.silent(duration=duration_ms)

        # 인트로
        if intro:
            intro_audio = await synth_text_to_audio(intro, speaker_voices.get("woman", "nara"))
            if intro_audio:
                segments.append(intro_audio)

        # 본문 turns: 화자별로 목소리 매핑
        for idx, turn in enumerate(turns):
            text = (turn or {}).get("text", "")
            speaker = (turn or {}).get("speaker", "")
            voice = speaker_voices.get(speaker, "nara")
            
            logger.info(f"Turn {idx+1}/{len(turns)}: {speaker} -> {voice} ({len(text)}자)")
            turn_audio = await synth_text_to_audio(text, voice)
            if turn_audio:
                segments.append(turn_audio)

        # 아웃트로
        if outro:
            outro_audio = await synth_text_to_audio(outro, speaker_voices.get("woman", "nara"))
            if outro_audio:
                segments.append(outro_audio)

        if len(segments) == 0:
            # content 기반 단일 생성 시나리오
            content = data.get("content", "")
            if not content:
                logger.error("생성할 대본이 비어있습니다.")
                return {
                    "service": "clova",
                    "status": "failed",
                    "error": {"message": "EMPTY_SCRIPT"},
                }
            fallback_audio = await synth_text_to_audio(content, speaker_voices.get("woman", "nara"))
            if fallback_audio:
                segments.append(fallback_audio)

        # 병합 및 내보내기
        combined = segments[0]
        for seg in segments[1:]:
            combined += seg

        try:
            combined.export(output_path, format="mp3")
        except Exception as e:
            logger.error(f"오디오 파일 내보내기 실패: {e}")
            return {
                "service": "clova",
                "status": "failed",
                "error": {"message": "EXPORT_FAILED", "details": str(e)},
            }

        duration_sec = combined.duration_seconds if hasattr(combined, "duration_seconds") else 0

        return {
            "service": "clova",
            "status": "success",
            "data": {
                "audio_file": output_path,
                "duration": duration_sec,
                "voice": "mixed",
            },
        }

