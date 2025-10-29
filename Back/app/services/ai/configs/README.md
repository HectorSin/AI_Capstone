# AI 서비스 설정 및 프롬프트 관리

## 📁 새로운 폴더 구조

```
app/services/ai/
├── __init__.py              # 모듈 export
├── base.py                  # AI 서비스 베이스 클래스
├── config_manager.py        # 설정 관리 클래스들
├── perplexity.py            # Perplexity 서비스 (실제 API 구현)
├── gemini.py                # Gemini 서비스 (문서/대본 생성)
├── clova.py                 # Clova 서비스 (TTS)
├── README.md                # 개발 가이드
└── configs/                 # 설정 및 프롬프트 폴더
    ├── __init__.py
    ├── company_config.json   # 회사별 설정
    └── prompt_templates.json # 프롬프트 템플릿
```

## 🔧 설정 관리 시스템

### ConfigManager
- 설정 파일 로드 및 관리
- JSON 파일 파싱 및 검증

### CompanyInfoManager  
- 회사별 정보 관리
- 별칭(aliases) 지원
- 소스 선호도 관리

### PromptManager
- 프롬프트 템플릿 관리
- 동적 프롬프트 생성
- 다양한 용도별 프롬프트 제공

## 📋 설정 파일들

### company_config.json
```json
{
  "companies": {
    "GOOGLE": {
      "guideline": "Focus on latest technical developments...",
      "sources": ["research.google", "developers.googleblog.com"],
      "aliases": ["GOOGLE", "ALPHABET"]
    }
  },
  "default_sources": ["techcrunch.com", "arstechnica.com"],
  "source_categories": {
    "official_company": [...],
    "tech_news": [...],
    "academic": [...]
  }
}
```

### prompt_templates.json
```json
{
  "tech_news_prompt": {
    "system_role": "You are a technology news curator...",
    "content_focus": [...],
    "exclusions": [...],
    "quality_standards": [...]
  }
}
```

## 🚀 사용법

```python
from app.services.ai import PerplexityService, AIServiceConfig

# 서비스 초기화
service = PerplexityService(AIServiceConfig(api_key="your_key"))

# 토픽 크롤링
result = await service.crawl_topic("GOOGLE", ["AI", "ML"])
```

## ✨ 개선사항

1. **모듈화**: 설정과 프롬프트를 별도 폴더로 분리
2. **재사용성**: 설정 관리 클래스로 코드 중복 제거
3. **확장성**: 새로운 회사나 프롬프트 쉽게 추가 가능
4. **유지보수**: 설정 변경 시 코드 수정 불필요

## 🔄 다음 단계

1. Gemini, Clova 서비스도 동일한 패턴으로 개선
2. 프롬프트 템플릿 확장
3. 설정 검증 로직 추가
4. 캐싱 시스템 도입
