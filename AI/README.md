# 🎙️ AI 팟캐스트 생성 시스템

특정 카테고리의 기술 뉴스를 수집하여 AI가 생성한 2인 대화형 팟캐스트를 제작하는 시스템입니다.

## 🚀 주요 기능

- **뉴스 수집**: Perplexity API를 통한 실시간 기술 뉴스 수집
- **보고서 생성**: 수집된 뉴스를 종합 보고서로 변환
- **대본 생성**: 2인 대화형 팟캐스트 대본 자동 생성
- **음성 변환**: Google TTS를 통한 팟캐스트 음성 파일 생성
- **워크플로우 관리**: Airflow 통합을 위한 모듈화된 구조

## 📁 프로젝트 구조

```
AI/
├── modules/                          # AI 모듈 패키지
│   ├── data_collection/              # 뉴스 수집 모듈
│   │   ├── news_collector.py         # 뉴스 수집기
│   │   ├── prompt_generator.py       # 프롬프트 생성기
│   │   └── data_validator.py         # 데이터 검증기
│   ├── content_generation/           # 콘텐츠 생성 모듈
│   │   ├── report_generator.py       # 보고서 생성기
│   │   ├── script_generator.py       # 대본 생성기
│   │   └── content_manager.py        # 콘텐츠 관리자
│   ├── audio_processing/             # 오디오 처리 모듈
│   │   ├── tts_processor.py          # TTS 처리기
│   │   └── audio_manager.py          # 오디오 관리자
│   └── ai_workflow.py                # 메인 워크플로우
├── config/                           # 설정 파일
│   ├── company_config.json           # 회사별 설정
│   └── settings.py                   # 시스템 설정
├── tests/                            # 테스트 파일
│   └── test_ai_workflow.py           # 워크플로우 테스트
├── main.py                           # 메인 실행 파일
├── requirements.txt                  # 의존성 목록
└── README.md                         # 프로젝트 문서
```

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
cd /home/smart/capstone/AI
pip install -r requirements.txt
```

### 2. 환경변수 설정

Back 디렉토리의 `.env` 파일을 사용합니다. `Back/env.example`을 참고하여 `.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# 필수 API 키
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# 선택적 API 키 (LLM 기능용)
GOOGLE_API_KEY=your_google_api_key_here

# Google Cloud TTS용 서비스 계정 키 파일 경로
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# AI 팟캐스트 생성 시스템 설정
AI_CONFIG_PATH=../AI/config/company_config.json
AI_OUTPUT_DIR=../AI/data/output
AI_HOST1_NAME=김테크
AI_HOST2_NAME=박AI
```

**참고**: 모든 환경변수는 `Back/.env` 파일 하나에서 관리됩니다.

### 3. Google Cloud 설정 (TTS 사용시)

1. Google Cloud Console에서 프로젝트 생성
2. Text-to-Speech API 활성화
3. 서비스 계정 생성 및 키 파일 다운로드
4. 환경변수에 키 파일 경로 설정

## 🎯 사용 방법

### 기본 사용법

```bash
# 단일 카테고리 팟캐스트 생성
python main.py --category GOOGLE

# 사용자 정의 호스트로 생성
python main.py --category META --host1 "이테크" --host2 "김AI"

# 오디오 없이 대본만 생성
python main.py --category OPENAI --no-audio

# 여러 카테고리 일괄 처리
python main.py --categories GOOGLE META OPENAI
```

### 고급 옵션

```bash
# 검색 기간 설정 (day, week, month)
python main.py --category GOOGLE --search-recency week

# 출력 디렉토리 지정
python main.py --category GOOGLE --output-dir /custom/output/path

# 시스템 상태 확인
python main.py --status

# 테스트 실행
python main.py --test
```

## 📊 지원 카테고리

현재 지원하는 카테고리:
- **GOOGLE**: Google AI, DeepMind, Google Cloud 관련 뉴스
- **META**: Meta AI, Reality Labs, LLaMA 모델 관련 뉴스
- **MICROSOFT**: Azure AI, Copilot, GitHub 관련 뉴스
- **OPENAI**: GPT 모델, ChatGPT, API 업데이트 관련 뉴스
- **ANTHROPIC**: Claude 모델, Constitutional AI 관련 뉴스
- **NVIDIA**: GPU 아키텍처, CUDA, AI 칩 관련 뉴스
- **TESLA**: FSD, 자율주행, 뉴럴 네트워크 관련 뉴스
- **APPLE**: 머신러닝, iOS/macOS AI 기능 관련 뉴스
- **AMAZON**: AWS AI 서비스, Alexa 관련 뉴스

## 🔧 개발자 가이드

### 모듈 구조

각 모듈은 독립적으로 사용할 수 있도록 설계되었습니다:

```python
from modules.data_collection import NewsCollector
from modules.content_generation import ContentManager
from modules.audio_processing import AudioManager

# 뉴스 수집
collector = NewsCollector(api_key="your_api_key")
news_data = collector.collect_news_by_category("GOOGLE")

# 콘텐츠 생성
content_manager = ContentManager()
result = content_manager.run_complete_workflow("news.json", "GOOGLE")

# 오디오 처리
audio_manager = AudioManager()
audio_file = audio_manager.create_audio_workflow("script.md", "GOOGLE")
```

### 테스트 실행

```bash
# 전체 테스트 실행
python -m pytest tests/

# 특정 테스트 실행
python -m pytest tests/test_ai_workflow.py::TestAIWorkflow::test_news_collection

# 커버리지와 함께 실행
python -m pytest tests/ --cov=modules
```

### 설정 커스터마이징

`config/company_config.json` 파일에서 회사별 설정을 수정할 수 있습니다:

```json
{
  "companies": {
    "GOOGLE": {
      "guideline": "Google 관련 기술 뉴스 가이드라인",
      "sources": ["ai.googleblog.com", "research.google"],
      "aliases": ["ALPHABET", "DEEPMIND"]
    }
  }
}
```

## 🚀 Airflow 통합 준비

이 모듈들은 Airflow DAG에서 사용할 수 있도록 설계되었습니다:

```python
from modules.ai_workflow import AIWorkflow

def create_podcast_dag():
    workflow = AIWorkflow(
        perplexity_api_key="your_key",
        google_api_key="your_key"
    )
    
    result = workflow.run_complete_workflow("GOOGLE")
    return result
```

## 📝 로그 및 모니터링

시스템은 다음과 같은 로그 정보를 제공합니다:

- 뉴스 수집 상태
- 콘텐츠 생성 진행률
- 오디오 처리 상태
- 에러 및 경고 메시지

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🆘 문제 해결

### 일반적인 문제

1. **API 키 오류**: 환경변수 설정을 확인하세요
2. **TTS 오류**: Google Cloud 인증을 확인하세요
3. **의존성 오류**: `pip install -r requirements.txt`를 실행하세요

### 지원

문제가 발생하면 GitHub Issues에 보고해주세요.

---

**🎉 AI 팟캐스트 생성 시스템을 사용해보세요!**
