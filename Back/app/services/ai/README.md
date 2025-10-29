# AI 서비스 개발 가이드

## 📁 파일 구조

```
app/services/ai/
├── __init__.py          # 모듈 초기화 및 export
├── base.py              # AI 서비스 베이스 클래스 및 인터페이스
├── perplexity.py        # Perplexity AI 서비스 (데이터 크롤링)
├── gemini.py            # Gemini AI 서비스 (문서/대본 생성)
└── clova.py             # Clova Voice 서비스 (TTS)
```

## 🔧 개발 방향

### 1. Perplexity 서비스 (`perplexity.py`)

**목적**: 최신 정보 수집 및 데이터 크롤링

**TODO 구현 항목**:
- `generate()`: Perplexity API 실제 호출
- `crawl_topic()`: 토픽별 정보 크롤링 로직
- `search_articles()`: 최신 기사 검색 로직

**API 문서**: https://docs.perplexity.ai/

```python
# API 호출 예시
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama-3-sonar-huge-128k-online",
    "messages": [
        {"role": "system", "content": "...ших},
        {"role": "user", "content": prompt}
    ]
}
```

### 2. Gemini 서비스 (`gemini.py`)

**목적**: 문서 생성, 대본 작성, 요약

**TODO 구현 항목**:
- `generate()`: Gemini API 실제 호출
- `generate_article()`: 문서 생성 로직
- `generate_script()`: 팟캐스트 대본 생성 로직
- `summarize_text()`: 텍스트 요약 로직

**API 문서**: https://ai.google.dev/docs

```python
# API 호출 예시
import google.generativeai as genai

genai.configure(api_key=self.api_key)
model = genai.GenerativeModel(self.model)
response = model.generate_content(prompt)
```

### 3. Clova 서비스 (`clova.py`)

**목적**: 텍스트를 음성으로 변환 (TTS)

**TODO 구현 항목**:
- `generate()`: Clova TTS API 실제 호출
- `text_to_speech()`: TTS 변환 로직
- `generate_podcast_audio()`: 팟캐스트 음성 생성 로직

**API 문서**: https://www.ncloud.com/product/aiService/clovaVoice

```python
# API 호출 예시
headers = {
    "X-NCP-APIGW-API-KEY-ID": self.client_id,
    "X-NCP-APIGW-API-KEY": self.client_secret,
    "Content-Type": "application/x-www-form-urlencoded"
}

data = {
    "speaker": voice,
    "speed": speed,
    "text": text
}

response = requests.post(TTS_API_URL, headers=headers, data=data)
```

## 🔄 통합 서비스

`podcast_service.py`에서 모든 AI 서비스를 통합하여 팟캐스트를 생성합니다.

**프로세스**:
1. Perplexity로 주제 관련 데이터 크롤링
2. Gemini로 문서 생성
3. Gemini로 팟캐스트 대본 생성
4. Clova로 TTS 음성 생성

## 🚀 다음 단계

1. 각 AI 서비스의 TODO 항목 구현
2. 에러 핸들링 및 재시도 로직 추가
3. 응답 캐싱 구현 (선택사항)
4. 로깅 및 모니터링 강화
5. 단위 테스트 작성

## 💡 개선 아이디어

- 병렬 처리: 문서와 대본을 병렬로 생성
- 세그먼트 처리: 긴 대본을 여러 세그먼트로 나누어 TTS 처리
- 음성 효과: 백그라운드 음악, 효과음 추가
- 사용자 커스터마이징: 음성 종류, 속도 등 사용자 선택 가능

